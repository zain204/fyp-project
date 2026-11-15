from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class FindingOut(BaseModel):
    id: int
    evidence_id: int
    finding_type: str
    title: str
    description: Optional[str] = None
    confidence_score: float
    severity: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisResult(BaseModel):
    evidence_id: int
    engine: str
    risk_score: int  # 0 - 100
    risk_level: str  # low | medium | high | critical
    summary: str
    findings: List[FindingOut]
    features: Dict[str, Any]
    extracted_text_preview: Optional[str] = None
    analyzed_at: datetime


class EvidenceRiskItem(BaseModel):
    evidence_id: int
    filename: str
    analyzed: bool
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    finding_count: int = 0
    analyzed_at: Optional[datetime] = None


class CaseAnalysisSummary(BaseModel):
    case_id: int
    total_evidence: int
    analyzed_evidence: int
    total_findings: int
    findings_by_severity: Dict[str, int]
    highest_risk_score: int
    items: List[EvidenceRiskItem]