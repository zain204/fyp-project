import hashlib
import hmac
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MB


def sha256_of_file(file_path: str | Path) -> str:
    """File ka SHA-256 hash (badi files bhi chunk me parh ke, memory nahi bharti)."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hashes_match(hash_a: str, hash_b: str) -> bool:
    """Constant-time comparison."""
    return hmac.compare_digest(hash_a.lower(), hash_b.lower())