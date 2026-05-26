# Agent Artifact Tracker

Last updated: 2026-05-26

## Status legend
- ⏳ Waiting on user
- ✅ Received and ingested
- 🟡 Received, needs clarification
- ⏭️ User chose to skip

## Required (blocking — repo can't be considered complete without these)

| # | Artifact | Status | Notes |
|---|---|---|---|
| 1 | Firmware repo (pwm-rewrite-configurable branch) clone path or zip | ⏳ | Need: local clone path or git URL + branch confirmation |
| 2 | Old experimental repo path (feaksel/5level-inverter) | ⏳ | Archive reference only; for salvageable parts |
| 3 | KiCad project for single-bridge v4 (folder or zip) | ⏳ | Phase 3 |
| 4 | Build Guide v4.0 markdown | ✅ | Present in working dir as `build-guide-v4.md` (59923 bytes) |
| 5 | Gerber ZIP sent to JLCPCB | ⏳ | Phase 3 |
| 6 | Final BOM CSV with Turkish supplier links | ⏳ | Phase 3 — may build from KiCad netlist + build guide §3 |
| 7 | Populated board photos (top + bottom, both modules) | ⏳ | Phase 3 — min 4 photos |
| 8 | Oscilloscope captures (gate, dead-time, 5-level output, thermal) | ⏳ | Phase 3 |
| 9 | Simulink model file (.slx) | ⏳ | Phase 4 |
| 10 | ELE 401 term report (paste or file) | ⏳ | Phase 5 — user will paste from prior chat |
| 11 | ELE 402 interim report v4 (24-page PDF or markdown) | ⏳ | Phase 5 |
| 12 | Project decisions (PHASE 0 questions) | ✅ | All defaults accepted 2026-05-26 |

## Optional (repo improves with these, but ships without)

| # | Artifact | Status | Notes |
|---|---|---|---|
| 13 | RISC-V SoC RTL + GDSII | ⏳ | Goes in experimental/ — confirmed include-in-repo / omit-from-report |
| 14 | Team photo / supervisor info for About page | ⏳ | Phase 7 |
| 15 | Hacettepe University logo asset (with usage rights) | ⏳ | Phase 7 |
| 16 | Demo video links (YouTube/Drive) | ⏳ | For landing page |
| 17 | Replay/log files from bench sessions | ⏳ | Documentation supplement |
| 18 | Datasheets for key parts (already linked, PDFs nice to have) | ⏳ | |

## Decisions log

(Filled in as decisions are made with the user. Format: date — question — answer.)

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
