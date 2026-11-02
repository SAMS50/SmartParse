# Validation record — 2026-11-02

* Base: Studio `4fa5b85`; dedicated feature branch, no merge to main.
* Architecture: `ebee9f1`; history: `3cfdf75`; semantics: `dcb691d`;
  ranking: `f1d5c7c`; backend: `e80a084`; frontend: `f8e8724`;
  benchmark/demo/refinements: `82c2100`.
* Repository unittest discovery: **523 tests, OK, 28 skips**. Optional compiler
  capabilities account for skips. Final additions checked separately below.
* Final v11 unittest discovery: **11 tests, OK**.
* Studio Vitest: **8 files, 69 tests passed**.
* Final TypeScript/Vite build: **passed**; bundled Monaco chunk size warning.
* Actual Chrome/Playwright demo: **passed**, recording a real delimiter deletion,
  request history, intended repair, visible read-only diff, repeated analysis
  with identical source, working Monaco undo and zero browser page errors.
* Final benchmark: 20 cases, ranking-only and independent full-system runs.
  Exact intended recommendation 7/20 full vs 5/20 same-pool existing score;
  incorrect recommendations 1/20 vs 12/20; abstentions 12/20 vs 3/20.
  Old parser plan exact 2/20. Full-case accuracy conditional on recommendation:
  7/8. Misleading valid history remains the explicit failure.
* Clang and GCC diagnostic rejection: 20/20 each; applicable machine fix-its
  Clang 4/20 with exact restoration 2/4; GCC 0 applicable cases.
* Original sources and frozen evaluation fixtures unchanged. A legacy test
  regenerated `results/verified_performance.csv`; it was restored to its clean
  pre-test committed contents. Pre-existing untracked acceptance outputs were
  preserved and excluded. No historical artifacts are included in the diff.
* Secret/private-path scan of new milestone sources/results: no matches for
  common token/private-key signatures or user-profile paths. No dependencies,
  temporary workspaces, browser reports/screenshots or local acceptance outputs
  are staged. Curated benchmark/demo JSON is intentionally included.

Restricted execution initially prevented temporary Studio worker workspaces and
Vite build helpers. Tests were rerun successfully with normal local process/temp
access. No package installation or authentication bypass was used.

The browser regression exposed Monaco 0.57's deferred diff-view-model release.
Explicit ownership/disposal of that view model cancels in-flight worker work
before text models disappear. This was verified by actual reanalysis and undo.

Raw browser artifacts remain local under `.studio-artifacts/m11/browser/` and
contain machine-specific paths; only reproducible test code is committed.
See the root milestone report for formulas, metrics, limitations and commands.
