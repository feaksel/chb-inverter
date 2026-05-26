# Experimental — FPGA controller

> ⚠️ **Concept only.** Nothing has been written, simulated, or wired.

A placeholder for a future controller that would replace the STM32 with an FPGA — likely Zynq-7000 or Cyclone V — to:

- Move the modulator into hardware for sub-microsecond determinism.
- Add space for closed-loop control with on-fabric ADC interfacing.
- Provide a path to integrating the [RISC-V SoC](../risc-v-soc/) RTL as a soft core for the dashboard/UART side, with the hard FPGA handling the modulation.

When someone takes this on, populate this directory with the HDL sources, the constraints file, and the bring-up plan. Until then it is intentionally empty.
