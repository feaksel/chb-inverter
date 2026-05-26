# Agent Artifact Tracker

Last updated: 2026-05-26 (post-Drive-import)

## Status legend
- ⏳ Waiting on user
- ✅ Received and ingested
- 🟡 Received, needs clarification
- ⏭️ User chose to skip

## Required (blocking — repo can't be considered complete without these)

| # | Artifact | Status | Notes |
|---|---|---|---|
| 1 | Firmware repo (pwm-rewrite-configurable branch) | ✅ | Imported via `git subtree` 2026-05-26; 11 upstream commits preserved |
| 2 | Old experimental repo (feaksel/5level-inverter) | ⏭️ | Skipped for now — focus is the as-built path |
| 3 | KiCad project for single-bridge v4 | ✅ | `CHB_INVERTER.kicad_*` imported from Drive; project + 7 subsheets at `hardware/single-bridge-v4/kicad/` |
| 4 | Build Guide v4.0 markdown | ✅ | At `docs/hardware/build-guide-v4.md` |
| 5 | Gerber ZIP sent to JLCPCB | 🟡 | Two zips imported: `gerber_draft.zip` (370 KB) + `chb_final.zip` (488 KB). User to confirm which is the as-fabricated set. |
| 6 | Final BOM CSV with Turkish supplier links | 🟡 | Canonical CSV at `hardware/single-bridge-v4/bom.csv` (built from v3.2 source). Open items: IRFB4110 Motorobit URL TBD, reference designators TBD (need KiCad netlist cross-check), per-module vs per-project quantities. |
| 7 | Populated board photos | ✅ | 6 bench-session photos (2026-03-05) + 7 demo-day photos uploaded by user 2026-05-26. See `docs/assets/images/` and `hardware/single-bridge-v4/photos/`. |
| 8 | Oscilloscope captures (gate, dead-time, 5-level out, thermal) | 🟡 | 5 PWM scope captures now (2 from initial drop + 3 more from raw-files dump: `scope-pwm-working.jpg`, `scope-pwm-correct-freq.jpg`, `scope-pwm-full-correct.jpg`). Dead-time-edge zoom + thermal scan still pending. |
| 9 | Simulink model file (.slx) | ✅ | Three models imported: `chb-5level-v1.slx`, `chb-5level-v2.slx`, `chb-5level-rl-nospike.slx` |
| 10 | ELE 401 term report | ✅ | `ELE401_Fall2025_IR_Group1.pdf` imported (1 MB); full text extracted into docs source for Phase 5 final-report drafting |
| 11 | ELE 402 interim report v4 | ✅ | Both PDF (3 MB) and DOCX (3.5 MB) imported at `docs/assets/pdfs/ELE402_Spring2026_IR_v4.*` |
| 12 | Project decisions (PHASE 0 questions) | ✅ | All defaults accepted 2026-05-26 |

## Optional (repo improves with these, but ships without)

| # | Artifact | Status | Notes |
|---|---|---|---|
| 13 | RISC-V SoC RTL + GDSII | ✅ | Full tape-out package imported 2026-05-26 from `raw-files/bitirmeRV/`: 8 hierarchical macros (GDS + LEF + SDC + netlist), full RTL source, 12 architecture docs, synthesis scripts (Cadence + open-source), 88 layout renders. Lives at `experimental/risc-v-soc/`. |
| 14 | Team photo / supervisor info for About page | ✅ | Group demo-stand photo used on README + About index + team page. Supervisor and institution pages written. |
| 15 | Hacettepe University logo (with usage rights) | ✅ | Imported from `raw-files/cropped-logo-hacettepe.png` → `docs/assets/images/hacettepe-logo.png`. Used on README + institution page. |
| 16 | Demo video links | ⏳ | Bench videos exist in Drive `Media/` folder but are 100s of MB; user can upload trimmed/hosted-elsewhere links. |
| 17 | Replay/log files from bench sessions | ⏳ | Not found in Drive; dashboard supports replay via `ReplaySource`. |
| 18 | Datasheets PDFs | 🟡 | TLP250 imported (`docs/assets/pdfs/tlp250-datasheet.pdf`); others (IRFB4110, MCP3201, ACS712, 6N137, B0515S, IR2110, 78L05, 1.5KE62A) still useful as additions. |

## Bonus artifacts imported from Drive (over and above the tracker list)

| Item | Location |
|---|---|
| Older Build Guide v3.1 docx | `docs/assets/pdfs/CHB_Inverter_Build_Guide_v3_1.docx` (for iteration history) |
| Reference paper (IEEE) on 5-Level CHB implementation | `docs/assets/pdfs/Implementation_5L_CHB_reference_paper.pdf` |
| Poster v5 PDF + editable PPTX | `docs/assets/pdfs/CHB_Inverter_Poster_v5.pdf`, `CHB_Inverter_Poster.pptx` |
| HVLV and SystemLevelDiagram drawio PDFs | `docs/assets/pdfs/HVLV-diagram.pdf`, `SystemLevelDiagram.pdf` |
| Schematic block-level images (HS / LS / drivers / sensing / 5V→15V) | `docs/assets/images/schematic-*.{png,jpg}` |
| PWM scope captures (100 Hz / 500 Hz / values / bridges separate / cascade overlap) | `docs/assets/images/pwm-*.png`, `cascade-control-overlap.png` |
| System diagrams (abstract / hybrid / STM32-only) | `docs/assets/images/abstract-system-diagram.png` etc. |
| KiCad footprint catalogue xlsx | `hardware/single-bridge-v4/kicad-footprints.xlsx` |
| Earlier-iteration KiCad zip backups | `hardware/legacy/iteration-3/{untrackedCHB_INVERTER.zip, 2026-04-07_Full_Bridge_Backup.zip}` |
| 5 of the 16 Drive bench videos | _skipped — too large for repo_ |

## Decisions log

| Date | Question | Answer |
|---|---|---|
| 2026-05-26 | License | Apache-2.0 (default) |
| 2026-05-26 | Repo visibility | Public (default) |
| 2026-05-26 | Repo name + GitHub user/org | `feaksel/chb-inverter` (default) |
| 2026-05-26 | Docs domain | GitHub Pages default — `feaksel.github.io/chb-inverter/` |
| 2026-05-26 | MkDocs theme color scheme | Material slate dark + light toggle, primary teal, accent amber |
| 2026-05-26 | Firmware import method | `git subtree` with preserved history |
| 2026-05-26 | GitHub Pages deployment branch | `gh-pages` (auto-managed by docs workflow) |
| 2026-05-26 | Local working directory | Initialize git in place at `Multilevel_Inverter/`; remote = `feaksel/chb-inverter` |
| 2026-05-26 | gh CLI installed via winget; authenticated as feaksel | Repo created at github.com/feaksel/chb-inverter; pushed main |
| 2026-05-26 | Workflow scope added | gh OAuth token now has 'repo, read:org, gist, workflow' |
| 2026-05-26 | Drive folder explored | 1Vop48XvfmdLgib1eSkH6jaqIBVMh9a8y; 58 of 63 binary artifacts pulled (gdown + MCP fallback) |

## Outstanding questions for the user

1. **Gerber ZIP** — `gerber_draft.zip` vs `chb_final.zip`: which is the file actually sent to JLCPCB for the as-built boards?
2. **BOM reference designators** — should I run the KiCad netlist export to populate the `Reference` column, or do you want to do that pass yourself?
3. **MOSFET URL** — what is the exact Motorobit URL for the IRFB4110 you ordered? (`bom.csv` currently has TBD.)
4. **Per-module BOM split** — the v3.2 source lists project totals; do you want me to also produce a per-PCB BOM (need × 0.5 for most lines, with the sensing-asymmetric notes for the two islands)?
5. **Final-demo photos** — would you like to share photos from demo day (the populated v4 boards on the cascade bench)? The Drive only has the March 5 bench session.
6. **Scope captures** — gate switching, dead-time, 5-level output, thermal — these are missing from Drive. Can you share?
7. **RISC-V SoC RTL + GDSII** — when you have a moment, drop these in for the `experimental/risc-v-soc/` track.
