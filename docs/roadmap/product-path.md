# Product path

!!! info "Phase 5 stub"
    What would turning this from a graduation deliverable into a product actually take?

The reality is: **the gap is not the inverter** — the as-built hardware/firmware is small and well-characterised. The gap is everything that surrounds a product:

## Engineering work

| Track | Effort estimate (engineer-months) | Notes |
|---|---|---|
| [LC output filter](lc-filter.md) | 1 | Hardware + characterisation. Required before any non-trivial load. |
| [Closed-loop control](closed-loop-control.md) | 2 | Software + tuning. Requires AC voltage sense. |
| [Grid tie](grid-tie.md) | 4–6 | PLL, anti-islanding, compliance testing. The hardest single track. |
| [Thermal enclosure](thermal-enclosure.md) | 2 | Mechanical + EMI rework. |
| Productisation of dashboard | 1–2 | Auth, multi-unit support, telemetry persistence. |
| Field test rig | 1 | A safe way to run the inverter on real load before deployment. |

## Compliance work

| Standard | Why |
|---|---|
| IEEE 519-2022 | Harmonic distortion — already targeted in the design, needs measurement at the deployment power level. |
| IEEE 1547-2018 | DER interconnection — required for any grid-coupled deployment. |
| IEC 62109-1 / -2 | Safety of power converters for renewable-energy systems. |
| CE / UKCA / TSE marking | Regional regulatory marks. |
| Operational manual | Real one, with safety notices and a service procedure. |

## Realistic next step

If the team or a follow-on group wants to keep this alive as a product candidate:

1. Pick **one** application — single-phase residential PV inverter is the most natural fit for the topology.
2. Build the **LC filter + closed-loop control** in parallel with the application-specific work.
3. Defer **grid tie** and **compliance** to a phase 2 where there's funding and a real lab partner.

For a research / educational use, the as-built system is already useful — it makes a great teaching tool for CHB modulation, gate-drive isolation, and bring-up workflow. Documentation here supports that use case directly.
