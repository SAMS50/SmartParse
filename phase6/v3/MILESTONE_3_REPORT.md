# Phase 6 Milestone 3: resumed implementation and validation

Status: implemented and tested; stopped for review. No commit, push, Milestone 4 work, or final release acceptance.

## Recovery of interrupted work

The existing engine, byte-oriented policy, budget model, CLI, tests, fixtures, initial benchmark capture, and protected hash inventory were inspected and retained. Nothing was restarted or reverted. Initial checks used only the small relevant tests under explicit deadlines, before full discovery. Native process inspection found no lingering Python/Clang/GCC processes at that time; detailed CIM process inspection was denied by Windows permissions. No recursive discovery failure or unbounded candidate loop was observed.

**The earlier hour-long wall time has no established root cause.** The retained initial benchmark capture records 2.438 seconds and 26 compiler invocations, with its slowest call about 0.141 seconds. It does not substantiate an hour-long compiler hang. Inspection identified a possible inherited-output-pipe wait in Python's Windows subprocess timeout cleanup. The new execution wrapper uses regular-file output capture and finite owned-process-tree cleanup, avoiding that wait. A real parent/grandchild timeout test verifies bounded return. This is preventive hardening, not a claim that the previous run's cause has been proven.

All discovery, capability probes, compiler checks, AST inventories, preprocessing, and analyzer runs now share the same invocation/deadline accountant. Validation additionally runs each targeted live method, the full suite, and CLI cases under external supervision with captured progress logs. No validation command timed out during the measured run.

## Measured verification

Environment: Windows, Python 3.12.5; selected live recovery backend **Clang 17.0.2**, Android build 11349228/r487747e, executable `C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe`. Existing GCC 6.3.0 regressions remain included. No software was installed.

| Check | Result |
| --- | --- |
| Complete automated suite | **334 passed, 0 failures, 0 errors, 0 skipped** |
| Suite duration | 91.672 seconds; external supervisor 91.953 seconds, 240-second limit |
| Existing tests | 300 passed, including original SmartParse/CGAR and Phase 5/v1/v2 |
| New v3 tests | 34 passed: 21 policy/budget tests and 13 live integration methods |
| Independent CLI/case validation | 14 cases, expected exit codes, report invariants and cleanup passed |
| Protected pre-v3 files | 260 checked; no final byte differences |
| Historical CSVs | All 17 retain original bytes |
| New v3 fixtures | No byte differences during validation |

Evidence: [tests.json](outputs/tests.json), [tests.txt](outputs/tests.txt), [suite supervision](outputs/suite_supervision.json), [case summaries](outputs/cases.json), [preservation](outputs/preservation.json). Targeted logs also retain per-method deadlines and output. The legacy performance regression rewrote `results/verified_performance.csv`; the preservation runner restored the snapshotted bytes in `finally`. This is disclosed in `legacy_csv_writes_restored`, rather than claiming the old test performed no write. Recovery itself never writes original sources or historical artifacts.

Tests cover disabled-by-default behavior, machine fix-its, Windows escaped/Unicode/space-containing paths, CRLF and byte mapping, ambiguous AST nodes, macro/header rejection, unknown encoding and presumed-line directives, non-semicolon/nonzero ranges, expressions/semantic assumptions, all policy budgets, elapsed deadlines, timeout latching, actual inherited-output timeout behavior, binary capture, compiler-new-error rejection, preprocessing-change rejection, and real analyzer provenance. Supporting analyzer notes are not independent defects.

## Cleaned 500-line benchmark

The existing cleaned source remains unchanged: SHA-256 `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`. The original numbered source and existing acceptance artifacts also remain protected. Disabled/enabled recovery runs produced identical baseline analysis hashes: `681fd27d465e339b91faf4c6bfb01be02c2c06576e2f246da675152b51d0e180`.

| Candidate | Original location | Edit | Decision |
| --- | --- | --- | --- |
| C1 / V1 | Line 30, byte column 21, byte offset 691 | Insert `;` after `int global_count = 0` | Accepted |
| C2 / V2 | Line 82, byte column 13, byte offset 2225 | Insert `;` after `return 0` | Accepted |

Both edits have compiler machine fix-its, unique physical AST boundaries, strict compiler error-subset validation, preprocessing-token validation, cumulative hashes and byte maps. No benchmark candidate was rejected; exploration stopped when the remaining blockers required semantic assumptions. Baseline: **7 errors, 12 warnings, 11 notes**. Last temporary variant: **5 errors, 14 warnings, 12 notes**. These are observations, not counts of unique defects. No historical 16/68 or v1 evaluation score was changed.

**Actual eligibility did not improve on this benchmark.** Both syntax errors were removed, but the frontend still rejected the variant. Baseline analyzer completion was partial; intermediate variants remained blocked and the analyzer was not rerun on them. No repair-conditioned analyzer findings were produced. No function/path coverage was certified. The five remaining compiler errors are:

| Line | Compiler message |
| --- | --- |
| 393 | incompatible pointer to integer conversion returning 'char[6]' from a function with result type 'int' |
| 409 | too few arguments to function call, expected 2, have 1 |
| 414 | use of undeclared identifier 'mystery_value' |
| 415 | use of undeclared identifier 'mystery_value'; did you mean 'last_value'? |
| 415 | incompatible pointer to integer conversion returning 'int (int *, int)' from a function with result type 'int' |

The two line-415 observations may be recovery/cascade-related; they are not asserted to be two independent defects. The benchmark repair run took **7.797 seconds, 29 compiler invocations**, slowest invocation **0.734 seconds**. Baseline-only took 3.171 seconds and 18 invocations. Both CLI exits were 3 because requested static analysis did not complete; the source errors and independent completion states remain in JSON.

## Independent cases

| Case | Candidates / decision | Actual eligibility |
| --- | --- | --- |
| `positive_declaration` | 1 accepted | Frontend newly accepted |
| `positive_return` | 1 accepted | Frontend newly accepted |
| `positive_analyzer` | 1 accepted | Frontend newly accepted; analyzer newly completed |
| `positive_two` | 2 accepted, sequential rounds | Frontend newly accepted |
| `unicode_crlf` | 1 accepted | Frontend newly accepted; byte/CRLF preservation verified |
| `negative_unbraced` | 1 rejected: no unique admissible AST boundary | Remains blocked |
| `negative_macro` | 1 rejected: no unique admissible AST boundary | Remains blocked |
| `negative_header` | 1 rejected: fix-it outside main source | Remains blocked |
| `negative_expression` | No admissible candidate | Remains blocked |
| `negative_semantic` | No syntax repair attempted | Remains blocked |
| `negative_legal` | No edit | Frontend already accepted |
| `invocation_budget` | Stops after 1 compiler invocation | No completed baseline; explicit exit 3 |

Across the normal repair cases including the benchmark, **8 candidate insertions were accepted and 3 rejected**; the disabled and invocation-budget cases applied none. In `positive_analyzer`, Clang Static Analyzer produced **one warning**, `core.NullDereference`, at original line 4, column 12, plus two explanatory notes. All three records link to V1/C1 and are repair-conditioned; the notes are not separate defects. Frontend/analyzer completion is reported independently. No function/path coverage is certified even on successful examples.

## Files and scope

All implementation and generated validation output is confined to `phase6/v3/`.

Retained interrupted implementation: `engine.py`, `execution.py`, `policy.py`, `__main__.py`, `__init__.py`, `test_recovery.py`, and 12 C/header fixtures under `fixtures/`. Existing `outputs/initial_sample.json` and `outputs/protected_hashes.json` were preserved.

Resume modifications: `execution.py` adds finite file-backed subprocess handling; `engine.py` tightens eligibility/preservation and budget reporting; `__main__.py` validates configuration and incomplete/budget/cleanup exit states; `test_recovery.py` adds real timeout/binary capture and preprocessing validation tests.

Resume additions: `supervision.py`, `run_targeted.py`, `run_validation.py`, `validation.py`, `README.md`, this report, and captured `outputs/` test/case/supervision/preservation JSON and logs. [README](README.md) documents CLI/API, stable versioned envelope, provenance/mapping, budgets, exit codes and limitations. Existing SmartParse/CGAR, Extended C APIs, Phase 5, v1/v2, reference datasets, historical CSV contents, old fixtures and research scripts are unchanged.

## Remaining limitations

Recovery is deliberately narrow and Clang-specific; unsupported Clang AST/fix-it/VFS versions abstain. GCC remains baseline-only here. UTF-8/UTF-8 BOM and CRLF byte handling are supported; other encodings, multiline boundaries, macro expansions, header fixes, ambiguous control flow, pointer/array/typedef declaration repair, semantic changes, and function isolation are excluded. A strict error-subset check rejects even legitimate repairs that reveal new errors. Preprocessing checks are not a proof of equivalent intent and do not freeze an entire external build tree.

Timeouts have finite process-cleanup grace, not a hard real-time OS guarantee; output/source processing is not a full hostile-input resource sandbox. There is no universal defect-detection claim. The benchmark remains semantically blocked; its recovery results do not justify an increased confirmed-reference detection score. Any future semantic repair or isolation requires a separately reviewed milestone.
