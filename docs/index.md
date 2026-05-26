---
title: 5-Level CHB Inverter
hide:
  - navigation
---

# 5-Level Cascaded H-Bridge Inverter

Modular cascaded H-bridge multilevel inverter built around two single-bridge PCB modules and an STM32 Nucleo-F303RE running phase-shifted carrier PWM at 5&nbsp;kHz. Built as the ELE 401/402 graduation project at Hacettepe University EEE — Spring 2026.

!!! success "Project status — May 2026"
    Hardware fabricated, populated, and bench-validated. Firmware deployed. Five distinct cascade output levels confirmed on the oscilloscope; bridges thermally balanced under sustained load. Demonstration successful.

<div class="grid cards" markdown>

-   :material-cube-outline:{ .lg .middle } &nbsp;**Hardware**

    ---

    Two identical single-bridge modules, 4-layer JLCPCB-fabricated, IRFB4110 power MOSFETs.

    [:octicons-arrow-right-24: Architecture](hardware/index.md)

-   :material-chip:{ .lg .middle } &nbsp;**Firmware**

    ---

    STM32 F303RE source, PSC-PWM modulator, bit-banged isolated sensing, and the PySide6 dashboard.

    [:octicons-arrow-right-24: Firmware overview](firmware/index.md)

-   :material-bookshelf:{ .lg .middle } &nbsp;**Build guide**

    ---

    Canonical engineering reference (v4.0, May 2026). Supersedes the older v3.1 PDF in full.

    [:octicons-arrow-right-24: Build Guide v4.0](hardware/build-guide-v4.md)

-   :material-clipboard-text-clock-outline:{ .lg .middle } &nbsp;**Bring-up notes**

    ---

    What we saw on the bench, what went wrong, what we changed.

    [:octicons-arrow-right-24: Bring-up](bringup/index.md)

</div>

## What's in this documentation

| Section | Contents |
|---|---|
| [Getting started](getting-started/index.md) | What the project is, who it's for, how to read these docs. |
| [Hardware](hardware/index.md) | KiCad sources, gerbers, BOM, populated photos, and Build Guide v4.0. |
| [Firmware](firmware/index.md) | STM32 source, the PSC-PWM modulator, the state machine, the UART protocol. |
| [Dashboard](dashboard/index.md) | The PySide6 operator interface — install, run, use. |
| [Simulation](simulation/index.md) | The Simulink model and the THD analysis that informed the topology choices. |
| [Bring-up](bringup/index.md) | First-bench-session notes and the hardware bring-up reference. |
| [Design notes](design-notes/index.md) | Standalone design-decision pieces — bootstrap fundamentals, CHB isolation, PSC vs. LSPWM, etc. |
| [Iteration history](iteration-history/index.md) | Per-iteration story: what was attempted, what failed, what was learned. |
| [Roadmap](roadmap/index.md) | Future work — what would be picked up after the graduation deliverable. |
| [Final report](final-report/index.md) | Consolidated graduation report (supersedes ELE 401 + ELE 402 interim). |
| [About](about/index.md) | Team, supervisor, institution, license. |

## Team

Project group **Cereyan Hacıları**, supervised by **Assoc. Prof. Dr. Rasım Doğan**.

| Person | Role |
|---|---|
| Furkan Emir Aksel | Lead, firmware, dashboard |
| Ahmet Koçak | Hardware, bring-up |
| Faruk Gökhan Abay | Simulation, analysis |
| Mücahit Aydın | Hardware, assembly |

Hacettepe University, Department of Electrical and Electronics Engineering — Ankara, 2026.
