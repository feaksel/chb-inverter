"""
Generate the ELE 402 Final Report PDF for the 5-Level CHB Inverter project.

Follows the Hacettepe University EEE ELE402 final-report template structure:
- Title page (with Hacettepe logo)
- Abstract
- Table of contents
- List of figures and tables
- 1. Introduction
- 2. Project Description
- 3. Engineering Standards and Design Constraints
- 4. Sustainable Development Goals
- 5. Literature Review (Background)
- 6. Methods
- 7. Preliminary Design
- 8. Prototype (First Prototype)
- 9. Design Iterations
- 10. Final Design (+ meeting constraints, cost analysis)
- 11. Teamwork
- 12. Comments and Conclusions
- References

Run: py -3.12 tools/generate-final-report.py
Output: docs/assets/pdfs/ELE402_Spring2026_FR_CereyanHacilari.pdf
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, ListFlowable, ListItem,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    NextPageTemplate,
)
from reportlab.platypus.flowables import HRFlowable

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None


# ===== Fonts (with Turkish character support) ========================================
# Helvetica (default PDF font) doesn't have ı, ş, ğ, ç, ü, ö. Register Arial from
# Windows fonts (or DejaVu Sans on Linux/Mac) so Turkish names render correctly.

def _register_fonts() -> tuple[str, str, str, str]:
    candidates = [
        # (family-name, regular, bold, italic, bold-italic)
        ("Arial",
         "C:/Windows/Fonts/arial.ttf",
         "C:/Windows/Fonts/arialbd.ttf",
         "C:/Windows/Fonts/ariali.ttf",
         "C:/Windows/Fonts/arialbi.ttf"),
        ("DejaVu",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    ]
    for fam, reg, bold, ita, bi in candidates:
        if all(os.path.exists(p) for p in (reg, bold, ita, bi)):
            try:
                pdfmetrics.registerFont(TTFont(f"{fam}", reg))
                pdfmetrics.registerFont(TTFont(f"{fam}-Bold", bold))
                pdfmetrics.registerFont(TTFont(f"{fam}-Italic", ita))
                pdfmetrics.registerFont(TTFont(f"{fam}-BoldItalic", bi))
                registerFontFamily(fam,
                                   normal=fam, bold=f"{fam}-Bold",
                                   italic=f"{fam}-Italic", boldItalic=f"{fam}-BoldItalic")
                print(f"  font: registered {fam} (Turkish characters supported)")
                return fam, f"{fam}-Bold", f"{fam}-Italic", f"{fam}-BoldItalic"
            except Exception as exc:
                print(f"  font: {fam} registration failed: {exc}")
                continue
    print("  font: WARNING — falling back to Helvetica (no Turkish character support)")
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"


FONT, FONT_BOLD, FONT_ITALIC, FONT_BOLDITALIC = _register_fonts()


# ===== Constants =====================================================================

REPO = Path(__file__).resolve().parent.parent
IMG = REPO / "docs" / "assets" / "images"
OUT = REPO / "docs" / "assets" / "pdfs" / "ELE402_Spring2026_FR_CereyanHacilari.pdf"

# Color palette — teal/slate matches the docs site theme; conservative for academic
TEAL = colors.HexColor("#00695C")
TEAL_DARK = colors.HexColor("#004D40")
AMBER = colors.HexColor("#FF8F00")
GREY_LIGHT = colors.HexColor("#ECEFF1")
GREY_TEXT = colors.HexColor("#37474F")
GREY_RULE = colors.HexColor("#B0BEC5")


# ===== Styles =========================================================================

_base = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "Title", parent=_base["Title"],
    fontName=FONT_BOLD, fontSize=24, leading=30,
    alignment=TA_CENTER, textColor=TEAL_DARK, spaceAfter=10,
)
SUBTITLE = ParagraphStyle(
    "Subtitle", parent=_base["Title"],
    fontName=FONT_BOLD, fontSize=18, leading=22,
    alignment=TA_CENTER, textColor=TEAL_DARK, spaceAfter=20,
)
TITLE_PAGE_LABEL = ParagraphStyle(
    "TitlePageLabel", parent=_base["Normal"],
    fontName=FONT_BOLD, fontSize=11, leading=14,
    alignment=TA_CENTER, textColor=GREY_TEXT, spaceAfter=4,
)
TITLE_PAGE_VALUE = ParagraphStyle(
    "TitlePageValue", parent=_base["Normal"],
    fontName=FONT, fontSize=11, leading=14,
    alignment=TA_CENTER, textColor=colors.black, spaceAfter=16,
)

H1 = ParagraphStyle(
    "H1", parent=_base["Heading1"],
    fontName=FONT_BOLD, fontSize=18, leading=22,
    textColor=TEAL_DARK, spaceBefore=18, spaceAfter=12,
    keepWithNext=True,
)
H2 = ParagraphStyle(
    "H2", parent=_base["Heading2"],
    fontName=FONT_BOLD, fontSize=14, leading=18,
    textColor=TEAL, spaceBefore=14, spaceAfter=8,
    keepWithNext=True,
)
H3 = ParagraphStyle(
    "H3", parent=_base["Heading3"],
    fontName=FONT_BOLD, fontSize=12, leading=16,
    textColor=TEAL, spaceBefore=10, spaceAfter=6,
    keepWithNext=True,
)
BODY = ParagraphStyle(
    "Body", parent=_base["BodyText"],
    fontName=FONT, fontSize=10.5, leading=15,
    alignment=TA_JUSTIFY, spaceAfter=8, textColor=colors.black,
)
BODY_BOLD = ParagraphStyle("BodyBold", parent=BODY, fontName=FONT_BOLD)
BULLET = ParagraphStyle(
    "Bullet", parent=BODY, leftIndent=18, bulletIndent=6, spaceAfter=4,
)
CAPTION = ParagraphStyle(
    "Caption", parent=BODY,
    fontName=FONT_ITALIC, fontSize=9.5, leading=13,
    alignment=TA_CENTER, textColor=GREY_TEXT, spaceBefore=2, spaceAfter=14,
)
CELL = ParagraphStyle(
    "Cell", parent=BODY,
    fontName=FONT, fontSize=9, leading=12,
    alignment=TA_LEFT, spaceAfter=0, spaceBefore=0,
)
CELL_HEADER = ParagraphStyle(
    "CellHeader", parent=CELL,
    fontName=FONT_BOLD, textColor=colors.white,
)
REF = ParagraphStyle(
    "Ref", parent=BODY, fontSize=9.5, leading=13, leftIndent=20,
    bulletIndent=6, spaceAfter=4,
)
TOC_ENTRY = ParagraphStyle(
    "TOC", parent=BODY, fontSize=10.5, leading=18, spaceAfter=0,
)
LABEL = ParagraphStyle(
    "Label", parent=BODY, fontName=FONT_BOLD,
    textColor=GREY_TEXT, fontSize=9.5, leading=13,
)


# ===== Figure registry =================================================================

_FIGURES: list[tuple[int, str, str]] = []
_TABLES: list[tuple[int, str]] = []


def fig(path: str, caption: str, width_cm: float = 14) -> list:
    """Register a numbered figure and produce the flowables that render it."""
    n = len(_FIGURES) + 1
    _FIGURES.append((n, str(path.name), caption))
    p = IMG / path
    if not p.exists():
        # Render a placeholder text block if image missing
        return [
            Paragraph(f"<i>[Figure {n} — image not available: {path}]</i>", CAPTION),
            Paragraph(f"<b>Figure {n}.</b> {caption}", CAPTION),
        ]
    img = Image(str(p))
    # Scale to width_cm preserving aspect
    src_w, src_h = img.imageWidth, img.imageHeight
    target_w = width_cm * cm
    target_h = target_w * src_h / src_w
    # Hard cap height so a tall image doesn't overflow the page
    max_h = 18 * cm
    if target_h > max_h:
        target_h = max_h
        target_w = target_h * src_w / src_h
    img.drawWidth = target_w
    img.drawHeight = target_h
    img.hAlign = "CENTER"
    return [
        Spacer(0, 4),
        img,
        Paragraph(f"<b>Figure {n}.</b> {caption}", CAPTION),
    ]


def table_caption(caption: str) -> Paragraph:
    n = len(_TABLES) + 1
    _TABLES.append((n, caption))
    return Paragraph(f"<b>Table {n}.</b> {caption}", CAPTION)


def _clean_text(text: str) -> str:
    """Strip em/en-dashes and normalise whitespace for clean PDF output."""
    return (text.strip()
                .replace("\n", " ")
                .replace("—", "-")
                .replace("–", "-"))


def themed_table(data: list[list], col_widths: list[float] | None = None,
                 first_row_header: bool = True, first_col_label: bool = False) -> Table:
    """Build a small data table with the report's teal accent.

    Cell strings are wrapped in Paragraph flowables so text wraps inside the
    cell. Em-dashes are stripped from cell content.
    """
    def wrap(item, *, header: bool):
        if isinstance(item, Paragraph):
            return item
        if isinstance(item, str):
            style = CELL_HEADER if header else CELL
            return Paragraph(_clean_text(item), style)
        return item

    wrapped = []
    for r_idx, row in enumerate(data):
        wrapped.append([wrap(c, header=(first_row_header and r_idx == 0))
                        for c in row])

    t = Table(wrapped, colWidths=col_widths,
              repeatRows=1 if first_row_header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, GREY_RULE),
    ]
    if first_row_header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), TEAL))
    if first_col_label:
        # When first col is a label, swap its cell style to bold-but-not-header
        for r in range(1, len(wrapped)):
            cell = wrapped[r][0]
            if isinstance(cell, Paragraph):
                wrapped[r][0] = Paragraph(_clean_text(cell.text), CELL_HEADER)
    t.setStyle(TableStyle(style))
    return t


# ===== Page templates ==================================================================

class FooterCanvas(canvas.Canvas):
    """Adds 'Page N of M' footer and a thin teal rule on every body page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states: list = []

    def showPage(self):
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total: int):
        page = self._pageNumber
        # Skip footer on title page (page 1)
        if page == 1:
            return
        self.saveState()
        self.setStrokeColor(TEAL)
        self.setLineWidth(0.6)
        self.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
        self.setFont("Helvetica", 9)
        self.setFillColor(GREY_TEXT)
        self.drawString(2 * cm, 1.1 * cm, "ELE 402 — Cereyan Hacıları — 5-Level CHB Inverter Final Report")
        self.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {page} of {total}")
        self.restoreState()


def _build_doc() -> BaseDocTemplate:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.0 * cm, bottomMargin=2.2 * cm,
        title="ELE 402 Final Report — 5-Level Cascaded H-Bridge Inverter",
        author="Cereyan Hacıları (F. E. Aksel, A. Koçak, F. G. Abay, M. Aydın)",
        subject="ELE 402 Graduation Project II Final Report",
        creator="reportlab + tools/generate-final-report.py",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="body")
    body = PageTemplate(id="body", frames=[frame])
    doc.addPageTemplates([body])
    return doc


# ===== Helper for paragraphs =========================================================

def P(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    """Build a Paragraph, normalising whitespace and stripping em-dashes."""
    return Paragraph(_clean_text(text), style)


def bullets(items: list[str], style: ParagraphStyle = BULLET) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(it, style), leftIndent=12) for it in items],
        bulletType="bullet", bulletColor=TEAL, leftIndent=18, bulletFontSize=10,
    )


def numbered(items: list[str], style: ParagraphStyle = BULLET) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(it, style), leftIndent=12) for it in items],
        bulletType="1", bulletColor=TEAL, leftIndent=18, bulletFontSize=10,
    )


# ===== Content builders ================================================================

def title_page() -> list:
    story = []
    story.append(Spacer(0, 1.2 * cm))
    story.append(P("ELE 402 — GRADUATION PROJECT II", TITLE))
    story.append(P("FINAL REPORT", SUBTITLE))
    story.append(Spacer(0, 0.4 * cm))

    # Hacettepe logo — explicit w + h from PIL so aspect ratio is preserved
    logo_path = IMG / "hacettepe-logo.png"
    if logo_path.exists():
        target = 5 * cm
        # Get true pixel dimensions
        if PILImage is not None:
            with PILImage.open(logo_path) as im:
                w_px, h_px = im.size
        else:
            tmp = Image(str(logo_path))
            w_px, h_px = tmp.imageWidth, tmp.imageHeight
        # Fit into target × target box, preserve aspect
        if h_px >= w_px:
            h = target
            w = target * w_px / h_px
        else:
            w = target
            h = target * h_px / w_px
        logo = Image(str(logo_path), width=w, height=h)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(0, 0.4 * cm))

    story.append(P("HACETTEPE UNIVERSITY", TITLE_PAGE_LABEL))
    story.append(P("DEPARTMENT OF ELECTRICAL AND ELECTRONICS ENGINEERING", TITLE_PAGE_LABEL))
    story.append(Spacer(0, 0.8 * cm))

    story.append(P("PROJECT GROUP", TITLE_PAGE_LABEL))
    story.append(P("Cereyan Hacıları", TITLE_PAGE_VALUE))

    story.append(P("PROJECT TITLE", TITLE_PAGE_LABEL))
    story.append(P(
        "Design and Implementation of a 5-Level Cascaded H-Bridge "
        "Multilevel Inverter with PWM-Based Control",
        TITLE_PAGE_VALUE,
    ))

    story.append(P("PROJECT GROUP MEMBERS", TITLE_PAGE_LABEL))
    story.append(P("Furkan Emir Aksel · Ahmet Koçak · Faruk Gökhan Abay · Mücahit Aydın",
                   TITLE_PAGE_VALUE))

    story.append(P("PROJECT SUPERVISOR", TITLE_PAGE_LABEL))
    story.append(P("Assoc. Prof. Dr. Rasım Doğan", TITLE_PAGE_VALUE))

    story.append(P("SUBMISSION DATE", TITLE_PAGE_LABEL))
    story.append(P("June 2026", TITLE_PAGE_VALUE))

    story.append(Spacer(0, 1.5 * cm))
    story.append(P("SPRING 2025–2026", TITLE_PAGE_LABEL))

    story.append(PageBreak())
    return story


def abstract_page() -> list:
    story = []
    story.append(P("ABSTRACT", H1))
    story.append(P("""
        This report documents the design, fabrication, firmware development, bench
        validation, and demonstration of a <b>single-phase 5-level cascaded
        H-bridge (CHB) multilevel inverter</b>, built as the ELE 401 / 402
        graduation project at Hacettepe University EEE during the 2025–26 academic
        year. The system uses <b>two identical single-bridge PCB modules</b>
        (4-layer JLCPCB-fabricated, IRFB4110 N-channel MOSFETs) cascaded externally
        so their AC outputs sum to five distinct voltage levels at the inverter
        terminals. The controller is an STM32 Nucleo-F303RE running
        <b>phase-shifted carrier PWM (PSC-PWM)</b> at 5 kHz with hardware-enforced
        3 µs dead time. Isolated bit-banged MCP3201 SPI ADCs sense per-bridge DC
        bus voltages and output current via 6N137 optocouplers; an isolated 5 V
        → 15 V B0515S DC-DC supplies the TLP250 optical gate drivers per bridge.
        A PySide6 desktop dashboard provides full operator control, 20 Hz
        telemetry visualization, replay, and a PC-only fault-scenario simulator.
        The headline bench result, achieved after the ELE 401 simulation phase
        and four hardware iterations: <b>five distinct cascade output levels
        visible on the oscilloscope at 100 V cascade output</b>, under sustained
        5 kHz PSC-PWM operation with no output filter; both bridges thermally
        matched within ≈ 3 °C; no false sensor-loss or protection-trip events
        across multi-minute runs. The system meets IEEE 519-2022 voltage-THD
        compliance margin (Simulink prediction 4.9 %, well below the 8 % limit).
    """))
    story.append(PageBreak())
    return story


def toc_page() -> list:
    story = []
    story.append(P("TABLE OF CONTENTS", H1))
    entries = [
        ("ABSTRACT", "1"),
        ("TABLE OF CONTENTS", "2"),
        ("LIST OF FIGURES AND TABLES", "3"),
        ("1. INTRODUCTION", "4"),
        ("2. PROJECT DESCRIPTION", "5"),
        ("3. ENGINEERING STANDARDS AND DESIGN CONSTRAINTS", "7"),
        ("    3.1. Engineering Standards", "7"),
        ("    3.2. Design Constraints", "8"),
        ("4. SUSTAINABLE DEVELOPMENT GOALS", "10"),
        ("5. LITERATURE REVIEW", "11"),
        ("    5.1. Multilevel inverter theory", "11"),
        ("    5.2. Level-shifted and phase-shifted carrier PWM", "12"),
        ("    5.3. Gate-driver requirements in CHB topology", "12"),
        ("    5.4. Power semiconductor selection at low voltage", "13"),
        ("6. METHODS", "14"),
        ("    6.1. Method 1 — Cascaded H-Bridge with PSC-PWM", "14"),
        ("    6.2. Method 2 — Alternative topologies and modulators (evaluated)", "16"),
        ("7. PRELIMINARY DESIGN", "17"),
        ("8. PROTOTYPE", "19"),
        ("9. DESIGN ITERATIONS", "21"),
        ("    9.1. Iteration 1 — single dual-bridge PCB, IRFZ44N, IPD LS-PWM", "21"),
        ("    9.2. Iteration 2 — revised gate-drive routing, bootstrap lessons", "23"),
        ("    9.3. Iteration 3 — per-bridge isolation, MISO rework, MOSFET swap", "25"),
        ("    9.4. Iteration 4 — as-built (single-bridge modules, IRFB4110, PSC)", "27"),
        ("10. FINAL DESIGN", "29"),
        ("    10.1. Meeting the constraints and engineering standards", "32"),
        ("    10.2. Cost analysis", "33"),
        ("11. TEAMWORK", "34"),
        ("12. COMMENTS AND CONCLUSIONS", "35"),
        ("REFERENCES", "37"),
    ]
    # Build TOC as table for clean alignment
    data = [[Paragraph(name, TOC_ENTRY), Paragraph(page, TOC_ENTRY)]
            for name, page in entries]
    t = Table(data, colWidths=[None, 1.3 * cm])
    t.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story


def list_of_figures_tables_page() -> list:
    """Filled after the rest of the report has been assembled; we list both
    figure and table captions with their numbers."""
    story = []
    story.append(P("LIST OF FIGURES AND TABLES", H1))
    story.append(P("Figures", H2))
    for n, _name, cap in _FIGURES:
        story.append(P(f"Figure {n}. {cap}", TOC_ENTRY))
    story.append(Spacer(0, 0.5 * cm))
    story.append(P("Tables", H2))
    for n, cap in _TABLES:
        story.append(P(f"Table {n}. {cap}", TOC_ENTRY))
    story.append(PageBreak())
    return story


# --- Body sections ----------------------------------------------------------------------

def section_introduction() -> list:
    s = [P("1. INTRODUCTION", H1)]
    s.append(P("""
        This report consolidates the final state of the ELE 402 Graduation Project II
        carried out by the project group <b>Cereyan Hacıları</b> at Hacettepe
        University, Department of Electrical and Electronics Engineering, during
        the Spring 2025–2026 semester. The project was launched in the ELE 401
        Fall 2025 semester with a focus on simulation, topology selection, and
        preliminary component justification. The interim report (ELE 402 v4)
        documented progress through PCB fabrication and the start of bring-up;
        this final report covers the remaining work — completion of bench
        validation across four hardware iterations, firmware finalisation
        through the <i>pwm-rewrite-configurable</i> branch, the consolidation of
        the team's bring-up notes, and the public demonstration.
    """))
    s.append(P("""
        The headline accomplishment in this period: the inverter was driven to
        its design operating point (100 V cascade output, 5 kHz PSC-PWM, no
        output filter) and produced <b>five distinct cascade output levels
        visible on the oscilloscope</b> with both bridges thermally matched
        within ≈ 3 °C, satisfying the project deliverable specification agreed
        with the supervisor at the 23 October 2025 project meeting.
    """))
    s.append(P("""
        The work since the ELE 402 interim report added: (a) the
        <i>pwm-rewrite-configurable</i> firmware branch, which introduced the
        PSC modulator with a runtime carrier-phase lock diagnostic and replaced
        the original IPD LS-PWM modulator that had caused bridge-thermal
        asymmetry; (b) the iteration-4 hardware re-architecture, in which the
        single dual-bridge PCB was split into two identical single-bridge
        modules with a 4-layer stack-up that resolves the iteration-3 grounding
        problem; (c) the substitution of IRFB4110 MOSFETs for the IRFZ44N parts
        originally specified in Build Guide v3.1, with corresponding firmware
        dead-time adjustment; (d) the PySide6 operator dashboard, including its
        auto-cancel of the firmware's auto-start path when an operator is
        present; and (e) the completion of the four bench-validation phases
        documented in the FIRST_BENCH_SESSION and HARDWARE_BRINGUP reference
        documents that now ship alongside the firmware source.
    """))
    s.append(P("""
        The remainder of this report is organised per the ELE 402 template
        guidance: the project description and the engineering standards and
        design constraints that bound the work; the Sustainable Development
        Goals the project advances; the literature and theoretical background;
        the methods evaluated and chosen; the preliminary design; the prototype
        as it stood at the end of ELE 401; the four design iterations through
        the Spring 2026 semester; the final design with constraint satisfaction
        and cost analysis; the teamwork structure; and the concluding
        comments, takeaways, and proposed future work.
    """))
    s.append(PageBreak())
    return s


def section_project_description() -> list:
    s = [P("2. PROJECT DESCRIPTION", H1)]
    s.append(P("""
        The project is a <b>single-phase 5-level cascaded H-bridge multilevel
        inverter</b>, designed to convert two independent isolated DC sources
        into an AC output with five distinct voltage levels at the inverter
        terminals. The system is intended as a laboratory-scale demonstration
        of multilevel inverter principles, suitable for power-electronics
        teaching, with a clear path toward extension to a deployable off-grid
        or grid-tied power converter.
    """))
    s.append(P("System configuration", H3))
    s.append(P("""
        Two identical single-bridge PCB modules are cascaded externally so
        their AC outputs sum. Each module hosts a full H-bridge — four
        N-channel power MOSFETs in TO-220 packages — together with its own
        isolated 15 V gate-drive supply, optical gate drivers, and isolated
        ADC sensing chain. The two modules are driven from a common STM32
        Nucleo-F303RE controller and share a single operator dashboard over
        UART, but their power-side electronics are fully isolated from each
        other and from the controller.
    """))
    s.extend(fig(Path("inverter-pcb.png"),
                 "Populated single-bridge v4 PCB module — IRFB4110 H-bridge with TLP250 "
                 "optical gate drive and isolated MCP3201 sensing. Two identical instances "
                 "of this module are cascaded externally to produce the 5-level output.",
                 width_cm=14))
    s.append(P("System block diagram", H3))
    s.extend(fig(Path("diagram-system-block.png"),
                 "System block diagram - two H-bridge cells driven from a single "
                 "STM32 controller. Solid arrows are PWM (TIM1 / TIM8); dotted "
                 "arrows are isolated MCP3201 sensing returns through 6N137 "
                 "optocouplers. The dashboard talks to the controller over UART.",
                 width_cm=15))
    s.append(P("Key specifications", H3))
    spec_table = themed_table([
        ["Parameter", "Value"],
        ["Topology", "5-level Cascaded H-Bridge, 2 cells"],
        ["Per-bridge DC bus", "50 V nominal (5–60 V runtime-tunable via VNOM)"],
        ["Cascade output", "±100 V peak, 5 distinct levels"],
        ["Output power", "≈ 400 W demonstrated; design ceiling ≈ 700 W"],
        ["Power MOSFET", "IRFB4110 (100 V, 180 A, 4.5 mΩ R_DS(on))"],
        ["Gate drive", "TLP250 optical (2.5 kV galvanic) + B0515S isolated 15 V"],
        ["Sensing", "MCP3201 12-bit SPI ADC × 3, isolated via 6N137 optocouplers"],
        ["Current sensing", "ACS712 Hall-effect (100 mV/A, 2.5 V zero, per bridge)"],
        ["Controller", "STM32 Nucleo-F303RE, Cortex-M4 at 64 MHz (HSI/2 × PLL)"],
        ["Modulator (as-built)", "PSC-PWM at 5 kHz, runtime-tunable 100 Hz – 20 kHz"],
        ["Dead time", "3 µs (hardware-enforced via BDTR.DTG = 0xA0)"],
        ["Protection", "UV / OV / OC / IMBAL with 3 ms N-of-M debounce + FAULT_OUT pin"],
        ["Operator UI", "PySide6 dashboard, UART 115200 8N1, 20 Hz telemetry"],
        ["PCB", "4-layer FR-4 TG155, JLCPCB-fabricated, 1.6 mm thickness"],
    ], col_widths=[5 * cm, 11 * cm])
    s.append(table_caption("Headline specifications of the as-built single-bridge v4 module."))
    s.append(spec_table)
    s.append(Spacer(0, 0.4 * cm))
    s.append(P("Operator interaction", H3))
    s.append(P("""
        The controller exposes a single USART2 link over the Nucleo's ST-LINK
        virtual COM port. A line-based command protocol gives the operator
        runtime control over every relevant parameter — modulator selection,
        switching frequency, fundamental frequency, modulation index,
        single-bridge isolation mode, nominal bus voltage for protection
        scaling, and overcurrent trip. A 20 Hz NMEA-style telemetry frame
        returns state, sensing mode, fault bits, all sensor values, and the
        current modulator level. Each PWM configuration change emits a fresh
        configuration line carrying the measured TIM8 ↔ TIM1 counter offset
        and a <i>lock=OK|BAD</i> status, so the operator can confirm the PSC
        carrier phase is locked before arming the bridges.
    """))
    s.append(PageBreak())
    return s


def section_standards_constraints() -> list:
    s = [P("3. ENGINEERING STANDARDS AND DESIGN CONSTRAINTS", H1)]
    s.append(P("""
        The design is bounded by both formal engineering standards (international
        and domestic) and a set of project-specific realistic constraints. This
        section identifies the standards adopted and the constraints applied.
        Both were established in the ELE 401 interim report; this final report
        documents how the as-built system satisfies each.
    """))
    s.append(P("3.1. Engineering standards", H2))
    s.append(P("""
        The following standards apply to the project. Each is briefly described,
        with the specific clauses or limits that affected design decisions.
    """))
    s.append(P("IEEE 519-2022 — Harmonic Control in Electric Power Systems", H3))
    s.append(P("""
        IEEE 519-2022 establishes voltage and current distortion limits for
        power systems. For systems rated below 1 kV at the Point of Common
        Coupling, total voltage distortion (THD<sub>V</sub>) must not exceed
        <b>8 %</b>. The project targets THD<sub>V</sub> &lt; 5 % to provide
        comfortable margin. The Simulink simulation of the as-designed LS-PWM
        modulator produced THD<sub>V</sub> = <b>4.9 %</b> at the headline
        operating point pre-filter, satisfying the target. Bench measurement
        of THD is deferred to the future-work LC-filter integration phase.
        The methodology for THD measurement follows IEC 61000-4-7 — 10-cycle
        rectangular windows for the 50 Hz system.
    """))
    s.append(P("IEEE 1547-2018 — Distributed Energy Resource Interconnection", H3))
    s.append(P("""
        IEEE 1547-2018 governs interconnection between distributed energy
        resources and the utility grid. The project is bench-validated as a
        stand-alone inverter; grid-coupling compliance work is outside the
        graduation deliverable scope. The control architecture was nevertheless
        designed with future grid-tie in mind — the modulation pipeline is
        clean enough to accept a SOGI phase-locked loop, and the protection
        chain already supports the anti-islanding semantics IEEE 1547-2018 §4.6
        would require (latched fault on sensor or condition loss, with operator
        clear). See §12 for the future-work discussion.
    """))
    s.append(P("IEC 61000-4-7:2002 — Harmonic Measurement Methodology", H3))
    s.append(P("""
        IEC 61000-4-7 defines the measurement methodology for harmonic and
        interharmonic content. The simulation harmonic analysis uses 10-cycle
        FFT windows with rectangular weighting as per the standard. The
        post-bench FFT analysis (a future work item) will follow the same
        methodology to ensure direct comparability with the simulation.
    """))
    s.append(P("3.2. Design constraints", H2))
    s.append(P("""
        Beyond formal standards, six realistic constraints shaped the design.
        Each is identified below with the design decision it produced.
    """))
    s.append(P("Voltage and current ratings (semiconductor headroom)", H3))
    s.append(P("""
        Each H-bridge module operates at 50 V DC input nominal. The MOSFET
        breakdown voltage V<sub>DSS</sub> must exceed the bus voltage with
        sufficient margin to absorb switching transients and any TVS-clamped
        spikes. Iteration 1 used IRFZ44N (V<sub>DSS</sub> = 55 V) with only
        ≈ 10 % nominal headroom, which gate-loop ringing readily exceeded.
        Iteration 4 substituted IRFB4110 (V<sub>DSS</sub> = 100 V),
        approximately doubling headroom and bringing the protection chain (TVS
        clamping at 84.5 V) safely below MOSFET breakdown. Continuous current
        rating is ≥ 5 A RMS with comfortable margin to the 49 A / 180 A
        ratings of the two MOSFET candidates.
    """))
    s.append(P("Galvanic isolation between cells (topology requirement)", H3))
    s.append(P("""
        The CHB topology requires absolute galvanic isolation between every
        non-ground-referenced bridge and the controller. This is not a
        preference but a structural consequence of the cascaded series
        connection — the upper bridge's source nodes float at the cascade
        voltage minus their bridge voltage. Bootstrap-based gate drivers
        (IR2110 and similar) fundamentally cannot supply gate voltage
        referenced to a floating V<sub>S</sub> that never returns to true
        ground each PWM period. This was simulation-validated in Simulink
        (see §5.3 and §6.1) before silicon was committed, and led to the
        TLP250 + B0515S isolated-driver chain in the as-built design.
    """))
    s.append(P("Total harmonic distortion (output power quality)", H3))
    s.append(P("""
        Per IEEE 519-2022, THD<sub>V</sub> &lt; 5 % at the inverter terminals.
        Met in simulation (4.9 %). Bench FFT pending the LC-filter integration.
    """))
    s.append(P("Control loop timing (real-time constraint)", H3))
    s.append(P("""
        The STM32 must execute the modulator update within the PWM period:
        200 µs at 5 kHz. The TIM1 update IRQ handler (the modulator hot path)
        is measured at ≈ 16 µs per invocation — well within budget. The 1 kHz
        sensing loop and the 20 Hz telemetry loop are both serviced in the
        main loop with adequate headroom.
    """))
    s.append(P("Cost (academic project budget)", H3))
    s.append(P("""
        The project targets a per-PCB BOM under 1500 TL and a project-total
        under 2500 TL including spares. The as-built BOM (Table 5 in §10.2)
        is ≈ 1985 TL for two modules plus spares. Components sourced
        exclusively from Turkish domestic suppliers (Motorobit, Direnc.net,
        Robotistan) to avoid international shipping and customs friction.
    """))
    s.append(P("Safety and protection (operator and equipment)", H3))
    s.append(P("""
        Multi-layer protection: hardware (TVS, fuse, RC snubber), firmware
        (UV / OV / OC / IMBAL with N-of-M debounce, sensor-lost detection,
        operator-forced TRIP), and an active-LOW hardware FAULT_OUT pin for
        external interlock. All MOSFETs are guaranteed off in BOOT / IDLE /
        FAULT via TLP250 non-inverting topology + BDTR.OSSI = 1, so any
        firmware state where the bridge is nominally disabled actually drives
        every MOSFET off.
    """))
    s.append(PageBreak())
    return s


def section_sdg() -> list:
    s = [P("4. SUSTAINABLE DEVELOPMENT GOALS", H1)]
    s.append(P("""
        Three of the United Nations Sustainable Development Goals are directly
        advanced by this project. Each is discussed below with the specific
        contribution the project makes.
    """))
    s.append(P("Goal 7 — Affordable and Clean Energy", H3))
    s.append(P("""
        Targets 7.2 (increase renewable energy share) and 7.3 (double energy
        efficiency improvement rate) are both addressed. The CHB topology is
        especially well-matched to renewable-energy integration: the requirement
        for isolated DC sources per cell maps naturally to independent
        photovoltaic strings or battery packs. The project's &gt; 95 %
        efficiency target (achieved in simulation; consistent with the bench
        thermal observations) maximises the fraction of renewable energy
        delivered to the load. The modular two-PCB architecture supports
        scaling from small residential to medium-power industrial deployments
        by adding cells rather than redesigning the controller.
    """))
    s.append(P("Goal 9 — Industry, Innovation and Infrastructure", H3))
    s.append(P("""
        Targets 9.4 (upgrade infrastructure for sustainability) and 9.5
        (enhance scientific research capabilities) are addressed. The project
        advances multilevel-inverter control practice through the runtime
        carrier-phase lock diagnostic — a small piece of defensive
        instrumentation that catches a real failure mode (TIM8 / TIM1 counter
        drift) before it manifests on the scope. The companion exploratory
        RISC-V SoC track explores custom-silicon controllers for power
        electronics — RTL through GDSII against the SkyWater 130 nm
        open-source PDK — as a parallel research exercise. The educational
        value of the consolidated documentation (Build Guide v4.0,
        hardware bring-up reference, design notes) directly supports
        next-generation engineer training at Hacettepe University EEE.
    """))
    s.append(P("Goal 13 — Climate Action", H3))
    s.append(P("""
        Target 13.2 (integrate climate measures into planning) is addressed
        through the project's role as an enabler for efficient renewable
        energy integration. By reducing the conversion losses in the renewable
        → AC path, the system supports the broader transition away from
        fossil-fuel generation. The modular topology and open documentation
        also lower the barrier for similar projects in other universities and
        small enterprises, multiplying the climate impact beyond a single
        deployment.
    """))
    s.append(PageBreak())
    return s


def section_literature_review() -> list:
    s = [P("5. LITERATURE REVIEW", H1)]
    s.append(P("""
        The theoretical foundation for this project draws on four areas
        of undergraduate coursework and on focused literature studies
        conducted during ELE 401. Each is summarised below.
    """))
    s.append(P("5.1. Multilevel inverter theory", H2))
    s.append(P("""
        Multilevel inverters synthesise AC voltage from multiple DC levels,
        producing stepped waveforms that approach a sinusoidal shape.
        Increasing the number of voltage levels reduces harmonic distortion
        and minimises filtering requirements [1, 2]. The three established
        topologies are:
    """))
    s.append(bullets([
        "<b>Neutral Point Clamped (NPC):</b> single DC source, uses clamping diodes, "
        "voltage-balancing challenges at higher levels and uneven loss distribution.",
        "<b>Flying Capacitor (FC):</b> uses flying capacitors instead of clamping "
        "diodes, requires complex pre-charging, capacitor aging issues at industrial timescales.",
        "<b>Cascaded H-Bridge (CHB):</b> modular structure, requires isolated DC "
        "sources per cell, simplest control architecture [4]. Selected for this project.",
    ]))
    s.append(P("""
        The CHB topology was selected because its modularity matches the
        per-cell isolated-DC requirement that PV strings and battery packs
        naturally provide, and because its control complexity scales linearly
        with cell count — important for student-scale projects where every
        added complexity multiplies the bring-up effort. The detailed
        topology comparison and selection rationale is in [4, 7] and was
        replicated in the ELE 401 interim report §6.1.
    """))
    s.append(P("5.2. Level-shifted and phase-shifted carrier PWM", H2))
    s.append(P("""
        Two carrier-based modulation strategies are standard for multilevel
        inverters [3, 5]:
    """))
    s.append(bullets([
        "<b>In-Phase Disposition Level-Shifted PWM (IPD LS-PWM):</b> uses N "
        "triangular carriers vertically stacked in different voltage bands, all "
        "in phase. A single sinusoidal reference is compared with all carriers. "
        "Implementation is simple — single timer configuration replicated across "
        "cells. The downside is bridge-loss asymmetry: the bridge mapped to the "
        "inner band always carries the most-frequent switching transitions, "
        "creating thermal imbalance.",
        "<b>Phase-Shifted Carrier PWM (PSC-PWM):</b> uses N carriers shifted by "
        "360°/N (or 180°/N for unipolar modulation in 2-cell systems), each "
        "compared with the same sinusoidal reference. Effective switching "
        "frequency at the output is N × f<sub>sw</sub>, halving the LC-filter "
        "size for equivalent attenuation. Bridge-loss is symmetric.",
    ]))
    s.append(P("""
        The simulation phase initially adopted IPD LS-PWM for its
        implementation simplicity, achieving a 4.9 % THD<sub>V</sub>
        prediction. The bench-discovered thermal asymmetry in iteration 1
        prompted reconsideration; the firmware was rewritten on the
        <i>pwm-rewrite-configurable</i> branch to add PSC-PWM as the new
        as-built default. PSC's runtime carrier-phase lock diagnostic was
        added as defensive instrumentation against the TIM8 / TIM1 counter
        drift that would degrade the cascade output from 5 levels to 3.
    """))
    s.append(P("5.3. Gate-driver requirements in CHB topology", H2))
    s.append(P("""
        A critical and often overlooked aspect in multilevel-inverter
        implementation is the gate-driver isolation requirement. Corzine and
        Familiant [9] emphasise that CHB topology requires <b>true galvanic
        isolation</b> for each H-bridge module above the ground-referenced
        cell, because each upper cell operates at a different floating
        potential.
    """))
    s.append(P("""
        Bootstrap-based drivers (IR2110 family) are designed for
        ground-referenced applications where the low-side switch source
        terminal connects to ground or a common reference. In CHB topology,
        only the bottom cell is ground-referenced; the upper cell floats. The
        bootstrap capacitor voltage references the floating high-side source
        terminal, the common-mode voltage across the driver exceeds the
        bootstrap driver's isolation rating, and the result is inadequate or
        failed gate drive for the upper cell. The team validated this in
        Simulink with an IR2110 behavioural model — gate drive collapsed to
        less than 5 V on the upper cell, MOSFETs failed to turn on. This is
        the simulation evidence that killed the bootstrap path before silicon
        was committed.
    """))
    s.append(P("""
        Three practical isolation approaches exist [10]:
    """))
    s.append(bullets([
        "Optical isolation — e.g. TLP250 (2.5 kV galvanic), requires isolated power supply per driver. <b>Selected.</b>",
        "Magnetic isolation — e.g. Si827x (5 kV), integrated isolated power. Higher cost; harder to source domestically.",
        "Capacitive isolation — e.g. UCC27531, requires isolated power per driver. Comparable to optical in this application.",
    ]))
    s.append(P("5.4. Power semiconductor selection at low voltage", H2))
    s.append(P("""
        At 50 V per cell and 5 kHz switching, all selection criteria favour
        MOSFETs over IGBTs [10]:
    """))
    s.append(bullets([
        "Lower switching losses — MOSFET turn-off has no tail current; IGBT tail current contributes ≈ 5 W per device at this f<sub>sw</sub>.",
        "Resistive on-state characteristic — better efficiency at light loads (loss scales with I²).",
        "Faster switching enabling higher frequencies if desired.",
        "Integrated body diode for free-wheeling — IGBTs require an external anti-parallel diode.",
    ]))
    s.append(P("""
        The crossover voltage where IGBTs begin to win is typically &gt; 250 V
        V<sub>DS</sub> and &gt; 20 kHz — well outside this project's operating
        point. The detailed loss arithmetic is in §6.1 and the design note on
        IGBT vs. MOSFET.
    """))
    s.append(PageBreak())
    return s


def section_methods() -> list:
    s = [P("6. METHODS", H1)]
    s.append(P("""
        Two methodological approaches were evaluated against the project
        requirements during the ELE 401 simulation phase. Method 1 (CHB
        with PSC-PWM) was selected and forms the basis of the as-built design.
        Method 2 (alternative topologies and modulators) was evaluated and
        documented for completeness; this section captures both, with the
        rationale for selection.
    """))
    s.append(P("6.1. Method 1 — Cascaded H-Bridge with PSC-PWM (selected)", H2))
    s.append(P("Topology", H3))
    s.append(P("""
        Two full H-bridge cells connected in series, each generating three
        voltage levels (+V<sub>DC</sub>, 0, −V<sub>DC</sub>). The series
        connection produces five output levels: {−2V<sub>DC</sub>,
        −V<sub>DC</sub>, 0, +V<sub>DC</sub>, +2V<sub>DC</sub>}. Each cell has
        its own isolated DC source. The cells' output terminals are wired in
        series externally; the controller drives both cells from a single
        STM32 using TIM1 (Bridge 1) and TIM8 (Bridge 2).
    """))
    s.append(P("Modulation strategy — PSC-PWM", H3))
    s.append(P("""
        Each cell uses unipolar phase-shifted-carrier SPWM. The two carriers
        are shifted by 90° (the TIM8 counter is preset to ARR/2 at
        configuration time to give this shift). Each cell produces a 3-level
        output (±V<sub>DC</sub>, 0); the series sum produces 5 distinct
        cascade levels. Both cells switch the same number of times per
        fundamental period, giving symmetric bridge loading.
    """))
    s.append(P("""
        Modulation parameters runtime-configurable from UART /
        dashboard:
    """))
    s.append(bullets([
        "<b>Switching frequency</b> 100 Hz – 20 kHz (default 5 kHz);",
        "<b>Fundamental frequency</b> 10 Hz – 400 Hz (default 50 Hz);",
        "<b>Modulation index</b> 0.0 – 0.95 (default 0.95);",
        "<b>Bridge select</b> BOTH / B1 / B2 (for per-bridge isolation testing);",
        "<b>Modulator</b> STAIR / PSC / STAIR_ALT (default STAIR on boot for the known-good staircase; switched to PSC after PSC lock confirmed).",
    ]))
    s.extend(fig(Path("cascade-control-overlap.png"),
                 "Modulation visual — the two cells' carriers and the resulting cascade "
                 "output overlap as the modulator combines them into five distinct levels.",
                 width_cm=14))
    s.append(P("Gate drive — TLP250 + B0515S", H3))
    s.append(P("""
        Each MOSFET is driven by a TLP250 optical gate driver providing 2.5 kV
        galvanic isolation between the controller's PWM output and the MOSFET
        gate. Each cell's TLP250 array is powered from an isolated 15 V rail
        derived by a B0515S 5 V → 15 V DC-DC converter. The 22 Ω gate series
        resistor and 10 kΩ gate-source pull-down per MOSFET keep gate ringing
        controlled and ensure the MOSFET is held off whenever the driver is
        unpowered. The selection of TLP250 over IR2110 was driven by the
        Simulink IR2110 simulation result; see §5.3 and Figure below.
    """))
    s.extend(fig(Path("simulink-ir2110-circuit-rejected.jpeg"),
                 "Simulink behavioural model of the IR2110 driver in the upper-cell role. "
                 "Bootstrap reference collapses under the cascade's floating-V_S — the "
                 "evidence that killed the bootstrap-driver path before silicon was committed.",
                 width_cm=14))
    s.append(P("Sensing — MCP3201 + 6N137", H3))
    s.append(P("""
        Per-bridge DC bus voltage and AC output current are sampled by MCP3201
        12-bit SPI ADCs on the floating cell side, with the SPI signals
        crossed back to the controller through 6N137 high-speed optocouplers.
        Each cell's island includes a 78L05 deriving its local 5 V logic
        supply from the 15 V gate-drive rail, decoupling the cell from any
        controller-side power-supply noise. Current sensing on each cell uses
        an ACS712 Hall-effect sensor (100 mV/A, 2.5 V zero offset).
    """))
    s.append(P("Controller — STM32 Nucleo-F303RE", H3))
    s.append(P("""
        Chosen for dual advanced-control timers (TIM1 + TIM8) with
        complementary outputs and hardware dead-time, hardware FPU,
        on-board ST-LINK for both flashing and the virtual COM port used by
        the UART protocol. Runs at 64 MHz from HSI/2 × PLL (no external
        crystal required, simplifying the BOM). The firmware is CMSIS
        bare-metal with a minimal HAL bring-up shim retained from CubeMX
        — total Flash footprint 36 KB / 512 KB, RAM 4.1 KB / 64 KB, zero
        warnings under -Wall -Wextra -Wshadow -Wundef.
    """))
    s.append(P("Advantages of Method 1", H3))
    s.append(bullets([
        "<b>Modularity:</b> independent testing and maintenance of each H-bridge cell.",
        "<b>Scalability:</b> linear increase in output levels with added cells.",
        "<b>Bridge balance:</b> PSC-PWM gives symmetric switching distribution between cells.",
        "<b>Suitable for renewables:</b> multiple isolated DC sources naturally available from PV strings.",
        "<b>Higher effective switching frequency at output (PSC):</b> 2 × f<sub>sw</sub> output ripple at 5 kHz per cell.",
        "<b>Existing tooling:</b> Cadence, ST CubeIDE, KiCad all natively support the parts and the workflow.",
    ]))
    s.append(P("Disadvantages of Method 1", H3))
    s.append(bullets([
        "Requires isolated DC sources per cell (acceptable for renewable applications).",
        "Requires galvanic isolation in gate drivers (handled by TLP250 + B0515S).",
        "PSC requires precise inter-timer phase synchronisation (mitigated by runtime lock diagnostic).",
    ]))
    s.append(P("6.2. Method 2 — Alternative topologies and modulators (evaluated)", H2))
    s.append(P("NPC (Neutral Point Clamped)", H3))
    s.append(P("""
        Single DC source split across capacitor stack, with clamping diodes
        steering the current. <b>Advantages:</b> single DC source (no need for
        multiple isolated supplies). <b>Disadvantages:</b> complex
        voltage-balancing dynamics across the capacitor stack at higher
        levels, unequal loss distribution between inner and outer switches,
        clamping diode complexity. <b>Evaluation:</b> NPC's DC-source
        simplicity is attractive but introduces capacitor-balancing control
        challenges that are unsuitable for a first multilevel implementation
        in a student project timeline. Not selected.
    """))
    s.append(P("Flying Capacitor (FC)", H3))
    s.append(P("""
        Uses flying capacitors instead of clamping diodes; redundant switching
        states allow capacitor voltage balancing through state selection.
        <b>Advantages:</b> no clamping diodes; multiple redundant switching
        states. <b>Disadvantages:</b> large pre-charged capacitors required;
        complex pre-charging sequence; capacitor aging issues at industrial
        timescales. <b>Evaluation:</b> impractical for a laboratory-scale
        prototype due to cost and bring-up complexity of the pre-charge.
        Not selected.
    """))
    s.append(P("IPD LS-PWM (alternative modulator)", H3))
    s.append(P("""
        Originally adopted for its implementation simplicity (single timer
        configuration replicated across cells, identical for all H-bridges,
        easier debugging because all switching edges are temporally aligned).
        Bench testing in iteration 1 surfaced the bridge-loss asymmetry that
        is inherent to IPD — the cell mapped to the inner band carries the
        most switching transitions and runs measurably hotter. The team
        evaluated an "alternating bridge swap" mitigation (where the
        inner-band role swaps each fundamental cycle) but concluded that PSC,
        which is naturally bridge-balanced, was a strictly better choice.
        IPD remains in the firmware as the STAIR modulator's underlying
        principle (though STAIR is a 500 Hz quantising staircase, not LS-PWM
        per se) and as a known-good fallback. STAIR_ALT was added as a
        hard-fallback that gives symmetric loading even when PSC's carrier
        phase cannot be locked.
    """))
    s.append(PageBreak())
    return s


def section_preliminary_design() -> list:
    s = [P("7. PRELIMINARY DESIGN", H1)]
    s.append(P("""
        Following the Method 1 selection (CHB + PSC-PWM + TLP250 isolated
        drive + STM32F303 control), the preliminary design phase identified
        the parameters and design choices that would need to be fixed during
        prototyping. Per the ELE 402 template guidance, this section
        identifies parameters and design choices without necessarily fixing
        their final values; the as-built values are given in §10.
    """))
    s.append(P("Topology and architecture", H3))
    s.extend(fig(Path("simulink-final-circuit.jpeg"),
                 "Simulink circuit for the final-design simulation — two cascaded H-bridge "
                 "cells with TLP250-isolated gate drive, the LS-PWM/PSC modulator, and "
                 "the LC filter + load stage. This is the model used to validate the "
                 "preliminary design before any silicon was committed.", width_cm=15))
    s.append(P("Preliminary parameters identified for fixing during prototyping", H3))
    pre_table = themed_table([
        ["Parameter", "Range considered", "Driver / dependency"],
        ["Per-cell DC bus voltage", "12 V – 60 V", "Supervisor meeting; bench supply availability"],
        ["Switching frequency", "1 kHz – 20 kHz", "MOSFET switching loss vs. LC filter size"],
        ["Modulation index", "0.5 – 0.95", "Output amplitude vs. duty-clamp constraint"],
        ["Dead time", "1 µs – 5 µs", "MOSFET gate-charge / TLP250 driver speed"],
        ["MOSFET part", "IRFZ44N / IRF540N / IRF3205 / IRFB4110", "V_DSS headroom + R_DS(on) + cost"],
        ["TVS clamp voltage", "60 V – 100 V", "Must sit below MOSFET V_DSS"],
        ["LC filter cutoff", "100 Hz – 500 Hz", "Output power-quality target"],
        ["Sense ADC sampling", "1 kHz – 20 kHz", "Protection latency vs. SPI bandwidth"],
    ], col_widths=[4 * cm, 4.5 * cm, 7.5 * cm])
    s.append(table_caption("Parameters identified during preliminary design for fixing during prototyping."))
    s.append(pre_table)
    s.append(Spacer(0, 0.4 * cm))
    s.append(P("Simulation predictions at the preliminary operating point", H3))
    s.extend(fig(Path("simulink-5-level-output-and-current.jpeg"),
                 "Simulink result at the preliminary operating point — top trace: cascade "
                 "voltage with five distinct levels; bottom trace: per-MOSFET current. "
                 "This is the model output that produced the 4.9 % THD prediction.",
                 width_cm=14))
    s.extend(fig(Path("simulink-high-freq-output.jpeg"),
                 "Simulink output at elevated switching frequency, used during the "
                 "parameter-sweep phase. Higher f_sw sharpens the output and pushes "
                 "ripple energy where a smaller LC filter can attenuate it, at the "
                 "cost of additional switching loss.", width_cm=14))
    s.append(P("Control architecture (preliminary)", H3))
    s.append(P("""
        A hierarchical control architecture was planned with three loops:
    """))
    s.append(bullets([
        "<b>Inner current loop:</b> 5 kHz (synchronised with PWM period), Proportional-Resonant tuned to 50 Hz, ≈ 1 kHz bandwidth, &lt; 5 ms response.",
        "<b>Outer voltage loop:</b> 2 kHz, PI controller, ≈ 100 Hz bandwidth, ≈ 20 ms response.",
        "<b>DC-link balancing loop:</b> 100 Hz, active balancing through per-cell modulation-index corrections, ±5 % tolerance between cells.",
    ]))
    s.append(P("""
        The bench-validated firmware ultimately ships open-loop — the closed
        loops are deferred to future work because the bench-prototype
        deliverable (5-level output visible on the scope without filter) does
        not require closed-loop regulation. The control architecture is
        nevertheless documented as a roadmap item; see §12.
    """))
    s.append(PageBreak())
    return s


def section_prototype() -> list:
    s = [P("8. PROTOTYPE", H1)]
    s.append(P("""
        The first prototype (iteration 1) was built during the ELE 401 phase
        and reported in the corresponding interim document. This section
        introduces that prototype to set context for the iteration narrative
        that follows in §9.
    """))
    s.append(P("Purpose of the first prototype", H3))
    s.append(bullets([
        "Validate the CHB topology arithmetic on real silicon — confirm that two cascaded H-bridges actually produce five distinct output levels.",
        "Bench-characterise the IPD LS-PWM modulator's behaviour at the bench operating point.",
        "Surface any layout, sensing, or gate-drive issues before scaling to the production-intent design.",
        "Establish the bring-up procedure that would later be formalised in HARDWARE_BRINGUP.md and FIRST_BENCH_SESSION.md.",
    ]))
    s.append(P("Prototype configuration", H3))
    s.append(P("""
        The first prototype was a <b>single PCB hosting both H-bridges</b>,
        populated with the components specified in Build Guide v3.1 (the
        document the team used as their internal engineering reference at the
        time). Eight IRFZ44N MOSFETs in TO-220 packages formed the two
        H-bridges; eight TLP250 optical drivers handled the gates; three
        MCP3201 ADCs provided sensing (each on its own MISO line — the
        original firmware assumption); the controller was the STM32 Nucleo-F303RE
        running IPD LS-PWM at 500 Hz.
    """))
    s.append(P("Key features", H3))
    s.append(bullets([
        "<b>5 distinct levels demonstrated:</b> the cascade output was visible on the scope at 12 V per cell during the first power-up.",
        "<b>STM32 firmware bring-up:</b> the initial PWM generator was a 500 Hz quantising staircase that mapped the sine reference into five discrete levels.",
        "<b>Independent sensing chain:</b> three MISO lines, three CS lines, one shared SCK at ≈ 140 kHz.",
        "<b>Single-PCB topology:</b> both H-bridges on one board, simpler to fab but harder to isolate.",
    ]))
    s.extend(fig(Path("first-mosfet-test-light.jpeg"),
                 "Earliest gate-drive sanity check from the prototype era — a single "
                 "MOSFET driving an indicator light, confirming the TLP250 isolation "
                 "chain works end-to-end before scaling to the full H-bridge.",
                 width_cm=11))
    s.extend(fig(Path("breadboard-irfz44n-test.jpg"),
                 "Breadboard IRFZ44N MOSFET characterisation during the prototype phase — "
                 "the V_DSS-headroom problem visible on this rig before the first board "
                 "was ordered prompted the eventual IRFB4110 substitution in iteration 4.",
                 width_cm=14))
    s.append(P("""
        The prototype validated the topology arithmetic and the firmware
        approach but surfaced a small set of structural issues — V<sub>DSS</sub>
        headroom too tight, TVS-clamp / MOSFET-V<sub>DSS</sub> mismatch, and
        bridge-1 thermal asymmetry under IPD modulation — that drove the
        four subsequent iterations documented in §9.
    """))
    s.append(PageBreak())
    return s


def section_design_iterations() -> list:
    s = [P("9. DESIGN ITERATIONS", H1)]
    s.append(P("""
        Four hardware iterations were completed across the ELE 401 and ELE 402
        terms. Each is documented below with the modifications attempted, the
        testing performed, the bench results, and the evaluation that drove
        the next iteration. The full narrative — including iteration-era
        KiCad backups where they survived — is preserved at <i>hardware/legacy/</i>
        in the repository.
    """))

    # --- Iteration 1 -----------------------------------------------------------
    s.append(P("9.1. Iteration 1 — single dual-bridge PCB, IRFZ44N, IPD LS-PWM", H2))
    s.append(P("""
        The first iteration is the prototype introduced in §8. Both H-bridges
        on a single PCB, IRFZ44N MOSFETs, TLP250 gate drivers, IPD LS-PWM at
        500 Hz, three independent MISO lines.
    """))
    s.append(P("9.1.1. Testing and results", H3))
    s.append(P("""
        Bench tested at 12 V per cell on the lab supplies. Five distinct
        cascade output levels were visible on the oscilloscope, validating
        the topology arithmetic. Continuous-run thermal observation showed
        one of Bridge 1's MOSFETs running measurably hotter than its
        counterparts. Bench supplies were stepped from 12 V toward 24 V per
        cell to characterise V<sub>DS</sub> margin; switching transients
        were observed to approach the 55 V V<sub>DSS</sub> limit faster than
        expected due to gate-loop ringing.
    """))
    s.append(P("9.1.2. Evaluation", H3))
    s.append(P("""
        Three structural problems were identified:
    """))
    s.append(bullets([
        "<b>MOSFET V<sub>DSS</sub> too tight</b> — 55 V V<sub>DSS</sub> with the planned 50 V bus left only ≈ 10 % nominal headroom, which gate-loop parasitics readily exceeded under switching transients.",
        "<b>TVS / MOSFET V<sub>DSS</sub> mismatch</b> — the 1.5KE62A TVS clamps at 84.5 V, well above the IRFZ44N's 55 V V<sub>DSS</sub>. A TVS-firing event would still damage the MOSFETs. The protection chain didn't actually protect.",
        "<b>Bridge-1 thermal asymmetry</b> — IPD's mapping of the inner-band switching to Bridge 1 made one bridge run hotter than the other. Symmetric loading would require either an active bridge-swap each fundamental cycle (adding firmware complexity) or a switch to a balanced modulator (PSC).",
    ]))
    s.append(P("""
        These three issues were taken forward into the planning for
        iteration 2 and ultimately iteration 4.
    """))

    # --- Iteration 2 -----------------------------------------------------------
    s.append(P("9.2. Iteration 2 — revised gate-drive routing, bootstrap lessons", H2))
    s.append(P("""
        Iteration 2 retained the iteration-1 architecture (single dual-bridge
        PCB, IRFZ44N, IPD LS-PWM, three independent MISOs) and reworked the
        gate-drive routing to address the ringing observed in iteration 1.
    """))
    s.append(P("Modifications", H3))
    s.append(bullets([
        "<b>Gate-loop trace lengths shortened</b> — the iteration-1 layout had TLP250 outputs running several centimetres before reaching MOSFET gates, picking up significant loop inductance.",
        "<b>Gate resistor value tweaked</b> — finer trade between switching speed and shoot-through margin.",
        "<b>Bootstrap diode + cap repositioned</b> closer to the gate driver and the MOSFET source, reducing bootstrap-loop length.",
        "<b>Better TLP250 V<sub>CC</sub> decoupling</b> — 100 nF ceramic at every TLP250 in addition to bulk decoupling.",
    ]))
    s.append(P("9.2.1. Testing and results", H3))
    s.append(P("""
        Bench testing at modulation indices above 0.9 revealed a
        <b>bootstrap timing issue</b> that hadn't shown up in iteration 1.
        The bootstrap capacitor voltage drooped over consecutive cycles, the
        high-side gate voltage went below the IRFZ44N's V<sub>th</sub>, and
        the high-side leg failed to turn on cleanly. The bench symptoms
        looked at first like a noise problem; a careful session looking at
        the LS-on window vs. bootstrap-cap droop diagnosed the cause.
    """))
    s.extend(fig(Path("breadboard-first-chb-test.jpg"),
                 "First cascaded H-bridge bench test from the iteration-2 era — two "
                 "H-bridges wired in series with the iteration-2 gate-drive routing changes. "
                 "This is the rig where the bootstrap-timing problem at high modulation "
                 "indices was diagnosed.", width_cm=14))
    s.append(P("9.2.2. Evaluation", H3))
    s.append(P("""
        Two lessons crystallised. First, <b>bootstrap is a duty constraint,
        not just a parts choice</b> — the 95 % HIGH-duty clamp that landed in
        the firmware in iteration 4 has its origin here. Second, and more
        importantly, the team noticed that Bridge 2's bootstrap path was
        <b>structurally different from Bridge 1's</b>: Bridge 2 sits at a
        floating reference, and the bootstrap diode had no real return to a
        stable ground. This was the early warning that bootstrap drive
        cannot work for cascaded floating bridges — the lesson that drove
        the iteration-3 commitment to per-bridge isolated 15 V supply
        (B0515S DC-DC) and removed bootstrap entirely from the design path.
    """))
    s.append(P("""
        The 6 ms PRECHARGE state also landed in this iteration. Before
        iteration 2 the firmware enabled MOE and ran immediately; after
        iteration 2, MOE-enable → 6 ms of forced-LS-on → then PWM. This is
        the PRECHARGE state in the supervisory FSM today.
    """))

    # --- Iteration 3 -----------------------------------------------------------
    s.append(P("9.3. Iteration 3 — per-bridge isolation, MISO rework, MOSFET swap", H2))
    s.append(P("""
        Iteration 3 was the first board to implement the full per-bridge
        isolation architecture: B0515S DC-DC per bridge, 6N137 optocouplers
        on every SPI line, 78L05 deriving the 5 V island-side logic supply
        from the local 15 V rail. This is the architecture that survives
        into iteration 4.
    """))
    s.append(P("9.3.1. Testing and results", H3))
    s.append(P("""
        Three problems surfaced during iteration-3 bring-up:
    """))
    s.append(P("""
        <b>(a) The 5V_GND ↔ 50V_GND coupling problem.</b> The board had
        inadvertent coupling between the controller's 5V_GND and the
        bridges' 50V_GND through (i) a continuous inner-plane ground pour
        that extended across the isolation boundary and (ii) marginal copper
        creepage on the optocoupler footprints. The combined effect was
        intermittent <i>SENSOR_LOST</i> events under load, garbage STATUS
        values when Bridge 2 was switching at the cascade peak, and
        occasional protection-trip glitches during clean-load runs — all
        classical signs of broken isolation.
    """))
    s.append(P("""
        <b>(b) MISO-topology surprise.</b> The firmware had been written
        assuming three independent MISO lines (one per MCP3201). The
        iteration-3 board surfaced the reality: the upper-bridge island
        actually has only two MISO data-return lines, with DC2 and current
        sharing one (on the PC3 pin). The firmware was rewritten
        — the <i>pwm-rewrite-configurable</i> branch — to perform strictly
        sequential one-channel-per-CS reads. The board was not respun: it
        was cheaper and faster to fix the firmware than to refab.
    """))
    s.append(P("""
        <b>(c) Pin-mismatch errata.</b> Three pin-assignment errors in the
        v3.1 build-guide PDF were discovered: PWM_1L (the guide said PA10;
        the actual board uses PA12 and the firmware was already wired
        correctly), MCP3201 pins 5/7 (CS and SCK swapped in the guide), and
        78L05 pins 1/3 (V<sub>I</sub> and V<sub>O</sub> swapped). The
        schematic was correct in each case; the documentation was wrong.
        Build Guide v4.0 corrects all three.
    """))
    s.append(P("9.3.2. Evaluation", H3))
    s.append(P("""
        The grounding issue confirmed that <b>galvanic isolation is not
        automatic from picking the right ICs</b>. Layout matters — a shared
        inner-plane via can defeat 2.5 kV-rated parts through parasitic AC
        coupling. The MISO topology rework taught the team that <b>hardware
        reality wins over firmware assumptions</b>: when the board layout
        couldn't accommodate the three-MISO scheme, rewriting the firmware
        was the right call. The pin errata reinforced that <b>the schematic
        is the authoritative source for what gets fabricated</b>; the build
        guide is documentation. Build Guide v4.0 was published with all
        three errors corrected.
    """))
    s.append(P("""
        The iteration-3 KiCad zip backups are preserved at
        <i>hardware/legacy/iteration-3/</i> in the repository for reference.
    """))

    # --- Iteration 4 -----------------------------------------------------------
    s.append(P("9.4. Iteration 4 — as-built (two single-bridge modules, IRFB4110, PSC)", H2))
    s.append(P("""
        Iteration 4 was a <b>re-architecture from iteration-3 lessons</b>, not
        an incremental tweak. Six structural changes were applied together.
    """))
    s.append(P("Modifications", H3))
    it4 = themed_table([
        ["Change", "From (iteration 3)", "To (as-built v4)"],
        ["Board topology", "Single dual-bridge PCB", "Two identical single-bridge PCB modules"],
        ["Stack-up", "2-layer", "4-layer FR-4 1.6 mm, JLCPCB"],
        ["Power MOSFET", "IRFZ44N (55 V)", "IRFB4110 (100 V, 4.5 mΩ)"],
        ["Modulator", "IPD LS-PWM at 500 Hz", "PSC-PWM at 5 kHz"],
        ["Dead time", "2 µs (BDTR.DTG ≈ 0x80)", "3 µs (BDTR.DTG = 0xA0)"],
        ["MISO topology", "3-independent assumption", "2 lines (1 lower + 1 upper-shared)"],
    ], col_widths=[3.5 * cm, 5 * cm, 7.5 * cm])
    s.append(table_caption("Iteration-4 structural changes vs. iteration 3."))
    s.append(it4)
    s.append(Spacer(0, 0.4 * cm))
    s.append(P("9.4.1. Testing and results", H3))
    s.append(P("""
        Bench validation against the project deliverable specification:
    """))
    s.extend(fig(Path("100v-output-5-levels.png"),
                 "Headline bench result — 100 V cascade output with five distinct levels "
                 "under sustained PSC-PWM at 5 kHz, no filter. The project deliverable as "
                 "agreed with the supervisor at the 23 October 2025 project meeting.",
                 width_cm=14))
    s.append(P("All headline goals met:"))
    s.append(bullets([
        "<b>5 distinct cascade output levels visible on scope at 100 V output</b> ✅",
        "<b>PSC carrier phase lock</b> — <i>lock=OK</i> reported consistently on the $C config line ✅",
        "<b>Bridges thermally matched</b> within ≈ 3 °C under sustained PSC load ✅",
        "<b>Sensing clean throughout the run</b> — no false <i>SENSOR_LOST</i> events, STATUS line stable over multi-minute sessions ✅",
        "<b>Dashboard auto-cancel</b> of firmware auto-start including across Nucleo resets ✅",
        "<b>Protection chain protects</b> — TVS clamps below MOSFET V<sub>DSS</sub>; UV / OV / OC / IMBAL with N-of-M debounce; FAULT_OUT pulled LOW on trip ✅",
    ]))
    s.extend(fig(Path("scope-pwm-cascade-output.jpeg"),
                 "PSC cascade output capture — five distinct levels visible across the "
                 "fundamental, with bridges thermally matched.", width_cm=14))
    s.append(P("9.4.2. Evaluation", H3))
    s.append(P("""
        Iteration 4 satisfies the project deliverable. Two things remain
        soft, both carried into the roadmap: the system has no LC output
        filter (the demo ran into a resistive load) and the control loop is
        open (modulation index is set by the operator, not regulated against
        output voltage). Both are deliberate scope decisions for the
        graduation deliverable; both have clear paths forward and are
        discussed in §12.
    """))
    s.append(PageBreak())
    return s


def section_final_design() -> list:
    s = [P("10. FINAL DESIGN", H1)]
    s.append(P("""
        The final design is the iteration-4 hardware combined with the
        firmware on the <i>pwm-rewrite-configurable</i> branch and the
        PySide6 operator dashboard. This section describes each subsystem
        as it ships, then discusses constraint satisfaction and cost.
    """))

    s.append(P("10.0.1. Hardware — single-bridge v4 PCB", H3))
    s.append(P("""
        Two identical single-bridge PCB modules, each a 4-layer FR-4 board
        of 1.6 mm thickness fabricated by JLCPCB. The 4-layer stack-up
        carries separate inner ground pours — 5V_GND on L2 (controller
        region only) and per-bridge 50V_GND on L3 (each bridge in its own
        region, never connected to other bridges or to 5V_GND). The four
        isolation parts (TLP250 × 4, B0515S, 6N137 SCK/CS, 6N137 MISO) are
        the only paths between any pair of these grounds.
    """))
    s.extend(fig(Path("pcb-top-down-kicad.jpeg"),
                 "Top-down KiCad render of the as-built single-bridge v4 PCB.",
                 width_cm=14))
    s.append(P("Hierarchical schematic", H3))
    s.append(P("""
        The KiCad schematic decomposes into seven hierarchical sheets:
    """))
    s.append(bullets([
        "<b>TOPDESIGN</b> — top-level integration of the cell into the cascade.",
        "<b>Highside_cell / Lowside_cell</b> — the two MOSFET pairs of the H-bridge.",
        "<b>driver_cell</b> — TLP250 wiring, gate resistor, GS pull-down.",
        "<b>5v-15v_sch</b> — B0515S isolated 5V → 15V DC-DC for the gate-drive rail.",
        "<b>Voltage_sensing_sch</b> — DC bus voltage divider into the MCP3201.",
        "<b>current_sensing_sch</b> — ACS712 current sensor into the MCP3201.",
    ]))
    s.append(P("10.0.2. Firmware — STM32F303RE bare-metal CMSIS", H3))
    s.append(P("""
        Bare-metal CMSIS implementation with a thin HAL bring-up shim
        retained from CubeMX so HAL_IncTick still fires from SysTick.
        64 MHz from HSI/2 × PLL (no external crystal). Total Flash usage
        36 KB / 512 KB, RAM 4.1 KB / 64 KB, zero warnings under
        -Wall -Wextra -Wshadow -Wundef. Source preserved with full
        upstream history via <i>git subtree</i> from the firmware repository.
    """))
    s.extend(fig(Path("stm32-only-diagram.png"),
                 "STM32 firmware architecture — TIM1 drives Bridge 1, TIM8 drives Bridge 2 "
                 "with a 90° carrier phase shift (preset at TIM8 CNT = ARR/2). Bit-banged "
                 "MCP3201 sensing crosses the isolation barrier through 6N137 optocouplers; "
                 "UART telemetry feeds the PySide6 dashboard.", width_cm=14))
    s.append(P("Pin map (as wired)", H3))
    s.extend(fig(Path("stm32-pins.jpeg"),
                 "STM32 Nucleo-F303RE pin assignments for the as-built design. "
                 "This table supersedes the v3.1 build-guide pin assignments.",
                 width_cm=14))
    s.append(P("Firmware FSM", H3))
    s.append(P("""
        Five states - BOOT, IDLE, PRECHARGE, RUN, FAULT. The
        supervisory FSM owns the MOE bit (PWM master-output-enable), the
        sensor mode, and the protection latch. PRECHARGE forces all
        low-sides ON for 6 ms (3 PWM periods at 500 Hz) to seed any
        bootstrap-style charge equilibrium before allowing PWM to run. A
        layered auto-start path issues a self-START if no UART byte arrives
        within 3 s of boot, supporting unattended-demo deployments; the
        dashboard cancels auto-start by transmitting STATUS on connect.
    """))
    s.extend(fig(Path("diagram-fsm.png"),
                 "Firmware supervisory FSM. Five states with the transitions used "
                 "during the bench session: START arms the bridges through "
                 "PRECHARGE into RUN; STOP returns to IDLE from either; UV / OV / "
                 "OC / IMBAL trips raise FAULT from any active state; CLEAR "
                 "returns to IDLE after the fault condition has cleared.",
                 width_cm=16))
    s.append(P("Modulators", H3))
    s.append(P("""
        Three modulators ship in the firmware, runtime-selectable over UART:
    """))
    s.append(bullets([
        "<b>PSC</b> — phase-shifted carrier, the as-built default after bench validation. Bridges thermally balanced.",
        "<b>STAIR</b> — 500 Hz quantising staircase; Bridge 1 carries the ±1 step. Known-good fallback; not real PWM.",
        "<b>STAIR_ALT</b> — staircase output with bridge that carries the ±1 step alternating each fundamental cycle. Hard-fallback if PSC carrier phase cannot be locked.",
    ]))
    s.append(P("""
        The PSC implementation hardens the TIM8 ↔ TIM1 counter offset
        (which must hold at exactly ARR/2 for the 90° carrier shift):
        TIM8 CNT is written after CR1_CEN is set so the post-EGR_UG
        sequence cannot clobber it; the actual measured offset is
        read back as g_pwm_measured_cnt_offset; a boolean lock is
        published on the $C config line (<i>cntoff=N, lock=OK|BAD</i>) so
        the operator can confirm the carrier phase is locked before
        arming the bridges.
    """))
    s.append(P("Sensing and protection", H3))
    s.append(P("""
        Six sensing modes (FULL / DC_ONLY / CUR_ONLY / OPEN / DC1 / DC2)
        auto-selected at boot based on ADC self-test. Protection chain
        includes UV, OV, OC, IMBAL — all VNOM-scaled for low-voltage
        bench testing — plus SENSOR_LOST and MANUAL fault bits. Every
        trip condition has a 3-sample (3 ms at 1 kHz) N-of-M debounce
        to reject single-sample noise. On trip, the FSM forces
        BDTR.MOE = 0 (all MOSFETs off via TLP250 + OSSI = 1), latches the
        fault bits, pulls FAULT_OUT (PB5) LOW, and emits a $F telemetry
        line.
    """))
    s.append(P("UART protocol", H3))
    s.append(P("""
        Line-based, 115200 8N1, NMEA-style with $T (telemetry), $S
        (status), $C (PWM config), $P (protection config), $A (async
        event), $E (async error), $F (fault), $R (raw ADC), $H (help)
        prefixes. 20 Hz telemetry frame format:
        <i>$T,&lt;ms&gt;,&lt;state&gt;,&lt;mode&gt;,&lt;fault&gt;,
        &lt;vdc1&gt;,&lt;vdc2&gt;,&lt;iout&gt;,&lt;level&gt;*&lt;chk&gt;
        \\r\\n</i> — 8-bit XOR checksum between $ and *.
    """))
    s.append(P("10.0.3. PySide6 operator dashboard", H3))
    s.append(P("""
        A Windows-friendly desktop application that connects over UART
        and provides: live 20 Hz telemetry visualization, a PC-only
        simulator with 8 pre-baked fault scenarios for safe demos, every
        firmware command exposed through the GUI (with an
        <i>Arm live START</i> checkbox gating commands that energize the
        bridges), sensor graphing with auto-follow and manual zoom, and
        a modulation visual twin that overlays the carrier and reference
        waveforms. The dashboard's SerialSource transmits STATUS on
        connect and on every detected $A,BOOT_SELF_TEST_DONE, which
        suppresses the firmware's 3 s auto-start window whenever an
        operator is present. Unit tests for the parser and simulator
        are pure-Python and run headless in CI.
    """))
    # No dashboard image — user explicitly said skip
    s.append(P("""
        <i>(A screenshot of the dashboard is intentionally omitted from
        this report; the dashboard ships with the firmware and its
        operation is described in dashboard/README.md.)</i>
    """))
    s.append(P("Bench results", H3))
    s.append(P("Headline bench-validated numbers:"))
    res = themed_table([
        ["Metric", "Result"],
        ["Cascade output levels (no filter)", "5 distinct"],
        ["Cascade output voltage", "100 V peak"],
        ["Switching frequency", "5 kHz (PSC)"],
        ["Fundamental frequency", "50 Hz"],
        ["PSC carrier phase lock", "lock=OK consistent across runs"],
        ["Inter-bridge thermal delta", "≈ 3 °C under sustained run"],
        ["False SENSOR_LOST events", "0 over multi-minute runs"],
        ["Auto-start cancellation", "Working, across Nucleo resets"],
        ["Firmware Flash usage", "36 KB / 512 KB"],
        ["Firmware RAM usage", "4.1 KB / 64 KB"],
        ["Compile warnings", "0 under -Wall -Wextra -Wshadow -Wundef"],
        ["THD<sub>V</sub> (simulation)", "4.9 % pre-filter, < 8 % IEEE 519 limit"],
    ], col_widths=[7 * cm, 9 * cm])
    s.append(table_caption("Bench-validated headline metrics for the final design."))
    s.append(res)
    s.append(Spacer(0, 0.4 * cm))

    s.append(P("10.1. Meeting the constraints and engineering standards", H2))
    s.append(P("""
        Each engineering standard and each design constraint identified in §3
        is reviewed below against the as-built design.
    """))
    s.append(P("Engineering standards", H3))
    s.append(bullets([
        "<b>IEEE 519-2022 (THD<sub>V</sub> &lt; 8 %)</b> — met in simulation at 4.9 %. Bench FFT pending LC-filter integration. ✅ (simulation), ⏳ (bench).",
        "<b>IEEE 1547-2018 (grid interconnection)</b> — out of scope for the graduation deliverable. The control architecture is grid-tie-compatible by design (clean modulation pipeline, fault chain that can be repurposed for anti-islanding). Future work.",
        "<b>IEC 61000-4-7 (harmonic measurement)</b> — methodology adopted for simulation. Adopted for the future bench FFT.",
    ]))
    s.append(P("Design constraints", H3))
    s.append(bullets([
        "<b>V/I ratings</b> — IRFB4110 V<sub>DSS</sub> = 100 V vs. 50 V nominal bus = 2× headroom; 180 A continuous rating vs. ≤ 10 A peak operating current. ✅",
        "<b>Galvanic isolation</b> — TLP250 (2.5 kV) + B0515S + 6N137 chain. All four isolation barriers verified by clean multi-minute bench runs. ✅",
        "<b>THD &lt; 5 %</b> — met in simulation (4.9 %). ✅ (simulation).",
        "<b>Control loop timing</b> — TIM1 ISR ≈ 16 µs against 200 µs PWM period budget. ✅",
        "<b>Cost</b> — total BOM ≈ 1985 TL for two-module set with spares; well under the 2500 TL target. ✅",
        "<b>Safety and protection</b> — multi-layer (TVS, fuse, snubber, firmware UV/OV/OC/IMBAL with debounce, FAULT_OUT pin, MOSFETs guaranteed off in disabled states). ✅",
    ]))
    s.append(P("10.2. Cost analysis", H2))
    s.append(P("""
        The bill of materials is preserved at <i>hardware/single-bridge-v4/bom.csv</i>
        in the repository (GitHub renders CSV as a sortable table). Headline
        cost breakdown for the two-module project plus spares:
    """))
    cost = themed_table([
        ["Section", "Lines", "Need qty", "Subtotal (TL)"],
        ["A. Power semiconductors", "6", "28", "1 151.6"],
        ["B. Sensing ICs", "4", "12", "539.0"],
        ["C. DC-bus bulk + protection", "3", "5", "86.0"],
        ["D. Gate-drive passives", "4", "60", "24.0"],
        ["E. Bootstrap caps", "1", "4", "6.0"],
        ["F. Snubber network", "2", "16", "36.0"],
        ["G. Isolated-supply passives", "2", "6", "3.2"],
        ["H. DC-bus sensing passives", "5", "13", "5.8"],
        ["I. Current-sense passives", "2", "2", "0.6"],
        ["J. Connectors + mechanical", "5", "35", "132.5"],
        ["", "", "", ""],
        ["Project total (2 modules + spares)", "34", "181", "≈ 1 985 TL"],
    ], col_widths=[7.5 * cm, 2.0 * cm, 2.5 * cm, 4.0 * cm])
    s.append(table_caption("Bill of materials cost breakdown (Turkish suppliers only — Motorobit, Direnc.net, Robotistan)."))
    s.append(cost)
    s.append(Spacer(0, 0.4 * cm))
    s.append(P("""
        All components sourced exclusively from Turkish domestic suppliers
        — Motorobit, Direnc.net, Robotistan — to avoid international
        shipping and customs friction. The IRFZ44N → IRFB4110 substitution
        (line A.1) was made at order time; the v3.2 source spreadsheet
        still carries the IRFZ44N entry for historical traceability, with
        the corrected entry in the canonical CSV.
    """))
    s.append(P("""
        Cost effectiveness: at ≈ 1985 TL for a two-module bench-validated
        5-level inverter capable of ≈ 400 W output, the cost per output watt
        is ≈ 5 TL/W — competitive for a one-off academic build, although
        well above what a production scale-out would target. The cost is
        dominated by power semiconductors (58 %) and sensing ICs (27 %),
        with passives and mechanical adding the remaining 15 %. Production
        scale-out would target a lower-cost current-sense alternative to
        the ACS712 modules and a single integrated isolated DC-DC + driver
        IC to replace the discrete B0515S + TLP250 chain.
    """))
    s.append(PageBreak())
    return s


def section_teamwork() -> list:
    s = [P("11. TEAMWORK", H1)]
    s.append(P("""
        The project was conducted by a four-person group with each member
        owning a domain but with the cross-domain milestones (bench
        sessions, PCB reviews, integration tests) staffed by at least two
        members. The natural decomposition into hardware design and
        fabrication, firmware and dashboard, simulation and analysis, and
        assembly and bring-up maps cleanly onto the four members' roles.
    """))
    s.append(P("Individual contributions", H3))
    team = themed_table([
        ["Member", "Primary domain", "Specific contributions"],
        ["Furkan Emir Aksel",
         "Project lead, firmware, dashboard",
         "Wrote the STM32 firmware end-to-end — bare-metal CMSIS modulator "
         "(STAIR, PSC, STAIR_ALT), supervisory FSM, bit-banged MCP3201 driver "
         "with SPIINV mask, UART command parser and 20 Hz telemetry, auto-start "
         "with dashboard-aware cancellation. Built the PySide6 operator "
         "dashboard. Authored CHANGELOG, FIRST_BENCH_SESSION, HARDWARE_BRINGUP. "
         "Drove the consolidation of the project into the public monorepo."],
        ["Ahmet Koçak",
         "Hardware design, bring-up",
         "Designed the KiCad schematic and PCB layout through all four iterations. "
         "Owned the JLCPCB fab order workflow. Ran the bench bring-up sessions and "
         "caught the iteration-3 grounding issue on the scope. Drove the 4-layer "
         "stack-up redesign for iteration 4. Authored the build-guide-vs-KiCad "
         "errata document."],
        ["Faruk Gökhan Abay",
         "Simulation, harmonic analysis",
         "Built the Simulink models that produced the 4.9 % THD prediction and, "
         "critically, the simulation evidence that killed the IR2110 bootstrap "
         "path before silicon was committed. Authored sections of the ELE 402 "
         "interim report including the gate-driver and modulation comparison "
         "tables."],
        ["Mücahit Aydın",
         "Hardware assembly, MCU foundations",
         "Performed populated-board assembly. Authored the early STM32F303-RE pin "
         "and foundations-for-PWM documents that gave the firmware its initial "
         "pin map (later corrected in iteration 3 to the as-built v4 layout)."],
    ], col_widths=[3.5 * cm, 3.5 * cm, 9 * cm])
    s.append(table_caption("Project group member contributions."))
    s.append(team)
    s.append(Spacer(0, 0.4 * cm))
    s.append(P("Cross-domain milestones", H3))
    s.append(P("""
        Every bench bring-up session required at least one operator at the
        supplies and one at the scope. Every PCB review before a fab order
        was the schematic author plus at least one independent reviewer.
        Firmware bring-up sessions paired the firmware author with the
        hardware author so the gap between "what the firmware expects" and
        "what is actually wired" was always closeable in real time.
    """))
    s.append(P("""
        The decision to switch from IPD LS-PWM to PSC-PWM — a substantial
        deviation from Build Guide v3.1 — was made jointly after Ahmet's
        bench measurement of the bridge-1 thermal imbalance, Furkan's
        firmware-side analysis of what the IPD asymmetry meant for sustained
        operation, and Faruk's simulation evidence that PSC's
        bridge-symmetric carrier scheme would resolve the issue. The team
        had confidence to make the change without losing weeks of bench
        time because all three perspectives had been reconciled before any
        code or hardware changed.
    """))
    s.extend(fig(Path("demo-stand-group-photo.jpeg"),
                 "The four-person team Cereyan Hacıları on the demo stand under "
                 "Assoc. Prof. Dr. Rasım Doğan.", width_cm=13))
    s.append(PageBreak())
    return s


def section_comments_conclusions() -> list:
    s = [P("12. COMMENTS AND CONCLUSIONS", H1)]
    s.append(P("Summary of the project and its results", H3))
    s.append(P("""
        Across two academic semesters and four hardware iterations, the
        project team Cereyan Hacıları designed, fabricated, brought up,
        and demonstrated a 5-level cascaded H-bridge multilevel inverter
        that satisfies the supervisor-agreed deliverable specification:
        five distinct cascade output levels at 100 V cascade output,
        under sustained PSC-PWM at 5 kHz, with both bridges thermally
        matched. The headline metrics from §10 confirm that the system
        meets every engineering standard and constraint identified at the
        outset within the bench-scope of the project, with the formal IEEE
        519-2022 voltage-THD compliance validated through simulation
        (4.9 % vs. the 8 % limit) and pending only the LC-filter
        integration for direct bench measurement.
    """))
    s.append(P("""
        The work produced more than a working inverter. It produced a
        consolidated public engineering record — Build Guide v4.0 superseding
        v3.1, a documentation website with per-subsystem deep-dives, four
        per-iteration narratives that honestly account for what failed and
        what was learned, five design-decision notes documenting the
        non-obvious choices (bootstrap fundamentals, CHB isolation, PSC vs.
        LS-PWM, IGBT vs. MOSFET, the grounding fix), a Cadence-Genus /
        Innovus / GDSII flow for an experimental RISC-V SoC with PWM
        accelerator (preserved as an exploratory track outside the
        graduation deliverable), and a dashboard with a scenario-based
        simulator that can demonstrate every fault chain without touching
        real silicon.
    """))
    s.append(P("Takeaways and lessons learned", H3))
    s.append(P("""
        Five themes recurred across the four iterations and the firmware
        bring-up that the team would carry into any follow-on power-
        electronics project:
    """))
    s.append(P("""
        <b>1. Topology imposes hardware requirements that aren't optional.</b>
        CHB requires galvanic isolation between every floating bridge and
        the controller. This is not a preference, not "good practice", not
        "for noise immunity" — it is a structural consequence of the
        cascaded series connection. Bootstrap-based drivers cannot drive a
        non-ground-referenced bridge; the Simulink simulation that confirmed
        this saved at least one wasted board iteration.
    """))
    s.append(P("""
        <b>2. Component substitutions need the firmware and the protection
        chain updated together.</b> The IRFZ44N → IRFB4110 swap was three
        coupled changes, not one: the MOSFET part, the firmware dead time
        (2 µs → 3 µs to accommodate the higher gate charge), and a check
        that the TVS clamp (84.5 V) sat below the new V<sub>DSS</sub>
        (100 V). Treating the substitution as a single-line BOM edit would
        have left a latent defect.
    """))
    s.append(P("""
        <b>3. Defensive instrumentation pays off.</b> The PSC carrier-shift
        <i>lock=OK|BAD</i> diagnostic was added before the first bench
        session on the theory that "if it's wrong, we want to know without
        scope-debugging". It caught a real problem on day one — the
        post-EGR_UG sequence was clobbering TIM8 CNT, dropping PSC to
        3-level output. The fix was straightforward once the symptom was
        visible. Without the diagnostic, the team would have spent an
        afternoon scoping carrier alignments. Cheap instrumentation, large
        dividend.
    """))
    s.append(P("""
        <b>4. Build guide is documentation; schematic is source of truth.</b>
        The v3.1 build-guide PDF had three pin-assignment errors that the
        project survived only because the schematic was authored against
        the datasheets. When documentation disagrees with what gets
        fabricated, what gets fabricated wins. Build Guide v4.0 carries
        all three corrections.
    """))
    s.append(P("""
        <b>5. Simulation kills bad design paths cheaply.</b> The IR2110
        incompatibility with CHB topology was identified in Simulink
        before any board was built. A wasted iteration would have cost
        ≈ 3 weeks (PCB design + fab + assembly + bring-up). The Simulink
        work cost ≈ 3 days. The leverage ratio for design-phase simulation
        is enormous when it kills an architectural mistake.
    """))
    s.append(P("Future work and proposed next steps", H3))
    s.append(P("""
        Six tracks are documented in the project's roadmap, in rough order
        of engineering cost:
    """))
    fut = themed_table([
        ["Track", "Engineer-months", "What it unlocks"],
        ["LC output filter", "1", "Driving non-trivial loads (motor / transformer / RL) without injecting cascade-step harmonics."],
        ["Closed-loop control", "2", "Output-voltage regulation against load and bus drift (currently open-loop)."],
        ["Thermal enclosure", "2", "Moving from open-bench to enclosed deployment (forced air + EMI filtering)."],
        ["PSC tuning extensions", "0.5", "fsw sweep, phase-offset sweep, closed-loop carrier lock with auto-recovery."],
        ["Grid tie", "4–6", "PLL + anti-islanding + compliance testing — the hardest single track."],
        ["Product path", "6–9", "Full productisation including dashboard scale-out and compliance certification."],
    ], col_widths=[3.5 * cm, 2.5 * cm, 10 * cm])
    s.append(table_caption("Roadmap of future work."))
    s.append(fut)
    s.append(Spacer(0, 0.4 * cm))
    s.append(P("""
        The recommended ordering is LC filter → closed-loop → thermal
        enclosure → (PSC tuning at any time) → grid tie, with product
        path layered on top. The LC filter is the prerequisite for
        everything downstream: closed-loop control on an unfiltered cascade
        is unstable; grid tie without filtering is unacceptable to any
        utility; thermal enclosure has to dissipate the LC's losses too.
        Building the LC filter first keeps the rest of the roadmap unblocked.
    """))
    s.append(P("""
        For research or educational use, the as-built system is already
        useful as a teaching tool for CHB modulation, gate-drive isolation,
        and structured bring-up workflow. The documentation supports that
        use case directly through Build Guide v4.0, the per-iteration
        narratives, and the five design-decision notes.
    """))
    s.append(P("Closing remarks", H3))
    s.append(P("""
        The graduation project deliverable is the inverter component. The
        architectural decisions documented in this report — CHB topology,
        TLP250 + B0515S isolation, PSC modulation, modular two-PCB
        boards — all held up under bench validation. Each was justified
        through the design-decision narrative and tested through the
        iteration cycle. The team's work is the foundation on which a
        product, an academic extension, or a follow-on graduation project
        can be built.
    """))
    s.append(P("""
        The team Cereyan Hacıları thanks Assoc. Prof. Dr. Rasım Doğan for
        supervisory guidance through the four iterations, the Hacettepe
        University EEE department for lab access and equipment, and one
        another for the willingness to do bench-debug sessions that ran
        past midnight.
    """))
    s.append(PageBreak())
    return s


def references() -> list:
    s = [P("REFERENCES", H1)]
    refs = [
        '[1] J. Rodriguez, J. S. Lai, and F. Z. Peng, "Multilevel inverters: a survey '
        'of topologies, controls, and applications," <i>IEEE Trans. Ind. Electron.</i>, '
        'vol. 49, no. 4, pp. 724–738, Aug. 2002.',
        '[2] S. Kouro et al., "Recent advances and industrial applications of multilevel '
        'converters," <i>IEEE Trans. Ind. Electron.</i>, vol. 57, no. 8, pp. 2553–2580, '
        'Aug. 2010.',
        '[3] B. P. McGrath and D. G. Holmes, "Multicarrier PWM strategies for multilevel '
        'inverters," <i>IEEE Trans. Ind. Electron.</i>, vol. 49, no. 4, pp. 858–867, '
        'Aug. 2002.',
        '[4] F. Z. Peng, "A generalized multilevel inverter topology with self voltage '
        'balancing," <i>IEEE Trans. Ind. Appl.</i>, vol. 37, no. 2, pp. 611–618, '
        'Mar./Apr. 2001.',
        '[5] D. G. Holmes and T. A. Lipo, <i>Pulse Width Modulation for Power Converters: '
        'Principles and Practice.</i> Hoboken, NJ: Wiley-IEEE Press, 2003.',
        '[6] L. G. Franquelo et al., "The age of multilevel converters arrives," '
        '<i>IEEE Ind. Electron. Mag.</i>, vol. 2, no. 2, pp. 28–39, Jun. 2008.',
        '[7] M. Malinowski et al., "A survey on cascaded multilevel inverters," '
        '<i>IEEE Trans. Ind. Electron.</i>, vol. 57, no. 7, pp. 2197–2206, Jul. 2010.',
        '[8] X. Yuan et al., "Stationary-frame generalized integrators for current '
        'control of active power filters," <i>IEEE Trans. Ind. Appl.</i>, vol. 38, '
        'no. 2, pp. 523–532, Mar./Apr. 2002.',
        '[9] K. A. Corzine and Y. L. Familiant, "A new cascaded multilevel H-bridge '
        'drive," <i>IEEE Trans. Power Electron.</i>, vol. 17, no. 1, pp. 125–131, '
        'Jan. 2002.',
        '[10] B. J. Baliga, "Power semiconductor device figure of merit for high-frequency '
        'applications," <i>IEEE Electron Device Lett.</i>, vol. 10, no. 10, pp. 455–457, '
        'Oct. 1989.',
        '[11] IEEE Std 519-2022, <i>Recommended Practice and Requirements for Harmonic '
        'Control in Electric Power Systems</i>, IEEE Power and Energy Society, 2022.',
        '[12] IEEE Std 1547-2018, <i>Standard for Interconnection and Interoperability '
        'of Distributed Energy Resources with Associated Electric Power Systems '
        'Interfaces</i>, IEEE Standards Coordinating Committee 21, 2018.',
        '[13] IEC 61000-4-7:2002, <i>Electromagnetic compatibility (EMC) — Part 4-7: '
        'Testing and measurement techniques — General guide on harmonics and '
        'interharmonics measurements and instrumentation</i>, International '
        'Electrotechnical Commission, 2002.',
        '[14] STMicroelectronics, <i>STM32F303xD/xE Reference Manual</i> (RM0316), '
        '2019. [Online]. Available: https://www.st.com/resource/en/reference_manual/'
        'rm0316-stm32f303xbcde-stm32f303x68-stm32f328x8-stm32f358xc-stm32f398xe-advanced-armbased-mcus-stmicroelectronics.pdf',
        '[15] Infineon Technologies, <i>IRFB4110 N-Channel HEXFET Power MOSFET Datasheet</i>, '
        'rev. C, 2015.',
        '[16] Toshiba Semiconductor, <i>TLP250H Photocoupler Datasheet</i>, '
        '2020.',
        '[17] Microchip Technology, <i>MCP3201 2.7V 12-Bit A/D Converter with SPI '
        'Serial Interface</i>, 2007.',
        '[18] Allegro MicroSystems, <i>ACS712 Fully Integrated, Hall-Effect-Based '
        'Linear Current Sensor IC</i>, 2017.',
        '[19] Onsemi, <i>6N137, HCPL2601, HCPL2611 Single-Channel, High Speed Optocoupler</i>, '
        'Rev. 16, 2019.',
        '[20] Mornsun, <i>B0515S-1WR3 1 W Isolated DC/DC Converter Datasheet</i>, 2018.',
    ]
    for r in refs:
        s.append(P(r, REF))
    return s


# ===== Main ==========================================================================

def main() -> int:
    print(f"Generating final report PDF → {OUT.relative_to(REPO)}")
    doc = _build_doc()
    story: list = []

    # Two-pass: build content first (populates _FIGURES, _TABLES), then prepend
    # title + abstract + TOC + LoF/LoT. Body sections only — fronts inserted after.
    body: list = []
    body += section_introduction()
    body += section_project_description()
    body += section_standards_constraints()
    body += section_sdg()
    body += section_literature_review()
    body += section_methods()
    body += section_preliminary_design()
    body += section_prototype()
    body += section_design_iterations()
    body += section_final_design()
    body += section_teamwork()
    body += section_comments_conclusions()
    body += references()

    # Now assemble final document order
    story += title_page()
    story += abstract_page()
    story += toc_page()
    story += list_of_figures_tables_page()
    story += body

    doc.build(story, canvasmaker=FooterCanvas)

    print(f"  → wrote {OUT.stat().st_size / 1024:.0f} KB")
    print(f"  → {len(_FIGURES)} figures, {len(_TABLES)} tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
