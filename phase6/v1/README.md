# Phase 6 v1 — Milestone 1: reference and evaluation model

Scope: evaluation only. No source repair, compiler recovery, new defect detector,
or original SmartParse/CGAR change is implemented. Everything new is under
`phase6/v1/` except the empty parent package marker needed for test discovery.

## Frozen baseline and new reference

The original 68-entry oracle, historical 16/68 Clang comparison, GCC/Clang reports,
all Phase 5 acceptance files, existing C fixtures and 17 research CSVs remain
unchanged. `outputs/preimplementation_hashes.json` records 194 readable existing
files, including the external numbered original. Git metadata, bytecode caches,
and inaccessible empty temporary directories are outside that manifest's scope.
The full-suite runner verifies these hashes and restores legacy CSV test writes
in `finally`. It does not regenerate any Phase 5 acceptance artifact.

`reference.json` has schema version **1.0**, dataset version **1.0.0**, and **76
atomic issues**. Each has a stable version-local ID, historical entry/line,
primary category and secondary tags, logical source ID and source content hash,
source/sink lines, admissible diagnostic anchors, triggering conditions, required
contracts, oracle status, required analysis, evidence-meaning rules, review
provenance, root-cause ID, and relationships. Locations are physical line numbers
in the unchanged cleaned source; the logical source/hash disambiguates files.
Column/range evidence can be retained in diagnostics but is not required by this
line-anchored reference. An unrelated file with the same basename cannot match.

The migration is reproducible using `build_reference.py`; it is **a documented
manual migration, not automatic source understanding**. All reference decisions
are provisional, single-agent source review; independent human oracle review is
still required. Rebuilding deliberately invalidates reviews if metadata changes.

| Historical line | New atoms | Reason for separation |
|---|---:|---|
| 55 | 2 | Writes to students and read of scores concern different objects; share one erroneous loop-bound root |
| 71 | 2 | Invalid free at 70 and later expired-stack-pointer use at 71 differ; both relate to the producer at 129 and share its root |
| 104 | 2 | Suspicious assignment and downstream null dereference require different evidence |
| 278 | 2 | Failed-open/null-stream use differs from uninitialized return after failed conversion on a valid stream |
| 317 | 2 | Intended factorial-loop behavior differs from signed arithmetic overflow on entered-loop paths |
| 432 | 3 | Allocation extent, allocation failure, and loss of prior ownership have different triggers |
| 439 | 2 | Write after successful release differs from a null write in initial global state |

Other entries are retained as one atom unless a justified split was made. A
reference version is not a claim of exhaustive ground truth. For example, using
a source operation after an earlier undefined operation is evaluated as a local
potential issue, not evidence that a valid whole-program execution reaches it.

## Outcome semantics and precedence

Every issue retains evidence, coverage and contract axes as well as one primary
outcome. Primary outcome precedence is explicit:

1. `uncertain` when reference intent/environment itself is unresolved, even if a warning matches.
2. `conditional` when a required contract has not been established or has been refuted.
3. `detected` only for admissible evidence explicitly accepted by an attributed reviewer, with established applicability.
4. `uncertain` for unreviewed compatible evidence or an ambiguous review.
5. `missed` when an applicable supported analysis was declared completed but no accepted evidence exists.
6. `blocked` when the applicable analysis could not complete and no completed applicable pass exists.
7. `unsupported` when all declared applicable passes lack an enabled supported check.
8. `uncertain` when coverage itself is unknown.

The report still includes underlying coverage and contract decisions, so a
conditional issue does not hide the fact that its analyzer pass was blocked.
Refuted contracts have `applicability: excluded_by_contract` and must not enter a
false-negative denominator. `compiler completed` is an operational declaration,
not proof that every possible warning was evaluated. Coverage is supplied as an
explicit evaluation annotation; the evaluator cannot independently prove tool
exploration completeness.

Floating behavior at 382 remains uncertain; its primary UB-category placement
does not assert that floating division is integer division-by-zero UB. Missing
return at 405 now explicitly requires a consumer using the absent value on the
nonpositive path. It is conditional until that contract is reviewed. This does
not erase the historical Phase 5 miss recorded under the older reference.

## Evidence matching and review

`evaluation.py` consumes stored diagnostics; it never invokes compilers. A
candidate requires:

- An exact reported-path binding to a logical source with the expected content hash.
- An admissible source anchor (not an arbitrary proximity window).
- A supported backend/severity and, when specified, diagnostic identifier.
- All configured message-meaning predicates, not severity/line alone.

Rules are conservative wording filters. They do not prove semantics or programmer
intent. An agent or human reviewer must accept a specific evidence-to-atom link
with reviewer identity and rationale. Notes alone, a producer's escaping-address
warning used to claim a later use, or an undeclared-name cascade used to claim an
allocation defect are inadmissible. One diagnostic cannot silently confirm two
atoms. Unrecognized wording remains unmatched/unknown rather than false.

Reviews are bound to fingerprints of the entire dataset and evidence manifest;
stale reviews are rejected. A contract decision separately requires a reviewer,
rationale, and `satisfied`, `unknown`, or `refuted` state. No application contracts
are silently marked satisfied in the supplied review.

A reviewer can accept genuinely equivalent new wording using an explicit
`semantic_override` containing a claim and evidence explanation. This is stored
as a human/agent judgment, not automatic certainty. Source/hash binding, allowed
backend/severity, anchor scope, and the prohibition on note-only confirmation
still apply. Without that explicit override, incompatible wording cannot be
promoted merely by setting `decision: match`.

Evidence is retained across backends and compiler/analyzer passes. Exact repeated
records within a pass are recorded as duplicates, while per-atom and unique
root-cause summaries prevent inflation from repeated warnings or multiple tools.
The root relationships are themselves provisional review decisions, not an
automatic universal root-cause clustering algorithm.

Finding adjudications are independent of issue outcomes:

- `unknown`: unlisted/unresolved finding; **not** a false positive.
- `false_positive`: explicit reviewed false claim, with rationale and a finding-group ID for duplicate accounting.
- `cascade`: secondary compiler-recovery evidence, not a new confirmed defect.
- `non_defect`: reviewed suspicious-but-legal construct.
- `duplicate`: reviewed duplicate with an existing evidence target.
- `context_note`: supporting context, never a standalone defect or false positive.

`reviewed_support` does not always mean a true positive: it may support a
conditional/uncertain reference. A warning correctly identifying an intentional
assignment is not automatically a false compiler diagnostic. False-positive
judgments must concern the actual claim made by a tool.

## Outputs and reproduction

```powershell
python -m phase6.v1.evaluate_saved
python -m phase6.v1.evaluate_saved --review phase6/v1/assisted_review.json
python -m unittest phase6.v1.test_evaluation -v
python -m phase6.v1.run_tests --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe"
```

Use normal user access for live analyzer tests: the agent's restricted Windows
token cannot traverse `TemporaryDirectory`'s private ACLs. The approved full run
therefore uses execution outside that sandbox. PATH is adjusted only in the test
process and its children. No software is installed, and no C binary is executed.

- `outputs/evaluation_unreviewed.json`: no automatic detections; compatible evidence awaits review.
- `assisted_review.json`: 42 explicit evidence links plus four cascade adjudications, authored by Codex assisted review; **not independent human approval**.
- `outputs/evaluation_reviewed.json`: reproducible assisted-review example, with category/outcome counts, source-bound evidence, provenance, applicability, and finding adjudications.
- `outputs/tests.json`, `tests.txt`, `preservation.json`: new test/preservation evidence only.

With the assisted review the 76 issues are **12 detected, 0 missed, 20 blocked,
1 unsupported, 22 conditional and 21 uncertain**. Categories and unique roots
are reported separately. The four previously credited assignment-condition
warnings stay matched evidence but no longer establish comparison intent, hence
12 rather than 16 detected. The new atomic denominator, applicability rules,
and review standard differ: **12/76 must not be compared as detector recall to
historical 16/68**. Zero primary misses does not mean zero undetected defects;
blocked, conditional, and uncertain issues remain explicitly present.

The unreviewed report has zero detected, 20 blocked, one unsupported, 22
conditional, and 33 uncertain. This intentionally demonstrates that a regex match
cannot certify detection. In that report, 46 non-note observations are unknown,
not 46 confirmed false positives. The assisted report has 16 context notes and
four cascade records; those are not independent confirmed defects. No real
false positives have been independently adjudicated. Synthetic independent tests
exercise false-positive decisions and duplicate finding groups.

Precision and recall remain JSON `null` with an explanation: this oracle is
non-exhaustive and independently adjudicated truth/negative controls are still
pending. This milestone supplies accounting and review mechanisms, not a new
accuracy claim, new detector, or repaired-source analysis.
