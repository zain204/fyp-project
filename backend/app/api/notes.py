from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.evidence import _get_case_for_user
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.investigation_notes import InvestigationNote
from app.models.user import User, UserRole
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate

router = APIRouter()


# ---------------- Helpers ----------------
def _log(
    db: Session,
    user: User,
    action: str,
    note_id: Optional[int],
    request: Request,
    details: Optional[str] = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            resource_type="note",
            resource_id=note_id,
            details=details,
            ip_address=request.client.host if request.client else "unknown",
        )
    )


def _to_out(note: InvestigationNote) -> NoteOut:
    return NoteOut(
        id=note.id,
        case_id=note.case_id,
        author_id=note.author_id,
        author_name=note.author.full_name if note.author else "Unknown",
        content=note.content,
        created_at=note.created_at,
    )


def _get_note_or_404(db: Session, note_id: int, user: User) -> InvestigationNote:
    note = (
        db.query(InvestigationNote).filter(InvestigationNote.id == note_id).first()
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    _get_case_for_user(db, note.case_id, user)  # access check
    return note


# ---------------- Endpoints ----------------
@router.post(
    "/case/{case_id}", response_model=NoteOut, status_code=status.HTTP_201_CREATED
)
def create_note(
    case_id: int,
    data: NoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_case_for_user(db, case_id, current_user)

    note = InvestigationNote(
        case_id=case_id,
        author_id=current_user.id,
        content=data.content,
    )
    db.add(note)
    db.flush()
    _log(db, current_user, "CREATE_NOTE", note.id, request, f"case={case_id}")
    db.commit()
    db.refresh(note)
    return _to_out(note)


@router.get("/case/{case_id}", response_model=List[NoteOut])
def list_notes(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_case_for_user(db, case_id, current_user)
    notes = (
        db.query(InvestigationNote)
        .filter(InvestigationNote.case_id == case_id)
        .order_by(InvestigationNote.created_at.asc())
        .all()
    )
    return [_to_out(n) for n in notes]


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    data: NoteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = _get_note_or_404(db, note_id, current_user)

    if note.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author can edit this note",
        )

    old_content = note.content
    note.content = data.content
    # The previous text is kept in the audit log so edits stay traceable
    _log(
        db,
        current_user,
        "UPDATE_NOTE",
        note.id,
        request,
        f"previous content: {old_content[:300]}",
    )
    db.commit()
    db.refresh(note)
    return _to_out(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = _get_note_or_404(db, note_id, current_user)

    if note.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or an admin can delete this note",
        )

    _log(
        db,
        current_user,
        "DELETE_NOTE",
        note.id,
        request,
        f"deleted content: {note.content[:300]}",
    )
    db.delete(note)
    db.commit()
    return None