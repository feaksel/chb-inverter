# Tools

Repository maintenance scripts. Run from the repo root with `py -3.12 tools/<script>.py`.

| Script | Purpose | Phase added |
|---|---|---|
| `bom-validator.py` | Cross-checks `hardware/single-bridge-v4/bom.csv` against the KiCad netlist; flags missing supplier links and column-format errors. | Phase 3 |
| `render-pcb.py` | Wraps `kicad-cli pcb render` to produce top/bottom/isometric PNGs for the docs site. | Phase 3 |
| `docs-link-check.py` | Crawls the built MkDocs site and reports broken internal links. | Phase 1 |

These scripts have no external runtime dependencies beyond what `pyproject.toml` already pins for the docs build.
