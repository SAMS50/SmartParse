# Phase 6 v8 evaluation

This workspace evaluates unchanged SmartParse and compiler-assisted analysis. It adds no detectors or heuristic changes. The dataset is **author-created, not independent**. All proposed defects and tool findings await human review. Confirmed TP/FP/FN, precision, recall and F1 are unavailable (`null` in JSON, blank in CSV), rather than zero.

`MILESTONE_8_REPORT.md` contains the measured results and limitations. Historical 12-program syntax scores, the 16/68 comparison and Milestones 1–7 remain separate and unchanged.

## Reproduce

Run from the repository root with Python 3.12 and the recorded installed tools. No installation is performed. Tool locations, versions and executable hashes are in `outputs/environment.json`; exact flags and budgets are frozen in `configurations.json`. Header/library models and target ABIs differ across the installed toolchains, so this is not a hermetic cross-compiler experiment.

```powershell
python -m unittest phase6.v8.test_evaluation -v
python -m phase6.v8.runner --syntax-only
python -m phase6.v8.runner
python -m phase6.v8.report
python -m phase6.v8.audit_results
python -m phase6.v8.figures
python -m phase6.v8.validate --full-suite
```

The runner resumes existing result/supervisor pairs. For a fresh repetition, use a separate checkout and archive the prior v8 outputs before regenerating them; never regenerate or alter the frozen inputs. `prepare.py` is the one-time authoring script and refuses to overwrite an existing freeze. `--limit N` runs only a subset and is not a complete evaluation. A missing compiler produces a failed worker report, not substitution with another compiler. The worker supervisor has a 45-second deadline; internal evaluation allows 30 seconds and 5 seconds per tool call, with invocation budgets. Owned-child cleanup has additional finite grace. These are practical limits, not a hostile-input sandbox or hard real-time guarantee.

Only the existing external GCC analyzer creates private object files; it never links or executes them. Clang runs syntax, AST and analyzer passes. User source files are never rewritten; repair and isolation use the existing private variants with provenance. These conditional findings remain distinct from original-source evidence.

The legacy regression suite rewrites a historical performance CSV. `validate.py` snapshots all 17 historical CSVs and restores changed bytes in `finally`, then checks every protected hash. Final bytes are preserved; timestamps and absence of transient legacy writes are not claimed.

## Frozen protocol and evidence

`manifest.json` lists 12 restricted-grammar syntax cases and 20 full-C cases, source hashes, proposed roots, evidence anchors, intended syntax counterparts and review status. None is byte-identical to an earlier preserved file. That check does not establish conceptual independence: the same author knows the existing tools. No external dataset was downloaded. No random generation or seed is used.

`freeze.json` binds the 46 input/reference/configuration files before the tool evaluation. `policy.json` records category/identifier/meaning and source-location requirements. One root per diagnostic is permitted; ambiguous matches remain separate; multiple supporting diagnostics collapse at the root. Notes never independently establish a defect. Unmatched warnings are unknown, not confirmed false positives, and an unobserved author proposal is not automatically a false negative.

Syntax matching protocol 1.1 corrects a formatting asymmetry: panic mode prints `Expected ; before`, while SmartParse may quote `';'`. The same expected punctuation at the exact frozen anchor is now recognized in either spelling. `protocol_amendment_1_1.json` documents this correction after first-pass observations; all 48 syntax evaluations were repeated and original outputs retained in `outputs/syntax_protocol_1_0/`. Frozen sources, intended repairs and full-C matching rules were unchanged.

Two authored intended syntax references, S04 and S07, use `void` parameter forms unsupported by the restricted parser. S12 contains an unsupported lexer character. They are retained and flagged, not repaired or relabeled to improve scores. The other nine cases are the grammar-supported syntax cohort. Reaching EOF is parser control-flow progress, not proof that every statement survived or that the repaired token stream matches intent. The default context configuration already enables local validation and aliases `validation_on`; those rows are not independent experiments.

The extended baseline is the previous v6 compiler/CSA/memory/semantic pipeline. Recovery and isolation use the same pipeline with only the respective existing opt-in feature enabled. GCC 6.3 and Clang compiler-only rows provide separate frontend baselines. GCC14 and Cppcheck use the unchanged v7 selected profiles. The combined optional configuration is a derived union of original-source supported root proposals, not an additional subprocess run. Conditioned cohorts are excluded from that union.

## Outputs and schemas

The frozen matcher omits actual v6 `alpha.unix.Stream` and `SP6.contradictory_int_conjunction` IDs and uses a next-token semicolon anchor that differs from some compiler locations. Raw evidence remains present. See `review/frozen_matching_limitations.json`: automated exclusive-match lists do not establish unique detection capability. Those rules were retained rather than broadened after observing outcomes.

- `outputs/extended/CONFIG/CASE.json`: unchanged existing report nested under `result`, plus configuration, source hash and wall time. Corresponding `.process.json` and `.log` files record the external supervisor.
- `outputs/syntax/CONFIG/CASE.json`: diagnostics, repairs, exact authored-anchor/repair matches, replay validity, intended token equality, EOF progress and trace-only statement observations.
- `outputs/evaluation.json`: `smartparse.descriptive_evaluation` version 1.0, cases/configurations, normalized evidence, independent eligibility states, provisional matching and unavailable confirmed metrics.
- `outputs/root_comparison.json`: root unions, intersections, exclusive support and unobserved author proposals. No warning-count accuracy claims.
- `outputs/benchmark_prior_evidence_comparison.json`: exact reproduction of unchanged prior Cppcheck diagnostic evidence with historical root relationships retained; no new human confirmation.
- `review/REVIEW_PACKAGE.md` and `review/decisions.json`: line-numbered source, author proposals, diagnostic records and blank reviewer/decision/date fields. Review full raw path notes and contracts before deciding root identity, duplicates, false positives or misses.
- `tables/table_I_*.csv` through `table_V_*.csv`: syntax, capabilities, category evidence, pending adjudication/blocked cases and benchmark diagnostics. Blank confirmed metrics explicitly mean unavailable.
- `figures/`: five Matplotlib figures as SVG, PDF and PNG, with descriptive labels and pending-review qualifications.
- `outputs/regression.*`, `outputs/preservation.json`: full test log/supervision and hash verification.

Per-function/path completeness remains uncertified even when an analyzer process completes. Frontend rejection blocks custom semantic analysis; diagnostics emitted on malformed input do not certify all regions. A category absent from these small cases is unevaluated, not universally unsupported. Human adjudication, separately authored real-project holdouts, broader build configurations and repeated timing experiments remain necessary before paper-level accuracy or significance claims.
