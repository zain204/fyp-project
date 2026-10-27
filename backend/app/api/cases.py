from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.case import Case, CasePriority, CaseStatus
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate, CaseOut, CaseStats, CaseUpdate

router = APIRouter()


# ---------------- Helpers ----------------
def _log(
    db: Session,
    user: User,
    action: str,
    case_id: Optional[int],
    request: Request,
    details: Optional[str] = None,
):
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            resource_type="case",
            resource_id=case_id,
            details=details,
            ip_address=request.client.host if request.client else "unknown",
        )
    )
    db.commit()


def _generate_case_number(db: Session) -> str:
    """CASE-2026-001, CASE-2026-002 ... (har saal naye sirey se)."""
    year = datetime.now(timezone.utc).year
    prefix = f"CASE-{year}-"
    count = db.query(Case).filter(Case.case_number.like(f"{prefix}%")).count()
    number = count + 1
    while db.query(Case).filter(Case.case_number == f"{prefix}{number:03d}").first():
        number += 1
    return f"{prefix}{number:03d}"


def _get_case_or_404(db: Session, case_id: int, user: User) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case nahi mila"
        )
    # Investigator sirf apna case dekh sakta hai, admin sab
    if user.role != UserRole.admin and case.investigator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye case aap ko assign nahi hai",
        )
    return case


def _check_investigator_exists(db: Session, investigator_id: int) -> User:
    target = db.query(User).filter(User.id == investigator_id).first()
    if not target or not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ye investigator maujood nahi hai",
        )
    return target


# ---------------- Endpoints ----------------
@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    data: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investigator_id = current_user.id

    # Admin kisi aur ko case assign kar sakta hai
    if data.investigator_id is not None and current_user.role == UserRole.admin:
        _check_investigator_exists(db, data.investigator_id)
        investigator_id = data.investigator_id

    case = Case(
        case_number=_generate_case_number(db),
        title=data.title.strip(),
        description=data.description,
        crime_type=data.crime_type,
        priority=data.priority,
        investigator_id=investigator_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    _log(db, current_user, "CREATE_CASE", case.id, request, case.case_number)
    return case


@router.get("/", response_model=List[CaseOut])
def list_cases(
    status_filter: Optional[CaseStatus] = Query(default=None, alias="status"),
    priority: Optional[CasePriority] = None,
    search: Optional[str] = Query(default=None, description="title ya case number me dhoondo"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Case)

    if current_user.role != UserRole.admin:
        query = query.filter(Case.investigator_id == current_user.id)

    if status_filter:
        query = query.filter(Case.status == status_filter)
    if priority:
        query = query.filter(Case.priority == priority)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            or_(Case.title.ilike(like), Case.case_number.ilike(like))
        )

    return query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()


# NOTE: /stats/summary ko /{case_id} se pehle rakhna zaroori hai
@router.get("/stats/summary", response_model=CaseStats)
def case_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = db.query(Case)
    if current_user.role != UserRole.admin:
        base = base.filter(Case.investigator_id == current_user.id)

    def count(case_status: CaseStatus) -> int:
        return base.filter(Case.status == case_status).count()

    return CaseStats(
        total=base.count(),
        open=count(CaseStatus.open),
        in_progress=count(CaseStatus.in_progress),
        under_review=count(CaseStatus.under_review),
        closed=count(CaseStatus.closed),
    )


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_case_or_404(db, case_id, current_user)


@router.put("/{case_id}", response_model=CaseOut)
def update_case(
    case_id: int,
    data: CaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = _get_case_or_404(db, case_id, current_user)
    changes = data.model_dump(exclude_unset=True)

    # Case dobara assign karna sirf admin ka kaam hai
    if "investigator_id" in changes:
        if current_user.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Case assign sirf admin kar sakta hai",
            )
        if changes["investigator_id"] is not None:
            _check_investigator_exists(db, changes["investigator_id"])
        else:
            changes.pop("investigator_id")

    # Ye fields khali (None) nahi ho sakte
    for field in ("title", "status", "priority"):
        if field in changes and changes[field] is None:
            changes.pop(field)

    for field, value in changes.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)

    _log(db, current_user, "UPDATE_CASE", case.id, request, ", ".join(changes.keys()))
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case nahi mila"
        )

    number = case.case_number
    db.delete(case)
    db.commit()

    _log(db, admin, "DELETE_CASE", case_id, request, number)
    return None