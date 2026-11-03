# Milestone 14 ? Evidence-adaptive recovery and real-C compatibility

Implemented on `feature/milestone-14-adaptive-recovery`, based on `59b9eb3`.
The result restores useful reviewable proposals, but does **not** demonstrate
research superiority or establish acceptable general wrong-repair risk.

## Findings and real-world results

Milestone 13 was reproduced before algorithm changes. All 79 eligible final
intent-aware abstentions were audited: 45 had no generated programs, 10 had
programs but no validated candidate, and 24 had a validated singleton. Missing
recorded history and unsupported preprocessing prevented intent-aware selection;
all 24 singleton cases had seven unknown structural checks. Candidate generation
and selection failures are recorded separately. The 20 existing exact repairs and
four mismatches are identified in the [complete root-cause ledger](phase6/v14/ROOT_CAUSE_ANALYSIS.md).
A theoretically possible compiler-valid fallback is not evidence of safe intent.

Development uses the original 20 records. The previously inspected 80-record final
split is labeled **exposed**, with 79 eligible A records and one B record whose
reference does not compile locally. A further 80 previously unexamined inferred
source families provide the new evaluation; all are A. IDs, inferred families and
canonical source hashes are disjoint from the original 100. All come from the
same pinned TEGCER student-error archive, not independent projects. No genuine
preceding edit histories exist. Corrections enter evaluator checks only after
candidate generation and selection. Public results exclude student programs.

| Split / system | Exact | Wrong exact match | Alternatives | Abstentions |
|---|---:|---:|---:|---:|
| Development 20 / adaptive combined | 2 | 0 | 5 | 13 |
| New 80 / v13 existing | 13 | 0 | 0 | 67 |
| New 80 / v13 full intent | 0 | 0 | 0 | 80 |
| New 80 / adaptive custom | 0 | 0 | 3 | 77 |
| New 80 / adaptive compiler | 12 | 0 | 5 | 63 |
| New 80 / adaptive combined | 12 | 0 | 8 | 60 |
| New 80 / simple combined fallback | 17 | 3 | 0 | 60 |
| Exposed eligible 79 / v13 existing | 20 | 4 | 0 | 55 |
| Exposed eligible 79 / adaptive combined | 18 | 4 | 4 | 53 |
| Exposed eligible 79 / simple combined fallback | 21 | 5 | 0 | 53 |

All 12 new adaptive recommendations and all 22 exposed recommendations originate
from **Clang**. Custom-only supplies one exact candidate on development and none
on either evaluation split; it makes no recommendations. Combined intended
candidate coverage is 17/80 new and 21/79 exposed. Semantic/history positive-evidence
ablations have identical outcomes here because those signals are absent or
unsupported; they are not evidence that history is useless in other settings.

The preregistered simple combined fallback repairs five more new cases correctly
but adds three mismatches. Existing scoring repairs one more correctly with no
observed mismatches. A **post-hoc descriptive** compiler-only singleton check
would repair 17/80 exactly with no mismatches, exceeding adaptive selection.
It was neither tuned nor deployed. There is no demonstrated algorithmic advantage
over that simple compiler fallback. Exact mismatches include one token-equivalent
exposed repair and do not all establish behavior changes. The same four exposed
mismatches remain; none is blacklisted. Lower abstention alone is not success.

For 12/12 recommended exact matches, the Wilson 95% lower bound is about 0.758;
zero wrong/80 has an upper bound about 0.046. These small samples do not prove
zero risk. All new recommendations use SYNTAX_ONLY; the remaining 68 decisions
are INSUFFICIENT_EVIDENCE. See [full results, intervals, timings, paired family
bootstrap, provider attribution and case-level ledgers](phase6/v14/EVALUATION_REPORT.md).
Compiler-assisted preparation adds substantial runtime; committed measurements
are single-run local values affected by concurrent validation, not performance claims.

## Implementation and policy

`phase6/v14` adds five explicit evidence modes: FULL_EVIDENCE, SEMANTIC_EVIDENCE,
HISTORY_EVIDENCE, SYNTAX_ONLY and INSUFFICIENT_EVIDENCE. Output separates a
recommended repair, suggested alternatives and abstention. Invalid, blocked and
unverified candidates remain separate. Nothing automatically applies a repair.

Missing evidence contributes zero instead of a penalty. Ranking records the
existing heuristic, available history score, 20 points for supported structural
agreement and an edit cost of two points per hunk. Scores are transparent ordering
terms, not probabilities. Verified replay alone is distinguished from strong
snapshot-restoration intent support. Alternatives within margin 12 remain
ambiguous; unverified alternatives and ambiguous boundary histories block selection.
The development-only comparison of one versus two edit hunks tied at two exact,
zero wrong; the predeclared tie rule selected one. Evaluation fingerprints enforce
that frozen choice. No final-case IDs occur in selection logic.

The lower-assurance syntax policy permits a unique validated token program with
one insertion hunk containing only semicolons/commas and no nonwhitespace deletion.
It does not permit arbitrary brace/operator repairs. Structural checks distinguish
VERIFIED_STRUCTURAL_CHANGE, NO_DETECTED_STRUCTURAL_CHANGE, UNKNOWN,
UNSUPPORTED and CHECK_FAILED. Known structural changes, failed checks and unreliable
macro mapping are hard vetoes, including in positive-evidence ablations. Unknown
is no proof of safety; unsupported is no detected hazard. Supported comparisons
are partial structural analyses, not equivalence proofs. A Clang AST null-body
check detects inserted empty control bodies; user function ranges exclude header
AST nodes and convert UTF-8 editor locations to Clang byte offsets.

Custom generation masks and restores protected preprocessor lines for proposals,
then validates the complete source with headers. It does not relabel compiler
hints as custom work. The Clang provider extracts structured physical fix-its,
rejects overlaps/invalid ranges/directive edits, normalizes character and byte
ranges, verifies replay and deduplicates programs while retaining every origin.
One bounded follow-up round can repair additional errors. Custom/compiler/combined
pools are evaluated separately; combined-policy ablations share one pool.

Validation uses temporary source copies, capped compiler calls/deadlines and input
safety checks, including historical snapshots. It never executes analyzed C or
writes repaired programs over originals. The CLI rejects output paths aliasing
input/history. Compiler subprocesses use argument arrays, not arbitrary shell
commands. Temporary cleanup is tested. These controls are not an OS sandbox or a
hard real-time guarantee. Existing infrastructure still has limited real-C
semantic support, especially preprocessing, macros and multi-error cases.

## Studio and compatibility

Studio's existing intent-recovery opt-in explicitly requests v14 with combined
providers; external API requests omitting a version retain v12. `intent_provider`
accepts custom/compiler/combined. Recovery shows evidence available/missing,
reasons, origin and potential impact, and distinguishes rejected/blocked/unverified
entries. The editor, tabs, comparison and undo remain in place. Browser checks
exercise actual history restoration/diff/undo, imported header-bearing C,
Clang credit, lower assurance and repeated analysis preserving source.

## Correctness amendment

Final validation found a character/byte offset mismatch in the new structural
check. `2e395c1` corrects it and adds a non-ASCII regression. Two exposed inputs
contain non-ASCII text; development/new inputs are ASCII. First runs were preserved
locally, then calibration and both evaluations rerun without policy tuning.
All 180 cases across eight systems retain identical recommendations, selected
hashes, outcomes, modes, providers, candidate IDs and reasons. The
[comparison record](phase6/v14/results/correctness-rerun.json) preserves fingerprints.
The new set was unexamined before its first run; the rerun is not a pristine unseen
test. Future policy tuning requires a new evaluation split.

## Reproduction in Windows PowerShell

Use the existing environment/setup in [Studio developer documentation](smartparse_studio/README.md).
Clang and GCC must be discoverable; compiler profiles/hashes are in result JSON.
The acquisition command requires network access to the pinned upstream archive;
subsequent evaluation is local. Dataset code checks the acquisition lock and keeps
GPL-3.0 student code under ignored `.studio-artifacts`, with source-free Git records.

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v13.acquire --lock phase6/v13/acquisition-lock.json
.\.studio-venv\Scripts\python.exe -m phase6.v14.dataset
.\.studio-venv\Scripts\python.exe -m phase6.v14.evaluate --split development --selection .studio-artifacts/m14/reproduced-selection.json --output .studio-artifacts/m14/reproduced-development.json
.\.studio-venv\Scripts\python.exe -m phase6.v14.evaluate --split independent --selection .studio-artifacts/m14/reproduced-selection.json --output .studio-artifacts/m14/reproduced-independent.json
.\.studio-venv\Scripts\python.exe -m phase6.v14.evaluate --split exposed --selection .studio-artifacts/m14/reproduced-selection.json --output .studio-artifacts/m14/reproduced-exposed.json
.\.studio-venv\Scripts\python.exe -m phase6.v14.report
.\.studio-venv\Scripts\python.exe -m phase6.v14 example.c --provider combined
.\.studio-venv\Scripts\python.exe -m phase6.v14.validate
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v11 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v12 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v13 -t .
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v14 -t .
Push-Location studio
npm.cmd test -- --run
npm.cmd run build
Pop-Location
```

`report` regenerates from committed curated records; it does not automatically
replace them with your new timing measurements. For the historical reproduction,
use v13's report instructions (including its ingest step). `phase6.v14.audit`
consumes the preserved local v13 reproduction/private captures; the committed
root-cause ledger is the reviewable record made before implementation.

In separate terminals, start API/Vite as documented, then:

```powershell
python -m phase6.v14.browser_smoke --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

System Python needs Playwright; the browser smoke uses installed Chrome. Browser
screenshots/raw response programs remain local. See [validation evidence](phase6/v14/VALIDATION.md)
for exact test counts, skips, preservation and build results.

## Files and commit checkpoints

New `phase6/v14` modules: audit, dataset, providers, semantics, policy, engine,
evaluate, report, validate, CLI and browser smoke; three test modules; frozen
selection, source-free sample manifest and development/new/exposed/root-cause/
correctness/validation result records; protocol, root-cause, evaluation and
validation documentation. Integration edits touch API models/worker, frontend
API/types/Inspector and their tests. README and Studio developer docs describe the
new behavior. Earlier engines, benchmarks and acceptance artifacts are preserved.

- `b735ce0`: reproduce v13 and diagnose all 79 abstentions.
- `9484357`: adaptive engine and attributed candidate providers.
- `f69e5a1`: development-only calibration and frozen evaluation protocol.
- `fba3fcf`: Studio integration, backend/frontend tests and browser workflows.
- `2e395c1`: UTF-8 structural-risk location correction and regression.
- `e69f2b0`: corrected frozen evaluations, complete ledgers and rerun comparison.

Final evaluation/documentation commits appear in Git history. No push, merge or
external upload was performed. The engineering contribution is explicit evidence
routing, conservative hard gates and transparent compiler integration. The real-C
repair benefit is compiler-derived. Safe general intent recovery and a meaningful
selection advantage remain unresolved.
