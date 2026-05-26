# Tests

Repo-level CI tests. Orthogonal to the dashboard's own unit tests (which live at `firmware/stm32-f303re/dashboard/tests/` after the Phase 2 subtree import).

| Test | Purpose |
|---|---|
| `test_bom_format.py` | Confirms the BOM CSV has the required columns, no blank cells in required fields, and every supplier URL resolves to one of the four approved domains. |
| `test_docs_buildable.py` | Runs `mkdocs build --strict` in a tempdir and fails on any warning. |

Run locally: `py -3.12 -m unittest discover tests`.
