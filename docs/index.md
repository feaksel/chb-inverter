---
title: 5-Level CHB Inverter
hide:
  - navigation
---

# 5-Level Cascaded H-Bridge Inverter

Modular cascaded H-bridge multilevel inverter built around two single-bridge PCB modules and an STM32 Nucleo-F303RE running phase-shifted carrier PWM at 5&nbsp;kHz. Built as the ELE 401/402 graduation project at Hacettepe University EEE — Spring 2026.

!!! success "Project status — May 2026"
    Hardware fabricated, populated, and bench-validated. Firmware deployed. Five distinct cascade output levels confirmed on the oscilloscope at 100 V cascade output; bridges thermally balanced under sustained load. Demonstration successful.

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

-   :material-file-document-multiple-outline:{ .lg .middle } &nbsp;**Final report**

    ---

    Consolidated graduation report — supersedes ELE 401 and ELE 402 interim reports.

    [:octicons-arrow-right-24: Final report](final-report/index.md)

-   :material-account-group:{ .lg .middle } &nbsp;**Team & About**

    ---

    Cereyan Hacıları + supervisor + institution + license.

    [:octicons-arrow-right-24: About](about/index.md)

</div>

## What's in this documentation

| Section | Contents |
|---|---|
| [Hardware](hardware/index.md) | KiCad sources, gerbers, BOM, populated photos, and Build Guide v4.0. |
| [Firmware](firmware/index.md) | STM32 source, the PSC-PWM modulator, the state machine, the UART protocol. |
| [Dashboard](dashboard/index.md) | The PySide6 operator interface — install, run, use. |
| [Simulation](simulation/index.md) | The Simulink model and the THD analysis that informed the topology choices. |
| [Bring-up](bringup/index.md) | First-bench-session notes and the hardware bring-up reference. |
| [Design notes](design-notes/index.md) | Standalone design-decision pieces — bootstrap fundamentals, CHB isolation, PSC vs. LSPWM, IGBT vs. MOSFET, grounding fix, plus the [glossary](design-notes/glossary.md). |
| [Iteration history](iteration-history/index.md) | Per-iteration story: what was attempted, what failed, what was learned. |
| [Roadmap](roadmap/index.md) | Future work — what would be picked up after the graduation deliverable. |
| [Final report](final-report/index.md) | Consolidated graduation report (supersedes ELE 401 + ELE 402 interim). |
| [About](about/index.md) | Team, supervisor, institution, license. |

## Team

<figure markdown="span">
  ![Cereyan Hacıları on the demo stand](assets/images/demo-stand-group-photo.jpeg){ loading=lazy width=70% }
  <figcaption>Project group <b>Cereyan Hacıları</b> on the demo stand, under <b>Assoc. Prof. Dr. Rasım Doğan</b>.</figcaption>
</figure>

| Person | Role |
|---|---|
| Furkan Emir Aksel | Lead, firmware, dashboard |
| Ahmet Koçak | Hardware, bring-up |
| Faruk Gökhan Abay | Simulation, analysis |
| Mücahit Aydın | Hardware, assembly |

Hacettepe University, Department of Electrical and Electronics Engineering — Ankara, 2026.

<figure markdown="span">
  ![Populated single-bridge v4 PCB module — IRFB4110 H-bridge with TLP250 optical gate drive and isolated MCP3201 sensing](assets/images/inverter-pcb.png){ loading=lazy }
  <figcaption>One of two identical single-bridge v4 modules — 4-layer JLCPCB, IRFB4110 power MOSFETs in a full H-bridge, TLP250 optical gate drive on a B0515S isolated 15 V rail, bit-banged MCP3201 sensing through 6N137 optocouplers. Cascading two of these externally produces the 5-level output documented in the <a href="final-report/">final report</a>.</figcaption>
</figure>
