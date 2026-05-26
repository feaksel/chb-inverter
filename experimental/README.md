# Experimental

> ⚠️ **The tracks in this directory are not validated in hardware.** No silicon was taped out; no FPGA bring-up exists. These are exploratory designs preserved for continuity.
>
> Do not treat anything here as a working subsystem of the inverter. The validated firmware and hardware live in [`../firmware/`](../firmware/) and [`../hardware/`](../hardware/).

## Contents

| Path | Maturity | Notes |
|---|---|---|
| [`risc-v-soc/`](risc-v-soc/) | RTL + GDSII complete; **no silicon** | Custom RV32IM core + integrated peripherals (PWM, ADC, protection, UART, GPIO, memory). Full Cadence Genus → Innovus → GDSII flow against the SkyWater 130 nm PDK. See [`risc-v-soc/README.md`](risc-v-soc/README.md). |
| [`fpga-controller/`](fpga-controller/) | Concept only | Placeholder for a future FPGA-based controller (Zynq or Cyclone). No HDL written. |

## What would be needed to bring these to life

- **RISC-V SoC** — port the RTL to an FPGA first for functional validation, then pick a foundry shuttle (SkyWater open-shuttle, IHP, EuroPractice) for an actual tape-out. Add JTAG, design-for-test, and a level-shifter board to interface the SoC's PWM outputs into the existing TLP250 + 6N137 isolation chain.
- **FPGA controller** — choose a target board, port the modulator from the C firmware to HDL or HLS, and re-do the bring-up on the inverter hardware with the FPGA in place of the STM32.

Neither track is in scope for the graduation report. They are documented here so the work isn't lost, and so a follow-on group can pick up where the team left off.

## Disk economics

The RISC-V SoC track is ≈ 175 MB on disk because of the GDSII files (up to 49 MB for the full SoC layout) and the layout renders. Everything large is tracked through **Git LFS** — see [`../.gitattributes`](../.gitattributes) for the patterns. A fresh clone needs `git lfs install` and `git lfs pull` to retrieve the binaries.

If you only want the inverter and not the experimental tracks, `git clone --filter=blob:none` plus a partial checkout that excludes `experimental/` will save the LFS bandwidth.
