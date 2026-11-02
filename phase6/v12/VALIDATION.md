# Milestone 12 validation — 2026-11-03

Base: pushed Milestone 11 `d261ec3`; branch
`feature/milestone-12-repair-optimization`. No merge or push performed.

| Check | Actual outcome |
|---|---|
| Frozen v11 benchmark reproduction | All four ablations reproduced; full 7 correct, 1 wrong, 12 abstentions / 20 |
| Final repository unittest discovery | **539 tests, OK, 28 optional-tool skips** |
| Separate v11 suite | **11 tests, OK** |
| Separate v12 suite | **13 tests, OK** |
| Backend | Included in full suite; additional real v12 worker/reliability/cleanup checks pass |
| Frontend Vitest | **8 files, 69 tests pass** |
| TypeScript/Vite production build | **Pass**, existing large Monaco bundle warning |
| Actual Chrome workflow | **Pass**: real edit capture, intended repair, read-only diff, unchanged source on reanalysis, editor undo |
| Actual Chrome ambiguous history | **Pass**: real EOF-brace deletion, abstention and reliability display, unchanged source, zero page errors |
| Preserved historical/acceptance files | **1,969 checked, zero changed** |
| Fingerprint | Frozen algorithm/dataset unchanged after held-out evaluation |
| Diff/secret/artifact review | `git diff --check` passes; no token/private-key signatures or user-profile paths in curated v12 records |

The regression preservation wrapper restores only `results/verified_performance.csv`
to its exact pre-run bytes after a legacy test regenerates it. Existing untracked
acceptance outputs are hashed and left untouched. Generated JSON/JSONL/TXT under
`acceptance/output/` is now ignored; its tracked Markdown reports remain tracked.

Curated machine-readable record: `results/validation.json`, including exact local
compiler version strings and preservation status, without machine/user paths.
Browser results/screenshots remain local in `.studio-artifacts/m12/browser/`.

## Checkpoints

* `b549b68`: reproduced v11 and complete twenty-case failure audit.
* `5c7d150`: tested bounded generation, history guard and structural consensus.
* `d91f95c`: development refinements and frozen split/margin selection, committed
  **before** held-out evaluation.
* `47abe77`: backend/frontend reliability integration and preservation runner.
* `30c8fcb`: held-out/historical results, uncertainty/selective analysis,
  evaluation-integrity tests and successful actual-browser workflow.
* Final documentation commit follows these checkpoints; obtain its hash with
  `git log -1 --oneline`.

Development: v12 full 19 correct / 0 wrong / 13 abstentions out of 32.
Held-out: v12 full 28 / 0 / 24 out of 52, versus v11 full 16 / 4 / 32.
Historical: v12 full 8 / 0 / 12 out of 20, versus v11 full 7 / 1 / 12.
Both primary systems use margin 12. No algorithm changes or retuning followed
held-out results. These synthetic observations do not establish general safety
or statistical significance; see `EVALUATION_REPORT.md`.

## Commands

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v12.validate
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v11 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v12 -t .
Push-Location studio
npm.cmd test
npm.cmd run build
Pop-Location
python -m phase6.v12.browser_smoke --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

Browser command requires the local API and Vite servers. It uses existing
Playwright in system Python; the Studio venv was used for engine/API tests.
Normal local child-process/temp-directory access was needed for compiler/Vite
tests; no dependency installation or authentication workaround was used.
