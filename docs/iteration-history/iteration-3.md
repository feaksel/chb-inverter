---
title: Iteration 3 — grounding rework, MISO topology change, MOSFET swap
---

# Iteration 3 — grounding rework, MISO topology change, MOSFET swap

> **Status:** superseded. KiCad zip backups for iteration 3 are preserved at [`hardware/legacy/iteration-3/`](https://github.com/feaksel/chb-inverter/tree/main/hardware/legacy/iteration-3) — `untrackedCHB_INVERTER.zip` (the working tree at the iteration-3 freeze) and `2026-04-07_Full_Bridge_Backup.zip` (a mid-iteration snapshot).

## What was attempted

Iteration 3 committed to the **per-bridge isolated supply** plan that came out of iteration 2, and reworked the board to support it:

- **B0515S 5V→15V isolated DC-DC** per bridge (one per side), feeding the TLP250 V<sub>CC</sub> on each gate driver.
- **6N137 optocouplers** added to every SPI line crossing the isolation barrier (SCK, CS, MISO — one optocoupler per signal per island).
- **MCP3201 sensing** rewired: each isolated island has its own MCP3201(s), accessed via the 6N137-isolated SPI.
- **78L05 5 V regulator** on each island to derive the MCP3201 supply from the local 15 V rail.

The intent was to deliver the full isolation architecture that the [CHB isolation design note](../design-notes/chb-isolation.md) describes.

## What failed

Three distinct issues showed up during iteration-3 bring-up. None alone was fatal; together they made the board unreliable enough to drive iteration 4.

### 1. The 5V_GND ↔ 50V_GND coupling problem (the headline issue)

The iteration-3 layout had **inadvertent coupling** between the controller's 5V_GND and the bridges' 50V_GND, defeating the otherwise-correct isolation parts. Specifics — reconstructed from the bench notes and the iteration-3 KiCad backup:

- A continuous inner-plane ground pour extended slightly across the isolation boundary, providing an AC coupling path.
- The TLP250 and 6N137 footprints had marginal creepage on the PCB-level routing — input-side and output-side copper were close enough to couple parasitic AC current at the cascade-peak common-mode swing.

The symptoms were the classical ones for broken isolation: **intermittent false `SENSOR_LOST` events**, garbage `STATUS` values when Bridge 2 was switching at peak, and occasional protection-trip glitches during clean-load runs.

The fix path — physical separation in the 4-layer stack-up — became the iteration-4 layer plan. See [grounding fix](../design-notes/grounding-fix.md) for the full story.

### 2. MISO-topology surprise

The firmware (per [`Core/Src/spi_mcp3201.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/spi_mcp3201.c)) had been written assuming **three independent MISO lines** — one per MCP3201. The iteration-3 board surfaced reality: the upper-bridge island has only **two** MISO data-return lines, with **DC2 and current ADCs sharing one** (the wire on PC3).

The fix landed in the firmware (the `pwm-rewrite-configurable` branch) rather than the board:

- `Core/Src/spi_mcp3201.c` rewritten to perform a **strictly sequential one-channel-per-CS read** instead of asserting multiple CS lines and reading three MISOs in parallel.
- `config.h` updated: `MISO_CUR` moved from PC4 to PC3 (shared with MISO_DC2).
- The build-guide v3.1 section 3.6.2 already described the sequential read sequence — the firmware just needed to match it.

### 3. The MCP3201 / 78L05 pin-mismatch errata

Ahmet's [BUILD GUIDE KICAD MISSMATCH](https://docs.google.com/document/d/1OZg99BuMBouSNAyDJaxDF2wN3VL8Gx59R-8T9DeY7k0) note captures two pin-assignment errors between the build guide and the KiCad symbols used in iteration 3:

| Part | What was wrong |
|---|---|
| **MCP3201** | Build guide had pin 5 = CS, pin 7 = SCK. The actual datasheet has these swapped: **pin 5 = SCK, pin 7 = CS**. The KiCad footprint followed the datasheet; the build guide had it wrong. |
| **78L05** | Build guide had pin 1 = V<sub>O</sub>, pin 3 = V<sub>I</sub>. The actual datasheet has these swapped: **pin 1 = V<sub>O</sub>**, **pin 3 = V<sub>I</sub>**. Same direction of error — schematic followed datasheet, build guide had it wrong. |

These were paper errata only — the iteration-3 board was built to the schematic (the datasheet-correct version), and the v3.1 PDF build guide had the misprint. Build Guide v4 corrects both. The same errata page logs the **PWM_1L** pin error (PA10 in v3.1 → PA12 in firmware and as-built — see [pin map](../firmware/pin-map.md)).

## What was learned

- **Isolation parts don't isolate by themselves.** The board's copper layout must respect the isolation boundary just as strictly as the parts do. A continuous inner-plane that "should be ground" can defeat 2.5 kV-rated optocouplers via parasitic AC coupling.
- **Hardware reality wins over firmware assumptions.** When the board layout couldn't accommodate three independent MISOs, the firmware was rewritten rather than the board. This is the right call — board respins are expensive, firmware revisions are cheap, and the upstream root-cause (the 3-MISO assumption) was the firmware's responsibility anyway.
- **Schematic-as-source-of-truth pays off.** The MCP3201/78L05 pin errors were caught because the schematic followed the datasheet, not the build guide. The build guide is documentation; the schematic is the authoritative source for what gets fabricated.

## What changed for iteration 4

Iteration 4 (the as-built) made these specific changes:

1. **Board topology**: split the single dual-bridge PCB into **two identical single-bridge PCB modules**, cascaded externally.
2. **Stack-up**: moved from 2-layer to **4-layer** with the dedicated, separated ground plane plan (see [grounding fix](../design-notes/grounding-fix.md)).
3. **MOSFETs**: **IRFZ44N → IRFB4110**, resolving the V<sub>DSS</sub> headroom + TVS-mismatch issue from iteration 1.
4. **Modulator**: kept IPD as the default for a while, then **rewrote to PSC** in the `pwm-rewrite-configurable` firmware branch, resolving the bridge-thermal-asymmetry issue from iteration 1.
5. **Dead time**: raised from 2 µs (IRFZ44N) to 3 µs (IRFB4110) to accommodate the higher gate charge.
6. **Build Guide v4** published with the errata from this iteration baked in.

Iteration 4 is the as-built. See [iteration 4](iteration-4.md).
