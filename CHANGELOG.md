# Repository Changelog

This changelog tracks the state of the **consolidated monorepo**. The firmware has its own changelog at [`firmware/stm32-f303re/CHANGELOG.md`](firmware/stm32-f303re/CHANGELOG.md) once imported.

## [Unreleased]

### Added
- Initial repository skeleton: directory tree, license, .gitignore, .gitattributes (Git LFS rules for large binaries), CITATION.cff.
- Build Guide v4.0 placed at `docs/hardware/build-guide-v4.md` (canonical engineering reference; supersedes v3.1).
- Agent tracking files: `_AGENT_TRACKER.md` (artifact checklist) and `_AGENT_HANDOVER.md` (populated in Phase 8).

### Pending (in-flight phases)
- Phase 1 — MkDocs Material site + GitHub Actions pipelines.
- Phase 2 — Firmware import via `git subtree` (history preserved).
- Phase 3 — KiCad project, gerbers, BOM, populated photos, scope captures.
- Phase 4 — Simulink model + THD/FFT analysis.
- Phase 5 — Design notes, iteration history, consolidated final report.
- Phase 6 — Experimental RISC-V SoC track.
- Phase 7 — Polish (front-door README, issue/PR templates, About pages).
- Phase 8 — Verification suite + handover document.
