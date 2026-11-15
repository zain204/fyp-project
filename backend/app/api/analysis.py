from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.evidence import (
    _add_audit,
    _add_custody,
    _get_case_for_user,
    _get_evidence_for_user,
)
from app.database.connection import get_db
from app.models.ai_finding import AIFinding
from app.models.evidence import Evidence
from app.models.evidence_features import EvidenceFeatures
from app.models.user import User
from app.schemas.analysis import (
    AnalysisResult,
    CaseAnalysisSummary,
    EvidenceRiskItem,
    FindingOut,
)
from app.services.ai_analysis import ENGINE_NAME, analyze_file, compute_risk
from app.services.hashing import hashes_match, sha256_of_file
from app.services.storage import resolve_path

router = APIRouter()


# ---------------- Helpers ----------------
def _build_result(
    evidence: Evidence,
    features_row: EvidenceFeatures,
    findings: List[AIFinding],
) -> AnalysisResult:
    risk_score, risk_level = compute_risk([f.confidence_score for f in findings])
    features = features_row.features or {}

    if findings:
        summary = (
            f"{len(findings)} suspicious indicator(s) detected. "
            "Review the findings below."
        )
    else:
        summary = (
            "No suspicious indicators were detected by the automated checks. "
            "This does not prove the evidence is harmless."
        )

    preview = (features_row.extracted_text or "")[:1000] or None

    return AnalysisResult(
        evidence_id=evidence.id,
        engine=features.get("analysis_engine", ENGINE_NAME),
        risk_score=risk_score,
        risk_level=risk_level,
        summary=summary,
        findings=[FindingOut.model_validate(f) for f in findings],
        features=features,
        extracted_text_preview=preview,
        analyzed_at=features_row.extracted_at,
    )


def _sorted_findings(db: Session, evidence_id: int) -> List[AIFinding]:
    return (
        db.query(AIFinding)
        .filter(AIFinding.evidence_id == evidence_id)
        .order_by(AIFinding.confidence_score.desc())
        .all()
    )


# ---------------- Endpoints ----------------
@router.post("/evidence/{evidence_id}", response_model=AnalysisResult)
def analyze_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Runs the automated analysis on an evidence file.
    The file hash is verified first; a tampered file is never analyzed.
    Running it again replaces the previous findings.
    """
    evidence = _get_evidence_for_user(db, evidence_id, current_user)

    path = resolve_path(evidence.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The evidence file is missing from the server",
        )

    # Integrity check before analysis
    current_hash = sha256_of_file(path)
    if not hashes_match(current_hash, evidence.sha256_hash):
        evidence.is_verified = False
        _add_custody(
            db,
            evidence.id,
            current_user,
            "verified",
            request,
            "RESULT: TAMPERED (analysis blocked)",
        )
        _add_audit(
            db, current_user, "ANALYZE_BLOCKED", evidence.id, request, "hash mismatch"
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Integrity check failed: the evidence file does not match its stored hash. Analysis was blocked.",
        )

    try:
        output = analyze_file(path, evidence.original_filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Automated analysis failed for this file",
        ) from exc

    now = datetime.now(timezone.utc)

    # Replace old results
    db.query(AIFinding).filter(AIFinding.evidence_id == evidence.id).delete(
        synchronize_session=False
    )

    features_row = (
        db.query(EvidenceFeatures)
        .filter(EvidenceFeatures.evidence_id == evidence.id)
        .first()
    )
    if features_row is None:
        features_row = EvidenceFeatures(evidence_id=evidence.id)
        db.add(features_row)
    features_row.features = output.features
    features_row.extracted_text = output.extracted_text
    features_row.extracted_at = now

    for item in output.findings:
        db.add(
            AIFinding(
                evidence_id=evidence.id,
                finding_type=item.finding_type,
                title=item.title,
                description=item.description,
                confidence_score=item.confidence,
                severity=item.severity,
            )
        )
    db.flush()

    findings = _sorted_findings(db, evidence.id)
    risk_score, risk_level = compute_risk([f.confidence_score for f in findings])

    _add_custody(
        db,
        evidence.id,
        current_user,
        "analyzed",
        request,
        f"Automated analysis ({ENGINE_NAME}): {len(findings)} finding(s), risk {risk_score}/100 ({risk_level})",
    )
    _add_audit(
        db,
        current_user,
        "ANALYZE_EVIDENCE",
        evidence.id,
        request,
        f"findings={len(findings)}, risk={risk_score}",
    )
    db.commit()
    db.refresh(features_row)

    return _build_result(evidence, features_row, findings)


@router.get("/evidence/{evidence_id}", response_model=AnalysisResult)
def get_analysis(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the latest saved analysis of an evidence item."""
    evidence = _get_evidence_for_user(db, evidence_id, current_user)

    features_row = (
        db.query(EvidenceFeatures)
        .filter(EvidenceFeatures.evidence_id == evidence.id)
        .first()
    )
    if features_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This evidence has not been analyzed yet",
        )

    return _build_result(evidence, features_row, _sorted_findings(db, evidence.id))


@router.get("/case/{case_id}/summary", response_model=CaseAnalysisSummary)
def case_analysis_summary(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analysis overview of every evidence item in a case."""
    _get_case_for_user(db, case_id, current_user)

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.uploaded_at.desc())
        .all()
    )
    ids = [e.id for e in evidence_items]

    features_by_evidence: Dict[int, EvidenceFeatures] = {}
    findings_by_evidence: Dict[int, List[AIFinding]] = {}
    if ids:
        for row in (
            db.query(EvidenceFeatures).filter(EvidenceFeatures.evidence_id.in_(ids)).all()
        ):
            features_by_evidence[row.evidence_id] = row
        for finding in db.query(AIFinding).filter(AIFinding.evidence_id.in_(ids)).all():
            findings_by_evidence.setdefault(finding.evidence_id, []).append(finding)

    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    items: List[EvidenceRiskItem] = []
    total_findings = 0
    analyzed_count = 0
    highest = 0

    for evidence in evidence_items:
        row = features_by_evidence.get(evidence.id)
        findings = findings_by_evidence.get(evidence.id, [])

        if row is None:
            items.append(
                EvidenceRiskItem(
                    evidence_id=evidence.id,
                    filename=evidence.original_filename,
                    analyzed=False,
                )
            )
            continue

        analyzed_count += 1
        risk_score, risk_level = compute_risk([f.confidence_score for f in findings])
        highest = max(highest, risk_score)
        total_findings += len(findings)
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1

        items.append(
            EvidenceRiskItem(
                evidence_id=evidence.id,
                filename=evidence.original_filename,
                analyzed=True,
                risk_score=risk_score,
                risk_level=risk_level,
                finding_count=len(findings),
                analyzed_at=row.extracted_at,
            )
        )

    items.sort(key=lambda i: i.risk_score if i.risk_score is not None else -1, reverse=True)

    return CaseAnalysisSummary(
        case_id=case_id,
        total_evidence=len(evidence_items),
        analyzed_evidence=analyzed_count,
        total_findings=total_findings,
        findings_by_severity=severity_counts,
        highest_risk_score=highest,
        items=items,
    )