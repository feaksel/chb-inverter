# single-bridge-v4

The PCB module that was fabricated, populated, and demonstrated. Two identical instances are cascaded to form the 5-level inverter.

## Specifications

| | |
|---|---|
| Layers | 4 (1 oz top/bottom, 0.5 oz inner) |
| Fabricator | JLCPCB |
| Power MOSFETs | IRFB4110 (×4 per module, full H-bridge) |
| Gate drive | IR2110 high/low-side with bootstrap |
| Sensing | MCP3201 12-bit ADC, isolated via 6N137 optocoupler (bit-banged SPI) |
| Current sense | ACS712 (×1 per module, on the bridge return) |
| Bridge supply | Independent isolated DC source per module |
| Logic supply | Common 5 V from the STM32 carrier |

Full reference: [Build Guide v4.0](../../docs/hardware/build-guide-v4.md).

## Subdirectories

| Path | Contents |
|---|---|
| [`kicad/`](kicad/) | KiCad project: schematic, board, libraries, footprints, 3D models. |
| [`gerbers/`](gerbers/) | JLCPCB-ready gerber ZIP and extracted per-layer artwork. |
| [`renders/`](renders/) | 3D PNG renders (top, bottom, isometric). Regenerable from `kicad/` via `tools/render-pcb.py`. |
| [`photos/`](photos/) | Populated-board photos and oscilloscope captures from bring-up. Tracked via Git LFS. |

## Files (to be added in Phase 3)

- `bom.csv` — fully populated BOM with Turkish supplier links.
- `pick-and-place.csv` — produced by KiCad.
- `stackup.md` — 4-layer stack details and the design rationale.
