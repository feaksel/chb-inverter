# PCB layout

The PCB source is [`CHB_INVERTER.kicad_pcb`](https://github.com/feaksel/chb-inverter/blob/main/hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb) — a **4-layer, 1.6 mm FR-4** board with an outer copper weight of 1 oz and an inner copper weight of 0.5 oz, fabricated by **JLCPCB**.

## Renders

### 3D view

![PCB 3D render](https://raw.githubusercontent.com/feaksel/chb-inverter/main/hardware/single-bridge-v4/renders/pcb-3d-render.png)

(Render saved as `hardware/single-bridge-v4/renders/pcb-3d-render.png`.)

### Top-down KiCad view

![PCB top-down](https://raw.githubusercontent.com/feaksel/chb-inverter/main/hardware/single-bridge-v4/renders/pcb-top-down-kicad.jpeg)

(Render saved as `hardware/single-bridge-v4/renders/pcb-top-down-kicad.jpeg`.)

## Stack-up

| Layer | Copper | Role |
|---|---|---|
| L1 (top) | 1 oz | Signal + power-stage routing; MOSFET D/S + TLP250 input |
| L2 | 0.5 oz | Ground pour |
| L3 | 0.5 oz | Power pour (DC bus + 15 V driver rail) |
| L4 (bottom) | 1 oz | Signal return + isolated SPI routing |

Full stack-up rationale: [`hardware/single-bridge-v4/stackup.md`](https://github.com/feaksel/chb-inverter/blob/main/hardware/single-bridge-v4/stackup.md).

## Layer renders

These are produced from the KiCad project via:

```powershell
kicad-cli pcb render --output renders/pcb-top.png --side top --background opaque --quality high hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
kicad-cli pcb render --output renders/pcb-bottom.png --side bottom --background opaque --quality high hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
kicad-cli pcb render --output renders/pcb-iso.png --side top --perspective --background opaque --quality high hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
```

(The first wave of renders is the 3D + top-down captures above. Per-layer renders will be added as the team regenerates them.)

## Gerbers

| File | Use |
|---|---|
| [`gerber_draft.zip`](https://github.com/feaksel/chb-inverter/blob/main/hardware/single-bridge-v4/gerbers/gerber_draft.zip) | Pre-fab review gerber pack. |
| [`chb_final.zip`](https://github.com/feaksel/chb-inverter/blob/main/hardware/single-bridge-v4/gerbers/chb_final.zip) | Final gerber pack sent to JLCPCB. |

The team's standard JLCPCB order options:
- Quantity: 5
- Board thickness: 1.6 mm
- Outer copper: 1 oz
- Inner copper: 0.5 oz
- Surface finish: HASL with lead
- Material: FR-4 TG155
- Min hole: 0.3 mm
- Min track / spacing: 6 / 6 mil

## How to open

```powershell
& "C:\Program Files\KiCad\9.0\bin\pcbnew.exe" hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
```
