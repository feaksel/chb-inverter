---
title: Product path
---

# Product path

What would turning this from a graduation deliverable into a **product** actually take?

The reality is: **the gap is not the inverter** — the as-built hardware/firmware is small and well-characterised. The gap is everything that surrounds a product.

## Engineering work

In rough order of cost (cheapest first):

| Track | Effort estimate (engineer-months) | Notes |
|---|---|---|
| [LC output filter](lc-filter.md) | 1 | Hardware + characterisation. Required before any non-trivial load. |
| [Closed-loop control](closed-loop-control.md) | 2 | Software + tuning. Requires AC voltage sense (hardware respin) or feedback reconstruction (software-only). |
| [Thermal enclosure](thermal-enclosure.md) | 2 | Mechanical + EMI rework. Required for any enclosed deployment. |
| Dashboard productisation | 1–2 | Auth, multi-unit support, telemetry persistence, alerting. Currently single-instance dev tool. |
| Field test rig | 1 | A safe way to run the inverter on real load before deployment. Includes ground-fault detection on the load side. |
| Manufacturing-test fixture | 1 | A bed-of-nails or pogo-pin jig + a structured test plan for each fab batch. |
| [Grid tie](grid-tie.md) | 4–6 | PLL, anti-islanding, compliance testing. The hardest single track and the longest calendar wait (for utility witness). |

## Compliance work

| Standard | Required for | Where |
|---|---|---|
| IEEE 519-2022 | Any deployment with non-trivial harmonic interaction (grid tie, shared bus) | Accredited test lab, ≈ 1 month wait |
| IEEE 1547-2018 | Grid-coupled deployment | Accredited test lab + utility witness |
| IEC 62109-1 / -2 | PV inverter safety | Accredited test lab |
| CE / UKCA / TSE marking | Regional regulatory marks for retail product | Notified body in Türkiye |
| Operational manual | Real one, with safety notices and a service procedure | Tech-writing engagement |

Compliance testing typically costs ≈ 50,000 TL per standard at a Turkish accredited lab (numbers vary; check current EPDK-approved labs). Total compliance budget: **200–400 k TL** for a grid-tied PV inverter.

## Minimum-viable product paths

Three plausible MVP scopes, smallest first:

### MVP-1 — bench instrument for teaching (smallest)

**No new engineering, no compliance work.** Package the as-built into a kit form for university labs:

- Two pre-populated single-bridge PCBs.
- Pre-flashed STM32 Nucleo-F303RE.
- Pre-installed dashboard on a Raspberry Pi.
- Step-by-step exercise sheets (bring-up → STAIR → STAIR_ALT → PSC).
- Safety enclosure for the supplies + load (the bridges themselves can stay open for visibility).

Price point: ≈ 3000 TL per kit. Market: Hacettepe + other Turkish university EEE departments running power-electronics courses.

### MVP-2 — off-grid PV+battery hub (mid-scale)

**LC filter + thermal enclosure + closed-loop control** (so ≈ 5 engineer-months), no grid-tie work. Sell as a residential / small-commercial PV-storage unit:

- Built-in MPPT (which is a separate addition the project hasn't started).
- Battery management.
- Off-grid output to local load (no utility involvement → no IEEE 1547 → no anti-islanding → much shorter compliance loop).
- IEC 62109-1/-2 still required for safety.

Engineering effort: ≈ 6–8 engineer-months total. Compliance budget: ≈ 100 k TL.

### MVP-3 — grid-tied PV inverter (full product)

**Everything in the roadmap**, plus the compliance work, plus the utility relationship.

Engineering effort: ≈ 18–24 engineer-months. Compliance budget: ≈ 400 k TL. Calendar: ≈ 18 months from start to first utility-approved unit.

## Realistic recommendation

If the team or a follow-on group wants to keep this alive as a product candidate:

1. Pick **one** application — single-phase off-grid PV (MVP-2) is the most natural fit for the topology and the team's existing knowledge.
2. Build the **LC filter** first (cheapest single track, unblocks everything).
3. Build the **closed-loop control** in parallel with the application-specific work.
4. **Defer grid tie + compliance** to a phase 2 where there's funding and a lab partner.

For a research / educational use, **MVP-1 is essentially free** — the project is already useful as a teaching tool for CHB modulation, gate-drive isolation, and bring-up workflow. The documentation here supports that use case directly.

## What kills product attempts at this stage

Three failure modes, in order of likelihood:

1. **Underestimating compliance.** The compliance budget often exceeds the engineering budget; founders running out of money at the certification step is the most common failure.
2. **Trying to skip the LC filter.** "We'll do it in v2" is how a product never reaches v2.
3. **Over-scoping the first release.** MVP-1 is shippable in months. MVP-3 is shippable in years. Picking the wrong starting point usually means picking the harder one.

## Where this leaves the graduation work

This project is the **inverter component** of any of those three MVPs. The architectural decisions (CHB topology, TLP250 + B0515S isolation, PSC modulation, modular per-bridge boards) all hold up — they were each justified through the design notes and survived the bench-validation. The graduation work is the foundation. The product path is what someone builds on top of it.
