# Stack-up — single-bridge v4

**Fabricator:** JLCPCB.
**Board outline:** 1.6 mm FR-4 TG155.
**Layer count:** 4 (1 oz outer / 0.5 oz inner).
**Surface finish:** HASL with lead.
**Solder mask:** standard green.
**Min trace / spacing:** 6 mil / 6 mil.
**Min drill:** 0.3 mm.

## Stack

| # | Layer | Material | Copper | Thickness | Role |
|---:|---|---|---|---|---|
| 1 | L1 (top)    | Cu       | 1 oz   | 35 µm  | Signal + power-stage routing — MOSFET D/S islands, TLP250 input |
| – | Prepreg     | 2× 7628 | – | 0.36 mm | – |
| 2 | L2 (inner1) | Cu       | 0.5 oz | 17 µm  | Ground pour |
| – | Core        | 7628    | – | 0.71 mm | – |
| 3 | L3 (inner2) | Cu       | 0.5 oz | 17 µm  | Power pour (DC bus + 15 V driver rail) |
| – | Prepreg     | 2× 7628 | – | 0.36 mm | – |
| 4 | L4 (bottom) | Cu       | 1 oz   | 35 µm  | Signal return + isolated SPI routing |

Total board thickness: 1.6 mm ±10 %.

## Design rationale

- **Outer layers at 1 oz** because the power-stage current paths sit on L1 and the isolated SPI returns sit on L4 — both want decent copper for thermal headroom under continuous load.
- **Inner layers at 0.5 oz** because they serve as continuous reference planes (ground on L2, power on L3); they don't carry localized high current.
- **Stitched ground vias** along the boundary between primary and isolated regions to keep return paths short and the 5V_GND ↔ 50V_GND boundary clean (see [grounding-fix design note](../../docs/design-notes/grounding-fix.md) for the history of the issue).
- **4 layers instead of 2** to physically separate the floating bridge ground (on the upper-bridge isolated island) from the controller's primary ground — a 2-layer board kept routing the two grounds too close together, which is exactly the issue that bit iteration 3.

## JLCPCB order checklist

When reordering, use these JLCPCB options exactly:

| Field | Value |
|---|---|
| Quantity | 5 |
| Layers | 4 |
| Board thickness | 1.6 mm |
| Inner copper | 0.5 oz |
| Outer copper | 1 oz |
| Surface finish | HASL with lead |
| Solder mask | Green |
| Silkscreen | White |
| Material | FR-4 TG155 |
| Min hole | 0.3 mm |
| Min trace/spacing | 6/6 mil |
| Confirm production file | Yes |

(Match these in JLCPCB's gerber-upload review screen against the values in the gerber pack's `*.gko` / drill files.)
