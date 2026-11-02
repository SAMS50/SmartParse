# Milestone 13: real-world C evaluation

## Research outcome

**SmartParse full intent-aware recovery does not demonstrate a measurable
advantage on the genuine, previously unseen C mistakes evaluated here.** It
abstains on all 79 final primary cases. Existing scoring exactly repairs 20/79;
Clang machine fix-its exactly repair those same twenty cases. Full mode avoids
four existing-score exact-source mismatches by issuing no recommendations, so
the reduction is not achieved while maintaining useful coverage.

This is a negative generalization finding, not a claim that every future
intent-aware approach fails. Actual earlier editing histories are unavailable,
so the history-benefit research question remains unresolved. No future corrected
snapshot was reversed into artificial engine history. No algorithm change was
made in response to final outcomes.

## Existing implementation audit and frozen protocol

Started from pushed Milestone 12 `d48270d` on
`feature/milestone-13-real-world-validation`. Reviewed reports, dataset/scoring
code, candidate generation, Clang projections, replay, ablations and regression
infrastructure. V11/v12 code and evaluation artifacts remain unchanged. Studio
is unchanged. The protocol at `phase6/v13/RESEARCH_PROTOCOL.md` was committed as
`7332790` before acquiring case contents or examining outcomes.

The evaluation retains v12's existing/history/semantic/full modes, one identical
candidate pool per input, margin 12, 24-program cap, 240 original search trials
and 15-second compiler evidence budget. The source/history-only `RecoveryInput`
type has no correction field. Only evaluator code reads the target; target
compiler diagnostics are generated after recovery completes and never passed
back. Frozen engine and harness hashes, tool capabilities and sample hashes are
recorded in `experiment-lock.json`, committed at `2f3d270` before final evaluation.
Integrity tests verify those assets remain unchanged.

## Data sources, licenses and acquisition

Selected [TEGCER](https://github.com/umairzahmed/tegcer), revision
`0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5`. Its maintainers describe genuine
same-student compiler-failing/corrected C pairs from Prutor. The repository has
a GPL-3.0 license; the dataset archive has no separate notice. Data is used
locally for evaluation and is not redistributed in Git. Upstream attribution:
Ahmed et al., [TEGCER, ASE 2019](https://arxiv.org/abs/1909.00769), and Das et al.,
[Prutor, 2016](https://arxiv.org/abs/1608.03828). This is upstream human provenance,
not independent relabeling or student-identity verification.

Also audited [DeepFix](https://github.com/aar-gee/DeepFix), whose maintainers
document Apache-2.0 student data, and [DrRepair](https://github.com/michiyasunaga/DrRepair),
whose raw/synthetic distinction must be preserved. Unpaired errors and
model-generated corrections were not silently adopted as intended labels.

The hash-locked TEGCER archive is 9,651,167 bytes and contains one 88,942,404-byte
CSV. SHA-256:
`5bfc7485b7c7dc79d5fe55e530ba62fa2d4bc448f02df0ded0ea7e4d1bce3868`.
The downloader uses finite bounds/timeouts, verifies cached/downloaded hashes,
and never runs upstream scripts or extracts arbitrary archive paths.

### Realized sample and provenance categories

* **21,995 genuine-error/correction pairs acquired** in the public archive,
  according to upstream provenance; 100 inferred-family representatives evaluated.
* **100 published correction endpoints known; 99 locally verified corrections**
  across the two splits. Twenty development pairs are A; final has **79 A + 1 B**.
* **Zero actual recorded editing histories** and zero usable partial snapshots
  before the erroneous endpoints. The real-data condition is no history.
* No category C synthetic cases enter this experiment. No sampled category D
  exclusions are hidden; privacy/unsupported-policy exclusions happen before
  sampling and their counts are reported.

Ingestion excludes 172 unsupported include/directive rows, 11 unsupported
preprocessing forms and 5 privacy-screen rows, and removes 1,400 normalized
duplicate pairs. It retains 20,407 unique eligible pairs in 18,563 inferred
families. The fixed hash-seeded selection chooses 20 development and 80 final
families, one representative each, without compiler-outcome resampling.

Raw source-field and normalized-LF hashes are distinct. Original/normalized
source and correction are preserved locally. Public metadata contains hashes,
CSV ordinals, inferred families and counts, not student source, submission IDs,
raw timestamps or private diagnostics. Grouping masks identifiers/literals and
uses token-shingle SimHash distance <=3; a second pass checks erroneous sources.
This reduces near-duplicate leakage but cannot certify assignment independence
because assignment/student metadata is absent from the released schema.

Category A requires source rejection and corrected acceptance on at least one
same compiler. Category B retains a genuine reported mistake whose correction
cannot be verified with this installation. The final B case
`c23cde4be2a55ede8b3da081` is rejected by both tools and is excluded from accuracy
without replacement. Of 100 targets, 94 compile on both tools, five on GCC only,
one on neither. Compiler acceptance is not functional correctness.

## Compiler harness

Installed profiles, recorded exactly:

* GCC: MinGW.org GCC 6.3.0. The parseable-fix-it flag is unsupported.
* Clang: Android/NDK Clang 17.0.2, build 11349228. Parseable fix-its supported.

Both use C11 syntax-only checking with colors disabled. A private temporary
`input.c` is used; exact paths/commands/raw diagnostics stay local. The one-file
path is explicitly mapped for machine edit coordinates. Only whitelisted standard
headers and simple numeric defines are permitted; unsupported preprocessing and
obvious credentials/identifying text are excluded. No source is linked or run.
Calls use the existing bounded runner with timeout/process-tree cleanup and
private temporary files. This is not OS-level isolation, and trusted compilers
can read local headers.

Only machine edit records become repairs. UTF-8 byte boundaries, physical input
identity, nonoverlap, duplicate/alternative hints and edit limits are checked.
Automatic applicability, subsequent compilation and reference agreement are
separate outputs. Lack of a machine repair is not penalized as diagnostic quality.

## Actual comparative outcomes

Final intended-repair accuracy uses **79 A cases**, not all 80 final selections
or all 100 evaluated pairs. Exact source means normalized text match; token match
ignores comments/whitespace but retains identifiers/literals. Neither proves
behavioral equivalence. “Wrong” below means exact intended-source mismatch.

| System | Exact intended | Token match | Wrong | Recommendations | Abstentions | Exact top-3 |
|---|---:|---:|---:|---:|---:|---:|
| Existing scoring | 20/79 | 21/79 | 4/79 | 24/79 | 55/79 | 20/79 |
| History scoring | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 |
| Semantic scoring | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 |
| Full v12 | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 |

Existing selective exact accuracy is 20/24; all 24 recommendations compile in
independent compiler checks. Four are compilable exact mismatches, including one
token-equivalent formatting/comment difference. Full conditional accuracy is
**undefined (0/0)**, not perfect. History-only cannot restore an absent history;
the equal enhanced outcomes do not measure a causal history benefit.

Development is reported separately: all 20 are A; existing scoring exactly
repairs 3/20, with no wrong recommendations and 17 abstentions; enhanced modes
all abstain. No recovery tuning followed these observations.

| Final compiler baseline | Rejection diagnostics | Applicable repair bundles | Exact repairs | Compiling bundles |
|---|---:|---:|---:|---:|
| GCC 6.3 | 78/79 | 0/79 | unavailable conditional accuracy (0 outputs) | unavailable |
| Clang 17 | 79/79 | 36/79 | 20/36 applicable; 20/79 overall | 24/36 |

Clang token agreement is 21/36 applicable. Twelve applicable bundles still fail
compilation. Restricting to Clang-compatible references gives 75 cases, 35
applicable bundles and 20 exact repairs; this denominator is reported separately
to avoid silently treating dialect incompatibility as a repair failure. GCC's
one accepted source reflects compiler/settings compatibility; diagnostic
rejection is not human-rated diagnostic usefulness. These are observations about
installed profiles, not a claim about all/current GCC or Clang releases.

## Uncertainty, selectivity and runtime

Existing exact rate is 25.3%, Wilson 95% interval 17.0–35.9%. Full exact and
wrong rates are zero with Wilson upper bound 4.64%, but zero predictions cannot
establish conditional safety. The paired family-bootstrap full-minus-existing
exact-rate difference is −25.3 percentage points, exploratory 95% interval
−35.4 to −16.5 points, with 20 existing-only successes and no full-only successes.
The analogous difference versus Clang is the same; existing and Clang recover
the same exact cases. Inferred families may remain correlated by assignment,
and the one-dataset deterministic sample limits general inference. No formal
significance, broad superiority or equivalence claim is made.

Diagnostic-only score-gap selectors at 0, 12, 60, 120 and 240 are flat: every
eligible pool is a singleton. They cannot rescue absent candidates or unsupported
analysis. Policies and coverage denominators are shown explicitly.

Shared SmartParse end-to-end evidence construction on primary inputs: mean
168.85 ms, median 137.64 ms, p95 386.30 ms. Mean compiler calls per input: 1.56.
GCC original diagnostics: mean 93.29 ms, median 82.64 ms, p95 138.68 ms; Clang:
98.18 / 93.47 / 135.30 ms. These timings cover different work: compiler-only
diagnostics exclude reference/fix-it validation, whereas SmartParse includes
candidate evidence. No equal-work speedup claim is made. Output byte counts,
compiler invocations and retained-candidate bytes are recorded; process-tree CPU
and peak RSS were not instrumented on Windows (null, not zero). Timing was a
single run with concurrent local regression activity.

## Failure analysis and unresolved questions

Of 79 primary cases, **45 generate no program**, **10 generate no validating
program**, and **24 have a validated singleton with seven UNKNOWN semantic checks**.
All 24 validated inputs retain preprocessing directives, which the frozen
projection rejects. Full mode therefore withholds twenty correct repairs along
with four exact mismatches. Candidate-generation coverage is only 20/79 intended
programs. There is no evidence that numeric re-ranking alone solves these cases.

Diagnostic categories: 53 syntax/delimiter, 13 name/type, 5 type/expression and
8 other. There are 43 one-error-diagnostic cases and 36 with multiple diagnostics;
diagnostic cascades prevent treating these as independent defect counts. Results
are broken down by length, history, compatibility, candidate count and semantic
status in `phase6/v13/EVALUATION_REPORT.md`, and every final case appears in
`phase6/v13/FAILURE_ANALYSIS.md` without source excerpts.

RQ1/RQ2 show no coverage-preserving advantage on this sample. RQ3 requires real
prior histories unavailable here. RQ4 shows parity of existing exact selection
with Clang fix-its, while full mode has no coverage. RQ5 identifies scope and
generation gaps. Production C, multiple datasets, actual recorded histories,
assignment-level splits, behavioral oracles and supported preprocessing analysis
remain future work. Any optimization must use new development data and another
frozen final set, not retune this result away.

The optional history helper checks supplied chronology, replay and the presence
of a provenance URL; it does not authenticate a remote editing session by itself.
An additional source audit would be required before admitting such evidence as
real recorded history. No such evidence was used in this experiment.

## Reproduction in Windows PowerShell

From repository root using the existing environment and installed compilers:

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v13.acquire --lock phase6/v13/acquisition-lock.json
.\.studio-venv\Scripts\python.exe -m phase6.v13.ingest
.\.studio-venv\Scripts\python.exe -m unittest phase6.v13.test_pipeline
.\.studio-venv\Scripts\python.exe -m phase6.v13.evaluate --split development --output .studio-artifacts/m13/reproduced-development.json
.\.studio-venv\Scripts\python.exe -m phase6.v13.evaluate --split final --output .studio-artifacts/m13/reproduced-final.json
.\.studio-venv\Scripts\python.exe -m phase6.v13.validate
Push-Location studio
npm.cmd test
npm.cmd run build
Pop-Location
```

Network is needed only for pinned acquisition; subsequent ingestion/evaluation
uses local files. No dependencies, model weights or browsers were installed.
Existing `SMARTPARSE_CLANG` and `SMARTPARSE_GCC` overrides apply; changing tool
versions can change compatibility/results and must be reported. Use `python -m
phase6.v13.report` to regenerate Markdown from the **committed curated results**,
not from a new run automatically. Raw local captures are in
`.studio-artifacts/m13/private/`; generated experiments never overwrite v11/v12.

## Validation and Git delivery

Full repository/backend discovery: **554 tests, OK, 28 optional-tool skips**.
Targeted v13 suite: **15 tests pass**, including provenance/hash verification,
deduplication, chronology/leakage barriers, machine edits, unsupported compilers,
separate metrics, bootstrap determinism and frozen assets. Frontend: **69 tests
pass**; TypeScript/Vite production build passes with the existing Monaco bundle
warning. Studio source is unchanged. Historical protection checks **1,995 files**
including v11/v12 and existing acceptance outputs; **zero changed**. The known
legacy timing CSV is restored to its exact pre-run bytes by the runner.

Curated records contain no student code, private diagnostic excerpts, raw
timestamps, submission IDs or local user paths. External datasets remain ignored;
only necessary metadata/hashes, observed metrics and research documentation are
versioned. No push or merge is performed without approval.

Checkpoints: `7332790` protocol; `d78953e` tested acquisition/harness/frozen sample;
`2f3d270` final experiment lock; `c715da3` observed results and research reports.
Final documentation commit is reported separately in the delivery message.

## Changed-file inventory

Modified: `README.md` only outside the new research directory.

New: this report; under `phase6/v13/`: `__init__.py`, `acquire.py`, `ingest.py`,
`history.py`, `engine.py`, `compiler.py`, `metrics.py`, `evaluate.py`, `report.py`,
`validate.py`, `test_pipeline.py`, `acquisition-lock.json`, `sample-manifest.json`,
`experiment-lock.json`, `RESEARCH_PROTOCOL.md`, `REAL_WORLD_DATASET.md`,
`COMPILER_COMPARISON.md`, `FAILURE_ANALYSIS.md`, `EVALUATION_REPORT.md`,
`VALIDATION.md`; under `phase6/v13/results/`: `development.json`, `final.json`,
`validation.json`. No recovery engine, Studio component, prior benchmark or
external student dataset is modified/added to the branch.
