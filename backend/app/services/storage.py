import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings

CHUNK_SIZE = 1024 * 1024  # 1 MB


@dataclass
class SavedFile:
    original_filename: str
    stored_filename: str
    relative_path: str  # UPLOAD_DIR ke andar ka path, e.g. case_1/abc123.pdf
    size: int
    sha256: str


def _upload_root() -> Path:
    root = Path(settings.UPLOAD_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_path(relative_path: str) -> Path:
    """Relative path ko asli path me badalta hai (upload folder se bahar nahi jane deta)."""
    root = _upload_root()
    full = (root / relative_path).resolve()
    if root not in full.parents and full != root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path"
        )
    return full


def save_upload(file: UploadFile, case_id: int) -> SavedFile:
    """
    File ko disk pe save karta hai aur saath hi SHA-256 hash nikalta hai.
    Hash upload ke dauran hi bante hain, is liye file do dafa nahi parhni parti.
    """
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    original = Path(file.filename or "unnamed").name  # path tricks se bachao
    extension = Path(original).suffix.lower()[:20]
    stored_name = f"{uuid.uuid4().hex}{extension}"

    case_folder = f"case_{case_id}"
    folder = _upload_root() / case_folder
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / stored_name

    hasher = hashlib.sha256()
    size = 0

    try:
        with open(destination, "wb") as out:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File {settings.MAX_UPLOAD_SIZE_MB} MB se badi hai",
                    )
                hasher.update(chunk)
                out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File khali hai"
        )

    return SavedFile(
        original_filename=original,
        stored_filename=stored_name,
        relative_path=f"{case_folder}/{stored_name}",
        size=size,
        sha256=hasher.hexdigest(),
    )


def delete_file(relative_path: str) -> None:
    try:
        resolve_path(relative_path).unlink(missing_ok=True)
    except HTTPException:
        pass