import os
import hashlib
import datetime
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.core.config import settings
from app.core.logging import logger

class ReportPDFGenerator:
    """
    Renders official, evidentiary-grade PDF Incident Dossiers using ReportLab.
    Enforces clear epistemic distinctions, forensic evidence registers,
    integrity checksums, and chain-of-custody approval lines.
    """

    @classmethod
    def generate_pdf(cls, report_data: Dict[str, Any], output_path: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Generates PDF dossier and returns: (file_path, checksum_sha256, file_size_bytes)
        """
        report_num = report_data.get("report_number", f"REP-{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}")
        if not output_path:
            reports_dir = settings.get_absolute_path("data/reports")
            os.makedirs(reports_dir, exist_ok=True)
            output_path = str(reports_dir / f"{report_num}.pdf")
        else:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        header_banner_style = ParagraphStyle(
            "HeaderBanner",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#D32F2F"),
        )
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#211D2B"),
            alignment=TA_LEFT,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#554F60"),
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#4328A8"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#2B2638"),
        )
        alert_body_style = ParagraphStyle(
            "AlertBody",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#854D0E"),
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2B2638"),
        )
        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )

        elements = []

        # 1. Classification & Warning Header
        elements.append(Paragraph("CONFIDENTIAL // BORDER SECURITY COMMAND // LAW ENFORCEMENT SENSITIVE", header_banner_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(report_data.get("title", f"Surveillance Incident Dossier — {report_num}"), title_style))
        elements.append(Paragraph(f"Forensic Case File: {report_num} &bull; Generated: {report_data.get('created_at', datetime.datetime.now(datetime.timezone.utc).isoformat())}", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#7C5CFC"), spaceAfter=12))

        # 2. Executive Metadata Grid
        sections = report_data.get("sections", {})
        meta_data = [
            [
                Paragraph("<b>Report Number:</b>", table_cell_style),
                Paragraph(report_num, table_cell_style),
                Paragraph("<b>Review Status:</b>", table_cell_style),
                Paragraph(f"<b>{report_data.get('review_status', 'DRAFT')}</b>", table_cell_style),
            ],
            [
                Paragraph("<b>Incident ID:</b>", table_cell_style),
                Paragraph(f"INC-{report_data.get('incident_id', 'N/A')}", table_cell_style),
                Paragraph("<b>Model Name:</b>", table_cell_style),
                Paragraph(report_data.get("model_name", "gemini-2.5-flash"), table_cell_style),
            ],
            [
                Paragraph("<b>Prompt Version:</b>", table_cell_style),
                Paragraph(report_data.get("prompt_version", "2026.04.1"), table_cell_style),
                Paragraph("<b>Grounded Citations:</b>", table_cell_style),
                Paragraph(f"{int(report_data.get('valid_citation_rate', 1.0)*100)}% Verified", table_cell_style),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[110, 150, 110, 150])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F7FC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E1EE")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EDEAF5")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # 3. Executive Tactical Summary
        elements.append(Paragraph("1. Executive Incident Summary", section_heading))
        summary_text = sections.get("executive_summary", "No summary provided.")
        if sections.get("insufficient_evidence", False):
            summary_text = f"<b>[INSUFFICIENT EVIDENCE WARNING]</b>: {sections.get('insufficient_evidence_reason', 'Insufficient telemetry records to verify incident.')}<br/><br/>" + summary_text
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 12))

        # 4. Conflicting or Missing Evidence Warnings (If present)
        conflicts = sections.get("conflicting_evidence", [])
        missing_gaps = sections.get("missing_evidence_gaps", [])
        if conflicts or missing_gaps:
            elements.append(Paragraph("Evidentiary Discrepancies & Missing Data Gaps", section_heading))
            alert_items = []
            for conf in conflicts:
                desc = conf.get("description") if isinstance(conf, dict) else str(conf)
                alert_items.append(Paragraph(f"&bull; <b>CONFLICT DETECTED</b>: {desc}", alert_body_style))
            for gap in missing_gaps:
                desc = gap.get("description") if isinstance(gap, dict) else str(gap)
                interval = f" (Interval: {gap.get('interval')})" if isinstance(gap, dict) and gap.get("interval") else ""
                alert_items.append(Paragraph(f"&bull; <b>MISSING DATA GAP</b>: {desc}{interval}", alert_body_style))

            alert_table = Table([[item] for item in alert_items], colWidths=[520])
            alert_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF9C3")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#EAB308")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(alert_table)
            elements.append(Spacer(1, 12))

        # 5. Chronological Factual Statements & Evidence Citations
        statements = sections.get("factual_statements", [])
        elements.append(Paragraph(f"2. Verified Factual Statements ({len(statements)} Statements)", section_heading))
        if statements:
            stmt_table_data = [
                [
                    Paragraph("ID", table_header_style),
                    Paragraph("Type", table_header_style),
                    Paragraph("Time (UTC)", table_header_style),
                    Paragraph("Statement & Evidentiary Claim", table_header_style),
                    Paragraph("Evidence / Status", table_header_style),
                ]
            ]
            for s in statements:
                sid = str(s.get("statement_id", "-"))
                stype = s.get("statement_type", "OBSERVATION")
                ts = s.get("timestamp", "-") or "-"
                if "T" in ts:
                    ts = ts.split("T")[-1].replace("Z", "")
                text = s.get("text", "")
                corr = s.get("human_correction")
                if corr:
                    text += f"<br/><b>[Analyst Correction]</b>: <i>{corr}</i>"

                status = s.get("citation_status", "VERIFIED")
                ev_ids = s.get("supporting_evidence_ids", [])
                ev_str = f"Evid: {ev_ids}" if ev_ids else "Direct Ref"
                status_color = "#16A34A" if status == "VERIFIED" else "#DC2626"
                status_p = Paragraph(f"<b>{ev_str}</b><br/><font color='{status_color}'>{status}</font>", table_cell_style)

                stmt_table_data.append([
                    Paragraph(sid, table_cell_style),
                    Paragraph(f"<b>{stype}</b>", table_cell_style),
                    Paragraph(ts, table_cell_style),
                    Paragraph(text, table_cell_style),
                    status_p,
                ])

            stmt_table = Table(stmt_table_data, colWidths=[25, 80, 55, 260, 100])
            stmt_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4328A8")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E1EE")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF9FD")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(stmt_table)
        else:
            elements.append(Paragraph("<i>No verified factual statements recorded.</i>", body_style))
        elements.append(Spacer(1, 14))

        # 6. Forensic Evidence Register
        evidence_used = sections.get("evidence_used", [])
        elements.append(Paragraph(f"3. Forensic Evidence Register ({len(evidence_used)} Items)", section_heading))
        if evidence_used:
            ev_table_data = [
                [
                    Paragraph("ID", table_header_style),
                    Paragraph("Evidence Type", table_header_style),
                    Paragraph("SHA-256 Integrity Checksum", table_header_style),
                    Paragraph("Source Timestamp", table_header_style),
                ]
            ]
            for ev in evidence_used:
                eid = str(ev.get("evidence_id", "-"))
                etype = ev.get("evidence_type", "SNAPSHOT")
                sha = ev.get("checksum_sha256", "N/A") or "N/A"
                if len(sha) > 20:
                    sha = sha[:16] + "..." + sha[-8:]
                ts = ev.get("timestamp", "-") or "-"
                ev_table_data.append([
                    Paragraph(eid, table_cell_style),
                    Paragraph(f"<b>{etype}</b>", table_cell_style),
                    Paragraph(f"<font face='Courier'>{sha}</font>", table_cell_style),
                    Paragraph(ts, table_cell_style),
                ])

            ev_table = Table(ev_table_data, colWidths=[35, 110, 235, 140])
            ev_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#211D2B")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E1EE")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF9FD")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(ev_table)
        elements.append(Spacer(1, 14))

        # 7. Recommended Containment Strategies
        recs = sections.get("containment_recommendations", [])
        if recs:
            elements.append(Paragraph("4. Recommended Tactical Actions", section_heading))
            for r in recs:
                elements.append(Paragraph(f"[  ] {r}", body_style))
                elements.append(Spacer(1, 2))
            elements.append(Spacer(1, 10))

        # 8. Human Review & Chain of Custody Signature Block
        approval_box = [
            [
                Paragraph("<b>Lead Security Analyst Review:</b>", table_cell_style),
                Paragraph("<b>Authorized Command Approver:</b>", table_cell_style),
            ],
            [
                Paragraph(f"Status: <b>{report_data.get('review_status', 'DRAFT')}</b>", table_cell_style),
                Paragraph(f"Approved By: User #{report_data.get('approved_by_user_id', 'Pending')}", table_cell_style),
            ],
            [
                Paragraph(f"Date: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", table_cell_style),
                Paragraph(f"Signature: ____________________________________", table_cell_style),
            ],
        ]
        app_table = Table(approval_box, colWidths=[260, 260])
        app_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F7FC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#7C5CFC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E1EE")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(KeepTogether([app_table]))

        # Build PDF
        doc.build(elements)

        # Calculate cryptographic SHA-256 checksum
        hasher = hashlib.sha256()
        with open(output_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        sha256 = hasher.hexdigest()
        file_size = os.path.getsize(output_path)

        logger.info(f"Generated PDF report: {output_path} (size={file_size}B, sha256={sha256[:16]}...)")
        return output_path, sha256, file_size
