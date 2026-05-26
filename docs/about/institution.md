# Institution

<p align="center">
  <img src="../assets/images/hacettepe-logo.png" alt="Hacettepe University" width="200"/>
</p>

## Hacettepe University

Hacettepe University is a public research university in Ankara, Türkiye, founded in 1967. Its **Department of Electrical and Electronics Engineering** (EEE) within the **Faculty of Engineering** is the home department for this graduation project.

| | |
|---|---|
| Department | Electrical and Electronics Engineering |
| Faculty | Engineering |
| University | Hacettepe University |
| Location | Beytepe Campus, Ankara, Türkiye |
| Website | https://ee.hacettepe.edu.tr/ |

## Academic context

The project was completed as the **ELE 401 / 402 graduation project** sequence — the standard two-semester capstone for EEE undergraduates. The deliverables for each semester:

- **ELE 401** (Fall 2025): topology selection, component justification, Simulink modelling, interim report.
- **ELE 402** (Spring 2026): hardware fabrication, firmware development, bench validation, demonstration, final report.

Both interim reports are preserved in this repository at [`docs/assets/pdfs/ELE401_Fall2025_IR.pdf`](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/ELE401_Fall2025_IR.pdf) and [`docs/assets/pdfs/ELE402_Spring2026_IR_v4.pdf`](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/ELE402_Spring2026_IR_v4.pdf). The [final report on the docs site](../final-report/index.md) consolidates and supersedes both.

## Background coursework

The technical foundations for this project were laid in:

| Course | Foundations used |
|---|---|
| ELE 226 — Circuit Theory II | AC analysis, Fourier series, harmonic analysis, filtering |
| ELE 301 — Signals and Systems | FFT, sampling theory, DSP, filter design (LC sizing) |
| ELE 315 — Electronics II | Power semiconductors, switching characteristics, gate drives, thermal management |
| ELE 354 — Control Systems | PID design, stability analysis, digital control implementation |

The graduation project pulls all of these together: power electronics for the topology and thermal sizing, signals for the harmonic analysis, control for the per-bridge modulation timing, and circuits for the sensing and isolation chain.

## Companion course

The **RISC-V SoC track** in [`experimental/risc-v-soc/`](https://github.com/feaksel/chb-inverter/tree/main/experimental/risc-v-soc) was developed in parallel as part of **ELE 419** (Fall 2025), an elective covering custom-silicon design from RTL through GDSII. The ELE 419 report is preserved at [`docs/assets/pdfs/ELE419_Fall2025_Report.pdf`](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/ELE419_Fall2025_Report.pdf) for context. The SoC was not part of the graduation deliverable — see [the experimental README](https://github.com/feaksel/chb-inverter/blob/main/experimental/risc-v-soc/README.md).
