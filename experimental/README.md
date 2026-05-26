# Experimental

> ⚠️ **The tracks in this directory are not validated in hardware.** No silicon was taped out; no FPGA bring-up exists. These are exploratory designs preserved for continuity.
>
> Do not treat anything here as a working subsystem of the inverter. The validated firmware and hardware live in [`../firmware/`](../firmware/) and [`../hardware/`](../hardware/).

## Contents

| Path | Maturity | Notes |
|---|---|---|
| [`risc-v-soc/`](risc-v-soc/) | RTL + GDSII; no silicon | Custom RV32IM core with a PWM accelerator, taken through a SkyWater 130 nm flow in Cadence Innovus. |
| [`fpga-controller/`](fpga-controller/) | Concept only | Placeholder for a future FPGA-based controller (Zynq or Cyclone). |

## What would be needed to bring these to life

- **RISC-V SoC**: pick a vendor flow that can tape out at 130 nm (SkyWater shuttle, IHP), do design-for-test, then bring up on the first silicon. As an interim step, the RTL can be ported to an FPGA for in-system functional validation.
- **FPGA controller**: choose a target board, port the modulator from the C firmware to HDL or HLS, and re-do the bring-up on the inverter hardware with the FPGA in place of the STM32.

Neither track is in scope for the graduation report. They are documented here so the work isn't lost.
