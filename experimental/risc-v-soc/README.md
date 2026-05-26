# Experimental — RISC-V SoC

> ⚠️ **Not validated in silicon.** This directory holds RTL and a GDSII produced through a Cadence Innovus flow against the SkyWater 130 nm PDK. No chip was taped out; no FPGA equivalence check was performed.

## What's here

| Path | Contents | Status |
|---|---|---|
| [`rtl/`](rtl/) | Verilog sources for an RV32IM core with a PWM-generation accelerator block. | Compiles; not formally verified |
| [`synthesis/`](synthesis/) | Cadence Innovus reports — timing, area, power summaries. | Generated against SkyWater 130 nm |
| [`gds/`](gds/) | The final GDSII layout (`rv32im_soc_with_integrated_core.gds`). | Tracked via Git LFS |
| [`docs/`](docs/) | SoC block diagram, ISA extensions, integration notes for the PWM accelerator. | Stub |

## Why this exists

The team explored a custom-silicon controller as an alternative to the off-the-shelf STM32 path. The motivation was twofold: reduce the firmware-side modulation latency by accelerating PWM generation in hardware, and learn a full RTL-to-GDSII flow as a teaching exercise. **The graduation deliverables use the STM32 path** — the RISC-V work did not advance beyond layout.

## What would be needed to bring this up

- Pick a low-cost tape-out option (SkyWater shuttle, IHP) and re-run DRC/LVS with the chosen rule deck.
- Add a JTAG bring-up plan; the current design has no debug interface.
- Functional verification in simulation, then FPGA emulation, before any silicon commitment.
- Glue logic and a level-shifter board to connect the SoC's PWM outputs into the existing gate-drive ICs.

This work is **not referenced from the graduation report**.
