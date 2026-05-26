---
title: Final graduation report
---

# Final graduation report — 5-Level Cascaded H-Bridge Inverter

!!! info "Document status — skeleton (Pass 1)"
    This is the **Pass-1 skeleton** of the consolidated graduation report. Each section header below has a stub paragraph indicating the planned scope and sources. **Pass 2** expands every section using the source material; **Pass 3** does cross-references and terminology polish. The skeleton structure is locked once the user signs off.
    
    Target length: 30–40 pages of Markdown (Pass-2 expansion).
    Status (Pass 1): all 10 sections + appendices stubbed, no expansion yet.

This report **supersedes** the ELE 401 interim report (Fall 2025) and the ELE 402 interim report v4 (Spring 2026). Both source documents are preserved verbatim at [`docs/assets/pdfs/`](https://github.com/feaksel/chb-inverter/tree/main/docs/assets/pdfs).

**Authors:** Cereyan Hacıları — Furkan Emir Aksel, Ahmet Koçak, Faruk Gökhan Abay, Mücahit Aydın.
**Supervisor:** Assoc. Prof. Dr. Rasım Doğan.
**Institution:** Hacettepe University, Department of Electrical and Electronics Engineering — Ankara, Türkiye.
**Date:** May 2026.

---

## 1. Abstract & project summary

> **Pass-2 scope:** One-paragraph abstract (≈ 200 words) summarising the project's goal, the topology + modulation choices, the delivered as-built configuration, and the headline bench result (5 distinct cascade levels, bridges thermally matched at sustained 5 kHz PSC). Followed by a one-page project summary that walks the reader from the problem statement (a teaching-friendly 5-level CHB) through to what was actually built and demonstrated.
> 
> **Sources:** ELE 401 §1–2, ELE 402 v4 §1, [Build Guide v4.0](../hardware/build-guide-v4.md) "Document Status", [iteration-4 narrative](../iteration-history/iteration-4.md).

## 2. System architecture

> **Pass-2 scope:** The full system block diagram with both bridges, the controller, the dashboard, and the protection chain. Explanation of the cascade arithmetic (how two bridges produce 5 distinct levels), the isolation architecture (controller side, two floating bridge islands, four isolation barriers), and the operator workflow (UART command + 20 Hz telemetry). 5–6 pages.
> 
> **Sources:** [hardware/architecture](../hardware/architecture.md), [docs/firmware/overview](../firmware/overview.md), [CHB isolation design note](../design-notes/chb-isolation.md), Build Guide v4 §1–3.

## 3. Hardware design

> **Pass-2 scope:** Power stage (IRFB4110 + TLP250 + B0515S, with the IGBT-vs-MOSFET argument inlined), sensing chain (MCP3201 + 6N137 + ACS712, including the 2-MISO upper-island topology and the SPIINV runtime mask), protection chain (TVS, fuse, snubber), PCB stack-up + layout decisions (4-layer JLCPCB, ground separation, isolation creepage). Roughly 8 pages with figures.
> 
> **Sources:** [Build Guide v4.0](../hardware/build-guide-v4.md) §4–7, [IGBT vs. MOSFET](../design-notes/igbt-vs-mosfet.md), [grounding fix](../design-notes/grounding-fix.md), [PCB layout page](../hardware/pcb-layout.md), [stackup.md](https://github.com/feaksel/chb-inverter/blob/main/hardware/single-bridge-v4/stackup.md).

## 4. Firmware design

> **Pass-2 scope:** Architecture (CMSIS bare-metal + minimal HAL bring-up shim, 64 MHz HSI/PLL), the supervisory FSM with the per-mode protection table, the three modulators (STAIR / PSC / STAIR_ALT) with selection rationale, the bit-banged MCP3201 driver and SPIINV mask, the UART command set and telemetry frame, the protection chain with N-of-M debounce and VNOM-scaled thresholds. Roughly 6 pages.
> 
> **Sources:** Imported firmware repository (`firmware/stm32-f303re/`), [firmware overview](../firmware/overview.md), [state machine](../firmware/state-machine.md), [modulators](../firmware/modulators.md), [protection](../firmware/protection.md), [UART protocol](../firmware/uart-protocol.md), firmware CHANGELOG entry for `pwm-rewrite-configurable`.

## 5. Iteration history

> **Pass-2 scope:** Per-iteration narrative — what was attempted, what failed, what was learned, what changed for the next round. Links into the per-iteration pages for the long-form content; here in the report each iteration gets ≈ 1 page of summary. Particular attention to the **decisions that compounded** across iterations: IRFZ44N → IRFB4110 (V<sub>DSS</sub> + TVS-clamp + dead-time), single dual-bridge PCB → two identical single-bridge modules, 2-layer → 4-layer stack-up, IPD LS-PWM → PSC-PWM. 4 pages.
> 
> **Sources:** [iteration-history index + 4 per-iteration pages](../iteration-history/index.md), firmware CHANGELOG, [grounding fix](../design-notes/grounding-fix.md).

## 6. Bring-up & test results

> **Pass-2 scope:** The bring-up procedure (linking the [first bench session](../bringup/first-session.md) walkthrough), the bench-validated headline numbers (5-level cascade on scope, both bridges thermally matched within ~3 °C under 5 kHz PSC, no false `SENSOR_LOST` events over multi-minute sessions), scope captures (the two PWM oscilloscope photos imported from Drive), and the per-modulator bench comparison (STAIR vs. STAIR_ALT vs. PSC). 5 pages with photos.
> 
> **Sources:** [first bench session](../bringup/first-session.md), [bring-up reference](../bringup/reference.md), [populated photos](../hardware/populated-photos.md), [scope captures (PWM)](../hardware/populated-photos.md#oscilloscope-captures).
> 
> **Pass-2 dependency:** missing thermal-scan + dead-time-edge captures (tracker artifact #8). The bench-validated thermal-balance number will be inserted as soon as the team confirms the measurement value.

## 7. Lessons learned

> **Pass-2 scope:** What we'd do differently if starting over. One section per major theme:
> 
> 1. **Topology imposes hardware requirements that aren't optional.** CHB needs galvanic isolation — picked the right parts early (TLP250) but didn't initially respect layer-routing rules ([grounding fix](../design-notes/grounding-fix.md)).
> 2. **Component substitutions need the firmware + protection chain updated together.** IRFZ44N → IRFB4110 was the right call; the dead-time + TVS-clamp + heatsink chain all moved with it.
> 3. **Defensive instrumentation pays off.** The PSC carrier-shift `lock=OK|BAD` diagnostic was added before the first bench session — it caught a real issue immediately.
> 4. **Build guide is documentation; schematic is source of truth.** The v3.1 build-guide pin-assignment errata didn't propagate into the actual board because the schematic was right.
> 5. **Simulation kills bad design paths cheaply.** The IR2110-incompatibility-with-CHB conclusion came from Simulink before silicon was committed; saved a wasted board iteration.
> 
> Roughly 3 pages.

## 8. Future work / product roadmap

> **Pass-2 scope:** Short summary of each roadmap track with the engineering effort estimate. Section structure mirrors the [roadmap subsection of the docs site](../roadmap/index.md): PSC tuning, LC filter, closed-loop control, grid tie, thermal enclosure, product path. 2–3 pages.
> 
> **Sources:** [roadmap pages](../roadmap/index.md), Build Guide v4 §15.

## 9. References

> **Pass-2 scope:** IEEE-style references. The ELE 401 interim's reference list is the starting point; will be extended with: STM32F303RE reference manual, IRFB4110 datasheet, TLP250 datasheet (already imported as PDF), MCP3201 datasheet, ACS712 datasheet, IEEE 519-2022, IEEE 1547-2018, IEC 61000-4-7, and any additional papers cited in the design-decision narrative.
> 
> **Sources:** [ELE 401 interim §REFERENCES](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/ELE401_Fall2025_IR.pdf), reference paper [Implementation of 5-Level CHB Multilevel Inverter](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/Implementation_5L_CHB_reference_paper.pdf).

## 10. Appendices

> **Pass-2 scope:** Full BOM (table or link to `bom.csv`), full pin map, key code listings (the FSM transition table, the PSC modulator dispatch, the SPIINV mask handling), the IEEE 519-2022 / IEEE 1547-2018 / IEC 61000-4-7 compliance summary from the ELE 401 interim Appendix A, and the SDG alignment from Appendix B. Roughly 6–8 pages.
> 
> **Sources:** [bom.csv](https://github.com/feaksel/chb-inverter/blob/main/hardware/single-bridge-v4/bom.csv), [pin map](../firmware/pin-map.md), firmware source on GitHub, ELE 401 Appendix A + B.

---

## Pass-2 plan

Once the skeleton above is approved, expansion goes section by section. Approximate ordering (largest sections first):

1. §3 Hardware design (8 pages)
2. §10 Appendices (6–8 pages)
3. §4 Firmware design (6 pages)
4. §2 System architecture (5–6 pages)
5. §6 Bring-up & test results (5 pages)
6. §5 Iteration history (4 pages — summaries, with the per-iteration pages doing the heavy lifting)
7. §7 Lessons learned (3 pages)
8. §8 Future work (2–3 pages)
9. §1 Abstract (1 page; usually written last)
10. §9 References (continuous; refined throughout)

**Total target:** 35–45 Markdown pages, exportable to a single PDF via `pandoc` or `weasyprint` once stable.

## Pass-3 plan

- Cross-reference normalisation (every claim in §2–8 cites the source in §9 or a numbered figure).
- Terminology consistency pass (FSM state names, modulator names, fault bit names — all match firmware exactly).
- Figure numbering + captions.
- Final PDF export for submission.

## Open items blocking Pass-2

Items from [`_AGENT_TRACKER.md`](https://github.com/feaksel/chb-inverter/blob/main/_AGENT_TRACKER.md) that — if resolved — improve Pass-2 quality (none block ship; they make specific paragraphs more concrete):

- **#5 — gerber confirmation.** Knowing which of `gerber_draft.zip` / `chb_final.zip` is the as-fabricated set lets §3 reference the exact bytes JLCPCB received.
- **#6 — BOM reference designators.** Lets the Appendix BOM use real Q1/U1/R1 names instead of placeholders.
- **#8 — additional scope captures.** Dead-time-edge zoom + thermal scan would let §6 stand on bench data rather than asserted bench data.
- **Bench-measured numbers** the team has but I don't have yet: exact measured THD on PSC, exact bridge-temperature delta, exact MOSFET case temperatures at sustained 5 kHz.

None of these block Pass-2; they make individual sub-paragraphs sharper.
