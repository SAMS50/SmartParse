# Milestone 14 validation

Full repository discovery: **568 tests run, OK, 28 skipped**. Skips are retained
and do not count as executed checks. Milestone-specific package-aware discovery
also passed: v11 11, v12 13, v13 15, v14 14. Backend/API tests are included in full
discovery; new v14 API tests cover legacy default compatibility, explicit version
and provider validation, actual real-C fallback, source preservation and cleanup.

Frontend: **71 tests, eight files, passed**. `npm.cmd run build` runs `tsc -b`
and Vite production bundling; both passed. Vite retains the existing Monaco bundle
size warning. No layout redesign or dependency change was needed.

Actual Chrome/Playwright workflows passed after the UTF-8 fix: recent-edit capture,
intended historical repair, read-only comparison, original-source preservation,
Monaco undo, imported header-bearing source, adaptive fallback, visible Clang
origin and evidence availability, and repeated analysis. Zero browser errors.
An initial final rerun could not connect to stopped local servers; after starting
API/Vite it passed. Package-local unittest discovery without `-t .` was also
corrected to package-aware discovery; the commands below are the passing ones.

Historical preservation compared **2,018 files**, with **zero changes**. The
wrapper restores only the known legacy timing CSV side effect to its exact
pre-run bytes. A Git comparison against `59b9eb3` also shows no changes under
v11/v12/v13, results or acceptance/output. It does not hide source/test failures.

Final calibration and new/exposed evaluations were rerun after the UTF-8 offset
correction without policy changes; all 180 cases across eight arms have unchanged
predictions. The first runs remain local; source-free fingerprint and decision
comparison evidence is committed. No claim of pristine testing on the rerun.

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v14.validate
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v11 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v12 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v13 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v14 -t .
Push-Location studio
npm.cmd test -- --run
npm.cmd run build
Pop-Location
# With API and Vite running:
python -m phase6.v14.browser_smoke --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
git diff 59b9eb3 --name-only -- phase6/v11 phase6/v12 phase6/v13 results acceptance/output
git diff --check
```

Tests exercise all five evidence modes; missing versus failed/unsafe checks;
hard vetoes surviving ablations; ambiguous/invalid/unverified candidates;
macro mapping; Unicode byte locations; source edit replay/directive protection;
compiler attribution; unsafe history filtering; split separation and frozen
fingerprints. Benchmarks have no genuine history, so their evidence distribution
must not be generalized to history-rich use. C is compiled for analysis only,
never executed. Bounded subprocesses/input screens are not OS sandboxing.

Source-free summary: [results/validation.json](results/validation.json).
Detailed logs, screenshots, student code and compiler outputs remain ignored in
`.studio-artifacts/m14/`. Published JSON was checked for source/correction/raw
compiler/timestamp fields; changed text was reviewed for secrets before commits.
