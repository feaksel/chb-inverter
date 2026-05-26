# Supervisor

**Assoc. Prof. Dr. Rasım Doğan** — supervisor for the ELE 401 / 402 graduation project, Hacettepe University EEE.

## Role on the project

The supervisor's role was to (a) ensure the project met the **graduation deliverable spec** — 5 distinct cascade output levels visible without an output filter — and (b) provide oversight on the **safety and engineering practice** appropriate to a project that drives power stages.

Specific checkpoints:

| Checkpoint | What was reviewed |
|---|---|
| Topology selection | CHB vs. NPC vs. Flying Capacitor argument; CHB approved. |
| Component selection | MOSFET vs. IGBT analysis (quantitative), TLP250 gate-driver choice. |
| Power scaling decision | The team's choice to scale the bench prototype to 100 V cascade output and 5 A AC was approved at the 23 October 2025 project meeting — see the [meeting-notes summary](https://github.com/feaksel/chb-inverter/blob/main/docs/iteration-history/index.md). |
| PCB fab order approval | Each iteration's gerber pack required supervisor review before the JLCPCB order. |
| Bench bring-up sessions | Supervisor presence required for any session involving the populated boards under load. |
| Demo readiness | Sign-off on the demo procedure + the safety chain before the public demonstration. |

## Project-meeting takeaways

The 23 October 2025 meeting set the **bench-prototype scaling decision** — the inverter is a low-power proof-of-concept (100 V cascade, 5 A AC, ≈ 700 W), not a production deployment. Specifically:

- Bobinin (inductor) power rating must match the planned load (≥ 5 A continuous).
- MOSFET voltage selection must be justified against the bus voltage with margin.
- Per-MOSFET thermal measurement is required on the bench to confirm safe operation.

These constraints flowed into the iteration-1 component selection and stayed valid through to iteration 4 (the IRFZ44N → IRFB4110 swap was driven by exactly the V<sub>DSS</sub>-margin point the supervisor flagged at this meeting).
