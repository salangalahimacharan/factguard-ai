import io
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.schemas.fact_check import FactCheckResponse

logger = logging.getLogger("factguard.services.pdf")

class PDFReportGenerator:
    """Generates academic-grade PDF fact-check reports for FactGuard AI."""

    def generate_fact_check_pdf(self, response: FactCheckResponse) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        elements = []

        # Title Header
        elements.append(Paragraph("FactGuard AI — Multi-Agent Fact-Check Report", title_style))
        elements.append(Paragraph(f"Report ID: {response.id} | Generated: {response.created_at[:19].replace('T', ' ')}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

        # Input & Verdict Summary
        elements.append(Paragraph("<b>Submitted Claim Content:</b>", h2_style))
        elements.append(Paragraph(f"<i>\"{response.original_input}\"</i>", body_style))
        elements.append(Spacer(1, 10))

        # Overall Verdict Badge Table
        verdict_color = self._get_verdict_color(response.overall_verdict.value)
        verdict_data = [
            ["OVERALL VERDICT", "CONFIDENCE SCORE", "INPUT TYPE"],
            [response.overall_verdict.value, f"{response.confidence_score}%", response.input_type.value.upper()]
        ]
        t_verdict = Table(verdict_data, colWidths=[200, 170, 170])
        t_verdict.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#475569")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (0,1), verdict_color),
            ('TEXTCOLOR', (0,1), (0,1), colors.white),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,1), (-1,1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0"))
        ]))
        elements.append(t_verdict)
        elements.append(Spacer(1, 12))

        # Executive Summary
        elements.append(Paragraph("<b>Executive Synthesis & Explanation:</b>", h2_style))
        elements.append(Paragraph(response.summary, body_style))
        if response.key_context:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"<b>Key Context:</b> {response.key_context}", body_style))
        elements.append(Spacer(1, 12))

        # Individual Claims Breakdown
        elements.append(Paragraph("<b>Extracted Claims & Evidence Verdicts:</b>", h2_style))
        for cv in response.claim_verdicts:
            claim_text_para = Paragraph(f"<b>Claim {cv.claim_id}:</b> {cv.claim_text}<br/>"
                                        f"<b>Verdict:</b> {cv.verdict.value} (Confidence: {cv.confidence_score}%)<br/>"
                                        f"<b>Explanation:</b> {cv.explanation}", body_style)
            elements.append(claim_text_para)
            elements.append(Spacer(1, 8))

        # Sources List
        if response.sources:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("<b>Verified Primary & Secondary Sources:</b>", h2_style))
            for s in response.sources[:6]:
                src_para = Paragraph(f"• <b>{s.publisher}</b> — <a href=\"{s.url}\"><u>{s.title}</u></a><br/>"
                                     f"Credibility Score: {s.credibility_score}/100 ({s.credibility_rating.value}) | Type: {s.source_type}", body_style)
                elements.append(src_para)
                elements.append(Spacer(1, 4))

        # Academic Disclaimer
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))
        disclaimer_para = Paragraph(f"<i>Disclaimer: {response.disclaimer}</i>", ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8")))
        elements.append(disclaimer_para)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _get_verdict_color(self, verdict: str) -> colors.Color:
        v = verdict.upper()
        if "VERIFIED" in v:
            return colors.HexColor("#16a34a") # Green
        elif "FALSE" in v:
            return colors.HexColor("#dc2626") # Red
        elif "MISLEADING" in v:
            return colors.HexColor("#ea580c") # Orange
        elif "PARTIALLY" in v:
            return colors.HexColor("#d97706") # Amber
        elif "UNVERIFIED" in v:
            return colors.HexColor("#0284c7") # Blue
        else:
            return colors.HexColor("#64748b") # Slate gray

pdf_generator = PDFReportGenerator()
