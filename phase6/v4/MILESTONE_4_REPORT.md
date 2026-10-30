# Phase 6 Milestone 4: experimental unaffected-region analysis

Implemented as a separate, explicitly enabled experiment under `phase6/v4/`. Stopped for review; no commit, push, new detection rules, optional external analyzers, or further milestone work.

## Architecture and preserved behavior

The original SmartParse/CGAR, Extended C, Phase 5, Phase 6 v1–v3, source fixtures, reference datasets, and historical acceptance outputs were not edited. The v4 entry point composes v3 without changing its API. Original compiler diagnostics stay in the nested immutable recovery report; original-source analyzer completion/findings are stored separately from all isolation results. Static-analysis findings belong to Clang Static Analyzer, not CGAR. Historical 16/68 and later reference comparisons are not rescored.

Only whole physical AST function ranges can be omitted. The private variant replaces their non-newline bytes with spaces, preserving source size, CRLF, line numbers and byte offsets. No replacement function body, return value, argument, cast, declaration or allocation/condition change is introduced. Optional preceding v3 punctuation edits have their own explicit flag and provenance; original-location mappings compose both stages.

The selected Clang validates syntax without generating an executable, checks the VFS overlay's filename identity, and supplies physical AST evidence. Frontend error locations assign blockers to function bodies, not analysis coverage. Callers and address-takers of excluded definitions are transitively excluded; no missing definition is treated as an invented opaque function. Main-file globals, unsafe macros, indirect calls, persistent/external local state, unsupported attributes, header dependencies into main definitions, signature/header errors, unreliable ranges and unknown dependencies cause abstention. Build flags, includes and macro definitions are retained. Compiler acceptance, preprocessing consistency outside exclusions, and identical retained AST boundaries/function references are required before the analyzer runs.

One isolation variant is permitted. Default limits are 8 exclusions, 64 combined compiler invocations, 5 analyzer driver invocations including probes, 120 seconds combined recovery/isolation deadline and 10 seconds per process. Hard ceilings are documented in [README.md](README.md). Timeouts use the v3 finite file-backed capture/owned-process-tree cleanup. There is no shell invocation or execution of the user's C program. Private files are cleaned on all exit paths. Deadlines are checked before and after subprocess work; finite cleanup grace and Python/filesystem processing do not constitute hard real-time or hostile-input sandbox guarantees.

## Automated verification

The final full suite passed **363 tests, 0 failures, 0 errors, 0 skips**, in **216.531 seconds** (external supervisor 217.157 seconds, 300-second limit). Evidence is recorded in [outputs/tests.json](outputs/tests.json), with complete [test output](outputs/tests.txt) and [external supervision](outputs/suite_supervision.json). All existing 334 tests and 29 new v4 tests are included: 13 policy tests and 16 live integration methods.

Targeted tests ran first with external 20-second policy and 35-second per-live-method deadlines. An initial complete regression passed 362/362; final review then added a malformed diagnostic-location regression and a safeguard that clears findings/eligibility when source mapping fails. The complete suite was rerun for the final implementation; the final exact counts, errors and skips in `tests.json` are authoritative.

Coverage includes physical name/range validation, macro boundaries, global initialization, shared boundary lines, dependency closure, no independent functions remaining, exclusion/invocation/analyzer budgets, unknown and signature diagnostic locations, preprocessing changes/malformed markers, CRLF/Unicode/space-containing paths, disabled-by-default behavior, analyzer findings/provenance, duplicate/excluded warning suppression, partial analyzer output, malformed ASTs, injected timeout stops, and invalid finding mappings. Embedded eligibility is checked against v2's conservative contract.

The 12 supervised CLI cases in [outputs/cases.json](outputs/cases.json) passed expected exit codes, preservation, cleanup and budget checks. Two additional GCC compatibility checks passed in [outputs/gcc_checks.json](outputs/gcc_checks.json).

A further 35-second-supervised private CRLF composition check passed: v3 inserted a missing return semicolon, v4 excluded the still semantically blocked function, and the unrelated function's analyzer warning mapped to original **9:12**, byte offset 127. Both `repair_conditioned` and `isolation_conditioned` are true; the baseline still contains the two original errors. The run used 34 combined compiler invocations and 4 analyzer driver invocations, taking 7.860 seconds internally. Its temporary input and variant were removed. This is an additional end-to-end check, not an extra unittest or a new benchmark defect. Evidence: [composition_check.json](outputs/composition_check.json), [composition.json](outputs/composition.json).

Live compiler versions:

- Clang **17.0.2**, Android build 11349228/r487747e, installed at `C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe`.
- GCC **6.3.0**, `gcc.exe (MinGW.org GCC-6.3.0-1) 6.3.0`. Baseline valid-C analysis exited 0; explicitly requested isolation correctly abstained with exit 3 because no GCC isolation adapter exists.

No software was installed.

## Independent region and dependency results

| Program | Exclusions / decision | Analyzer eligibility | Additional unique primary warnings |
| --- | --- | --- | ---: |
| `independent.c` | Exclude `broken`, lines 1–4, for undeclared identifier/recovery AST body; retain `independent`, lines 5–9 | Original analyzer partial; isolated variant completed | 1 |
| `dependent.c` | Exclude `broken`, lines 1–4, and `caller`, lines 5–8, because caller depends on broken; retain `independent`, lines 9–13 | Original analyzer partial; isolated variant completed | 1 |
| `all_dependent.c` | No independent function survives dependency closure; no variant | Abstained | 0 |
| `global_blocker.c` | Main-file global initialization/error | Abstained | 0 |
| `global_initialization.c` | Main-file global state retained by dependent function | Abstained | 0 |
| `macro.c` | Main-file macro directive outside whitelist | Abstained | 0 |
| `header_macro.c` | Header macro expansion in retained function AST | Abstained | 0 |
| `indirect.c` | Indirect callback dependency not resolvable | Abstained | 0 |
| `malformed.c` | Inconsistent physical body boundaries | Abstained | 0 |
| `valid.c` | Frontend already accepted; no omission needed | Original analyzer completed; no new eligibility gain | 0 |

Successful independent isolation used **27 combined compiler invocations, including 4 analyzer driver invocations**. Measured case durations: 7.078 seconds for `independent.c`, 7.375 seconds for `dependent.c`. Excluded names/ranges, reasons, original-byte mappings and dependency assumptions appear in each machine-readable report. No exclusion is claimed to have been analyzed. Retained function/path coverage remains **unknown**, even when the isolated translation-unit analyzer invocation completed.

Actual additional Clang findings:

| Source | Original location | Checker | Message |
| --- | --- | --- | --- |
| `fixtures/independent.c` | 8:12 | `core.NullDereference` | Dereference of null pointer (loaded from variable 'pointer') |
| `fixtures/dependent.c` | 12:12 | `core.NullDereference` | Dereference of null pointer (loaded from variable 'pointer') |

Each warning has two supporting notes. Those notes do not add detections. These are two program-level observations of the same intentionally repeated fixture pattern, **not two new benchmark/reference defects**. Fixture inspection supports the warning: the retained body initializes its local pointer to zero and dereferences it, with no dependency on the omitted function. Nevertheless reports keep the result isolation-conditioned and unreviewed as an original-program defect; automated processing does not assert semantic certainty.

Unique identity uses original file, line, byte column, checker identifier and message. Exact repeated warnings collapse within a variant and are compared against baseline/recovery evidence. Warnings outside retained main-file functions, and traces touching excluded spans, are not counted. Different checker/messages can still represent the same cause; manual adjudication remains necessary. No precision/recall improvement is claimed from fixture warning counts.

## Cleaned 500-line benchmark

Source SHA-256 remains `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`. Both direct isolation and explicitly enabled v3-then-isolation were evaluated without editing the original or cleaned source.

| Run | Original compiler diagnostics | After optional punctuation recovery | Isolation outcome |
| --- | --- | --- | --- |
| Direct | 7 errors, 12 warnings, 11 notes | Not enabled | Abstained: unsupported main-file preprocessing directives |
| v3 then isolation | Same original baseline | Two accepted semicolons, lines 30 and 82; 5 errors, 14 warnings, 12 notes | Same conservative abstention |

Original compiler diagnostic records are identical to the preserved v3 benchmark baseline. The remaining semantic errors concern the return at line 393, invalid call at 409, undeclared identifier at 414/415 and its cascading conversion diagnostic. They are not treated as five independent defects. Main-file macro definitions appear at lines 14–16, and globals at lines 30–32 provide additional unsupported context for this initial isolation policy.

**No isolation variant was admitted, no functions were excluded, no analyzer coverage improved, and no additional isolation-supported benchmark finding was measured.** Function eligibility remains blocked/unknown under the existing conservative model. Original-source analyzer completion was partial. This is a safety abstention, not evidence of bug freedom or absence of potentially unaffected functions.

Measured direct case: 5.094 seconds, 21 total compiler invocations, 3 analyzer invocations including probes. v3-then-isolation: 8.422 seconds, 32 total compiler invocations, 3 analyzer invocations. Both exited 3 to signal unfulfilled requested isolation; original compiler errors and independent statuses remain available in JSON. Fewer compiler errors alone are not an eligibility improvement.

## Preservation and changed files

All additions are under `phase6/v4/`:

- `engine.py`, `policy.py`, `__main__.py`, `__init__.py`: opt-in pipeline, AST/dependency admission, temporary variant validation, reporting and CLI.
- `test_isolation.py`: 29 independent policy/live tests.
- `run_validation.py`: externally supervised targeted, full-suite and case stages, with preservation checks.
- `fixtures/`: 10 new independent C fixtures and one macro header. Existing fixtures are untouched.
- `README.md`, this report, and `outputs/`: schema/usage, measured test/case/GCC results, baseline/variant evidence, supervision logs and preservation hashes.

No pre-existing implementation file or historical report was modified. Preservation inventories cover **598 pre-v4 files**, including the original numbered source outside the workspace, all readable prior acceptance artifacts and v1–v3 outputs. All **17 historical CSVs** retain their exact bytes. The legacy regression suite writes `results/verified_performance.csv`; the runner snapshots and restores that file's original bytes in `finally`, explicitly disclosing it in [preservation_full.json](outputs/preservation_full.json). Targeted/case checks performed no historical CSV writes. Protection covers file bytes, not filesystem timestamps or a concurrent external writer.

## False-positive risks and unresolved limitations

Removing a definition changes the translation unit. A warning on an unchanged retained body can depend on lost interprocedural context, caller constraints, external calls/contracts or unseen build state; it is a conditional observation until reviewed. No runtime execution or original-program correctness proof is claimed. The policy avoids known direct dependencies and global/macro hazards but is not a complete C dependency/semantic proof.

The initial policy deliberately sacrifices coverage: all main-file globals and most preprocessing are rejected even when some could be shown safe by a future, separately reviewed analysis. External header trees are not snapshotted; preprocessing/AST checks detect many changes but cannot eliminate races. Clang version differences can force abstention; only installed Clang 17.0.2 received live validation here. Unsupported analyzer checks or zero observations do not prove safety. Complete per-function/path analyzer execution evidence is unavailable.

There are no fabricated replacement semantics, new defect rules or optional analyzers. Benchmark detection remains unchanged; historical reference baselines remain separate. Broadening macro/global-state support or interprocedural assumptions requires new evidence and review, not an automatic relaxation to increase warning counts.
