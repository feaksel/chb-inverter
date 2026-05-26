# Overview

## What this project is

A **5-level cascaded H-bridge (CHB) multilevel inverter**. Two identical single-bridge PCB modules are cascaded so their outputs sum to five distinct voltage levels at the inverter terminals, driven by phase-shifted carrier PWM (PSC-PWM) at 5&nbsp;kHz. The controller is an STM32 Nucleo-F303RE. An operator dashboard built in PySide6 handles UART command, telemetry, and replay.

The work was done as the ELE 401/402 graduation project at Hacettepe University EEE, Spring 2026, by a team of four.

## What was actually delivered

| Subsystem | Status |
|---|---|
| Two single-bridge PCB modules | Fabricated at JLCPCB (4 layers); populated by the team |
| Power stage | IRFB4110 MOSFETs in full H-bridge configuration per module |
| Gate drive | IR2110, bootstrap-supplied, dead time enforced in firmware |
| Sensing | MCP3201 12-bit ADC, isolated via 6N137 — bit-banged SPI |
| Controller | STM32 Nucleo-F303RE, Cortex-M4 at 72 MHz |
| Modulator | PSC-PWM at 5 kHz; PSC-PWM ALT and IPD LS-PWM also implemented |
| Protection | Per-bridge over-current trip from the ACS712 current sense |
| Operator UI | PySide6 desktop dashboard, full command + telemetry over UART |
| Bench validation | Five distinct cascade levels visible on the scope; bridges thermally balanced |

## What's documented here

This site is the **engineering reference** for the project. It is structured to be useful to:

- **Reviewers** who want to understand what was built and how.
- **Future students** who want to extend the work (the [roadmap](../roadmap/index.md) is for you).
- **The team itself**, six months from now, when memory has faded.

The [Build Guide v4.0](../hardware/build-guide-v4.md) is the canonical engineering reference and supersedes the older v3.1 PDF in full. Where this site repeats material from the guide, the guide wins.

## What's *not* in here

- **Marketing material.** This is an engineering record, not a pitch deck.
- **Production-grade certification.** The unit was bench-validated; it is not CE-marked, IEC-tested, or grid-qualified.
- **The RISC-V SoC track.** That work is preserved in [`experimental/risc-v-soc/`](https://github.com/feaksel/chb-inverter/tree/main/experimental/risc-v-soc) in the repository but is not part of the graduation deliverable. It has no silicon and no FPGA verification.
