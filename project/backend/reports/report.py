"""
report.py — PDF Report Generator.

Builds a premium, client-facing PDF report from the updated markdown report source.
Incorporates visual styling, embedded diagrams, and styled tables.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    Image
)
from reportlab.pdfgen import canvas

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils import get_logger

logger = get_logger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
SOURCE_REPORT = ROOT_DIR / "deliverables" / "reports" / "Assessment_Report.md"
OUTPUT_PDF = ROOT_DIR / "deliverables" / "reports" / "Project_Assessment_Report.pdf"


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count dynamically
    and draw professional headers/footers with 'Page X of Y'.
    """
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_elements(self, page_count):
        width, height = A4

        # 1. Cover Page — draw the ENTIRE cover directly on canvas
        if self._pageNumber == 1:
            self.saveState()
            
            # === BACKGROUND ===
            self.setFillColor(colors.HexColor("#0F172A"))
            self.rect(0, 0, width, height, fill=True, stroke=False)
            
            # Top accent bar
            self.setFillColor(colors.HexColor("#4F46E5"))
            self.rect(0, height - 18, width, 18, fill=True, stroke=False)
            
            # Bottom accent bar
            self.setFillColor(colors.HexColor("#0EA5E9"))
            self.rect(0, 0, width, 14, fill=True, stroke=False)
            
            # Decorative left accent line
            self.setStrokeColor(colors.HexColor("#818CF8"))
            self.setLineWidth(4)
            self.line(54, height / 2 - 40, 170, height / 2 - 40)
            
            # === BRAND LOGO ===
            self.setFont("Helvetica-Bold", 28)
            self.setFillColor(colors.HexColor("#FFFFFF"))
            self.drawString(54, height - 70, "Freight")
            self.setFillColor(colors.HexColor("#818CF8"))
            self.drawString(54 + self.stringWidth("Freight", "Helvetica-Bold", 28), height - 70, "AI")
            
            # Assessment badge (top-right)
            badge_text = "ML ENGINEER ASSESSMENT REPORT"
            self.setFont("Helvetica-Bold", 7)
            badge_w = self.stringWidth(badge_text, "Helvetica-Bold", 7) + 20
            badge_x = width - 54 - badge_w
            badge_y = height - 80
            self.setFillColor(colors.HexColor("#1E293B"))
            self.roundRect(badge_x, badge_y, badge_w, 22, 5, fill=True, stroke=False)
            self.setStrokeColor(colors.HexColor("#4F46E5"))
            self.setLineWidth(1)
            self.roundRect(badge_x, badge_y, badge_w, 22, 5, fill=False, stroke=True)
            self.setFillColor(colors.HexColor("#E0E7FF"))
            self.drawString(badge_x + 10, badge_y + 7, badge_text)
            
            # === MAIN TITLE ===
            self.setFont("Helvetica-Bold", 30)
            self.setFillColor(colors.HexColor("#FFFFFF"))
            title_y = height - 170
            self.drawString(54, title_y, "Freight Spot Rate Prediction")
            self.setFillColor(colors.HexColor("#C7D2FE"))
            self.drawString(54, title_y - 38, "& Explainable AI Platform")
            
            # === SUBTITLE ===
            self.setFont("Helvetica", 10)
            self.setFillColor(colors.HexColor("#A5B4FC"))
            subtitle = "End-to-End Production System for Spot Rate Forecasting, Explainable AI (SHAP),"
            subtitle2 = "5-Fold Algorithm Benchmarks, and REST Microservices."
            self.drawString(54, title_y - 70, subtitle)
            self.drawString(54, title_y - 84, subtitle2)
            
            # === HORIZONTAL DIVIDER ===
            self.setStrokeColor(colors.HexColor("#334155"))
            self.setLineWidth(0.8)
            self.line(54, title_y - 100, width - 54, title_y - 100)
            
            # === CANDIDATE INFO CARD ===
            card_y = title_y - 200
            card_h = 100
            self.setFillColor(colors.HexColor("#1E293B"))
            self.roundRect(54, card_y, width - 108, card_h, 8, fill=True, stroke=False)
            self.setStrokeColor(colors.HexColor("#334155"))
            self.setLineWidth(1)
            self.roundRect(54, card_y, width - 108, card_h, 8, fill=False, stroke=True)
            
            col_w = (width - 108) / 2
            
            # Row 1 labels
            self.setFont("Helvetica-Bold", 7)
            self.setFillColor(colors.HexColor("#94A3B8"))
            self.drawString(70, card_y + card_h - 20, "SUBMITTED BY")
            self.drawString(70 + col_w, card_y + card_h - 20, "TARGET ROLE")
            
            # Row 1 values
            self.setFont("Helvetica-Bold", 12)
            self.setFillColor(colors.HexColor("#FFFFFF"))
            self.drawString(70, card_y + card_h - 38, "Pruthviraj Tarode")
            self.drawString(70 + col_w, card_y + card_h - 38, "Machine Learning Engineer")
            
            # Divider
            self.setStrokeColor(colors.HexColor("#334155"))
            self.setLineWidth(0.5)
            self.line(70, card_y + card_h - 48, 54 + width - 108 - 16, card_y + card_h - 48)
            
            # Row 2 labels
            self.setFont("Helvetica-Bold", 7)
            self.setFillColor(colors.HexColor("#94A3B8"))
            self.drawString(70, card_y + card_h - 64, "EVALUATING ORGANIZATION")
            self.drawString(70 + col_w, card_y + card_h - 64, "SUBMISSION DATE")
            
            # Row 2 values
            self.setFont("Helvetica-Bold", 12)
            self.setFillColor(colors.HexColor("#FFFFFF"))
            self.drawString(70, card_y + card_h - 82, "Spotter Assessment Team")
            self.drawString(70 + col_w, card_y + card_h - 82, "August 2026")
            
            # === GITHUB LINK (clickable) ===
            link_y = card_y - 30
            self.setFont("Helvetica-Bold", 9)
            self.setFillColor(colors.HexColor("#818CF8"))
            self.drawString(54, link_y, "GitHub:")
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#93C5FD"))
            gh_text = "github.com/pruthvirajtarode/freight-rate"
            gh_x = 54 + 45
            gh_w = self.stringWidth(gh_text, "Helvetica", 9)
            self.drawString(gh_x, link_y, gh_text)
            # Underline
            self.setStrokeColor(colors.HexColor("#93C5FD"))
            self.setLineWidth(0.5)
            self.line(gh_x, link_y - 1, gh_x + gh_w, link_y - 1)
            # Clickable area
            self.linkURL("https://github.com/pruthvirajtarode/freight-rate",
                         (gh_x, link_y - 3, gh_x + gh_w, link_y + 10), relative=0)

            # === LIVE DASHBOARD LINK (clickable) ===
            link_y2 = link_y - 20
            self.setFont("Helvetica-Bold", 9)
            self.setFillColor(colors.HexColor("#818CF8"))
            self.drawString(54, link_y2, "Live Dashboard:")
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#93C5FD"))
            ld_text = "freight-rate-one.vercel.app"
            ld_x = 54 + 95
            ld_w = self.stringWidth(ld_text, "Helvetica", 9)
            self.drawString(ld_x, link_y2, ld_text)
            self.setStrokeColor(colors.HexColor("#93C5FD"))
            self.setLineWidth(0.5)
            self.line(ld_x, link_y2 - 1, ld_x + ld_w, link_y2 - 1)
            self.linkURL("https://freight-rate-one.vercel.app",
                         (ld_x, link_y2 - 3, ld_x + ld_w, link_y2 + 10), relative=0)
            
            # === FOOTER TEXT ===
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, 22, "Confidential Project Assessment Report")
            self.drawRightString(width - 54, 22, "Spotter MLE Assessment 2026")
            
            self.restoreState()
            return

        # 2. Inside Pages styling (page 2+)
        self.saveState()
        
        # Header text
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4F46E5"))
        self.drawString(54, height - 36, "FreightAI Platform \u2014 ML Engineer Assessment Report")
        
        # Thin header rule
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, height - 42, width - 54, height - 42)
        
        # Thin footer rule
        self.line(54, 50, width - 54, 50)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 36, "Confidential Project Report \u2014 Spotter MLE Assessment 2026")
        
        # Page numbering
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - 54, 36, page_text)
        
        self.restoreState()


def _build_styles():
    styles = getSampleStyleSheet()
    
    # Cover Page Styles
    styles.add(
        ParagraphStyle(
            name="CoverLogo",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.white,
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=colors.white,
            spaceAfter=15,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#A5B4FC"),
            spaceAfter=30,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#94A3B8"),
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.white,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverLink",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#CBD5E1"),
            spaceAfter=6,
        )
    )

    # Document Section Styles
    styles.add(
        ParagraphStyle(
            name="ReportHeading1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E1B4B"),
            spaceBefore=16,
            spaceAfter=8,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportHeading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            leftIndent=20,
            firstLineIndent=-10,
            spaceAfter=4,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportCode",
            parent=styles["BodyText"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportTableText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportTableHeaderText",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=colors.white,
        )
    )
    return styles


def _format_inline(text: str) -> str:
    # Normalize special characters to avoid PDF Helvetica font failures
    text = text.replace("×", "x").replace("■", "-").replace("✅", "[Selected Winner]").replace("🏆", "[Winner]")
    parts = escape(text)
    # Match markdown bold **text** -> <b>text</b>
    parts = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', parts)
    # Match markdown inline code `code` -> <font name='Courier'>code</font>
    parts = re.sub(r'`(.*?)`', r"<font name='Courier'>\1</font>", parts)
    return parts


def _append_paragraph(story, styles, text: str):
    story.append(Paragraph(_format_inline(text), styles["ReportBody"]))


def _append_heading(story, styles, text: str, level: int):
    style_name = "ReportHeading1" if level == 1 else "ReportHeading2"
    story.append(Paragraph(escape(text), styles[style_name]))


def _append_bullets(story, styles, items: list[str]):
    for item in items:
        if re.match(r'^\d+\.\s', item):
            num_match = re.match(r'^(\d+\.)\s(.*)', item)
            bullet = num_match.group(1)
            text = num_match.group(2)
            story.append(Paragraph(_format_inline(text), styles["ReportBullet"], bulletText=bullet))
        else:
            story.append(Paragraph(_format_inline(item), styles["ReportBullet"], bulletText="&bull;"))


def make_styled_table(data_rows: list[list[str]], col_widths: list[float] | None = None) -> Table:
    header_style = ParagraphStyle(
        name="HeaderStyle",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        name="CellStyle",
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1F2937"),
    )
    
    formatted_data = []
    # Header row
    header_row = [Paragraph(f"<b>{cell}</b>", header_style) for cell in data_rows[0]]
    formatted_data.append(header_row)
    
    # Data rows
    for row in data_rows[1:]:
        formatted_row = []
        is_winner = any("GradientBoosting" in cell or "Winner" in cell or "selected winner" in cell.lower() for cell in row)
        for cell in row:
            if is_winner:
                p_text = f"<font color='#137333'><b>{_format_inline(cell)}</b></font>"
            else:
                p_text = _format_inline(cell)
            formatted_row.append(Paragraph(p_text, cell_style))
        formatted_data.append(formatted_row)
        
    t = Table(formatted_data, colWidths=col_widths)
    t.hAlign = 'CENTER'
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]
    
    # Row styles: alternate rows & winner highlighting
    for r_idx, row in enumerate(data_rows[1:]):
        real_idx = r_idx + 1
        is_winner = any("GradientBoosting" in cell or "Winner" in cell or "selected winner" in cell.lower() for cell in row)
        if is_winner:
            t_style.append(('BACKGROUND', (0, real_idx), (-1, real_idx), colors.HexColor("#E6F4EA")))
        elif real_idx % 2 == 0:
            t_style.append(('BACKGROUND', (0, real_idx), (-1, real_idx), colors.HexColor("#F8FAFC")))
            
    t.setStyle(TableStyle(t_style))
    return t


def _append_table_block(story, styles, lines: list[str]):
    data_rows = []
    for line in lines:
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if all(c.replace('-', '').strip() == '' for c in cells):
            continue
        data_rows.append(cells)
        
    if not data_rows:
        return
        
    num_cols = len(data_rows[0])
    width_avail = A4[0] - 108 # margins are 54pt each, so A4 width - 108
    
    # Detect widths based on headers
    headers = [h.lower() for h in data_rows[0]]
    if "dataset" in headers:
        col_widths = [120, 80, width_avail - 200]
    elif "step" in headers:
        col_widths = [140, width_avail - 140]
    elif "model" in headers or "algorithm" in headers:
        col_widths = [140, 100, 100, width_avail - 340]
    elif "parameter" in headers:
        col_widths = [140, 140, width_avail - 280]
    elif "metric" in headers:
        col_widths = [200, width_avail - 200]
    elif "period" in headers:
        col_widths = [100, 140, width_avail - 240]
    elif "endpoint" in headers:
        col_widths = [140, 80, width_avail - 220]
    elif "test" in headers:
        col_widths = [140, width_avail - 230, 90]
    elif "item" in headers:
        col_widths = [width_avail - 120, 120]
    else:
        col_widths = [width_avail / num_cols] * num_cols
        
    t = make_styled_table(data_rows, col_widths)
    story.append(t)
    story.append(Spacer(1, 4))


def _append_code_block(story, styles, lines: list[str]):
    text = "\n".join(lines)
    code_p = Preformatted(text, styles["ReportCode"])
    width_avail = A4[0] - 108
    t = Table([[code_p]], colWidths=[width_avail])
    t.hAlign = 'CENTER'
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))


# Max image height in pts — prevents tall images from overflowing a page and leaving blank space
MAX_IMG_HEIGHT = 260


def load_embedded_image(filename: str, width_pt: float = 440) -> Image | None:
    """Load an image and cap its height to MAX_IMG_HEIGHT to avoid blank overflow pages."""
    path = ROOT_DIR / "project" / "backend" / "charts" / filename
    if not path.exists():
        path = ROOT_DIR / "deliverables" / "plots" / filename

    if not path.exists():
        logger.warning(f"Image not found: {filename}")
        return None

    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as img:
            w, h = img.size
            aspect = h / w
    except Exception as e:
        logger.warning(f"Could not open image {filename} with PIL: {e}")
        aspect = 0.55

    height_pt = width_pt * aspect

    # Cap height — if image is too tall, shrink width proportionally
    if height_pt > MAX_IMG_HEIGHT:
        height_pt = MAX_IMG_HEIGHT
        width_pt = height_pt / aspect

    return Image(str(path), width=width_pt, height=height_pt)


def make_image_card(filename: str, caption: str, width_pt: float = 440) -> Table | Paragraph:
    img_flowable = load_embedded_image(filename, width_pt - 24)
    if img_flowable is None:
        return Paragraph(f"<i>Image missing: {filename}</i>", ParagraphStyle('err', fontName='Helvetica-Oblique', fontSize=9, textColor=colors.red))
        
    caption_style = ParagraphStyle(
        name="ImageCaptionStyle",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#94A3B8"),
        spaceBefore=6
    )
    
    content = [
        Spacer(1, 4),
        img_flowable,
        Paragraph(caption, caption_style),
        Spacer(1, 4)
    ]
    
    t = Table([[content]], colWidths=[width_pt])
    t.hAlign = 'CENTER'
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0F172A")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    return t


def draw_cover_background(canvas, doc):
    width, height = A4
    canvas.saveState()
    # Deep slate/navy background
    canvas.setFillColor(colors.HexColor("#0F172A"))
    canvas.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Accent bars
    canvas.setFillColor(colors.HexColor("#4F46E5")) # Primary Indigo
    canvas.rect(0, height - 15, width, 15, fill=True, stroke=False)
    canvas.setFillColor(colors.HexColor("#0EA5E9")) # Accent Blue
    canvas.rect(0, 0, width, 12, fill=True, stroke=False)
    
    # Decorative accent line on cover page
    canvas.setStrokeColor(colors.HexColor("#818CF8"))
    canvas.setLineWidth(3)
    canvas.line(54, height / 2 - 50, 150, height / 2 - 50)
    canvas.restoreState()


def generate_pdf_report() -> Path:
    """Generate the client-facing PDF report from the markdown source."""
    if not SOURCE_REPORT.exists():
        raise FileNotFoundError(f"Report source not found: {SOURCE_REPORT}")

    styles = _build_styles()
    story = []
    
    # ---------------------------------------------------------
    # COVER PAGE — drawn entirely by NumberedCanvas on page 1
    # We just push a blank page here; the canvas draws everything
    # ---------------------------------------------------------
    story.append(PageBreak())

    # ---------------------------------------------------------
    # PARSE AND APPEND CONTENT
    # ---------------------------------------------------------
    lines = SOURCE_REPORT.read_text(encoding="utf-8").splitlines()
    index = 0
    in_code_block = False
    code_lines: list[str] = []
    table_lines: list[str] = []
    bullet_lines: list[str] = []

    def flush_bullets():
        nonlocal bullet_lines
        if bullet_lines:
            _append_bullets(story, styles, bullet_lines)
            bullet_lines = []

    def flush_table():
        nonlocal table_lines
        if table_lines:
            _append_table_block(story, styles, table_lines)
            table_lines = []

    while index < len(lines):
        line = lines[index]

        # Handle code blocks
        if line.startswith("```"):
            if in_code_block:
                _append_code_block(story, styles, code_lines)
                code_lines = []
                in_code_block = False
            else:
                flush_bullets()
                flush_table()
                in_code_block = True
            index += 1
            continue

        if in_code_block:
            code_lines.append(line)
            index += 1
            continue

        stripped = line.strip()
        if not stripped:
            flush_bullets()
            flush_table()
            story.append(Spacer(1, 4))
            index += 1
            continue

        # Handle headings
        if stripped.startswith("# "):
            flush_bullets()
            flush_table()
            _append_heading(story, styles, stripped[2:].strip(), 1)
        elif stripped.startswith("## "):
            flush_bullets()
            flush_table()
            
            heading_text = stripped[3:].strip()
            
            # Intercept section headings to inject charts/diagrams!
            # 1. Before Train / Validation Split — inject UML diagrams after Section 2
            if heading_text.startswith("3."):
                story.append(PageBreak())
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>System Architecture &amp; UML Diagrams</b>", styles["ReportHeading2"]))
                story.append(Spacer(1, 4))
                story.append(make_image_card("architecture_diagram.png", "Figure 2.1: End-to-End System Architecture (FastAPI + SPA + Optuna + SHAP)"))
                story.append(Spacer(1, 6))
                story.append(make_image_card("use_case_diagram.png", "Figure 2.2: Platform Use Case Diagram (Shipper, Broker &amp; Analyst Workflows)"))
                story.append(Spacer(1, 6))
                story.append(make_image_card("sequence_diagram.png", "Figure 2.3: Single Spot Rate Prediction Execution Sequence"))
                story.append(Spacer(1, 6))

            # 2. Before Preprocessing Pipeline — inject EDA charts after Section 3
            elif heading_text.startswith("4."):
                story.append(PageBreak())
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Exploratory Data Analysis &amp; Data Insights</b>", styles["ReportHeading2"]))
                story.append(Spacer(1, 4))
                story.append(make_image_card("target_distribution.png", "Figure 3.1: Distribution of Posted Freight Rates (USD)"))
                story.append(Spacer(1, 6))
                story.append(make_image_card("correlation_heatmap.png", "Figure 3.2: Feature Correlation Matrix Heatmap"))
                story.append(Spacer(1, 6))

            # 3. Before Model Interpretability — inject holdout eval charts after Section 8
            elif heading_text.startswith("9."):
                story.append(PageBreak())
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Model Performance &amp; Error Analysis (Holdout Validation)</b>", styles["ReportHeading2"]))
                story.append(Spacer(1, 4))
                story.append(make_image_card("prediction_scatter.png", "Figure 5.1: Actual vs. Predicted Freight Rates (Holdout Set)"))
                story.append(Spacer(1, 6))
                story.append(make_image_card("residuals.png", "Figure 5.2: Error Residual Distribution &amp; Normal Q-Q Alignment"))
                story.append(Spacer(1, 6))

            # 4. Before Predictions CSV — inject SHAP/XAI charts after Section 9
            elif heading_text.startswith("10."):
                story.append(PageBreak())
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Model Interpretability (XAI) Charts</b>", styles["ReportHeading2"]))
                story.append(Spacer(1, 4))
                story.append(make_image_card("shap_summary.png", "Figure 6.1: Global SHAP Summary Beeswarm Plot (Top Feature Directional Impact)"))
                story.append(Spacer(1, 6))
                story.append(make_image_card("feature_importance.png", "Figure 6.2: Relative Impurity Feature Importance Ranking"))
                story.append(Spacer(1, 6))

            # 5. Before API Endpoints — inject December forecast chart after Section 11
            elif heading_text.startswith("12."):
                story.append(PageBreak())
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>December 2025 Daily Spot Rate Forecast</b>", styles["ReportHeading2"]))
                story.append(Spacer(1, 4))
                story.append(make_image_card("december_forecast.png", "Figure 7.1: December 2025 Daily Spot Rate Forecast with Annotated Seasonal Trend Dynamics"))
                story.append(Spacer(1, 6))

            _append_heading(story, styles, heading_text, 2)
            
        # Handle lists
        elif stripped.startswith(('- ', '* ')):
            flush_table()
            bullet_lines.append(stripped[2:].strip())
        elif stripped.startswith(tuple(f"{number}. " for number in range(1, 10))):
            flush_table()
            bullet_lines.append(stripped)
            
        # Handle tables
        elif stripped.startswith("|"):
            flush_bullets()
            table_lines.append(stripped)
            
        # Handle regular paragraphs
        else:
            flush_bullets()
            flush_table()
            _append_paragraph(story, styles, stripped)

        index += 1

    flush_bullets()
    flush_table()

    # Generate document
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    logger.info(f"PDF report written to {OUTPUT_PDF}")
    return OUTPUT_PDF


if __name__ == "__main__":
    generate_pdf_report()
