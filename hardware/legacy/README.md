# Legacy hardware

Earlier design iterations preserved for the iteration-history narrative. **These boards are superseded by [`../single-bridge-v4/`](../single-bridge-v4/) and should not be fabricated.**

| Iteration | What it was | Why it was replaced |
|---|---|---|
| [`iteration-1/`](iteration-1/) | First-pass single dual-bridge layout, IRFZ44N MOSFETs, IPD LS-PWM | MOSFET thermal margin too tight; PWM strategy did not give cascade balance. |
| [`iteration-2/`](iteration-2/) | Second-pass layout with revised gate-drive routing | Bootstrap fundamentals issue; design notes preserved at [`../../docs/design-notes/bootstrap-fundamentals.md`](../../docs/design-notes/bootstrap-fundamentals.md). |
| [`iteration-3/`](iteration-3/) | Pre-final layout that exposed the 5V_GND ↔ 50V_GND coupling issue | Grounding fix and isolation rework documented in [`../../docs/design-notes/grounding-fix.md`](../../docs/design-notes/grounding-fix.md). |

Each subdirectory will hold whatever KiCad sources survived; some iterations may not have a recoverable project file. The story of each iteration is captured in [`../../docs/iteration-history/`](../../docs/iteration-history/).
