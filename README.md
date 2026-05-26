# 5-Level Cascaded H-Bridge Inverter

Modular cascaded H-bridge inverter using phase-shifted carrier PWM on STM32 Nucleo-F303RE, with a PySide6 operator dashboard, designed and built for the ELE 401/402 graduation project at Hacettepe University.

**Status:** Hardware fabricated and bench-validated. Firmware deployed. Demonstration successful.

| | |
|---|---|
| Docs site | https://feaksel.github.io/chb-inverter/ |
| Firmware | [`firmware/stm32-f303re/`](firmware/stm32-f303re/) |
| Hardware | [`hardware/single-bridge-v4/`](hardware/single-bridge-v4/) |
| Build guide | [Build Guide v4.0](docs/hardware/build-guide-v4.md) |
| Bring-up notes | [First bench session](docs/bringup/first-session.md) |
| Final report | [Graduation report](docs/final-report/index.md) |

## What was built

Two identical single-bridge PCB modules (4-layer, JLCPCB-fabricated, IRFB4110 MOSFETs) cascaded to produce 5 distinct output levels at the inverter terminals. STM32 F303RE generates phase-shifted carrier PWM at 5 kHz with bit-banged MCP3201 sensing isolated via 6N137 optocouplers. A PySide6 desktop dashboard provides full operator control over UART.

The PSC modulation was validated on the oscilloscope at 5 distinct cascade levels, bridges thermally balanced under sustained load.

## Team

| Role | Person |
|---|---|
| Lead, firmware, dashboard | Furkan Emir Aksel |
| Hardware, bring-up | Ahmet Koçak |
| Simulation, analysis | Faruk Gökhan Abay |
| Hardware, assembly | Mücahit Aydın |
| Supervisor | Assoc. Prof. Dr. Rasım Doğan |

Hacettepe University, Department of Electrical & Electronics Engineering — Ankara, 2026.

## Repository layout

```
chb-inverter/
├── docs/              # MkDocs Material source — every .md becomes a published page
├── hardware/          # KiCad, gerbers, BOM, photos
├── firmware/          # STM32 source (subtree of the firmware repo, history preserved)
├── simulation/        # Simulink models and analysis
├── experimental/      # Unverified tracks (RISC-V SoC, FPGA emulation)
├── tools/             # BOM validator, link checker, PCB renderer
└── tests/             # Repo-level CI tests
```

## License

Apache-2.0. See [LICENSE](LICENSE).

## Citation

See [CITATION.cff](CITATION.cff) for the citable metadata.

## Experimental / future work

The [`experimental/`](experimental/) directory contains tracks that were explored but **not validated in silicon or on an FPGA**. They are kept in the repo for continuity but should not be relied on. See the [roadmap](docs/roadmap/) for what could be picked up next.
