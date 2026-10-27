# Phase 6 Milestone 6: targeted semantic evidence

Implemented under `phase6/v6/` and stopped for review. No commit, push, Milestone 7 implementation, original parser/CGAR change, earlier API change, software installation, C-program execution or sanitizer use.

## Audit and scope decisions

Branch/checkpoint verified: `feature/phase6-recovery`, `38a44fa`. The existing Extended C and v1–v5 architecture, v5's capability inventory, reports, paired controls and remaining miss were inspected before detector implementation. [INITIAL_AUDIT.md](INITIAL_AUDIT.md) records the decisions and the allocation investigation; [preimplementation_audit.json](outputs/preimplementation_audit.json) contains actual compiler/AST probes.

Installed Clang **17.0.2**, Android build 11349228/r487747e, supplies typed JSON ASTs with declaration IDs, physical offsets, implicit-cast kinds and builtin/format attributes. Adjacent/on-audit-PATH `clang-check`, `clang-tidy` and `llvm-config` were found; no adjacent libclang DLL was found. No dependency on those tools or Python libclang was introduced. Existing driver AST support was sufficient.

Frozen baseline cohorts were established **before implementation**: 34 initial fixtures and five additional boundary/value-flow fixtures, each analyzed through unchanged v5. Their 70- and 11-file hash manifests remain intact. The additional cohort tested a three-term condition and existing unreachable-code support, rather than manufacturing a new detector for an already available warning. All earlier historical references/baselines remain untouched.

Measured existing capabilities:

- Clang already warns for two-term contradictory comparisons and oversized scanf widths. GCC **6.3.0** supports `-Wlogical-op` for the simple contradiction when explicitly requested.
- Clang/GCC comparison warning flags and `-Wconversion` did not diagnose `x >= 5 && x <= 5 && x == 6`. Installed `alpha.deadcode.UnreachableCode` **did** diagnose its branch. V6 clean-probes this experimental checker and combines its actual evidence with a narrow AST condition proof.
- Default `deadcode.DeadStores` diagnoses the explicit overwritten assignment. Reusing it is not a new root. The initialization-only counterpart is not diagnosed in the measured configuration; no intent-based custom rule was added.
- Integer division implicitly converted to floating point and unbounded scanf `%s` receive no relevant measured baseline diagnostic. Their new outputs are **conditional review targets**, not automatically confirmed bugs.

## Implemented and omitted checks

| Check | Implementation and evidence level | Conservative exclusions |
| --- | --- | --- |
| Contradictory conjunction | Intersect typed signed-int constraints on one local declaration ID; attach compiler/unreachable-checker support when available | Unsigned/mixed conversions, volatile/atomic values, side effects, different IDs, macros, nonlocal/unsupported types; no general reachability claim |
| Fixed-buffer input | Included compiler-builtin/format-attributed scanf, one literal `%s`, direct local `char[N]`; compare width plus NUL to capacity | Local lookalikes, unknown capacity, pointers/aliases, indirect calls, arbitrary formats, scansets, multiple conversions, `%c`, wide input; report risk only |
| Integer division into floating context | Direct `IntegralToFloating` AST conversion of supported integer quotient; explain operand/result/conversion types | Explicit casts, exact constant division, integer-only consumers, macros, volatile/side-effecting operands and known zero divisor; intent remains unknown |
| Value-flow | Keep existing upstream dead-store diagnostics | No name-based swap rule, general alias/value-flow inference or initialization-intent detector |

All custom scanning requires accepted frontend output and validated physical main-file function ranges. Invalid/recovery AST regions are never treated as verified. AST traversal, finding, conjunction, command, analyzer and runtime budgets are explicit. Source ranges, backend identity, confidence, eligibility and conditioning are retained. See [README.md](README.md) for the versioned JSON contract, CLI/API, budgets and precise whitelist.

## Reviewed comparison: roots, risks and duplicates

The new local reference contains **four structural evidence units** and **four conditional input/intent review targets**. It does not redefine historical defect totals or assert programmer intent. Source/hash binding, diagnostic identifier/meaning, admissible anchors and named agent review are enforced by the unchanged v1 evaluator. Independent human adjudication remains pending; precision/recall values are deliberately null.

| Evidence unit | Frozen v5 baseline | V6 |
| --- | --- | --- |
| Two-term contradiction | Already diagnosed | Same root; duplicate linked |
| Contradictory comparison boundary | Already diagnosed | Same root; duplicate linked |
| Three-term contradiction | Missed by existing profile | **New source-reviewed structural root** |
| Explicit overwritten assignment | Already diagnosed by default analyzer | Reused; no new-root credit |
| Oversized scanf `%s` width | Existing capacity warning; input contract unknown | Remains conditional, not confirmed overflow |
| Unbounded scanf into fixed array | No capacity diagnostic | New conditional review target |
| Implicit integer quotient in floating context | No relevant diagnostic | New conditional intent-review target |
| Non-exact constant quotient in floating context | No relevant diagnostic | New conditional intent-review target |

Thus established structural units move **3 → 4**, with **one new root, `ROOT-condition_three`**, no lost roots, and **four conditional outcomes remaining conditional**. The new root is the empty interval for `x >= 5 && x <= 5 && x == 6`; installed Clang's experimental unreachable checker independently reports the branch. This is a verifiable predicate fact, not proof that deliberate unreachable code is always a programmer mistake.

Of four semantic review suggestions, one (width plus NUL exceeding capacity) duplicates existing compiler evidence; three are new suggestions. None is promoted to an unconditional bug. The export/evaluator retains one additional-backend/AST duplicate as **one** reviewed root, not two. Two already diagnosed condition findings and the existing width warning are explicitly marked duplicate rather than increasing detection totals.

No unexpected semantic findings appeared on the **31 other controls/investigation sources** in the 39-fixture corpus. These include corrected/legitimate forms, macro and qualifier cases, unknown capacities, deliberate conversions, malformed input and allocation probes; they are not all asserted bug-free programs. Confirmed false-positive groups: **0**, but the evidence corpus is small and agent-reviewed. Eleven backend primary records remain unadjudicated/outside the local root reference: allocation diagnostics, signedness, malformed-source compiler/analyzer errors, zero-division warnings, an unused parameter and an unsupported unsigned contradiction. They are not silently classified as false positives or erased. Six notes remain context, and the reviewed duplicate is not an independent defect.

Evidence: [comparison.json](outputs/comparison.json), [baseline_evaluation.json](outputs/baseline_evaluation.json), [configured_evaluation.json](outputs/configured_evaluation.json), and [reference.json](reference.json). The review manifests bind to exact dataset/evidence fingerprints. Reported counts are provisional source review, not independently verified population precision/recall.

## Allocation-width investigation

The v5 miss remains unresolved. Raw evidence distinguishes these cases:

1. `int *p=malloc(1); ... *p=1`: no compiler/analyzer diagnostic.
2. `malloc(sizeof(char))` with the same store: `unix.MallocSizeof` reports incompatible operand/type.
3. `malloc(1)` followed by `p[1]=1`: `alpha.security.ArrayBoundV2` reports bounds error.
4. `malloc(sizeof *p)` with the scalar store: corrected control, no finding.

Additional measured `-Wconversion` configurations also did not report the literal-size case. This rules out **diagnostic matching** as the explanation and shows that the installed enabled profile has a source-structure-sensitive gap. It does not establish the exact internal analyzer mechanism or exclude every possible future configuration. A start-offset-versus-access-width limitation is a hypothesis, not a measured implementation fact. No custom allocation-size detector was added without a reliable target/extent/alias proof.

## Eligibility and conditioned cohorts

Both frozen and configured corpora have 37 successfully completed source profiles and two malformed cases. V6 explicitly reports the latter as **blocked**, without custom AST findings; baseline v5 analyzer statuses were partial. No completed function/path exploration is inferred from process completion.

Separately enabled v4 isolation makes the independent function in the malformed semantic case eligible and produces one isolation-conditioned condition fact. The protected v3 null fixture also validates a repaired upstream snapshot without adding an unrelated semantic finding. Neither cohort enters the unconditional reference score.

Two additional private CRLF checks verify actual findings across provenance combinations: a repaired integer-division suggestion is repair-only; a repaired broken function plus isolated independent condition produces one finding with **both repair and isolation flags true**. Original ranges remain valid, temporary inputs/variants are removed and baseline source rejection remains exit 1. See [provenance_checks.json](outputs/provenance_checks.json). No replacement values, bodies, arguments or semantics are invented by v6. Source maps distinguish snapshot ranges from original ranges, including exclusive endpoints at generated semicolons.

## Unchanged 500-line benchmark

Cleaned SHA-256 remains `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`. Original numbered source and previous research results are unchanged.

| Run | Compiler / memory evidence | Semantic result |
| --- | --- | --- |
| Baseline compiler | 7 errors, 12 warnings, 11 notes | Not requested |
| Current v5 memory profile, embedded in semantic run | Same compiler counts; analyzer partial, no memory observation | Frontend blocks v6 custom scanning |
| V6 enabled | Same accepted/rejected source state | **Blocked, zero new semantic facts/targets** |
| Explicit recovery + requested isolation + v6 | Two accepted v3 semicolons; 5 errors, 14 warnings, 12 notes; memory analyzer partial | Isolation abstains on preprocessing whitelist; repair-conditioned snapshot still frontend-rejected, zero semantic findings |

No actual benchmark eligibility or new root improvement is claimed. Remaining return/call/identifier blockers still produce five diagnostics, including cascades; raw error count is not independent defect count. V4's macro/global safety policy was not relaxed, and no benchmark-specific detection rule was introduced. The fresh v5 evidence is retained in [benchmark_v5_current.json](outputs/benchmark_v5_current.json), extracted from the actual semantic-run upstream report rather than counted as a separate duplicate execution. Historical 16/68 and v1/v5 scores are not replaced.

## Testing and measured execution

**413 tests passed; 0 failures, 0 errors, 0 skips**, in **224.547 seconds** (external supervisor 224.828 seconds, 480-second limit). This includes all 385 prior tests plus 28 v6 tests: 16 policy/evaluation/CLI tests and 12 live integration methods. Targeted tests ran first. Final results/logs: [tests.json](outputs/tests.json), [full.txt](outputs/full.txt), [full.supervision.json](outputs/full.supervision.json).

Tests exercise signedness, qualifiers, identity, side effects, conjunction budgets, NUL accounting, unknown capacity/callee, suppression, exact/zero division, explicit casts, malformed AST/frontend, macro abstention, duplicate handling, checker unavailability without fabricated evidence, timeouts/budgets, Windows paths/spaces/Unicode/CRLF, provenance and half-open mapping boundaries. The existing suite also exercises actual subprocess timeout cleanup. Unsupported optional checker state is reported; no installed-Clang test was skipped.

GCC **6.3.0** compatibility checks confirm disabled-profile valid-C analysis exits 0 and explicit Clang-only semantic analysis exits 3 with a clear reason, without an uncaught CLI traceback. No modern GCC capability was assumed. See [gcc_checks.json](outputs/gcc_checks.json).

| Completed evidence cohort | Source reports | Combined compiler commands | Analyzer driver commands | Sum of source-report seconds |
| --- | ---: | ---: | ---: | ---: |
| Frozen baseline | 39 | 752 | 85 | 94.217 |
| Configured semantic cohort | 39 | 852 | 152 | 88.628 |

Counts include discovery, capability, inventory and auxiliary AST operations, not just source passes. Additional preimplementation warning/AST probes have their own command logs. Timing differences reflect caching/scheduling and are **not a speedup claim**. [execution_summary.json](outputs/execution_summary.json) records every source. The resumed comparison batch took 82.578 seconds and reused eight verified completed artifacts; totals include those artifacts' actual completed measurements.

Benchmark compiler baseline: 15 commands, 1.688 seconds. V5-backed semantic request: 30 commands, 4.000 seconds. Explicitly conditioned request: 46 commands, 8.750 seconds. Compiler baseline exits 1 for source errors; requested semantic runs exit 3 for blocked analysis.

## Interruption and validation failures

The first comparison loader rejected a summary-list JSON artifact because it assumed every JSON was a dictionary. It was fixed by filtering report envelopes; no detector, test expectation or acceptance rule was weakened. The failure log remains [compare_loader_failure.txt](outputs/compare_loader_failure.txt).

The next comparison was interrupted between turns. Its supervisor recorded 694.656 seconds against a 240-second deadline, and a case reported runtime exhaustion. No relevant processes remained when resumed. All protected hashes matched. **The exact cause of this timing anomaly is unestablished**; these numbers do not prove an infinite detector/compiler loop, and are excluded from completed-case performance claims. The same case passed a short 20-second internal / 35-second external rerun in 2.704 seconds. Interrupted logs remain [compare_interrupted.txt](outputs/compare_interrupted.txt) and [compare_interrupted.supervision.json](outputs/compare_interrupted.supervision.json).

Comparison was resumed with verified completed results and separate 30-second internal / 45-second external child processes for remaining cases. Failed reports are now written before batch assertions. No failing test or case was silently omitted. OS scheduling/suspension, filesystem operations and finite cleanup grace are not hard real-time guarantees, even with bounded process waits. Subsequent comparison, benchmark and full-regression stages completed normally.

## Preservation and exact files

All **799 protected pre-v6 files** retain their hashes, including original SmartParse/CGAR, Extended C, v1–v5, old fixtures, source benchmark, historical references and acceptance outputs. The two v6 frozen manifests separately retain all **81 bound files**. All **17 historical CSVs** retain their exact bytes. The legacy performance test writes `results/verified_performance.csv`; the runner restores its prior bytes in `finally` and discloses the write in [preservation_full.json](outputs/preservation_full.json). File timestamps are not claimed unchanged. Earlier acceptance runners were not invoked.

Created implementation/document files: `__init__.py`, `__main__.py`, `detectors.py`, `engine.py`, `evaluation.py`, `test_semantics.py`, `run_validation.py`, `reference.json`, `INITIAL_AUDIT.md`, `README.md`, this report; 39 new C fixtures; and versioned audit/frozen/configured/benchmark/test/preservation outputs. All are under `phase6/v6/`. No pre-existing implementation file was modified. [added_files.json](outputs/added_files.json) is the exact non-bytecode file inventory; [acceptance_summary.json](outputs/acceptance_summary.json) provides final machine-readable verification.

## Limitations and recommended next priorities

The detector whitelist is deliberately small. General pointer/value flow, signed/unsigned conversion reasoning, aliases, nonlinear expressions, dynamic buffer capacities, arbitrary format strings, input contracts, programmer intent, concurrency and general logic correctness are not established. Experimental backend warnings can be incomplete or wrong; only the narrow independently checkable source facts are admitted. External header trees/build environment are not frozen against concurrent modification. Missing diagnostics and completed scans never prove safety.

Recommended Milestone 7 priorities, **not implemented here**:

1. Independent human adjudication and broader separately frozen holdouts, including legitimate deliberate truncation/unreachable code and modeled library replacements.
2. A reviewed target-ABI/access-width/extent/alias design for the remaining literal allocation miss, with positive/negative evidence before adding any custom rule.
3. Explicit input-capacity and fractional-result contracts so suggestions can be resolved without guessing intent from names.
4. Carefully evaluated type/conversion coverage and context-preserving macro/global eligibility improvements, without relaxing existing recovery/isolation safeguards merely to raise benchmark totals.
