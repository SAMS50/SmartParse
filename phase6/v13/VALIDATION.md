# Milestone 13 validation — 2026-11-03

Base `d48270d`; branch `feature/milestone-13-real-world-validation`.

* Full repository/backend suite: **554 tests, OK, 28 optional-tool skips**.
* Targeted ingestion/compiler/leakage/statistics suite: **15 tests, OK**.
* Frontend Vitest: **8 files, 69 tests pass**.
* TypeScript/Vite production build: **pass**, existing large Monaco chunk warning.
* Historical/acceptance preservation: **1,995 files checked, zero changed**,
  including v11/v12. The legacy timing CSV is restored to exact pre-run bytes.
* Frozen engine hash: `70619faa7804ad53cec98992c7ebdb80a50fb0e0017eec3623e09ef1da6f5d56`.
* Final sample: 80 genuine pairs; 79 A, 1 B. Development: 20 A. No C/D cases
  substituted into primary accuracy, no outcome-based replacements.
* Full mode: 0/79 recommendations. Existing: 20 exact / 4 exact mismatches / 55
  abstentions. Clang: 36 applicable bundles, 24 compile, 20 exact. GCC 6.3 lacks
  the probed fix-it flag; its conditional repair accuracy is unavailable.
* Source/reference hashes match frozen public manifest. Corrections and raw
  diagnostics are evaluator-only. Test-owned future histories are rejected.
* Public results checked for absence of student source, raw timestamps,
  submission IDs, private diagnostic excerpts, credentials and local user paths.
* Raw archive/code/private compiler captures remain under ignored
  `.studio-artifacts/m13/`; only metadata and observed metrics are committed.

The real-data pipeline was run without modifying v11/v12 recovery code, weights,
budgets or Studio. No untrusted binary was executed, and no dependency was
installed. Compiler calls require normal local process/temp-directory access;
the runner provides bounds and cleanup, not an OS sandbox.

## Reproducibility checkpoints

* `7332790`: protocol before contents/outcomes.
* `d78953e`: tested ingestion, fixed 100-family sample and leakage-safe harness.
* `2f3d270`: final tool/engine/harness lock before final outcomes.
* `c715da3`: actual real-world results and negative generalization analysis.
* Final documentation commit follows; read its hash with `git log -1 --oneline`.

No push or merge is performed. User approval is required before branch upload.
Machine-readable validation record: `results/validation.json`.

```powershell
.\.studio-venv\Scripts\python.exe -m unittest phase6.v13.test_pipeline
.\.studio-venv\Scripts\python.exe -m phase6.v13.validate
Push-Location studio
npm.cmd test
npm.cmd run build
Pop-Location
```
