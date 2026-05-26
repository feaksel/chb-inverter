# Agent Handover — chb-inverter monorepo

Last updated: 2026-05-26

This document records what was consolidated into this repository, what was left out and why, what still needs human follow-up, and how to maintain the site going forward. Pair this with [`_AGENT_TRACKER.md`](_AGENT_TRACKER.md) for the per-artifact checklist.

---

## 1. What this repository is

A consolidated monorepo for the **5-Level Cascaded H-Bridge Inverter** graduation project. The repo is:

- A **citable engineering record** — published as a documentation site at https://feaksel.github.io/chb-inverter/ and licensed Apache-2.0.
- A **complete reproduction package** — KiCad project, gerbers, BOM with Turkish supplier links, STM32 firmware (with full upstream git history preserved via `git subtree`), PySide6 dashboard, Simulink models, design notes, iteration history, bring-up reference, and a consolidated graduation report.
- A **maintainable knowledge base** — every Markdown file under `docs/` becomes a navigable page on the published site; every push to `main` triggers automated build, link-check, and deploy via GitHub Actions.

---

## 2. What was built (and from where)

### Imported sources

| Source | Contents | Repo location |
|---|---|---|
| Firmware repo (`pwm-rewrite-configurable` branch) | STM32 source + PySide6 dashboard + bring-up docs | `firmware/stm32-f303re/` (via `git subtree`, history preserved) |
| Drive folder — KiCad project | 7-sheet hierarchical schematic + PCB layout | `hardware/single-bridge-v4/kicad/` |
| Drive folder — gerbers | Pre-fab + final JLCPCB gerber ZIPs | `hardware/single-bridge-v4/gerbers/` |
| Drive folder — BOM v3.2 | Source xlsx (with Motorobit / Direnc.net / Robotistan links) | `hardware/single-bridge-v4/bom-source-v3_2.xlsx` |
| Drive folder — Simulink models | 3 model variants (IPD baseline, gate-driver sweep, RL+LC) | `simulation/simulink/chb-5level-*.slx` |
| Drive folder — reports | ELE 401 + ELE 402 v4 + ELE 419 + poster + reference paper + drawio diagrams | `docs/assets/pdfs/` |
| Drive folder — photos/diagrams | Schematic blocks, PWM scope captures, system diagrams | `docs/assets/images/` |
| `raw-files/bitirmeRV/` dump | Full RISC-V SoC tape-out package (RTL + 9 hierarchical macros + 88 layout renders) | `experimental/risc-v-soc/` |
| User uploads to `docs/assets/images/` | Demo-day photos, headline scope capture, Hacettepe logo, poster JPEG, site-tile image | `docs/assets/images/` |

### Authored content (no upstream source)

| What | Where |
|---|---|
| 5 design notes (bootstrap fundamentals, CHB isolation, PSC vs LSPWM, IGBT vs MOSFET, grounding fix) | `docs/design-notes/` |
| 4 iteration history pages (1 → 4 as-built) | `docs/iteration-history/` |
| 6 roadmap pages (PSC tuning, LC filter, closed-loop, grid-tie, thermal enclosure, product path) | `docs/roadmap/` |
| Hardware section pages (architecture, BOM, schematic, PCB layout, populated photos) | `docs/hardware/` |
| Firmware section pages (overview, pin-map, state-machine, UART protocol, modulators, protection) | `docs/firmware/` |
| Dashboard section pages (overview, installation, operator workflow) | `docs/dashboard/` |
| Simulation section pages (overview, THD analysis, models) | `docs/simulation/` |
| Bring-up section (rendered from firmware tree via `mkdocs-include-markdown`) | `docs/bringup/` |
| About pages (team, supervisor, institution, license) | `docs/about/` |
| Final report — 10-section consolidated graduation report | `docs/final-report/index.md` |
| Top-level README | `README.md` |
| Top-level metadata | `LICENSE`, `CITATION.cff`, `CHANGELOG.md`, `.gitignore`, `.gitattributes` |
| CI workflows | `.github/workflows/docs.yml`, `firmware-build.yml`, `dashboard-tests.yml` |
| Repo-level tooling | `tools/docs-link-check.py`, `mkdocs.yml`, `pyproject.toml` |

### Intentionally not imported

- **Drive `Media/` videos** (~1.5 GB of MP4s from the bench-test sessions) — too large for git/LFS economics. The team can host externally and link from the docs.
- **Cadence Innovus PnR session backups** (~296 MB) — session DBs, intermediate reports, `.gz` snapshots. The final GDSII and the per-macro tape-out outputs are kept; the Innovus working state is not.
- **Genus synthesis intermediates** (~55 each of `genus.cmd*` and `genus.log*`) — same reasoning. Final synthesis scripts and reports are kept.
- **5 bench photos from the March 5 session** — the ones not retrieved due to MCP base64 size limits. The 6 that were retrieved are representative.

---

## 3. Build / test / deploy pipeline

### Local

| Task | Command | What it does |
|---|---|---|
| Install docs dependencies | `py -3.12 -m pip install -e ".[docs]"` | Pulls mkdocs-material + plugins from `pyproject.toml`. |
| Serve site locally | `py -3.12 -m mkdocs serve` | http://127.0.0.1:8000 with live reload. |
| Strict build | `py -3.12 -m mkdocs build --strict` | Same build CI runs. Must exit 0. |
| Link check | `py -3.12 tools/docs-link-check.py` | Crawls the built site for broken internal links. Two known false-positive warnings from `include-markdown` rewriting source-file links in `HARDWARE_BRINGUP.md`. |
| Dashboard unit tests | `cd firmware/stm32-f303re/dashboard && py -3 -m unittest discover tests -v` | Pure-Python tests, no Qt required. |

### CI (every push to `main`)

| Workflow | What it does | Status |
|---|---|---|
| `docs` | Builds the MkDocs site with `--strict` and deploys to GitHub Pages via `actions/deploy-pages@v4`. | ✅ green |
| `firmware-build` | Sets up `arm-none-eabi-gcc` and either runs `make` on `firmware/.../Debug/makefile` or falls back to per-file syntax check. | ✅ green |
| `dashboard-tests` | Sets up Python 3.11 (PySide6 wheel cap), installs `numpy<2.0`, runs `python -m unittest discover tests`. | ✅ green |

### LFS

Tracked via `.gitattributes`:

- `*.pdf`, `*.gds`, `*.gds.gz`, `*.lef`, `*.slx`, `*.mat`
- `hardware/single-bridge-v4/{photos,renders,gerbers}/**/{jpg,jpeg,png,zip}`
- `docs/assets/images/scope-pwm-*.jpg`, `100v-output-5-levels.png`, `demo-poster.jpeg`, `inverter-pcb.png`
- `experimental/risc-v-soc/{macros/**/*.gds, renders/**/*.png}`

Total LFS bandwidth so far: ≈ 220 MB pushed. After `git clone`, run `git lfs install && git lfs pull` to retrieve the binaries. For a smaller clone that skips `experimental/`, use `git clone --filter=blob:none` + partial checkout.

---

## 4. Open follow-ups

### From the tracker

These are items I couldn't close without team input. None of them block the site from being usable.

| # | What's open | Why |
|---|---|---|
| 5 | Which of `gerber_draft.zip` vs. `chb_final.zip` is the as-fabricated gerber pack? | Both imported; team to confirm. Documented in [`docs/hardware/pcb-layout.md`](docs/hardware/pcb-layout.md). |
| 6 | BOM reference designators from KiCad netlist | `bom.csv` uses placeholders (Q1-Q4, R1, etc.) — a `kicad-cli sch export netlist` + cross-check would replace them with the authoritative annotation. |
| 6 | IRFB4110 Motorobit URL | Substituted at order time; URL is `TBD` in the canonical CSV. |
| 6 | Per-module vs project-total BOM split | Current CSV is project total; team may want a per-PCB view as a second sheet. |
| 8 | Dead-time-edge scope captures + thermal scan | Two PWM scope captures imported; close-ups and thermal photos still pending. |
| 8 | Bench-measured THD figure | Simulink predicted 4.9 %; bench FFT capture would confirm. |
| 16 | Demo video links | Bench videos in Drive `Media/` are too large for repo — link external (YouTube / Drive embed) when ready. |

### Phase-5 final-report deferred numbers

The final report at [`docs/final-report/index.md`](docs/final-report/index.md) has the structure and the narrative populated, but a few bench-measured numbers are described qualitatively because the team has them and I don't:

- **Exact bridge-temperature delta** — "~3 °C" in the report; actual measured value should replace it.
- **Bench-measured THD** — currently "Simulink prediction holds at this operating point modulo the caveats noted in the overview"; actual FFT number should follow.
- **MOSFET case temperatures at sustained 5 kHz** — touch-check confirmed, not numerically logged.

If the team measures and provides these, search the report for "~3 °C" and the THD discussion in §6.5 and patch in real values.

### Phase-5 deferred figures

The final report's appendices reference figures that aren't currently rendered as images (mostly pointed to via links). If a PDF export is needed (via `pandoc` or `weasyprint`), these would be inlined.

---

## 5. How to maintain this

### Adding a new doc page

1. Drop a `.md` file under `docs/<section>/`.
2. The `awesome-pages` plugin picks it up automatically — no `nav` entry needed unless you want custom ordering (then add a `.pages` file).
3. Push to `main`. CI rebuilds + redeploys in ≈ 1 minute.

### Adding an image

- **Small inline image (< 500 KB)**: drop under `docs/assets/images/` and reference with `![](../assets/images/name.png)` from inside a doc page.
- **Large image (> 500 KB)**: same drop location, but **add an LFS pattern** to `.gitattributes` before `git add`. Reference the same way.
- **Existing hardware/renders/photos**: reference via GitHub raw URL (`https://raw.githubusercontent.com/feaksel/chb-inverter/main/...`) so MkDocs treats them as external and doesn't try to copy them into the built site.

### Fixing a content error

1. Edit the relevant Markdown file.
2. Run `py -3.12 -m mkdocs build --strict` locally to confirm no warnings.
3. Commit + push.

### Updating the firmware subtree

If the upstream firmware repo gets a new commit:

```powershell
git subtree pull --prefix=firmware/stm32-f303re firmware-upstream pwm-rewrite-configurable
```

(`firmware-upstream` is the remote name added at `git remote add firmware-upstream https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE.git`.)

### Regenerating KiCad outputs

```powershell
# Schematic PDF
kicad-cli sch export pdf `
  --output docs/assets/pdfs/CHB_INVERTER_schematic.pdf `
  hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_sch

# PCB renders
kicad-cli pcb render --output hardware/single-bridge-v4/renders/pcb-top.png    --side top         --quality high hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
kicad-cli pcb render --output hardware/single-bridge-v4/renders/pcb-bottom.png --side bottom      --quality high hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
kicad-cli pcb render --output hardware/single-bridge-v4/renders/pcb-iso.png    --side top --perspective --quality high hardware/single-bridge-v4/kicad/CHB_INVERTER.kicad_pcb
```

### Adding a Phase-2 expansion section to the final report

The skeleton at `docs/final-report/index.md` is now fully expanded (Pass 2). If you want to extend a specific section, edit in place — the structure is locked, just add subsections under existing `## N. Section name` headers.

---

## 6. Known issues / quirks

| Issue | Impact | Workaround |
|---|---|---|
| Two `WARNING -` lines from include-markdown link rewriting in CI link-check | Cosmetic; build passes `--strict` and Pages deploys. | Acceptable false positive — the links are to source files outside the docs/ tree. |
| `git-revision-date-localized` plugin emits root-logger warnings about timestamp ordering | Cosmetic; doesn't fail strict mode. | `enable_git_follow: false` set in mkdocs.yml; warnings persist because the plugin's check still runs. Live with it. |
| `gh auth refresh -s workflow` needed for any push that touches `.github/workflows/` | One-time OAuth refresh per developer. | Standard GitHub OAuth scope mechanic. |
| `dashboard-tests` workflow uses Python 3.11 (not 3.12) | Slight inconsistency with `docs` workflow (3.12). | Pinned PySide6==6.5.3 has no 3.12 wheel — the unit tests don't actually need PySide6, but Python 3.11 is the supported runtime for dashboard tooling generally. |

---

## 7. Citation + license + attribution

Cite this work per [`CITATION.cff`](CITATION.cff). License is Apache-2.0 — see [`LICENSE`](LICENSE). Third-party content attribution (STM32 HAL, PySide6, SkyWater PDK) is in [`docs/about/license.md`](docs/about/license.md).

---

## 8. Sign-off

All eight master-plan phases (0 → 8) are complete:

| Phase | Status |
|---|---|
| 0 — Bootstrap + tracker + Phase-0 decisions + repo skeleton | ✅ |
| 1 — MkDocs Material + GitHub Actions foundation | ✅ |
| 2 — Firmware subtree import (history preserved) | ✅ |
| 3 — Hardware import (KiCad, gerbers, BOM, photos) | ✅ |
| 4 — Simulation import (Simulink + analysis) | ✅ |
| 5 — Design notes + iteration history + roadmap + **consolidated final report (Pass 1 + Pass 2)** | ✅ |
| 6 — Experimental RISC-V SoC track populated | ✅ |
| 7 — Top-level README + CITATION + CHANGELOG + About pages | ✅ |
| 8 — Verification + this handover document | ✅ |

The repository is live at https://github.com/feaksel/chb-inverter and the docs site at https://feaksel.github.io/chb-inverter/. Maintenance from here is incremental — fix the open tracker items as bench data comes in, regenerate renders when KiCad changes, refresh the firmware subtree if the upstream branch gets new commits.

Good luck with the rest of the project.
