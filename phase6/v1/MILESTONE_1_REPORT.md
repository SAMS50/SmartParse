# Phase 6 Milestone 1 — reference and evaluation foundation

Status: implementation complete for review. No recovery or defect-detection
algorithm changed. No commit or push performed. Work stops at Milestone 1.

## Verification

**265 tests passed, zero failures, zero errors, zero skips:** all 237 existing
tests plus 28 new evaluation tests, including all 141 original SmartParse/CGAR
tests. Installed MinGW GCC 6.3.0 and Android NDK Clang 17.0.2 were used by existing
live integrations. New evaluator tests use synthetic independent evidence and do
not compile or execute programs. The full suite analyzes C through the existing
safe compiler boundary and never executes a compiled user binary.

The full run is saved in [tests.txt](outputs/tests.txt) and
[tests.json](outputs/tests.json). After the final additive output-provenance fields,
all 28 evaluation tests were rechecked successfully. See
[preservation.json](outputs/preservation.json): **194 preexisting files unchanged**,
including all readable Phase 5 acceptance artifacts and the external original
sample; all **17 historical CSVs preserved byte-for-byte**. Legacy tests rewrote a
timing CSV internally, and the runner restored its exact original bytes in finally.
No original parser, CGAR, source fixture, evaluation script, or README was edited.

## New files

- `phase6/__init__.py`: empty discovery package marker.
- `phase6/v1/reference.json`: version 1.0.0 reference, 76 atomic issues with full lineage.
- `phase6/v1/build_reference.py`: reproducible, explicit manual migration decisions.
- `phase6/v1/evaluation.py`: validation, source-bound meaning candidates, attributed review, six outcomes, duplicate/root accounting, false-positive adjudication, category summaries.
- `phase6/v1/evaluate_saved.py`: replay of frozen GCC/Clang evidence without invoking a compiler or rewriting Phase 5 outputs.
- `phase6/v1/assisted_review.json`: 42 explicit evidence links and four cascade adjudications; agent-assisted review, independent human review pending.
- `phase6/v1/test_evaluation.py`: 28 tests, including independent synthetic source names, messages, contracts, backends, and coverage states.
- `phase6/v1/run_tests.py`: full-suite runner that preserves every protected preexisting artifact.
- `phase6/v1/README.md`, this report, version package marker, and `outputs/` JSON/log artifacts.

All new reports/data/tests live under `phase6/v1/`. The parent package marker is
the only new file outside that versioned directory. The original historical
68-entry source and 16/68 comparison remain separate, unchanged baselines.

## Reference changes

The 68 historical entries map to **76 atoms**. Splits at 55, 71, 104, 278, 317,
432, and 439 add eight entries while preserving all historical IDs/lineage.
Related manifestations carry root-cause groups and explicit relationships; more
atomic records do not mean more independent defects.

Each issue records category/tags, logical source/hash, source/sink lines,
triggering conditions, required contracts, admissible message/checker evidence,
oracle uncertainty, required analysis, and review provenance. Some previously
implied contracts are now explicit and deliberately unsatisfied or unresolved.

Examples:

| Former entry | New treatment |
|---|---|
| 278: null stream and uninitialized result | Separate atoms for failed-open stream use and failed conversion on a valid stream. A null-stream diagnostic cannot confirm the uninitialized-return atom |
| 432: allocation size, failure, ownership | Three atoms: missing terminator allocation, null destination on allocation failure, and loss of prior allocation. Prior ownership is a contract-dependent condition, not an assumed fact |
| 104: assignment and null dereference | Assignment warning supports an intent-uncertain construct; it does not confirm the separate dereference at 108. That analyzer assessment is blocked |
| 71 and producer at 129 | Distinguish invalid free and expired-stack-pointer use, link to the producer/root, and prohibit crediting a producer warning as evidence of the later use |
| 405: missing return | Explicitly record the consumer-used-result condition. Unknown applicability is conditional, while the original Phase 5 miss remains unchanged |
| 427: possible race | Remains uncertain: no concurrent callers are established by the source |

## Example evaluation, not a new detection experiment

The supplied assisted review yields:

| Category | Detected | Missed | Blocked | Unsupported | Conditional | Uncertain |
|---|---:|---:|---:|---:|---:|---:|
| Syntax | 2 | 0 | 0 | 0 | 0 | 0 |
| Semantic/type | 5 | 0 | 0 | 0 | 1 | 0 |
| Memory safety | 2 | 0 | 12 | 0 | 5 | 0 |
| Bounds | 1 | 0 | 4 | 0 | 13 | 0 |
| Undefined behavior | 0 | 0 | 4 | 0 | 2 | 1 |
| Program logic | 2 | 0 | 0 | 1 | 1 | 20 |
| **Total** | **12** | **0** | **20** | **1** | **22** | **21** |

The 12 detected atoms map to 12 root-cause groups. The lower number than historical
16 is caused by the stricter intent treatment of four assignment-condition
warnings, **not changed compiler behavior**. Zero primary misses is also not a
claim of complete detection: blocked and conditional references remain visible,
and the old return-value miss has changed applicability under the new oracle.
Neither 12/76 nor 16/68 should be described as general recall.

The [reviewed machine-readable report](outputs/evaluation_reviewed.json) contains
dataset/evaluator versions, input artifact hashes, source bindings, review scope,
all candidate/reviewed evidence, contracts, coverage, categories, and per-finding
dispositions. The [unreviewed report](outputs/evaluation_unreviewed.json) demonstrates
that compatible evidence alone yields no automatic detection claims.

Notes (16) are contextual. Four cascade observations are adjudicated separately.
Forty-two reviewed evidence links include repeated backend/pass evidence and
support for uncertain entries; **42 is not a true-positive or defect count**.

False positives require explicit attributed adjudication and a finding-group ID.
Unlisted findings stay unknown, not false. The unreviewed example has 46 unknown
non-note observations. No actual false positives have been independently
adjudicated here, and zero adjudicated false positives is not a zero-FP-rate
claim. Independent tests exercise confirmed false-positive and duplicate-group
handling. Precision/recall remain `null` with reasons.

## Limits and next review

This is a provisional single-agent oracle migration and assisted evidence review,
not independent human confirmation. Wording rules are conservative candidate
filters and may miss equivalent messages; a reviewer can supply a scoped,
attributed semantic override with an evidence explanation. Notes, wrong sources,
and out-of-scope locations cannot be promoted through that override. Reviews are
fingerprint-bound and become invalid if the reference or evidence changes.

Coverage annotations record known completed/blocked/unsupported passes but cannot
prove that a compiler explored every possible diagnostic. Root grouping and
contracts require future independent adjudication. The oracle is non-exhaustive;
negative controls/holdout expansion are not part of this milestone. No temporary
repair, function isolation, new checker, or analyzer setting was introduced.

Review the reference, relationships, contract assumptions, and assisted review
before treating this version as a locked evaluation oracle. Milestone 2 and later
remain unimplemented.
