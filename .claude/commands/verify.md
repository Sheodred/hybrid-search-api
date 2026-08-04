---
description: Full local verification sequence (venv, tests, lint) for hybrid-search-api
---

Run the standard verification sequence for this project and report results:

1. Confirm the venv is active (check that the Python executable resolves to
   `.venv\Scripts\python.exe`); if not, activate it first
   (`.\.venv\Scripts\Activate.ps1`).
2. Run `pytest -v` and report the pass/fail count.
3. Run `ruff check .` and report any errors.
4. If both pass, say so clearly. If either fails, show the relevant error
   output and propose a concrete fix - don't just report the failure and stop.
