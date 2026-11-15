from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.api.evidence import _get_case_for_user
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportOut
from app.services.hashing import sha256_of_file
from app.services.report_service import (
    build_report_pdf,
    build_summary,
    collect_report_data,
)
from app.services.storage import delete_file, resolve_path

router = APIRouter()


# ---------------- Helpers ----------------
def _log(
    db: Session,
    user: User,
    action: str,
    report_id: Optional[int],
    request: Request,
    details: Optional[str] = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            resource_type="report",
            resource_id=report_id,
            details=details,
            ip_address=request.client.host if request.client else "unknown",
        )
    )


def _get_report_for_user(db: Session, report_id: int, user: User) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    _get_case_for_user(db, report.case_id, user)  # access check
    return report


# ---------------- Endpoints ----------------
@router.post(
    "/case/{case_id}", response_model=ReportOut, status_code=status.HTTP_201_CREATED
)
def generate_report(
    case_id: int,
    request: Request,
    data: Optional[ReportCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a PDF investigation report for a case."""
    case: Case = _get_case_for_user(db, case_id, current_user)

    report_data = collect_report_data(db, case)

    title = (
        data.title.strip()
        if data and data.title and data.title.strip()
        else f"Investigation Report - {case.case_number}"
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    relative_path = f"reports/case_{case.id}/{case.case_number}_{stamp}.pdf"
    output_path = resolve_path(relative_path)

    try:
        build_report_pdf(
            report_data,
            output_path,
            title,
            current_user.full_name,
            current_user.role.value,
        )
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate the PDF report",
        ) from exc

    pdf_hash = sha256_of_file(output_path)
    summary = f"{build_summary(report_data)} PDF SHA-256: {pdf_hash}"

    try:
        report = Report(
            case_id=case.id,
            generated_by=current_user.id,
            title=title,
            summary=summary,
            file_path=relative_path,
        )
        db.add(report)
        db.flush()
        _log(
            db,
            current_user,
            "GENERATE_REPORT",
            report.id,
            request,
            f"case={case.case_number}",
        )
        db.commit()
        db.refresh(report)
    except Exception:
        db.rollback()
        delete_file(relative_path)
        raise

    return report


@router.get("/case/{case_id}", response_model=List[ReportOut])
def list_case_reports(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_case_for_user(db, case_id, current_user)
    return (
        db.query(Report)
        .filter(Report.case_id == case_id)
        .order_by(Report.generated_at.desc())
        .all()
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_report_for_user(db, report_id, current_user)


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _get_report_for_user(db, report_id, current_user)

    if not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This report has no PDF file",
        )

    path = resolve_path(report.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The report PDF is missing from the server",
        )

    _log(db, current_user, "DOWNLOAD_REPORT", report.id, request)
    db.commit()

    case = db.query(Case).filter(Case.id == report.case_id).first()
    case_number = case.case_number if case else f"case-{report.case_id}"

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"{case_number}_report_{report.id}.pdf",
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    stored_path = report.file_path
    _log(db, admin, "DELETE_REPORT", report.id, request, report.title)
    db.delete(report)
    db.commit()

    if stored_path:
        delete_file(stored_path)
    return None