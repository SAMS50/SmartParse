# Milestone 12: failure analysis and repair optimization

## Outcome

On the predeclared 52-case held-out set, v12 full made **28 correct, zero wrong
recommendations, and 24 abstentions**. V11 full made **16 correct, four wrong,
and 32 abstentions**. Recommendation coverage increased from 20/52 to 28/52;
accuracy among recommendations increased from 16/20 to 28/28. Intended-candidate
coverage increased from 36/52 to 40/52. Mean full-system runtime increased from
582.00 ms to 614.70 ms, an observed overhead of 32.70 ms (5.6%).

This is an improvement on this held-out synthetic/reconstructed benchmark with
no observed increase in wrong recommendations. It is not a statistical
non-inferiority result, proof of zero future errors, or general superiority on
real programmer edits. There are no recorded human sessions or independent human
labels. Full and semantic-only v12 tie on held-out outcomes, so no additional
held-out benefit from the numerical history score is established.

## Reproduced baseline and root causes

Started from committed/pushed Milestone 11 `d261ec3` on the requested new branch,
`feature/milestone-12-repair-optimization`. No original source or untracked
acceptance file was discarded. The unchanged v11 benchmark was rerun with all
four modes and independent full-system measurements: full **7 correct / 1 wrong /
12 abstained out of 20**, matching its committed results. The original parser
plan still exactly restored 2/20.

The complete twenty-row table is in `phase6/v12/FAILURE_ANALYSIS.md`; full
candidate sources, syntax results, history features, structural statuses, score
components, margins, explanations and recoverability assessments are in
`phase6/v12/results/failure-details.json`.

Observed historical classification: 7 correct recommendations; 6 appropriate
ambiguity abstentions; 2 generation failures (pointer brace); 1 overly conservative
abstention (unique multi-semicolon repair without history); 1 incorrect history
interpretation; 3 unsupported/unavailable-evidence abstentions. No validation
failure or numeric-ranking misclassification was demonstrated in those twenty.
Identified AST coverage gaps were audited separately rather than relabeled as
proven causes of historical mistakes.

The misleading case has exact replay, correct offsets and valid source versions.
Its valid historical return ownership differs from evaluator intent. Increasing
or decreasing history weight cannot recover information absent from the inputs;
the historical AST and history score are also not independent evidence. The old
ranker had a large score margin and still chose the wrong intent.

## Implemented changes and reasons

Milestone 11 remains frozen. New code is isolated under `phase6/v12/`, reusing its
lexer, repair generation, syntax validation, scoring and physical edit mappings.

* **Bounded generation:** reserve four of the existing 24 retained-program slots
  for lexer-aware unmatched-delimiter completion, at most two return/else brace
  boundaries, a first merged identifier/control-keyword boundary, and a bundle
  of at most three nonoverlapping compiler fix-its. The 240 original trial bound
  remains. Comments and strings do not affect delimiter inventory; preprocessing
  is excluded from supplemental search. Exact repaired text is deduplicated.
  Neither history nor ground truth enters candidate generation.
* **Reliability assessment:** distinguish missing history, unreliable mappings,
  verified replay, broad recent replacement, and conditional local-edit support.
  An EOF closing-brace deletion is ambiguous when valid supported alternatives
  have different structures. Enhanced modes abstain instead of treating valid
  replay as current intent. Broad replacements and unverified candidate validation
  also block recommendations; malformed/incomplete histories are not trusted.
* **Structural consensus:** without a supported valid historical reference,
  semantic/full modes may recommend when all validated candidates have the same
  supported projection and differ only by one to three non-brace punctuation
  edits. Existing historical checks remain UNKNOWN. The output identifies the
  basis as bounded candidate consensus, not preservation against an invalid or
  absent original AST. This can still be wrong if the pool misses intended
  alternatives; coverage is measured explicitly.
* **Semantic coverage:** permit scalar global declarations and resolve their
  bindings; explicitly record expression statements under control-flow owners,
  including branch positions. Function evidence includes signatures and direct
  body statement inventory. Changed inventory is structural membership/count
  evidence, not a proof that physical function boundaries moved. Unknown kinds,
  preprocessing, pointers, arrays, records, casts, volatile/atomic and non-ASCII
  analysis remain UNKNOWN. No aliasing or behavioral equivalence claim is made.
* **Development-discovered lexical/type constraint:** deleting a semicolon joined
  `a;if` into `aif`. A wrong alternate repair depended on a compiler extension
  accepting an implicit function declaration with diagnostics suppressed. V12
  validates function references against declarations in complete accepted ASTs
  for C99+, and refuses undeclared-function candidates. C89 remains conservative
  in semantic analysis. A bounded merged-keyword candidate restores the actual
  boundary. This refinement was tested and completed before held-out evaluation.

PRESERVED/CHANGED describe supported structural projections only. Possible
behavioral consequences are not proved; UNKNOWN remains explicit. Valid compiler
output is never treated as program correctness.

## Scoring and threshold selection

The explainable v11 score is retained:

`S = B + H - 18 (# CHANGED) - 4 (# UNKNOWN)`.

`B` is existing contextual/plan scoring (new boundary candidates use documented
origin scores 10, 20 or 35); history uses the unchanged deterministic
snapshot-restoration, changed-character-distance and proximity function. The
new rules refine evidence eligibility and abstention, rather than fitting weights
to the historical twenty cases. Modes remain existing, history, semantic and full;
each version shares one candidate pool across its modes. Reliability gates are
shared by enhanced modes. History-only excludes AST score penalties; semantic-only
excludes numerical history score but still uses reliability and valid historical
references. These are scoring ablations, not complete removal of history inputs.

Development-only sweeps used ambiguity margins 0, 6, 12 and 24. Selection minimizes
wrong recommendations, then maximizes correct recommendations, then prefers the
original default 12 on ties. All tested margins tied; 12 was retained. There is
no evidence that a different numeric margin is better. The fingerprint in
`results/selection.json` covers normalized algorithm/dataset sources; held-out
evaluation refuses a changed fingerprint. The selection was committed at
`d91f95c` before held-out evaluation. No algorithm changes followed that run.
Tie-breaking remains deterministic by repaired-source hash after validity/score.
Compiler/time budget exhaustion can reduce verified evidence and forces
conservative decisions; timing itself is not deterministic.

## Benchmark methodology and actual results

84 new cases: **32 development cases / 8 families**, **52 held-out cases / 13
families**. The held-out set comprises 48 authored scalar-routine mutations and
four distinct pre-existing repository C fixture mutations grouped into a single
resource-program family. Dataset generation is deterministic. Canonicalized
identifier/number fingerprints remove duplicates; family IDs and normalized
malformed programs are disjoint between splits. Conceptual similarity among
small C routines remains a generalization limitation.

Histories are synthetic/reconstructed and labeled as local, missing, misleading
or incomplete. A legitimate history can reconstruct a prior valid program; this
optimistic experimental condition is disclosed. Hidden evaluator ground truth
never enters the ranker/generator. Real browser-recorded automation verifies
integration but is excluded from accuracy denominators. Original twenty cases
are historical comparisons only. All reference programs are separately validated.

| Split / full mode | V11 correct | V11 wrong | V11 abstained | V12 correct | V12 wrong | V12 abstained |
|---|---:|---:|---:|---:|---:|---:|
| Development (32) | 11 | 3 | 18 | 19 | 0 | 13 |
| Held-out (52) | 16 | 4 | 32 | 28 | 0 | 24 |
| Historical (20) | 7 | 1 | 12 | 8 | 0 | 12 |

Held-out contextual scoring: 28 correct / 13 wrong / 11 abstained on either
version's pool. V12 history-only: 15 / 0 / 37; semantic-only: 28 / 0 / 24;
full: 28 / 0 / 24. Top-3 intended coverage improves 35/52 → 38/52 full-to-full.
All held-out ranking-only decisions match independent full-system decisions.

Missing history: v12 correctly recommends 11/12 versus v11 0/12, with no observed
wrong recommendations. Misleading history: v11 makes 4/4 wrong recommendations;
v12 abstains on all four. Both abstain on all three incomplete-history cases.
The four repository resource fixtures are not recovered by v12; unsupported
semantic analysis and missing candidates remain explicit limits.

On the historical set, v12 gains the unique missing-history multi-error repair
and the scalar-global case, removes the misleading-history error, but loses
the previously correct broad multi-edit-history recommendation. This is a real
conservatism cost: reconstructed aggregate events can look broad despite small
disjoint token deletions. It is documented rather than tuned away after testing.

See `phase6/v12/EVALUATION_REPORT.md` for all ablations, history subgroups,
case-level remaining failures, runtime tables, selective-prediction curves and
confidence intervals. The primary margin sweep was flat; an explicitly labeled
diagnostic-only stricter-gap selector illustrates loss of recommendation coverage
and sometimes worsening accuracy. Score gaps are not calibrated probabilities.

Exploratory 95% family-bootstrap exact-rate intervals: v11 0.212–0.423; v12
0.385–0.673. With zero observed v12 errors, bootstrap error intervals degenerate;
they do not prove zero future error. Under independent-family sampling assumptions,
13 zero-error families still allow a one-sided 95% upper bound of 0.206 on the
chance a family contains an error. Authored families are not random samples.
No significance, population-wide safety or broad superiority claim is made.
“Wrong” means a selected compiler-valid program differs from exact intended text;
the benchmark does not execute repaired programs or prove behavioral differences.

## Studio, validation and preservation

The existing Recovery tab adds one reliability/basis line. Candidates, alternatives,
impact explanations, comparisons, styling and editor undo are retained. No repair
auto-applies. The API defaults to v12 and accepts explicit `intent_version: "v11"`
for regression/comparison, retaining the previous response fields and limits.

Validation: full repository unittest discovery including backend and both
milestones; separate v11 and v12 suites; 69 frontend tests; TypeScript/Vite build;
real Chrome paste/edit/recovery/diff/reanalysis/undo; real EOF-history ambiguity
and reliability display. Exact final counts are in `phase6/v12/VALIDATION.md`.
The only build warning is the existing large Monaco bundle.

The preservation-aware runner checks 1,969 historical/acceptance files and
restores only the known legacy timing CSV to its exact pre-run bytes. No frozen
v11 source/result or older evaluation artifact is changed. Existing untracked
acceptance files remain in place. `.gitignore` now excludes reproducible JSON,
JSONL and TXT records under `acceptance/output/`; tracked Markdown reports remain
tracked. No files were deleted. Curated v12 evaluation JSON is intentionally
versioned; browser reports, screenshots, build products and temporary data stay
under ignored `.studio-artifacts/`.

## Reproduction in Windows PowerShell

From repository root, start API and Studio in separate terminals:

```powershell
.\.studio-venv\Scripts\python.exe -m uvicorn smartparse_studio.api.main:app --host 127.0.0.1 --port 8000
```

```powershell
Set-Location studio
npm.cmd run dev
```

Enable **Analysis settings → Intent-aware recovery**, edit valid C, then Analyze.
Standalone read-only v12 analysis (no history means conservative fallback):

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v12 example.c --mode full
```

Reproduce experiments without overwriting committed outputs:

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v12.evaluate --split development --full-system --selection .studio-artifacts/m12/reproduced-selection.json --output .studio-artifacts/m12/reproduced-development.json
.\.studio-venv\Scripts\python.exe -m phase6.v12.evaluate --split heldout --full-system --selection .studio-artifacts/m12/reproduced-selection.json --output .studio-artifacts/m12/reproduced-heldout.json
.\.studio-venv\Scripts\python.exe -m phase6.v12.evaluate --split historical --full-system --output .studio-artifacts/m12/reproduced-historical.json
.\.studio-venv\Scripts\python.exe -m phase6.v12.validate
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v11 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v12 -t .
Push-Location studio
npm.cmd test
npm.cmd run build
Pop-Location
python -m phase6.v12.browser_smoke --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

Browser testing uses the already-installed Playwright in system Python. The
Studio venv and compilers were reused; no package/browser installation occurred.
Compiler discovery supports existing `SMARTPARSE_CLANG`/`SMARTPARSE_GCC` overrides.
Historical detailed auditing can be repeated with `python -m phase6.v12.audit`;
it intentionally regenerates `FAILURE_ANALYSIS.md`, while raw output defaults to
`.studio-artifacts/m12/failure-details.json`.

## Changed-file inventory

Modified: `.gitignore`, `README.md`; `smartparse_studio/api/models.py`,
`smartparse_studio/api/worker.py`; `studio/src/types/report.ts`,
`studio/src/components/Inspector.tsx`, `studio/src/components/Inspector.test.tsx`.

New: this report; under `phase6/v12/`, `__init__.py`, `__main__.py`, `audit.py`,
`candidates.py`, `history.py`, `semantics.py`, `engine.py`, `dataset.py`,
`evaluate.py`, `report.py`, `validate.py`, `browser_smoke.py`, `test_recovery.py`,
`test_dataset.py`, `test_api.py`, `test_evaluation.py`, `FAILURE_ANALYSIS.md`,
`EVALUATION_REPORT.md`, `VALIDATION.md`; under `phase6/v12/results/`,
`baseline-reproduced.json`, `failure-details.json`, `development.json`,
`selection.json`, `heldout.json`, `historical.json`, `validation.json`.

## Remaining limitations

The supported subset and single-file context remain narrow. No real human
editing dataset, independent adjudication, runtime behavior oracle, formal
equivalence or broad full-C recovery claim. Bounded search misses twelve held-out
intended repairs. Broad aggregate edits cause false-negative history gates.
EOF-history guards cover one ambiguity family, not every misleading history.
Singleton/unanimous candidate pools can omit the true intended structure. AST
projection equality is coarse and does not prove semantic preservation. Confidence
intervals and small family counts limit inference. Further optimization requires
new development data and a new independent held-out set; this held-out set must
not become a repeatedly tuned success target.
