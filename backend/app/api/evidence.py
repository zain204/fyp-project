from datetime import datetime, timezone
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.custody_record import CustodyRecord
from app.models.evidence import Evidence
from app.models.user import User, UserRole
from app.schemas.evidence import CustodyRecordOut, EvidenceOut, VerifyResult
from app.services.blockchain_service import (
    add_evidence_block,
    get_block_for_evidence,
    verify_chain,
)
from app.services.hashing import hashes_match, sha256_of_file
from app.services.storage import delete_file, resolve_path, save_upload

router = APIRouter()


# ---------------- Helpers ----------------
def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _add_custody(
    db: Session,
    evidence_id: int,
    user: User,
    action: str,
    request: Request,
    notes: Optional[str] = None,
) -> None:
    db.add(
        CustodyRecord(
            evidence_id=evidence_id,
            user_id=user.id,
            action=action,
            notes=notes,
            ip_address=_ip(request),
        )
    )


def _add_audit(
    db: Session,
    user: User,
    action: str,
    evidence_id: Optional[int],
    request: Request,
    details: Optional[str] = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            resource_type="evidence",
            resource_id=evidence_id,
            details=details,
            ip_address=_ip(request),
        )
    )


def _get_case_for_user(db: Session, case_id: int, user: User) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found"
        )
    if user.role != UserRole.admin and case.investigator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This case is not assigned to you",
        )
    return case


def _get_evidence_for_user(db: Session, evidence_id: int, user: User) -> Evidence:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )
    _get_case_for_user(db, evidence.case_id, user)  # access check
    return evidence


# ---------------- Endpoints ----------------
@router.post("/upload", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    request: Request,
    case_id: int = Form(...),
    description: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload: save file -> SHA-256 hash -> DB record -> blockchain block -> chain of custody."""
    _get_case_for_user(db, case_id, current_user)

    saved = save_upload(file, case_id)

    try:
        evidence = Evidence(
            case_id=case_id,
            uploaded_by=current_user.id,
            original_filename=saved.original_filename,
            stored_filename=saved.stored_filename,
            file_path=saved.relative_path,
            file_type=file.content_type,
            file_size=saved.size,
            description=description,
            sha256_hash=saved.sha256,
            is_verified=True,
        )
        db.add(evidence)
        db.flush()  # generates evidence.id

        block = add_evidence_block(db, evidence)

        _add_custody(
            db,
            evidence.id,
            current_user,
            "uploaded",
            request,
            f"SHA-256: {saved.sha256} | Blockchain block: {block.block_index}",
        )
        _add_audit(
            db,
            current_user,
            "UPLOAD_EVIDENCE",
            evidence.id,
            request,
            f"case={case_id}, file={saved.original_filename}, block={block.block_index}",
        )
        db.commit()
        db.refresh(evidence)
    except Exception:
        db.rollback()
        delete_file(saved.relative_path)
        raise

    return evidence


@router.get("/case/{case_id}", response_model=List[EvidenceOut])
def list_case_evidence(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_case_for_user(db, case_id, current_user)
    return (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.uploaded_at.desc())
        .all()
    )


@router.get("/{evidence_id}", response_model=EvidenceOut)
def get_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = _get_evidence_for_user(db, evidence_id, current_user)
    _add_custody(db, evidence.id, current_user, "viewed", request)
    db.commit()
    return evidence


@router.get("/{evidence_id}/custody", response_model=List[CustodyRecordOut])
def get_custody_chain(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = _get_evidence_for_user(db, evidence_id, current_user)
    return (
        db.query(CustodyRecord)
        .filter(CustodyRecord.evidence_id == evidence.id)
        .order_by(CustodyRecord.timestamp.asc())
        .all()
    )


@router.get("/{evidence_id}/download")
def download_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = _get_evidence_for_user(db, evidence_id, current_user)

    path = resolve_path(evidence.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The evidence file is missing from the server",
        )

    _add_custody(db, evidence.id, current_user, "downloaded", request)
    _add_audit(db, current_user, "DOWNLOAD_EVIDENCE", evidence.id, request)
    db.commit()

    return FileResponse(
        path=str(path),
        filename=evidence.original_filename,
        media_type=evidence.file_type or "application/octet-stream",
    )


@router.post("/{evidence_id}/verify", response_model=VerifyResult)
def verify_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recomputes the file hash and checks it against:
    1) the hash stored in the database at upload time
    2) the hash stored in the blockchain ledger
    3) the integrity of the whole chain
    """
    evidence = _get_evidence_for_user(db, evidence_id, current_user)
    now = datetime.now(timezone.utc)

    block = get_block_for_evidence(db, evidence.id)
    ledger_hash = block.evidence_hash if block else None
    block_index = block.block_index if block else None

    chain = verify_chain(db)
    path = resolve_path(evidence.file_path)

    # ---- File is missing ----
    if not path.exists():
        evidence.is_verified = False
        _add_custody(
            db, evidence.id, current_user, "verified", request, "RESULT: MISSING"
        )
        _add_audit(db, current_user, "VERIFY_EVIDENCE", evidence.id, request, "missing")
        db.commit()
        return VerifyResult(
            evidence_id=evidence.id,
            original_hash=evidence.sha256_hash,
            current_hash=None,
            blockchain_hash=ledger_hash,
            block_index=block_index,
            blockchain_verified=None if block is None else False,
            chain_valid=chain.is_valid,
            is_intact=False,
            status="missing",
            message="The evidence file is missing from the server",
            verified_at=now,
        )

    current_hash = sha256_of_file(path)
    db_match = hashes_match(current_hash, evidence.sha256_hash)
    ledger_match = hashes_match(current_hash, ledger_hash) if ledger_hash else None

    intact = db_match and ledger_match is not False

    if not intact:
        result_status = "tampered"
        message = "WARNING: This evidence has been modified, the hash does not match"
    elif not chain.is_valid:
        intact = False
        result_status = "ledger_broken"
        message = f"The file is original but the blockchain is broken: {chain.message}"
    else:
        result_status = "intact"
        message = "Evidence is original, the database and blockchain hashes both match"

    evidence.is_verified = intact
    _add_custody(
        db,
        evidence.id,
        current_user,
        "verified",
        request,
        f"RESULT: {result_status.upper()}",
    )
    _add_audit(
        db, current_user, "VERIFY_EVIDENCE", evidence.id, request, result_status
    )
    db.commit()

    return VerifyResult(
        evidence_id=evidence.id,
        original_hash=evidence.sha256_hash,
        current_hash=current_hash,
        blockchain_hash=ledger_hash,
        block_index=block_index,
        blockchain_verified=ledger_match,
        chain_valid=chain.is_valid,
        is_intact=intact,
        status=result_status,
        message=message,
        verified_at=now,
    )


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin only. The blockchain record stays in the ledger even after deletion."""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )

    stored_path = evidence.file_path
    name = evidence.original_filename

    db.delete(evidence)
    _add_audit(db, admin, "DELETE_EVIDENCE", evidence_id, request, name)
    db.commit()

    delete_file(stored_path)
    return None