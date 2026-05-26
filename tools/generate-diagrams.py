"""
Render diagrams (FSM, system block) as PNG files for embedding in the
final-report PDF and the docs site.

Outputs:
  docs/assets/images/diagram-fsm.png
  docs/assets/images/diagram-system-block.png

Run: py -3.12 tools/generate-diagrams.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "assets" / "images"

TEAL = "#00695C"
TEAL_DARK = "#004D40"
AMBER = "#FF8F00"
GREY_RULE = "#B0BEC5"
TEXT = "#37474F"


# ============================================================================
# FSM diagram
# ============================================================================

def fsm_diagram():
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_aspect("equal")

    # State positions (centre coordinates)
    states = {
        "BOOT":      (1.1, 4.0),
        "IDLE":      (3.4, 4.0),
        "PRECHARGE": (5.9, 4.0),
        "RUN":       (8.5, 4.0),
        "FAULT":     (5.9, 1.2),
    }

    def state_box(name, x, y, w=1.7, h=0.7):
        rect = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=TEAL_DARK, edgecolor=TEAL_DARK, linewidth=1.5,
        )
        ax.add_patch(rect)
        ax.text(x, y, name, ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")

    for name, (x, y) in states.items():
        state_box(name, x, y)

    # Compute box boundary for clean arrow endpoints
    def edge(point, name, direction):
        x, y = states[name]
        hw, hh = 0.85, 0.35
        if direction == "right":  return (x + hw, y)
        if direction == "left":   return (x - hw, y)
        if direction == "top":    return (x, y + hh)
        if direction == "bottom": return (x, y - hh)
        return point

    def arrow(src, dst, label, src_side, dst_side,
              rad=0.0, label_xy=None, label_align=("center", "center")):
        sx, sy = edge(None, src, src_side)
        ex, ey = edge(None, dst, dst_side)
        connectionstyle = f"arc3,rad={rad}" if rad else "arc3,rad=0"
        arr = FancyArrowPatch(
            (sx, sy), (ex, ey),
            arrowstyle="->,head_width=4,head_length=6",
            color=TEAL, linewidth=1.4,
            connectionstyle=connectionstyle,
        )
        ax.add_patch(arr)
        if label_xy is None:
            label_xy = ((sx + ex) / 2, (sy + ey) / 2 + 0.18)
        ax.text(*label_xy, label, ha=label_align[0], va=label_align[1],
                fontsize=9, color=TEXT,
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                          edgecolor="none", alpha=0.85))

    # Straight horizontal arrows
    arrow("BOOT", "IDLE", "self-test", "right", "left")
    arrow("IDLE", "PRECHARGE", "START", "right", "left")
    arrow("PRECHARGE", "RUN", "g_precharge_done", "right", "left")

    # Down to FAULT
    arrow("IDLE", "FAULT", "sensor fault",
          "bottom", "top", rad=-0.25,
          label_xy=(3.6, 2.4), label_align=("right", "center"))
    arrow("PRECHARGE", "FAULT", "UV / OV / OC / IMBAL",
          "bottom", "top", rad=0,
          label_xy=(5.9, 2.4), label_align=("center", "center"))
    arrow("RUN", "FAULT", "UV / OV / OC / IMBAL",
          "bottom", "top", rad=0.25,
          label_xy=(8.2, 2.4), label_align=("left", "center"))

    # FAULT -> IDLE (CLEAR)
    arrow("FAULT", "IDLE", "CLEAR (after condition cleared)",
          "left", "bottom", rad=0.35,
          label_xy=(3.0, 1.5), label_align=("center", "center"))

    # STOP loops (curved over the top)
    # PRECHARGE -> IDLE
    arrow("PRECHARGE", "IDLE", "STOP", "top", "top", rad=-0.45,
          label_xy=(4.65, 5.0), label_align=("center", "center"))
    # RUN -> IDLE
    arrow("RUN", "IDLE", "STOP", "top", "top", rad=-0.55,
          label_xy=(6.5, 5.0), label_align=("center", "center"))

    out_path = OUT / "diagram-fsm.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    plt.close(fig)
    print(f"  -> {out_path.relative_to(REPO).as_posix()}")


# ============================================================================
# System block diagram
# ============================================================================

def system_block_diagram():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=150)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_aspect("equal")

    def box(x, y, w, h, label, sub=None, color=TEAL_DARK, text_color="white",
            sub_color="white", fontsize=10, sub_size=8):
        rect = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=color, edgecolor=color, linewidth=1.3,
        )
        ax.add_patch(rect)
        if sub:
            ax.text(x, y + 0.12, label, ha="center", va="center",
                    color=text_color, fontsize=fontsize, fontweight="bold")
            ax.text(x, y - 0.16, sub, ha="center", va="center",
                    color=sub_color, fontsize=sub_size)
        else:
            ax.text(x, y, label, ha="center", va="center",
                    color=text_color, fontsize=fontsize, fontweight="bold")

    def arrow(x1, y1, x2, y2, label="", label_offset=(0, 0.15), bidir=False,
              color=TEAL, ls="-"):
        arrowstyle = "<->" if bidir else "->,head_width=3,head_length=5"
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle=arrowstyle, color=color, linewidth=1.2,
            linestyle=ls,
        ))
        if label:
            mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
            ax.text(mx, my, label, ha="center", va="center",
                    fontsize=8, color=TEXT,
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                              edgecolor="none", alpha=0.9))

    # Controller block (top)
    box(5.5, 5.3, 4.0, 0.7,
        "STM32 Nucleo-F303RE controller",
        sub="bare-metal CMSIS @ 64 MHz, TIM1 + TIM8 PWM, USART2",
        color=TEAL_DARK)

    # Dashboard (top right, separate)
    box(9.4, 5.3, 1.7, 0.7,
        "Dashboard",
        sub="PySide6",
        color="#37474F")
    arrow(8.45, 5.3, 8.55, 5.3, label="UART 115200 8N1",
          label_offset=(0, 0.30), bidir=True, color="#37474F")

    # DC supplies
    box(1.2, 3.2, 1.5, 0.55,
        "DC supply 1",
        sub="50 V isolated", color="#37474F", fontsize=9)
    box(1.2, 1.5, 1.5, 0.55,
        "DC supply 2",
        sub="50 V isolated", color="#37474F", fontsize=9)

    # Bridge 1 (upper-bridge module)
    box(4.5, 3.2, 2.5, 1.6,
        "Bridge 1 module",
        sub="IRFB4110 H-bridge\nTLP250 + B0515S + MCP3201",
        color=TEAL, sub_size=8)
    # Bridge 2
    box(4.5, 1.5, 2.5, 1.6,
        "Bridge 2 module",
        sub="IRFB4110 H-bridge\nTLP250 + B0515S + MCP3201",
        color=TEAL, sub_size=8)

    # Cascade sum + load
    box(8.3, 2.35, 2.0, 0.75,
        "AC sum (series)",
        sub="cascade output -> load",
        color=AMBER, fontsize=10, sub_size=8)

    # Connections — DC supplies feed bridges
    arrow(1.95, 3.2, 3.25, 3.2)
    arrow(1.95, 1.5, 3.25, 1.5)

    # Bridges to cascade sum
    arrow(5.75, 3.2, 7.30, 2.55, label="V_DC1 swing", label_offset=(-0.05, 0.18))
    arrow(5.75, 1.5, 7.30, 2.15, label="V_DC2 swing", label_offset=(-0.05, -0.18))

    # Controller -> bridges (PWM, with dead-time)
    arrow(4.5, 4.95, 4.5, 4.0,
          label="TIM1 PWM\n+ 3 µs dead time",
          label_offset=(-1.05, 0.0))
    arrow(5.5, 4.95, 5.0, 2.3,
          label="TIM8 PWM\n+ 3 µs dead time",
          label_offset=(1.1, 0.0))

    # Bridges -> controller (sensing via opto)
    arrow(5.75, 3.6, 6.5, 4.95, label="MCP3201 / 6N137 opto",
          label_offset=(0.30, 0.10), ls=":")
    arrow(5.75, 1.9, 6.5, 4.95, label="", ls=":")

    out_path = OUT / "diagram-system-block.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    plt.close(fig)
    print(f"  -> {out_path.relative_to(REPO).as_posix()}")


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating diagrams...")
    fsm_diagram()
    system_block_diagram()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
