# License

The 5-Level Cascaded H-Bridge Inverter project is released under the **Apache License, Version 2.0** — a permissive open-source license that allows use, modification, and redistribution with attribution and a patent grant.

The full license text is at [LICENSE](https://github.com/feaksel/chb-inverter/blob/main/LICENSE) in the repository root.

## Copyright

```
Copyright 2026 Furkan Emir Aksel, Ahmet Koçak, Faruk Gökhan Abay, Mücahit Aydın

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

## What the license covers

| | License |
|---|---|
| Original schematic + PCB design (KiCad sources) | **Apache-2.0** (this project) |
| Firmware C source + dashboard Python | **Apache-2.0** (this project) |
| Original RISC-V SoC RTL (`experimental/risc-v-soc/rtl/`) | **Apache-2.0** (this project) |
| Documentation (everything in `docs/`) | **Apache-2.0** (this project), text licensed permissively |

## Third-party content and attribution

| Component | Origin | License | Where used |
|---|---|---|---|
| STM32 HAL libraries | STMicroelectronics | BSD-3-Clause | [`firmware/stm32-f303re/Drivers/`](https://github.com/feaksel/chb-inverter/tree/main/firmware/stm32-f303re/Drivers) |
| CMSIS device support | ARM / STMicroelectronics | Apache-2.0 | Bundled in the HAL tree |
| MkDocs + Material theme | Tom Christie / Martin Donath | BSD-2-Clause / MIT | Build-time dependency only; no part redistributed |
| PySide6 | Qt for Python (PySide6) | LGPLv3 / Commercial | Dashboard runtime dependency; not bundled |
| pyqtgraph, pyserial, numpy | Open-source Python ecosystem | MIT / BSD-3 | Dashboard runtime dependencies |
| Build Guide v3.1 PDF / DOCX | Project team (preserved for iteration history) | Apache-2.0 (this project) | [`docs/assets/pdfs/CHB_Inverter_Build_Guide_v3_1.docx`](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/CHB_Inverter_Build_Guide_v3_1.docx) |
| Reference paper PDF | Original authors, third-party | Likely copyrighted; kept under fair-use for reference | [`docs/assets/pdfs/Implementation_5L_CHB_reference_paper.pdf`](https://github.com/feaksel/chb-inverter/blob/main/docs/assets/pdfs/Implementation_5L_CHB_reference_paper.pdf) — review before redistributing |

## PDK notes (experimental track)

The RISC-V SoC in [`experimental/risc-v-soc/`](https://github.com/feaksel/chb-inverter/tree/main/experimental/risc-v-soc) was synthesized against the **SkyWater 130 nm PDK**. The PDK itself is Apache-2.0 (https://github.com/google/skywater-pdk) and is **not** included in this repository — only the project's own GDSII output, which references PDK cells by name. Anyone using the GDSII files to attempt a tape-out will need to install the SkyWater PDK separately.

## Logos and trademarks

| Asset | Owner | Usage in this repository |
|---|---|---|
| Hacettepe University logo | Hacettepe University | Used in About / README pages for institutional attribution under fair-use academic convention. Not redistributed for commercial purposes. |
| STM32, ARM, Cortex-M, Cadence | Their respective owners | Referenced by name only; no logos or trademarked assets bundled. |
| KiCad | KiCad project | Tool used to produce the schematic + PCB; KiCad license (GPL-3.0) does not propagate to KiCad-produced design files. |

## Citation

For academic use, please cite this project per [CITATION.cff](https://github.com/feaksel/chb-inverter/blob/main/CITATION.cff). BibTeX:

```bibtex
@software{aksel_2026_chb_inverter,
  author       = {Aksel, Furkan Emir and Koçak, Ahmet and Abay, Faruk Gökhan and Aydın, Mücahit},
  title        = {{5-Level Cascaded H-Bridge Inverter with STM32 Nucleo-F303RE}},
  year         = 2026,
  month        = 5,
  publisher    = {Hacettepe University, Department of Electrical and Electronics Engineering},
  version      = {1.0.0},
  url          = {https://github.com/feaksel/chb-inverter}
}
```

## Disclaimer

This project drives power stages. The Apache-2.0 license disclaims warranties including fitness for any particular purpose. Use the design at your own risk; review and modify for your own safety requirements before applying mains voltages, connecting to a grid, or operating outside the bench environment for which it was designed and validated.
