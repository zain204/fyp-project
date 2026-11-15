"""Builds the final investigation report (PDF) for a case."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.models.ai_finding import AIFinding
from app.models.case import Case
from app.models.custody_record import CustodyRecord
from app.models.evidence import Evidence
from app.models.evidence_features import EvidenceFeatures
from app.models.investigation_notes import InvestigationNote
from app.models.user import User
from app.services.ai_analysis import ENGINE_NAME, compute_risk
from app.services.blockchain_service import get_block_for_evidence, verify_chain
from app.services.hashing import hashes_match, sha256_of_file
from app.services.storage import resolve_path

NAVY = colors.HexColor("#1f2d4d")
HEADER_BG = colors.HexColor("#e9edf5")
GRID = colors.HexColor("#c5cbd8")

GREEN = "#2e7d32"
RED = "#b71c1c"
ORANGE = "#e65100"
AMBER = "#b28704"

SEVERITY_COLORS = {
    "critical": RED,
    "high": ORANGE,
    "medium": AMBER,
    "low": GREEN,
}


# ======================================================================
# Data collection
# ======================================================================
def _check_integrity(evidence: Evidence, block) -> Dict[str, Any]:
    """Re-computes the file hash right now and compares it with the database and the ledger."""
    path = resolve_path(evidence.file_path)
    if not path.exists():
        return {
            "status": "missing",
            "current_hash": None,
            "db_match": None,
            "ledger_match": None,
        }

    current = sha256_of_file(path)
    db_match = hashes_match(current, evidence.sha256_hash)
    ledger_match = (
        hashes_match(current, block.evidence_hash)
        if block is not None and block.evidence_hash
        else None
    )
    intact = db_match and ledger_match is not False
    return {
        "status": "intact" if intact else "tampered",
        "current_hash": current,
        "db_match": db_match,
        "ledger_match": ledger_match,
    }


def collect_report_data(db: Session, case: Case) -> Dict[str, Any]:
    users = {u.id: u for u in db.query(User).all()}
    investigator = users.get(case.investigator_id)

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case.id)
        .order_by(Evidence.uploaded_at.asc())
        .all()
    )
    notes = (
        db.query(InvestigationNote)
        .filter(InvestigationNote.case_id == case.id)
        .order_by(InvestigationNote.created_at.asc())
        .all()
    )
    chain = verify_chain(db)

    items: List[Dict[str, Any]] = []
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    total_findings = 0
    analyzed = 0
    intact = 0
    tampered = 0
    missing = 0
    highest = 0

    for ev in evidence_items:
        block = get_block_for_evidence(db, ev.id)

        custody_records = (
            db.query(CustodyRecord)
            .filter(CustodyRecord.evidence_id == ev.id)
            .order_by(CustodyRecord.timestamp.asc())
            .all()
        )
        custody = [
            (
                rec,
                users[rec.user_id].full_name if rec.user_id in users else "Unknown",
            )
            for rec in custody_records
        ]

        features_row = (
            db.query(EvidenceFeatures)
            .filter(EvidenceFeatures.evidence_id == ev.id)
            .first()
        )
        findings = (
            db.query(AIFinding)
            .filter(AIFinding.evidence_id == ev.id)
            .order_by(AIFinding.confidence_score.desc())
            .all()
        )

        risk_score: Optional[int] = None
        risk_level: Optional[str] = None
        if features_row is not None:
            analyzed += 1
            risk_score, risk_level = compute_risk(
                [f.confidence_score for f in findings]
            )
            highest = max(highest, risk_score)
            total_findings += len(findings)
            for f in findings:
                if f.severity in severity_counts:
                    severity_counts[f.severity] += 1

        integrity = _check_integrity(ev, block)
        if integrity["status"] == "intact":
            intact += 1
        elif integrity["status"] == "missing":
            missing += 1
        else:
            tampered += 1

        items.append(
            {
                "evidence": ev,
                "uploader_name": users[ev.uploaded_by].full_name
                if ev.uploaded_by in users
                else "Unknown",
                "block": block,
                "custody": custody,
                "analyzed": features_row is not None,
                "analysis_time": features_row.extracted_at if features_row else None,
                "findings": findings,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "integrity": integrity,
            }
        )

    return {
        "case": case,
        "investigator": investigator,
        "items": items,
        "notes": [
            (n, users[n.author_id].full_name if n.author_id in users else "Unknown")
            for n in notes
        ],
        "chain": chain,
        "generated_at": datetime.now(timezone.utc),
        "stats": {
            "evidence_count": len(evidence_items),
            "analyzed_count": analyzed,
            "total_findings": total_findings,
            "severity_counts": severity_counts,
            "highest_risk": highest,
            "intact_count": intact,
            "tampered_count": tampered,
            "missing_count": missing,
            "note_count": len(notes),
        },
    }


def build_summary(data: Dict[str, Any]) -> str:
    s = data["stats"]
    chain = data["chain"]
    return (
        f"{s['evidence_count']} evidence item(s), {s['analyzed_count']} analyzed, "
        f"{s['total_findings']} finding(s), highest risk {s['highest_risk']}/100. "
        f"Integrity: {s['intact_count']} intact, {s['tampered_count']} tampered, "
        f"{s['missing_count']} missing. "
        f"Blockchain: {'valid' if chain.is_valid else 'BROKEN'}."
    )


# ======================================================================
# PDF helpers
# ======================================================================
def _safe(text: Any) -> str:
    """The built-in PDF fonts support Latin-1 only; other characters become '?'."""
    if text is None or text == "":
        return "-"
    return str(text).encode("latin-1", "replace").decode("latin-1")


def P(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_safe(text)).replace("\n", "<br/>"), style)


def _colored(text: Any, color: str) -> str:
    return f'<font color="{color}"><b>{escape(_safe(text))}</b></font>'


def _fmt_dt(value: Optional[datetime]) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S") + " UTC"


def _fmt_size(size: Optional[int]) -> str:
    if size is None:
        return "-"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return "-"


def _label(enum_value: Any) -> str:
    raw = getattr(enum_value, "value", enum_value)
    return str(raw).replace("_", " ").title()


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    cell = ParagraphStyle(
        "RCell", parent=base["BodyText"], fontSize=8, leading=10.5, wordWrap="CJK"
    )
    return {
        "title": ParagraphStyle(
            "RTitle",
            parent=base["Title"],
            fontSize=21,
            leading=26,
            alignment=TA_CENTER,
            textColor=NAVY,
        ),
        "subtitle": ParagraphStyle(
            "RSubtitle",
            parent=base["BodyText"],
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
        ),
        "h1": ParagraphStyle(
            "RH1",
            parent=base["Heading1"],
            fontSize=14,
            leading=18,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "RH2",
            parent=base["Heading2"],
            fontSize=10.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "RBody", parent=base["BodyText"], fontSize=9.5, leading=13.5
        ),
        "small": ParagraphStyle(
            "RSmall",
            parent=base["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#555555"),
        ),
        "cell": cell,
        "cellb": ParagraphStyle(
            "RCellB", parent=cell, fontName="Helvetica-Bold", textColor=NAVY
        ),
        "mono": ParagraphStyle(
            "RMono", parent=cell, fontName="Courier", fontSize=7, leading=9
        ),
    }


def _table(rows: List[List[Any]], widths_mm: List[float], header: bool = True) -> Table:
    table = Table(
        rows, colWidths=[w * mm for w in widths_mm], repeatRows=1 if header else 0
    )
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HEADER_BG))
    table.setStyle(TableStyle(style))
    return table


def _kv_table(pairs: List[tuple], st: Dict[str, ParagraphStyle]) -> Table:
    rows = [[P(label, st["cellb"]), value] for label, value in pairs]
    table = Table(rows, colWidths=[42 * mm, 132 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("BACKGROUND", (0, 0), (0, -1), HEADER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _footer(case_number: str):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            18 * mm,
            10 * mm,
            _safe(f"Case {case_number} - CONFIDENTIAL - Digital Forensic Investigation Report"),
        )
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return draw


def _integrity_label(status: str) -> str:
    if status == "intact":
        return _colored("INTACT", GREEN)
    if status == "missing":
        return _colored("MISSING", RED)
    return _colored("TAMPERED", RED)


def _match_label(value: Optional[bool], none_text: str = "N/A") -> str:
    if value is None:
        return escape(none_text)
    return _colored("MATCH", GREEN) if value else _colored("MISMATCH", RED)


# ======================================================================
# PDF builder
# ======================================================================
def build_report_pdf(
    data: Dict[str, Any],
    output_path: Path,
    title: str,
    generated_by_name: str,
    generated_by_role: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    st = _styles()
    case: Case = data["case"]
    stats = data["stats"]
    chain = data["chain"]
    investigator: Optional[User] = data["investigator"]

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=_safe(title),
        author=_safe(generated_by_name),
    )

    story: List[Any] = []

    # ---------------- Title ----------------
    story.append(Spacer(1, 4 * mm))
    story.append(P("DIGITAL FORENSIC INVESTIGATION REPORT", st["title"]))
    story.append(P(title, st["subtitle"]))
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY))
    story.append(Spacer(1, 3 * mm))

    # ---------------- 1. Case information ----------------
    story.append(P("1. Case Information", st["h1"]))
    investigator_text = "-"
    if investigator is not None:
        investigator_text = investigator.full_name
        if investigator.badge_number:
            investigator_text += f" (Badge: {investigator.badge_number})"

    story.append(
        _kv_table(
            [
                ("Case number", P(case.case_number, st["cell"])),
                ("Title", P(case.title, st["cell"])),
                ("Crime type", P(case.crime_type, st["cell"])),
                ("Status", P(_label(case.status), st["cell"])),
                ("Priority", P(_label(case.priority), st["cell"])),
                ("Lead investigator", P(investigator_text, st["cell"])),
                ("Case opened", P(_fmt_dt(case.created_at), st["cell"])),
                ("Last updated", P(_fmt_dt(case.updated_at), st["cell"])),
                ("Report generated", P(_fmt_dt(data["generated_at"]), st["cell"])),
            ],
            st,
        )
    )
    if case.description:
        story.append(Spacer(1, 3 * mm))
        story.append(P("Case description", st["h2"]))
        story.append(P(case.description, st["body"]))

    # ---------------- 2. Executive summary ----------------
    story.append(P("2. Executive Summary", st["h1"]))
    story.append(
        P(
            f"{stats['evidence_count']} evidence item(s) are registered in this case. "
            f"{stats['analyzed_count']} item(s) were analyzed by the automated analysis engine "
            f"({ENGINE_NAME}), producing {stats['total_findings']} finding(s). "
            f"The highest risk score is {stats['highest_risk']} out of 100.",
            st["body"],
        )
    )
    story.append(Spacer(1, 2 * mm))

    if stats["evidence_count"] == 0:
        integrity_markup = "No evidence has been uploaded to this case yet."
    elif stats["tampered_count"] or stats["missing_count"]:
        integrity_markup = _colored(
            f"ATTENTION: {stats['tampered_count']} evidence item(s) failed integrity "
            f"verification and {stats['missing_count']} item(s) are missing.",
            RED,
        )
    else:
        integrity_markup = _colored(
            "All evidence items passed integrity verification against both the "
            "database and the blockchain ledger.",
            GREEN,
        )
    story.append(Paragraph(integrity_markup, st["body"]))
    story.append(Spacer(1, 1 * mm))

    chain_markup = (
        _colored("The blockchain ledger is valid.", GREEN)
        if chain.is_valid
        else _colored(f"The blockchain ledger is BROKEN: {chain.message}", RED)
    )
    story.append(Paragraph(chain_markup, st["body"]))
    story.append(Spacer(1, 3 * mm))

    sev = stats["severity_counts"]
    story.append(
        _kv_table(
            [
                ("Evidence items", P(stats["evidence_count"], st["cell"])),
                ("Analyzed", P(stats["analyzed_count"], st["cell"])),
                (
                    "Findings by severity",
                    P(
                        f"Critical: {sev['critical']}   High: {sev['high']}   "
                        f"Medium: {sev['medium']}   Low: {sev['low']}",
                        st["cell"],
                    ),
                ),
                ("Highest risk score", P(f"{stats['highest_risk']} / 100", st["cell"])),
                ("Investigation notes", P(stats["note_count"], st["cell"])),
            ],
            st,
        )
    )

    # ---------------- 3. Evidence inventory ----------------
    story.append(P("3. Evidence Inventory", st["h1"]))
    if not data["items"]:
        story.append(P("No evidence has been uploaded to this case.", st["body"]))
    else:
        rows: List[List[Any]] = [
            [
                P("#", st["cellb"]),
                P("File", st["cellb"]),
                P("Type / Size", st["cellb"]),
                P("Uploaded", st["cellb"]),
                P("SHA-256 (at upload)", st["cellb"]),
            ]
        ]
        for item in data["items"]:
            ev: Evidence = item["evidence"]
            rows.append(
                [
                    P(ev.id, st["cell"]),
                    P(
                        f"{ev.original_filename}\nBy: {item['uploader_name']}",
                        st["cell"],
                    ),
                    P(f"{ev.file_type or '-'}\n{_fmt_size(ev.file_size)}", st["cell"]),
                    P(_fmt_dt(ev.uploaded_at), st["cell"]),
                    P(ev.sha256_hash, st["mono"]),
                ]
            )
        story.append(_table(rows, [8, 46, 28, 28, 64]))

    # ---------------- 4. Integrity verification ----------------
    story.append(P("4. Integrity Verification", st["h1"]))
    story.append(
        P(
            "Every file hash was recomputed while generating this report and compared "
            "with the hash stored in the database and the hash stored in the blockchain ledger.",
            st["small"],
        )
    )
    story.append(Spacer(1, 2 * mm))
    if data["items"]:
        rows = [
            [
                P("#", st["cellb"]),
                P("File", st["cellb"]),
                P("Hash vs database", st["cellb"]),
                P("Hash vs blockchain", st["cellb"]),
                P("Block", st["cellb"]),
                P("Result", st["cellb"]),
            ]
        ]
        for item in data["items"]:
            ev = item["evidence"]
            integ = item["integrity"]
            block = item["block"]
            rows.append(
                [
                    P(ev.id, st["cell"]),
                    P(ev.original_filename, st["cell"]),
                    Paragraph(_match_label(integ["db_match"]), st["cell"]),
                    Paragraph(
                        _match_label(integ["ledger_match"], "NO BLOCK"), st["cell"]
                    ),
                    P(block.block_index if block else "-", st["cell"]),
                    Paragraph(_integrity_label(integ["status"]), st["cell"]),
                ]
            )
        story.append(_table(rows, [8, 54, 30, 30, 18, 34]))
        story.append(Spacer(1, 3 * mm))

    story.append(
        _kv_table(
            [
                ("Ledger blocks", P(chain.total_blocks, st["cell"])),
                (
                    "Ledger status",
                    Paragraph(
                        _colored("VALID", GREEN)
                        if chain.is_valid
                        else _colored("BROKEN", RED),
                        st["cell"],
                    ),
                ),
                ("Details", P(chain.message, st["cell"])),
            ],
            st,
        )
    )

    # ---------------- 5. Automated analysis ----------------
    story.append(P("5. Automated Analysis Findings", st["h1"]))
    story.append(
        P(
            f"Analysis engine: {ENGINE_NAME}. The findings are automated indicators and "
            "must be reviewed by a qualified investigator. They are not legal conclusions.",
            st["small"],
        )
    )
    if not data["items"]:
        story.append(P("No evidence to analyze.", st["body"]))

    for item in data["items"]:
        ev = item["evidence"]
        block_content: List[Any] = []

        if not item["analyzed"]:
            block_content.append(
                P(f"Evidence #{ev.id}: {ev.original_filename}", st["h2"])
            )
            block_content.append(P("This evidence has not been analyzed yet.", st["body"]))
            story.append(KeepTogether(block_content))
            continue

        level = item["risk_level"] or "low"
        heading = (
            f"Evidence #{ev.id}: {escape(_safe(ev.original_filename))} - "
            f'<font color="{SEVERITY_COLORS.get(level, GREEN)}"><b>'
            f"Risk {item['risk_score']}/100 ({level.upper()})</b></font>"
        )
        block_content.append(Paragraph(heading, st["h2"]))
        block_content.append(
            P(f"Analyzed at: {_fmt_dt(item['analysis_time'])}", st["small"])
        )

        if not item["findings"]:
            block_content.append(
                P(
                    "No suspicious indicators were detected by the automated checks. "
                    "This does not prove the evidence is harmless.",
                    st["body"],
                )
            )
            story.append(KeepTogether(block_content))
            continue

        rows = [
            [
                P("Severity", st["cellb"]),
                P("Type", st["cellb"]),
                P("Details", st["cellb"]),
                P("Confidence", st["cellb"]),
            ]
        ]
        for f in item["findings"]:
            color = SEVERITY_COLORS.get(f.severity, GREEN)
            rows.append(
                [
                    Paragraph(_colored(f.severity.upper(), color), st["cell"]),
                    P(f.finding_type.replace("_", " "), st["cell"]),
                    Paragraph(
                        f"<b>{escape(_safe(f.title))}</b><br/>"
                        f"{escape(_safe(f.description))}",
                        st["cell"],
                    ),
                    P(f"{round(f.confidence_score * 100)}%", st["cell"]),
                ]
            )
        block_content.append(_table(rows, [20, 30, 106, 18]))
        story.append(KeepTogether(block_content[:2]))
        story.append(block_content[2])

    # ---------------- 6. Investigation notes ----------------
    story.append(P("6. Investigation Notes", st["h1"]))
    if not data["notes"]:
        story.append(P("No investigation notes were recorded for this case.", st["body"]))
    for note, author_name in data["notes"]:
        story.append(
            Paragraph(
                f"<b>{escape(_safe(author_name))}</b> - {escape(_fmt_dt(note.created_at))}",
                st["small"],
            )
        )
        story.append(P(note.content, st["body"]))
        story.append(Spacer(1, 3 * mm))

    # ---------------- 7. Chain of custody ----------------
    story.append(P("7. Chain of Custody", st["h1"]))
    if not data["items"]:
        story.append(P("No evidence, so no custody records.", st["body"]))
    for item in data["items"]:
        ev = item["evidence"]
        story.append(P(f"Evidence #{ev.id}: {ev.original_filename}", st["h2"]))
        if not item["custody"]:
            story.append(P("No custody records found.", st["body"]))
            continue
        rows = [
            [
                P("Time", st["cellb"]),
                P("User", st["cellb"]),
                P("Action", st["cellb"]),
                P("Details", st["cellb"]),
            ]
        ]
        for rec, user_name in item["custody"]:
            rows.append(
                [
                    P(_fmt_dt(rec.timestamp), st["cell"]),
                    P(user_name, st["cell"]),
                    P(rec.action, st["cell"]),
                    P(rec.notes, st["cell"]),
                ]
            )
        story.append(_table(rows, [36, 34, 22, 82]))

    # ---------------- 8. Certification ----------------
    story.append(P("8. Report Information", st["h1"]))
    story.append(
        _kv_table(
            [
                (
                    "Prepared by",
                    P(f"{generated_by_name} ({generated_by_role})", st["cell"]),
                ),
                ("Generated at", P(_fmt_dt(data["generated_at"]), st["cell"])),
                ("Analysis engine", P(ENGINE_NAME, st["cell"])),
            ],
            st,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        P(
            "This report was generated automatically from the Forensic Evidence Management "
            "System. File hashes were recomputed at generation time. Automated findings are "
            "indicators only and require review by a qualified investigator.",
            st["small"],
        )
    )

    footer = _footer(case.case_number)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)