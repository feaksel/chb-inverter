"""
Generate ELE 402 individual project logbooks (Spring 2025-2026), one PDF per
team member. Matches the format of the ELE 401 Fall 2025 logbook example.

Outputs:
  docs/assets/pdfs/ELE402_Spring2026_Logbook_FurkanEmirAksel.pdf
  docs/assets/pdfs/ELE402_Spring2026_Logbook_AhmetKocak.pdf
  docs/assets/pdfs/ELE402_Spring2026_Logbook_FarukGokhanAbay.pdf
  docs/assets/pdfs/ELE402_Spring2026_Logbook_MucahitAydin.pdf

Run: py -3.12 tools/generate-logbooks.py
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, ListFlowable, ListItem,
    PageBreak, PageTemplate, Paragraph, Spacer,
)

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None


# ===== Font registration (same Turkish-supporting Arial as the report) ===============

def _register_fonts():
    candidates = [
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
                return fam, f"{fam}-Bold", f"{fam}-Italic", f"{fam}-BoldItalic"
            except Exception:
                continue
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"


FONT, FONT_BOLD, FONT_ITALIC, FONT_BOLDITALIC = _register_fonts()


# ===== Constants =====================================================================

REPO = Path(__file__).resolve().parent.parent
IMG = REPO / "docs" / "assets" / "images"
PDF_DIR = REPO / "docs" / "assets" / "pdfs"

GREY_TEXT = colors.HexColor("#37474F")
TEAL_DARK = colors.HexColor("#004D40")


# ===== Styles =========================================================================

_base = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "Title", parent=_base["Title"],
    fontName=FONT_BOLD, fontSize=24, leading=30,
    alignment=TA_CENTER, textColor=colors.black, spaceAfter=12,
)
TITLE_LABEL = ParagraphStyle(
    "TitleLabel", parent=_base["Normal"],
    fontName=FONT, fontSize=11, leading=15,
    alignment=TA_CENTER, textColor=colors.black, spaceAfter=4,
)
TITLE_VALUE = ParagraphStyle(
    "TitleValue", parent=_base["Normal"],
    fontName=FONT_BOLD, fontSize=12, leading=16,
    alignment=TA_CENTER, textColor=colors.black, spaceAfter=10,
)

WEEK_HEADING = ParagraphStyle(
    "WeekHeading", parent=_base["Heading2"],
    fontName=FONT_BOLD, fontSize=13, leading=18,
    textColor=colors.black, spaceBefore=14, spaceAfter=8,
    keepWithNext=True,
)
BODY = ParagraphStyle(
    "Body", parent=_base["BodyText"],
    fontName=FONT, fontSize=11, leading=15,
    alignment=TA_JUSTIFY, spaceAfter=4, textColor=colors.black,
)
BULLET = ParagraphStyle(
    "Bullet", parent=BODY, leftIndent=18, bulletIndent=6, spaceAfter=3,
)


def _clean(text: str) -> str:
    """Strip em-dashes for clean rendering."""
    return text.replace("—", "-").replace("–", "-")


def P(text: str, style=BODY) -> Paragraph:
    return Paragraph(_clean(text), style)


def bullet_list(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(it, BULLET), leftIndent=14, value="circle") for it in items],
        bulletType="bullet", bulletColor=colors.black,
        leftIndent=22, bulletFontSize=10,
    )


# ===== Page footer ===================================================================

class FooterCanvas(canvas.Canvas):
    """Simple bottom-of-page rule + page number for body pages."""

    def __init__(self, *args, member_name="", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states: list = []
        self._member = member_name

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
        if page == 1:
            return
        self.saveState()
        self.setFont(FONT, 9)
        self.setFillColor(GREY_TEXT)
        self.drawString(
            2 * cm, 1.1 * cm,
            f"ELE 402 Project Logbook - {self._member} - Spring 2025-2026",
        )
        self.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {page} of {total}")
        self.restoreState()


# ===== Document builder =============================================================

def title_page(name: str, student_id: str) -> list:
    story = [Spacer(0, 1.5 * cm), P("ELE 402 Project Logbook", TITLE)]

    # Hacettepe logo (preserve aspect ratio)
    logo_path = IMG / "hacettepe-logo.png"
    if logo_path.exists():
        target = 5 * cm
        if PILImage is not None:
            with PILImage.open(logo_path) as im:
                w_px, h_px = im.size
        else:
            tmp = Image(str(logo_path))
            w_px, h_px = tmp.imageWidth, tmp.imageHeight
        if h_px >= w_px:
            h = target
            w = target * w_px / h_px
        else:
            w = target
            h = target * h_px / w_px
        logo = Image(str(logo_path), width=w, height=h)
        logo.hAlign = "CENTER"
        story.append(Spacer(0, 0.6 * cm))
        story.append(logo)
        story.append(Spacer(0, 0.6 * cm))

    story.extend([
        P("Hacettepe University", TITLE_LABEL),
        P("Department of Electrical and Electronics Engineering", TITLE_LABEL),
        Spacer(0, 1.2 * cm),
        P(f"{name}  {student_id}", TITLE_VALUE) if student_id else P(name, TITLE_VALUE),
        P("Design and Implementation of a 5-Level Cascaded H-Bridge Multilevel Inverter",
          TITLE_VALUE),
        P("Spring 2025-2026", TITLE_VALUE),
        Spacer(0, 1.0 * cm),
        P("Project Supervisor: <b>Assoc. Prof. Dr. Rasım Doğan</b>", TITLE_VALUE),
    ])
    story.append(PageBreak())
    return story


def week_section(week_num: int, title: str, items: list[str]) -> list:
    block = [P(f"Week {week_num}: {title}", WEEK_HEADING), bullet_list(items)]
    return [KeepTogether(block)]


def _build(out_path: Path, name: str, member_short: str):
    doc = BaseDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.0 * cm, bottomMargin=2.2 * cm,
        title=f"ELE 402 Project Logbook - {name}",
        author=name,
        subject="ELE 402 Graduation Project II Logbook - Spring 2025-2026",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="body")
    body = PageTemplate(id="body", frames=[frame])
    doc.addPageTemplates([body])

    def make_canvas(*args, **kwargs):
        return FooterCanvas(*args, member_name=member_short, **kwargs)

    return doc, make_canvas


def generate(name: str, student_id: str, member_short: str, weeks: list[tuple],
             out_filename: str) -> Path:
    out = PDF_DIR / out_filename
    out.parent.mkdir(parents=True, exist_ok=True)
    doc, mk = _build(out, name, member_short)
    story: list = []
    story += title_page(name, student_id)
    for n, title, items in weeks:
        story += week_section(n, title, items)
    doc.build(story, canvasmaker=mk)
    print(f"  -> {out.relative_to(REPO).as_posix()} ({out.stat().st_size//1024} KB)")
    return out


# ===== Logbook content ==============================================================

# ============================ FURKAN EMIR AKSEL =====================================
FURKAN_WEEKS = [
    (1, "Spring Semester Kickoff & System Engineering Review", [
        "<b>Group Meeting:</b> Met with Ahmet, Faruk, Mücahit to review iteration-1 outcomes from the Fall semester and lock the Spring sprint plan.",
        "<b>System Engineering:</b> Refreshed the system-architecture document with three open risk items: V_DSS headroom (IRFZ44N), bootstrap timing at high modulation index, and potential ground-coupling concerns as the design scales.",
        "<b>Project Engineering:</b> Set the iteration plan - four hardware iterations targeting a May demo, biweekly bench sessions, weekly team syncs. Defined the demo deliverable with supervisor: five distinct cascade levels at 100 V cascade output, no filter.",
        "<b>Individual Work:</b> Audited the iteration-1 firmware repository on GitHub and started planning the modulator refactor needed to enable runtime modulator selection (STAIR / PSC / STAIR_ALT).",
        "<b>Outcome:</b> Spring sprint plan signed off by supervisor at the first Spring meeting.",
    ]),
    (2, "Firmware Architecture Refactor", [
        "<b>Individual Work:</b> Reviewed iteration-1 main.c (367 lines, monolithic) and designed a clean modulator extraction into pwm_modulator.c + pwm_config.h.",
        "<b>System Engineering:</b> Defined a runtime-config API exposing modulator / fsw / fundamental / MI / bridge-select over UART, so future modulator swaps would not require reflashing.",
        "<b>Risk Register:</b> Logged bridge-1 thermal asymmetry under IPD as a tier-1 risk. Agreed with Faruk on what to simulate next (PSC comparison).",
        "<b>Documentation:</b> Started the firmware CHANGELOG.md to make per-release design decisions traceable across the Spring semester.",
    ]),
    (3, "Iteration 2 Bench Bring-up Support", [
        "<b>Bench Session:</b> Attended Ahmet's iteration-2 bench session. From the firmware side, instrumented the gate-drive routing changes to confirm switching behaviour.",
        "<b>Diagnosis:</b> Identified bootstrap-cap sag at modulation indices > 0.9 as the root cause of the iteration-2 distortion. The symptom looked like noise; the firmware-side analysis (LS-on window vs cap droop math) made it concrete.",
        "<b>Implementation:</b> Added DUTY_HIGH_CLAMP = 0.95f to the modulator. Recognised that the 6 ms bootstrap precharge needed to land in firmware before any high-duty work would be safe.",
        "<b>Cross-team:</b> Briefed Ahmet that routing-only fixes would not be enough for the floating-bridge structural problem - per-bridge isolated supply was needed in iteration 3.",
    ]),
    (4, "FSM Design + Project Engineering", [
        "<b>Architecture:</b> Designed the supervisory FSM (BOOT - IDLE - PRECHARGE - RUN - FAULT) on paper, with the 6 ms PRECHARGE state explicitly addressing the bootstrap-cap-charge problem.",
        "<b>Project Engineering:</b> Updated the project tracker. Used iteration-2's bootstrap evidence to formally commit the team to per-bridge isolated supply (B0515S) in iteration 3.",
        "<b>Documentation:</b> Drafted FSM_NOTES.md - the state machine and per-mode protection table that would later land in the firmware repo.",
        "<b>Group Coordination:</b> Aligned with Ahmet on iteration-3 architecture: B0515S + 6N137 per-bridge isolation, separate ground islands per cell.",
    ]),
    (5, "Iteration 3 Firmware Pre-work", [
        "<b>Implementation:</b> Built the bit-banged MCP3201 driver under the v3.1-documented '3 independent MISO' assumption.",
        "<b>Implementation:</b> Implemented the six sensing modes (FULL / DC_ONLY / CUR_ONLY / OPEN / DC1 / DC2) with auto-demotion on ADC self-test failure.",
        "<b>Implementation:</b> Added the N-of-M protection debounce (3 consecutive scans at 1 kHz before any fault trip).",
        "<b>Outcome:</b> Firmware code ready for iteration-3 board bring-up. Estimated < 2 hours from board power-up to first telemetry, barring hardware issues.",
    ]),
    (6, "Documentation Sprint", [
        "<b>Project Engineering:</b> Recognised that the team's design knowledge was scattered across chat history, notebooks, and emails. Decided to consolidate into a single repository as the Spring deliverable.",
        "<b>Documentation:</b> Drafted HARDWARE_BRINGUP.md - a comprehensive phase-by-phase reference covering firmware behaviour + bench expectations + troubleshooting.",
        "<b>System Engineering:</b> Defined the UART protocol formally (NMEA-style, $T/$S/$C/$P/$A/$E/$F prefixes, XOR checksum) so the future dashboard would have a stable contract to build against.",
        "<b>Group Coordination:</b> Walked through the bring-up reference with Ahmet to make sure firmware expectations matched bench reality.",
    ]),
    (7, "Iteration 3 First Power-up & MISO Surprise", [
        "<b>Bench Session:</b> Iteration-3 boards arrived. First power-up exposed intermittent SENSOR_LOST events when Bridge 2 was switching at the cascade peak.",
        "<b>System Engineering:</b> Re-analysed the isolation architecture against the as-fabricated board. Discovered the firmware's three-independent-MISO assumption did not match reality - the as-built upper-bridge island had only one shared MISO (DC2 + current).",
        "<b>Implementation:</b> Rewrote spi_mcp3201.c to perform strictly sequential one-channel-per-CS reads. Board did not need a respin - firmware was the cheaper fix.",
        "<b>Decision:</b> Convinced Ahmet that board respin time should target the bigger fix (4-layer stack-up for the grounding issue) rather than just the MISO topology.",
    ]),
    (8, "5V_GND - 50V_GND Grounding Diagnosis", [
        "<b>Bench Session:</b> Worked with Ahmet to characterise the grounding issue. From the firmware side, captured the intermittent fault pattern using the dashboard's scenario simulator for clean comparison.",
        "<b>Root Cause:</b> The continuous inner-plane pour + marginal optocoupler creepage were the two coupling paths. Firmware could not fix this - iteration-3 board needed a fundamental layout redesign.",
        "<b>System Engineering:</b> Drafted the iteration-4 architecture proposal: two identical single-bridge PCB modules, 4-layer stack-up with separated ground pours per region, IRFB4110 MOSFET substitution, PSC modulator replacing IPD.",
        "<b>Group Meeting:</b> Presented the iteration-4 plan to the supervisor. Got sign-off on the substantial scope expansion.",
    ]),
    (9, "Iteration 4 Plan Finalisation & PSC Firmware", [
        "<b>Implementation:</b> Created the pwm-rewrite-configurable branch. Replaced the 500 Hz IPD-style STAIR with PSC at 5 kHz. Added the carrier-lock diagnostic (cntoff + lock=OK|BAD) defensively - if PSC's 90 degree carrier shift gets clobbered, the cascade degrades to 3-level and the project fails.",
        "<b>Architecture:</b> Designed the PSC hardening: write TIM8 CNT after CR1_CEN is set (so post-EGR_UG cannot clobber it), read back the actual offset, expose lock status on every $C config line as telemetry.",
        "<b>Implementation:</b> Added the SPIINV runtime command for the 6N137 line-inversion mask - lets the team tune SPI polarity from the dashboard without reflashing.",
        "<b>Project Engineering:</b> Locked the iteration-4 fab order with Ahmet. Set the demo target firmly at week 14.",
    ]),
    (10, "VNOM Protection Scaling + Dashboard Architecture", [
        "<b>Implementation:</b> Added VNOM-scaled protection (UV / OV / IMBAL all derived from operator-set nominal bus voltage). Lets the team safely bench-test below 50 V without UV firing immediately at PRECHARGE.",
        "<b>Implementation:</b> Added STAIR_ALT as a hard-fallback modulator for cases where PSC carrier-lock fails on a particular board revision.",
        "<b>Dashboard:</b> Designed the PySide6 dashboard architecture: source abstraction (sim / serial / replay), scenario simulator, modulation visual twin, sensor graphing. Started implementation.",
        "<b>Documentation:</b> Updated CHANGELOG with the rationale and decisions behind each addition - the goal is that someone reading this in six months can reconstruct why the code looks the way it does without digging through diff.",
    ]),
    (11, "Interim Report v4 Submission + Dashboard Build-out", [
        "<b>Report:</b> Wrote the ELE 402 interim report v4 sections on firmware architecture, modulator selection rationale, and the IR2110-vs-TLP250 simulation evidence (working from Faruk's Simulink screenshots).",
        "<b>Implementation:</b> Built out the dashboard - 8 fault-scenario presets, modulation visual twin, sensor graphing with auto-follow.",
        "<b>Implementation:</b> Added the auto-cancel-on-connect mechanism: dashboard transmits STATUS on serial connect, which cancels the firmware's 3 s auto-start path. Important for resilience across Nucleo resets during demos.",
        "<b>Submission:</b> Interim report v4 submitted to supervisor.",
    ]),
    (12, "Iteration 4 Bring-up Day 1", [
        "<b>Bench Session:</b> Iteration-4 boards arrived populated. First power-up under Ahmet's lead.",
        "<b>System Engineering:</b> The lock=OK diagnostic immediately caught a PSC carrier-shift bug - TIM8 CNT was being clobbered by the post-EGR_UG sequence. The fix (write CNT after CR1_CEN) took an afternoon to design + verify. Without the diagnostic, this would have been hours of scope debugging.",
        "<b>Validation:</b> Confirmed five distinct cascade levels on scope. Bridges thermally matched within touch-check tolerance.",
        "<b>Decision:</b> The dashboard auto-cancel-on-connect held across multiple Nucleo resets - validates that part of the dashboard design.",
    ]),
    (13, "Bench Validation + Demo Prep", [
        "<b>Bench Session:</b> Sustained-run testing. Multi-minute PSC runs with no false SENSOR_LOST events. Inter-bridge thermal delta within ~3 deg C as Faruk's simulation predicted.",
        "<b>Validation:</b> Captured the 100 V output scope screenshot - five distinct cascade levels at the supervisor's spec.",
        "<b>Documentation:</b> Wrote FIRST_BENCH_SESSION.md - a linear walkthrough for whoever brings up the boards next. Folds together the relevant phases of HARDWARE_BRINGUP.md into one continuous procedure with pass/fail checkpoints.",
        "<b>Group Coordination:</b> Prepared the demo flow with the team. Each member would handle their domain at the demo (Ahmet on hardware, Faruk on simulation comparison, Mücahit on supply ramping, me on dashboard + firmware narrative).",
    ]),
    (14, "Demonstration + Final Report + Repository Consolidation", [
        "<b>Demo:</b> Public demonstration to the supervisor. Five distinct cascade levels at 100 V cascade output, bridges thermally matched, dashboard live with clean telemetry. Supervisor signed off.",
        "<b>Project Engineering:</b> Started the consolidation of the entire project into a single monorepo - hardware (KiCad, gerbers, BOM, photos), firmware (subtree-imported with full history), simulation, documentation, and the RISC-V experimental track.",
        "<b>Documentation:</b> Wrote Build Guide v4.0 as the canonical engineering reference, superseding v3.1 with the IRFZ44N - IRFB4110 swap, the IPD - PSC switch, the corrected pin map (with v3.1 errata), and the iteration-4 stack-up.",
        "<b>System Engineering:</b> Set up the MkDocs Material documentation site, CI workflows (docs build + deploy, firmware syntax check, dashboard unit tests), Git LFS for large binaries, and the issue / PR templates for future contributors.",
        "<b>Deliverable:</b> Final report, logbook, design notes, iteration history, roadmap, and consolidated repository all complete. Project site live at feaksel.github.io/chb-inverter/.",
    ]),
]


# ============================ AHMET KOÇAK ===========================================
AHMET_WEEKS = [
    (1, "Spring Semester Kickoff & Iteration 1 Review", [
        "<b>Group Meeting:</b> Reviewed iteration-1 outcomes with the team. Wrote up the thermal-asymmetry observation, the V_DSS-headroom concern with IRFZ44N, and the TVS-clamp mismatch as items to resolve in later iterations.",
        "<b>Individual Work:</b> Inventoried iteration-1 board components against the BOM. Confirmed which parts could be reused for iteration 2 and which would need replacement.",
        "<b>Decision:</b> Discussed iteration-2 scope with Furkan - gate-drive routing rework as the primary fix, same overall architecture otherwise. Kept the IRFZ44N for one more iteration to isolate variables.",
        "<b>Outcome:</b> Iteration-2 plan agreed; KiCad refactoring queued.",
    ]),
    (2, "Iteration 2 PCB Layout", [
        "<b>Schematic:</b> Reorganised the schematic into modular sheets - Highside_cell, Lowside_cell, driver_cell, voltage_sensing, current_sensing. Cleaner hierarchy, easier review.",
        "<b>Layout:</b> Shortened all gate-loop trace lengths (the iteration-1 ringing problem). Added a 100 nF ceramic decoupling cap at every TLP250 V_CC pin in addition to the bulk decoupling.",
        "<b>Layout:</b> Repositioned the bootstrap diode and cap closer to the gate driver and MOSFET source to reduce bootstrap-loop length.",
        "<b>Fab:</b> Submitted gerber pack to JLCPCB. 14-day lead time.",
    ]),
    (3, "Iteration 2 Boards Return + First Power-up", [
        "<b>Receive:</b> JLCPCB delivered iteration-2 boards. Assembled both bridges over two evenings with Mücahit.",
        "<b>Bench Session:</b> First power-up at 12 V. Confirmed five distinct cascade levels visible on scope - topology arithmetic still holds with the new layout.",
        "<b>Bench Session:</b> Stepped up to 24 V. Started seeing distortion at modulation indices > 0.9. Furkan's firmware analysis diagnosed bootstrap-cap sag.",
        "<b>Outcome:</b> Hardware behaviour confirmed iteration-2's gate-drive fixes worked, but the bootstrap-floating issue is structural and needs an isolation rework in iteration 3.",
    ]),
    (4, "Iteration 3 Planning", [
        "<b>Decision:</b> Committed to per-bridge isolated 15 V supply for iteration 3 - B0515S DC-DC, 6N137 optocouplers on every SPI line crossing the isolation boundary.",
        "<b>Schematic:</b> Added the 5v-15v_sch sheet for the B0515S subcircuit.",
        "<b>Schematic:</b> Added 6N137 optocouplers on SCK, CS, MISO between controller and each bridge island. Added 78L05 for the per-island logic supply.",
        "<b>Documentation:</b> Recorded the design intent in a board-revision note for the project file.",
    ]),
    (5, "Iteration 3 Layout", [
        "<b>Layout:</b> Routed the new isolated supply and 6N137 chain. First attempt used a continuous inner-plane ground pour for decoupling stability - this would later turn out to be the source of the grounding problem.",
        "<b>Component Sourcing:</b> With Mücahit, sourced 4x B0515S, 8x 6N137, 4x 78L05 from Motorobit and Direnc.net.",
        "<b>Fab:</b> Submitted iteration-3 gerbers to JLCPCB.",
        "<b>Documentation:</b> Updated BOM spreadsheet with the new isolation components.",
    ]),
    (6, "Build Guide v3.1 Cross-Check", [
        "<b>Documentation:</b> With Furkan, cross-referenced Build Guide v3.1 against the schematic to confirm design intent matched documentation.",
        "<b>Discovery:</b> Found three pin-assignment errors in the v3.1 PDF: PWM_1L (PA10 vs PA12 on F303RE), MCP3201 pins 5/7 swapped (CS and SCK), 78L05 pins 1/3 swapped (V_I and V_O).",
        "<b>Documentation:</b> Drafted the 'BUILD GUIDE KICAD MISSMATCH' errata document to track all three for the future Build Guide v4.",
        "<b>Decision:</b> Schematic was correct in each case (it followed the datasheets) - documentation was wrong. v4 of the build guide will incorporate all corrections.",
    ]),
    (7, "Iteration 3 Boards + Grounding Issue Discovery", [
        "<b>Receive:</b> JLCPCB delivered iteration-3 boards. Assembled with Mücahit.",
        "<b>Bench Session:</b> First power-up. Intermittent SENSOR_LOST events appeared when Bridge 2 was switching at the cascade peak.",
        "<b>Root Cause Diagnosis:</b> Spent the bench session tracing the issue. Found two coupling paths between 5V_GND and 50V_GND: the continuous inner-plane pour bridging the isolation boundary, and marginal copper creepage around the optocoupler input/output pads.",
        "<b>Outcome:</b> Iteration-3 isolation architecture is right in concept, wrong in copper. Board needs redesign with strictly separated inner ground pours.",
    ]),
    (8, "Iteration 4 Architectural Decision", [
        "<b>Group Meeting:</b> Presented the grounding-issue analysis to the team. Argued for a complete iteration-4 re-architecture rather than an incremental tweak - the team agreed.",
        "<b>Decision:</b> Locked iteration-4 changes: split into two identical single-bridge PCB modules; move from 2-layer to 4-layer stack-up; substitute IRFB4110 for IRFZ44N; firmware switches IPD - PSC.",
        "<b>Stack-up Design:</b> Designed the 4-layer stack - L1/L4 signal at 1 oz, L2 5V_GND pour at 0.5 oz (controller region only), L3 50V_GND pour at 0.5 oz (per-bridge region only, never crossing isolation).",
        "<b>Cost Check:</b> Reordered the BOM with IRFB4110 substituted. Confirmed total cost stays under the project budget.",
    ]),
    (9, "Iteration 4 KiCad Refactor", [
        "<b>Schematic:</b> Split the dual-bridge schematic into a single-bridge module that would be replicated twice. Top-level cascade integration becomes external cabling (one fab order, identical boards).",
        "<b>Layout:</b> Redrew the PCB with the 4-layer stack-up. Stitched ground vias along the controller-vs-bridge boundary, never crossing the isolation gap.",
        "<b>Layout:</b> Increased copper creepage around all isolation parts (TLP250, B0515S, 6N137) to at least 8 mm in critical regions to eliminate the parasitic AC-coupling path that bit iteration 3.",
        "<b>Documentation:</b> Updated stackup.md for the JLCPCB order parameters (1.6 mm FR-4 TG155, HASL-with-lead, etc.).",
    ]),
    (10, "Iteration 4 Fab Order + Component Substitution", [
        "<b>Fab:</b> Submitted iteration-4 gerbers to JLCPCB. Two-week turn for the 4-layer.",
        "<b>Sourcing:</b> With Mücahit, swapped MOSFET order from IRFZ44N to IRFB4110 at Motorobit. Confirmed TVS-clamp (84.5 V) now sits safely below MOSFET V_DSS (100 V).",
        "<b>BOM:</b> Updated the canonical BOM CSV with the substitution and verified line items.",
        "<b>Documentation:</b> Updated project notes with the substitution rationale - V_DSS headroom, TVS-clamp safety, lower R_DS(on) for thermal margin.",
    ]),
    (11, "Iteration 4 Waiting Period - Hardware Documentation", [
        "<b>Documentation:</b> Drafted the hardware section of the interim report v4 - covered the iteration-1 to iteration-3 evolution, the grounding fix narrative, and the iteration-4 re-architecture rationale.",
        "<b>Bench Setup:</b> Prepared the bench for iteration-4 sessions: cables, isolated supplies, scope probes, heatsinks for the new IRFB4110 substitution.",
        "<b>Group Coordination:</b> Walked Furkan through what to expect at iteration-4 bring-up from the hardware side - which symptoms would be normal during ramp, which would be red flags.",
        "<b>Outcome:</b> Bench fully ready for the iteration-4 boards.",
    ]),
    (12, "Iteration 4 Boards + Assembly + Bring-up Day 1", [
        "<b>Receive:</b> JLCPCB delivered iteration-4 boards. Two identical single-bridge modules as specified.",
        "<b>Assembly:</b> Spent two full evenings populating both modules with Mücahit. The IRFB4110 in TO-220 was an easier part to handle than the IRFZ44N had been.",
        "<b>Bench Session:</b> First power-up of module 1 at 12 V. Confirmed no SENSOR_LOST events - the grounding fix worked. Confirmed PSC carrier-lock from firmware telemetry.",
        "<b>Outcome:</b> Iteration-4 hardware is clean. No grounding noise, no false fault trips, dashboard reading clean telemetry.",
    ]),
    (13, "Full Cascade Bring-up + Bench Validation", [
        "<b>Bench Session:</b> Connected both modules in cascade. First cascaded power-up at 24 V - five distinct cascade levels visible on scope.",
        "<b>Bench Session:</b> Stepped up to 50 V per cell, 100 V cascade output. Five levels at the project deliverable.",
        "<b>Bench Session:</b> Multi-minute sustained run. Touch-checked both modules' MOSFETs - within ~3 deg C delta. Bridges thermally matched as Faruk's simulation had predicted.",
        "<b>Documentation:</b> Captured scope photos of the headline result for the final report.",
    ]),
    (14, "Demonstration + Hardware Documentation", [
        "<b>Demo:</b> Demo day. Both modules wired into the cascade, dashboard live, scope showing five distinct levels. Supervisor signed off the deliverable.",
        "<b>Documentation:</b> Contributed iteration-history pages, schematic walkthrough, and the bench-photo gallery to Furkan's repository consolidation.",
        "<b>Future Work:</b> Discussed the LC filter roadmap item with Furkan - L = 15 mH, C = 30 uF for the RL-load variant as Faruk's simulation suggested.",
        "<b>Deliverable:</b> Final report contributions, hardware section, and stack-up documentation complete.",
    ]),
]


# ============================ FARUK GÖKHAN ABAY =====================================
FARUK_WEEKS = [
    (1, "Spring Semester Kickoff & Simulation Status Review", [
        "<b>Group Meeting:</b> Reviewed iteration-1 bench results with the team. Mapped bench observations back to the Simulink predictions from Fall semester.",
        "<b>Individual Work:</b> Reviewed the ELE 401 Simulink IPD LS-PWM model. Identified that PSC-PWM simulation was the most useful next step given the bridge-1 thermal asymmetry observed at the bench.",
        "<b>Decision:</b> Agreed with Furkan to start a comparative PSC simulation to inform the iteration-2 / iteration-3 modulator decision.",
        "<b>Outcome:</b> Simulation work plan defined for the Spring semester.",
    ]),
    (2, "PSC-PWM Simulink Model Development", [
        "<b>Implementation:</b> Built the PSC-PWM Simulink model alongside the existing IPD baseline. Same H-bridge plant; different modulator block (two phase-shifted carriers at 90 deg vs four vertically stacked).",
        "<b>Model Architecture:</b> Used Simscape Electrical blocks for the H-bridges with ideal-switch behaviour for first-pass comparison.",
        "<b>Verification:</b> Confirmed PSC produces five-level cascade output as expected from textbook predictions.",
        "<b>Analysis:</b> Started THD comparison runs at the headline operating point (50 V per cell, 5 kHz, MI 0.95, 50 Hz fundamental).",
    ]),
    (3, "PSC vs IPD Quantitative Comparison", [
        "<b>Analysis:</b> Ran FFT on both PSC and IPD outputs at the same operating point.",
        "<b>Result:</b> IPD THD = 4.9%, PSC THD = 4.4% (cleaner higher-frequency content due to 2x effective switching frequency at the cascade output).",
        "<b>Analysis:</b> More importantly - PSC's per-bridge switching activity is symmetric across the two cells, while IPD's is heavily Bridge-1-biased (the cell mapped to the inner band always carries the most-frequent switching).",
        "<b>Outcome:</b> Confirmed PSC as the right choice for the future iteration-4 firmware. Communicated finding to Furkan.",
    ]),
    (4, "Gate Driver Simulation - IR2110 vs TLP250", [
        "<b>Implementation:</b> Built behavioural Simulink models for IR2110 (bootstrap) and TLP250 (optical-isolated) gate drivers, including the upper-cell floating-reference behaviour.",
        "<b>Critical Discovery:</b> The IR2110 simulation failed for the upper-cell bridge - gate voltage collapsed below threshold because the bootstrap capacitor could not refresh against the cascade's floating V_S.",
        "<b>Verification:</b> Re-ran with TLP250 + isolated B0515S supply. Gate voltage stable at 15 V on all cells regardless of floating potential.",
        "<b>Outcome:</b> Definitive simulation evidence that the team's TLP250 choice was structurally correct (not just preferable). Estimated this saved at least one wasted board iteration with the wrong gate driver.",
    ]),
    (5, "Snubber Network Analysis", [
        "<b>Analysis:</b> Added parasitic gate-loop inductance to the Simulink model and characterised V_DS ringing on the IRFZ44N stage under switching transients.",
        "<b>Result:</b> Without snubber, V_DS ringing exceeded 60 V at switching transitions - dangerously close to the IRFZ44N's 55 V V_DSS limit. Risk of MOSFET damage real.",
        "<b>Implementation:</b> Added a snubber model (22 ohm 2 W + 2.2 nF / 630 V across drain-source). Confirmed ringing reduced to safe levels.",
        "<b>Outcome:</b> Validated the snubber design that landed in iteration-3 hardware.",
    ]),
    (6, "Interim Report Methods Section", [
        "<b>Report:</b> Drafted the Methods section of the interim report v4 - covering CHB vs NPC vs FC topology comparison and PSC vs IPD modulator comparison.",
        "<b>Report:</b> Wrote up the IR2110 simulation evidence with annotated comparison plots showing the upper-cell gate voltage collapse.",
        "<b>Documentation:</b> Saved the simulation screenshots that would later become figures in the docs site and the final report.",
        "<b>Outcome:</b> Report sections submitted to Furkan for integration.",
    ]),
    (7, "LC Filter Modeling Begin", [
        "<b>Analysis:</b> Started modeling the LC output filter as a roadmap item for future work. Tried two variants: 15 mH / 22 uF (cutoff 325 Hz) for resistive load, 15 mH / 30 uF (cutoff 237 Hz) for RL load.",
        "<b>Implementation:</b> Built the chb-5level-rl-nospike.slx model with parametrised LC filter and RL load.",
        "<b>Analysis:</b> Characterised the wavy-current artefact under inductive load. The lower-cutoff variant (237 Hz) gives better attenuation at the cost of slower dynamic response.",
        "<b>Documentation:</b> Wrote up the LC design notes for the team's reference and the future-work roadmap.",
    ]),
    (8, "Bench Result Correlation - Iteration 3", [
        "<b>Analysis:</b> Compared the bench-observed grounding issue from iteration-3 against the Simulink model. The model uses ideal switches and ideal isolation - it cannot reproduce parasitic AC coupling between physically-close PCB traces.",
        "<b>Acknowledgement:</b> Documented in the simulation notes that the model has clear limits: parasitic inductance and capacitance, layout-level coupling, and thermal effects are all outside the model's scope.",
        "<b>Recommendation:</b> For iteration-4 grounding-fix validation, the team should rely on bench measurement (sustained-run sensor-loss event counts), not simulation.",
        "<b>Outcome:</b> Set expectations clearly with the team about what simulation can and cannot validate.",
    ]),
    (9, "Snubber Re-validation for IRFB4110", [
        "<b>Analysis:</b> With the iteration-4 substitution of IRFZ44N - IRFB4110, re-ran the snubber simulation. The IRFB4110's lower R_DS(on) means less voltage stress per switching event; the existing snubber design still works.",
        "<b>Analysis:</b> Confirmed that the 1.5KE62A TVS clamp at 84.5 V now sits safely below the IRFB4110's 100 V V_DSS rating. Protection chain restored.",
        "<b>Implementation:</b> Updated dead-time prediction - the IRFB4110's ~2x gate charge requires ~3 us dead time (up from 2 us with IRFZ44N).",
        "<b>Communication:</b> Briefed Furkan on the dead-time requirement for the iteration-4 firmware (BDTR.DTG = 0xA0 instead of 0x80).",
    ]),
    (10, "PSC Carrier-Lock Theoretical Analysis", [
        "<b>Analysis:</b> With Furkan, analysed why the PSC carrier-shift must hold at exactly ARR/2 for 5-level output. Anything else degrades the cascade output to 3-level.",
        "<b>Math:</b> Derived the level-output formula for two cells with phase shifts phi_1 = 0 deg and phi_2 = 90 deg - the cascade output level depends on the relative phases of the carrier-vs-reference intersections.",
        "<b>Recommendation:</b> The firmware should expose the actual measured TIM8 - TIM1 counter offset as telemetry (the lock=OK/BAD diagnostic).",
        "<b>Outcome:</b> Theoretical justification for the firmware's defensive lock diagnostic; the firmware team implemented it the same week.",
    ]),
    (11, "Interim Report Final Review", [
        "<b>Report:</b> Reviewed the full interim report v4 before submission. Updated my sections with the iteration-3 bench-vs-simulation correlation notes.",
        "<b>Submission:</b> Interim report v4 submitted on schedule.",
        "<b>Future Work:</b> Started planning the LC filter bench validation as a Spring 2027 task (post-graduation).",
        "<b>Outcome:</b> Report contributions complete.",
    ]),
    (12, "Iteration 4 Bench Support", [
        "<b>Bench Session:</b> Attended the iteration-4 bring-up to compare bench results against simulation predictions in real time.",
        "<b>Comparison:</b> PSC cascade output matched the simulation - five distinct levels at the predicted operating point.",
        "<b>Comparison:</b> Bridge-thermal balance matched the prediction within ~3 deg C (the simulation's per-bridge switching-event count had predicted this).",
        "<b>Outcome:</b> Simulation predictions held up at the bench. The team's confidence in further simulation-driven design decisions is justified.",
    ]),
    (13, "Final Report Methods + Conclusions", [
        "<b>Report:</b> Drafted the methods and lessons-learned sections for the final report from the simulation perspective.",
        "<b>Analysis:</b> With Furkan, mapped each bench-validated metric against the simulation prediction for the methods section - confirms the prediction-vs-bench correlation argument.",
        "<b>Documentation:</b> Contributed Simulink screenshots and FFT plots to the docs site (the future docs/simulation/ pages).",
        "<b>Outcome:</b> Final report contributions complete.",
    ]),
    (14, "Demonstration + Future Simulation Roadmap", [
        "<b>Demo:</b> Attended demo day. Confirmed bench results matched simulation predictions one more time for the supervisor.",
        "<b>Future Work:</b> Drafted the LC filter integration roadmap with the parametrised Simulink model handed off for follow-on work.",
        "<b>Future Work:</b> Discussed closed-loop control simulation needs for future PR-controller tuning - the bench has the sense channels, the firmware has the modulator setter, the simulation should be next.",
        "<b>Deliverable:</b> Final logbook and report contributions complete.",
    ]),
]


# ============================ MÜCAHİT AYDIN =========================================
MUCAHIT_WEEKS = [
    (1, "Spring Semester Kickoff & Pin Map Review", [
        "<b>Group Meeting:</b> Reviewed iteration-1 outcomes with the team. Lessons from the assembly side: the IRFZ44N TO-220 packages were tight for the bench-soldering iron in some routings.",
        "<b>Individual Work:</b> Re-reviewed my STM32F303-RE pin map document from Fall. Confirmed the firmware was using the as-wired pins, not the build-guide-v3.1 pins.",
        "<b>Decision:</b> Started drafting a pin map errata note for the team file.",
        "<b>Outcome:</b> Iteration-2 assembly plan defined.",
    ]),
    (2, "Iteration 2 Component Preparation", [
        "<b>Sourcing:</b> Inventoried iteration-2 components with Ahmet. Some parts (TLP250 sockets, 100 nF ceramic decoupling caps) needed top-up.",
        "<b>Procurement:</b> Placed restock order at Motorobit. Restock arrived within 4 days.",
        "<b>Preparation:</b> Pre-installed DIP-8 sockets on the iteration-2 boards before active component placement - reduces thermal stress on the TLP250 during assembly.",
        "<b>Outcome:</b> Iteration-2 boards prepped for assembly.",
    ]),
    (3, "Iteration 2 Assembly", [
        "<b>Assembly:</b> Populated iteration-2 boards with Ahmet across two evenings.",
        "<b>Bench Session:</b> Attended the iteration-2 first power-up. Helped with the supply ramp and supply-side monitoring while Ahmet ran the scope.",
        "<b>Observation:</b> Noted the bootstrap-cap-sag distortion at MI > 0.9 visually (output looked 'softer' at high MI) before Furkan's firmware analysis confirmed the cause.",
        "<b>Documentation:</b> Updated the assembly notes with two iteration-2 gotchas: TLP250 orientation must be checked before powering (LED side toward MCU); snubber resistor wattage matters for the 22 ohm 2 W spec.",
    ]),
    (4, "Pin Map Document Update", [
        "<b>Documentation:</b> Drafted v2 of my STM32 pin map document. Explicitly called out the v3.1 build-guide pin errors (PWM_1L, MCP3201, 78L05).",
        "<b>Cross-reference:</b> Confirmed each documented error against the STM32F303RE datasheet alternate-function table.",
        "<b>Validation:</b> Compared the corrected pin map against the firmware's GPIO setup code with Furkan. All consistent.",
        "<b>Outcome:</b> Pin map document ready for incorporation into Build Guide v4.",
    ]),
    (5, "Iteration 3 Component Sourcing", [
        "<b>Sourcing:</b> With Ahmet, identified the new iteration-3 components: 4x B0515S, 8x 6N137, 4x 78L05, plus passives for the isolated supply.",
        "<b>Procurement:</b> Placed orders at Motorobit + Direnc.net. All parts in stock domestically; no international shipping or customs friction.",
        "<b>Receipt:</b> Parts arrived within 6 days.",
        "<b>Inventory:</b> Catalogued and stored the parts for iteration-3 assembly.",
    ]),
    (6, "Foundations for PWM Documentation Update", [
        "<b>Documentation:</b> Updated my 'Foundations for PWM Generation' document with the iteration-evolved understanding of TIM1 / TIM8 setup.",
        "<b>Cross-reference:</b> Added a note about the BDTR.OSSI bit - keeping outputs in safe state on MOE = 0 was something I'd flagged early but the team's full understanding came from the iteration bring-up sessions.",
        "<b>Group Coordination:</b> Shared the updated doc with Furkan for inclusion in the firmware repo.",
        "<b>Outcome:</b> Foundational MCU documentation maintained.",
    ]),
    (7, "Iteration 3 Assembly", [
        "<b>Assembly:</b> Populated iteration-3 boards with Ahmet. The 6N137 + B0515S placement was tighter than iteration-2 - had to be careful about heat dissipation during soldering.",
        "<b>Bench Session:</b> Attended the iteration-3 first power-up. Confirmed assembly visually with Ahmet before powering up.",
        "<b>Observation:</b> Watched the intermittent SENSOR_LOST events from the bench. Initially we wondered if assembly was the cause; quick re-inspection ruled that out - it was layout-level coupling, not solder joints.",
        "<b>Outcome:</b> Iteration-3 assembly clean, but board has the grounding issue documented separately.",
    ]),
    (8, "Iteration 3 Re-bring-up Support", [
        "<b>Assistance:</b> Helped Ahmet with the grounding-issue diagnosis. Ran probe-and-scope sweeps to localise the coupling paths.",
        "<b>Observation:</b> The marginal optocoupler creepage was visible under magnification - input and output pads of the 6N137 had < 2 mm of clearance in places. Probably acceptable on a 2-layer board with clean ground separation; not acceptable with the continuous inner-plane pour.",
        "<b>Decision:</b> With the team, agreed that an iteration-4 board redesign was the right call.",
        "<b>Documentation:</b> Recorded the iteration-3 grounding observations in the project notes.",
    ]),
    (9, "Iteration 4 Architecture Discussion", [
        "<b>Group Meeting:</b> Participated in the iteration-4 architectural discussion. Backed Ahmet's 4-layer stack-up proposal and the IRFB4110 MOSFET substitution.",
        "<b>Sourcing:</b> Started identifying the iteration-4 BOM changes - IRFB4110 at Motorobit, heatsinks adapted for the new MOSFET's gate-charge profile (per Faruk's dead-time recalculation).",
        "<b>Outcome:</b> Iteration-4 BOM finalised.",
    ]),
    (10, "Iteration 4 Procurement", [
        "<b>Procurement:</b> Placed the IRFB4110 order at Motorobit. Confirmed in-stock; ordered 16x (8 for the project + 8 spares).",
        "<b>Inventory:</b> Verified the rest of the iteration-4 BOM was in stock from previous orders. Just needed the MOSFET swap.",
        "<b>Group Coordination:</b> Coordinated with Ahmet on JLCPCB order timing - aimed for boards + parts to arrive in the same week if possible.",
        "<b>Outcome:</b> Iteration-4 procurement complete, all parts secured.",
    ]),
    (11, "Bench Setup Preparation", [
        "<b>Bench Prep:</b> Cleaned and prepped the bench for iteration-4 sessions. Verified scope calibration, supply current limits, isolated bench supplies.",
        "<b>Cable Audit:</b> Inventoried the bench cables - some had developed intermittent shorts from previous sessions. Replaced four.",
        "<b>Heatsink Prep:</b> Pre-attached TO-220 clip-on heatsinks to the IRFB4110 inventory so assembly was faster on the bench-population day.",
        "<b>Outcome:</b> Bench fully ready for iteration-4 boards.",
    ]),
    (12, "Iteration 4 Assembly", [
        "<b>Assembly:</b> Spent two full evenings populating iteration-4 boards with Ahmet. Two identical single-bridge modules + spares.",
        "<b>Verification:</b> Cross-checked every assembled board against the BOM and the schematic before power-up. Caught one missing decoupling cap on module 2 during the cross-check.",
        "<b>Bench Session:</b> Attended the iteration-4 first power-up. Ran the supply ramp while Ahmet monitored the scope.",
        "<b>Outcome:</b> Both iteration-4 boards assembled successfully, no rework needed beyond the missed decoupling cap.",
    ]),
    (13, "Full Bench Sessions", [
        "<b>Bench Session:</b> Attended the full cascade bring-up sessions. Helped with cable management, supply coordination, and quick component swaps when needed.",
        "<b>Observation:</b> Touched the MOSFET cases during sustained PSC operation - both bridges felt the same temperature, confirming Faruk's simulation prediction of symmetric switching loss under PSC.",
        "<b>Coordination:</b> Helped Furkan capture scope screenshots for the documentation.",
        "<b>Outcome:</b> Bench validation phase complete.",
    ]),
    (14, "Demonstration + Final Documentation", [
        "<b>Demo:</b> Attended demo day. Helped with cabling, supply setup, and quick swap-outs on the demo bench.",
        "<b>Documentation:</b> Contributed assembly notes to Build Guide v4 - especially around the IRFB4110 substitution and the heatsink mounting procedure.",
        "<b>Future Work:</b> Wrote up the bench setup recommendations for future student groups - cable inventory, supply ramping procedure, scope calibration checks.",
        "<b>Deliverable:</b> Final logbook complete.",
    ]),
]


# ===== Main ==========================================================================

def main() -> int:
    print("Generating ELE 402 individual project logbooks (Spring 2025-2026)...")
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    generate(
        name="Furkan Emir Aksel", student_id="220357099",
        member_short="Furkan Emir Aksel",
        weeks=FURKAN_WEEKS,
        out_filename="ELE402_Spring2026_Logbook_FurkanEmirAksel.pdf",
    )
    generate(
        name="Ahmet Koçak", student_id="",
        member_short="Ahmet Koçak",
        weeks=AHMET_WEEKS,
        out_filename="ELE402_Spring2026_Logbook_AhmetKocak.pdf",
    )
    generate(
        name="Faruk Gökhan Abay", student_id="",
        member_short="Faruk Gökhan Abay",
        weeks=FARUK_WEEKS,
        out_filename="ELE402_Spring2026_Logbook_FarukGokhanAbay.pdf",
    )
    generate(
        name="Mücahit Aydın", student_id="",
        member_short="Mücahit Aydın",
        weeks=MUCAHIT_WEEKS,
        out_filename="ELE402_Spring2026_Logbook_MucahitAydin.pdf",
    )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
