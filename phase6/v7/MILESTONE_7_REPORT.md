# Phase 6 Milestone 7: external-tool comparison and selective integration

Completed for review. No commit, push, Milestone 8 implementation, installation/upgrade, source repair, C-program execution or sanitizer use. All additions are under `phase6/v7/`; original SmartParse/CGAR and v1–v6 remain unchanged.

## Audit and discovered tools

Branch/checkpoint: `feature/phase6-recovery`, `08bc8d9`. The v1–v6 reports, capability/evaluation/provenance models, allocation miss and benchmark blockers were reviewed before integration. [INITIAL_AUDIT.md](INITIAL_AUDIT.md) records the experiment design. All 1,025 pre-v7 files were hashed, including historical frozen references and the original numbered source outside the workspace.

| Candidate | Measured version/configuration | Availability and selection |
| --- | --- | --- |
| Existing MinGW GCC | 6.3.0 | `-fanalyzer` rejected; original compiler baseline retained |
| CodeBlocks MinGW-w64 UCRT GCC | 14.2.0, x86_64 | Analyzer execution verified with an actual null diagnostic; JSON works; **selected** |
| MSYS2 UCRT64 GCC | 16.1.0, x86_64 | Per-child bin PATH required; actual analyzer verified; old JSON format rejected, SARIF-stderr works; comparison-only |
| Cppcheck | 2.16.0, CodeBlocks MinGW bin | XML2/error+warning checks, explicit win64 model; **selected** |
| NDK Clang-Tidy | LLVM 17.0.2 | Advertised correctness checks verified and evaluated; comparison-only |
| CodeBlocks Clang-Tidy | Version unavailable | Version calls timed out; excluded, not misrepresented as a negative finding result |
| CBMC | Not discovered | No run, integration, bounded-verification claim or fabricated result |

Paths, raw versions, help/check inventories, target/predefined macros and capability outputs are retained under `outputs/`. The common-root search was bounded and cut off; explicit locations were checked afterward. This is not an exhaustive whole-disk/WSL absence claim. Initial shared-budget probing stopped after a timeout, so independent probes were then used rather than marking unattempted tools missing. GCC16 needed its own bin directory in the child PATH and a different diagnostic format; no GCC version was silently substituted.

CBMC would require approved installation and a suitable preprocessor/harness/solver/bounds configuration. Its [official installation guide](https://diffblue.github.io/cbmc/installation_guide.html) points to platform releases; a future authorized Windows MSI install can be verified with `cbmc --version`. Availability alone would not justify integration or complete program verification. Nothing was downloaded or installed here. All other compared candidates were already installed.

## Frozen inputs and configuration fairness

Before candidate evaluation, fresh unchanged-v6 results were frozen for **74 inputs**: 22 v5 C fixtures, 39 v6 fixtures, the unchanged 500-line source and 12 new positive/corrected/unknown controls. All use explicit C11. [inputs.json](inputs.json) binds original paths/hashes; [frozen_baseline/hashes.json](outputs/frozen_baseline/hashes.json) binds 87 files, including reports, manifest and holdouts. Old v6 results remain separately preserved, not replaced.

New allocation cases cover literal size, size held in a variable, helper-returned allocation, three corrected counterparts, and unknown caller-supplied extent. New signed-widening and overlapping-copy pairs provide independent opportunities beyond that family. A legitimate unsigned-modular product is a deliberate noise control. No detection rule was tuned to benchmark lines or names.

Every usable candidate analyzed the same 74 original files. Exact commands/configurations are in [catalog.json](catalog.json), each report and [README.md](README.md):

- GCC: `-std=c11 -Wall -Wextra -O0 -fanalyzer -fmax-errors=20`, actual `-c` into a private object, version-probed JSON/SARIF format. Objects are deleted, never linked or executed. Flag acceptance with syntax-only mode was not mistaken for analyzer execution.
- Cppcheck: XML2, default errors plus warning checks, `--platform=win64 --std=c11 --max-configs=1`; private cache. No style/performance/all/inconclusive expansion.
- Clang-Tidy: explicit empty config and an advertised correctness allowlist including integer division, misplaced widening, sizeof and selected clang-analyzer checks; explicit C11/warnings after `--`. No fixes, style families or project build scripts.

GCC UCRT, Clang's installed headers and Cppcheck's models differ. These are reproducible explicit configurations, not a hermetic common compiler build. Different targets/builds/models need new evaluation. Tidy's clang-analyzer wrappers also reuse Clang's engine; duplicate warnings are not algorithmically independent confirmation.

## Candidate results on independent evidence units

The 23-unit review dataset includes established source-operation roots and conditional review targets. Exact source/hash, diagnostic ID and meaning are required. Named agent source-review rationales and evidence fingerprints are stored in [root_review.json](outputs/root_review.json). Source-identical v5/v6 copies are aliases; related allocation variants share a family label. Human adjudication remains pending. Precision/recall are null.

| Profile | Established program roots supported | Previously supported by frozen baseline | New program roots | New families |
| --- | ---: | ---: | ---: | --- |
| Frozen v6 baseline | 12 | 12 | — | — |
| GCC14 alone | 13 | 8 | 5 | Allocation extent, overlapping copy |
| GCC16 alone | 13 | 8 | 5 | Same as GCC14 |
| Cppcheck alone | 11 | 9 | 2 | Late signed widening, overlapping copy |
| Clang-Tidy alone | 6 | 5 | 1 | Late signed widening |
| Baseline + selected GCC14 + Cppcheck | **18** | **12 retained** | **6** | **Three families** |

The six additional program units are the original v5 allocation miss, three new allocation-structure variants, one overlapping-copy program and one late-signed-widening program. This is **not six new bug categories**, nor a population recall claim. Three allocation variants plus the original allocation case test one family. No roots are lost in the augmented pipeline because existing evidence is preserved.

New, independently inspectable source facts:

- Allocation extent: successful allocation supplies one byte while the selected target's `int` store needs four. Literal/variable/helper controls allocate `sizeof(int)` or `sizeof *pointer` and do not trigger warnings.
- Overlap: `memcpy(bytes+1,bytes,5)` reads `[0,5)` and writes `[1,6)`, which overlap. Correct `memmove` counterpart produces no warning.
- Late widening: `INT_MAX==2147483647` is statically asserted, and local values `50000*50000` overflow signed int before the cast. Casting an operand before multiplication fixes it. Cppcheck reports `integerOverflow`; Tidy's warning is less specific.

The selected tools produce **zero primary diagnostics on 24 corrected/modular controls**. Tidy produces one misplaced-widening warning on the intentional unsigned-modular control; source review rejects interpreting that as a defect. It remains review burden, not a fabricated confirmed bug. Unknown findings elsewhere are not automatically false positives. Independent human false-positive adjudication is still pending; no general precision value is claimed.

## Why these adapters

[integration_decision.json](integration_decision.json) records the decision after measurement. GCC14 recovers the priority allocation-width gap and overlap root with no measured control warning. Cppcheck adds signed-overflow evidence beyond GCC14 and useful analysis of original malformed code. Both are explicit opt-in profiles.

GCC16 supplies the same incremental reviewed roots as GCC14 in this corpus, so adding a second GCC profile is unnecessary. Clang-Tidy's increment is covered by Cppcheck while it adds legitimate-control review noise and remains frontend-blocked on the benchmark. CBMC lacks an available, measured setup. Those candidates remain comparison-only/unavailable, not silently enabled.

The production-facing adapter supports **original files only**. Explicit repair/isolation provenance is rejected as unsupported, not promoted into original-source claims. GCC14/Cppcheck live version and actual capability are checked per requested analysis. Probe CTU/cache state is separate from source CTU/cache state, preventing synthetic probe declarations from influencing the user's analysis. No old default CLI/API changes were made.

## Critical allocation-size miss

| Variant | Frozen v6 | GCC14 | GCC16 | Cppcheck | Tidy17 |
| --- | --- | --- | --- | --- | --- |
| Original literal `malloc(1)` then int store | Not detected | Source-supported | Source-supported | Not detected | Not detected |
| New literal-size program | Not detected | Source-supported | Source-supported | Not detected | Not detected |
| Size in local variable | Not detected | Source-supported | Source-supported | Not detected | Not detected |
| Allocation returned through helper | Not detected | Source-supported | Source-supported | Not detected | Not detected |
| Three correctly sized counterparts | No finding | No finding | No finding | No finding | No finding |
| Caller-provided unknown extent | No finding; applicability unknown | One allocation-size/multiple warning, **unverified** | Same | No finding; extent unknown | No finding; extent unknown |

GCC14 emits three messages for the original literal case: `-Walloc-size`, `-Wanalyzer-allocation-size`, and `-Wanalyzer-out-of-bounds`. These support **one root**, not three. The variable case has two messages, and the helper has a path-sensitive bounds warning. GCC16 adds another size warning in the helper case; that does not increase root coverage.

Some allocation-size warnings describe a pointee-size multiple rather than a definite overflow. Strong fixture judgments therefore depend on reviewed extent/access facts, not identifier/message alone. New arbitrary-program findings remain tool-reported/unverified. Extra padded allocations, custom allocators, aliases and caller contracts need broader controls before general reliability claims.

## Unchanged erroneous 500-line benchmark

Original and cleaned source are unchanged; cleaned SHA-256 remains `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`. No syntax error was removed and no recovery/isolation variant was supplied.

| Candidate | Process / frontend state | Analysis evidence |
| --- | --- | --- |
| Frozen v6 | Clang frontend blocked | Existing compiler diagnostics; no custom semantic scan of invalid AST |
| GCC14/GCC16 | Drivers started; frontend errors remain; partial | Regular compiler diagnostics, no proof that useful analyzer path exploration completed |
| Clang-Tidy | Started; frontend errors; partial | One integer-division suggestion, not a new confirmed logic defect |
| Cppcheck | Started; selected configuration returned valid XML and operationally completed | 24 diagnostic groups; source review below; **no full-region/path coverage proof** |

Cppcheck's independent modeling can report useful evidence on this original erroneous input. That is not improved Clang eligibility, a valid compilation result, or evidence every function was analyzed. Tool completion and actual diagnosed locations are separate from exhaustive region coverage.

Explicit [benchmark_source_review.json](outputs/benchmark_source_review.json), tied to unchanged v1 reference/source hashes, supports **15 established local potential root facts**. Of these, **six were already warned** by the current/preserved compiler pipeline or share a previously warned cause. In particular printf line 421 was already warned by GCC6; the null consequence at 108 shares the already-warned assignment root at 104. Neither gets independent new-root credit.

The remaining **nine additional source-supported roots** are:

| Reference root | Evidence/source rationale |
| --- | --- |
| `ROOT-L0065` | Zero count passed to average at 65, integer division at 99 |
| `ROOT-L0078` | Zero divisor passed at 78, division at 142 |
| `ROOT-L0081` | Concrete null reset_student call; first member store at 134 |
| `ROOT-L0263` | Caller-visible pointer receives address of automatic local at 263 |
| `ROOT-L0271` | Successful allocation loses ownership at function exit without free |
| `ROOT-L0287` | Successful stream is never closed in write_report |
| `ROOT-L0307` | Successful-open branch returns before close |
| `ROOT-L0308` | Only failed-open/null branch reaches fclose |
| `ROOT-L0368` | Ordinary int month cannot be simultaneously below 1 and above 12; no inferred OR repair |

Five repeated null/path records collapse into their shared root groups. Three other reference consequences remain conditional: double-free with unresolved owned/non-null pointer contract, unbounded scanf with unresolved input-length contract, and missing-return use with unresolved consumer contract. Missing-return warning anchors at 404 rather than old 405; the source-reviewed anchor difference is explicit and does not rewrite v1 rules. One uninitialized-value report after an invalid sscanf call remains unmatched/uncertain, not a manufactured extra root.

These are **agent-reviewed local potential operation facts**, following v1's scope: no successful whole-program execution past earlier UB is asserted. No independent human-confirmed count or revised historical 16/68 score is claimed. The benchmark review is separate from the small independent-corpus root comparison; counts are not summed into a new recall score.

## Diagnostics, duplicates, failures and performance

All four candidates evaluated all 74 inputs; no candidate case exhausted its cohort quota or timed out. GCC/Tidy each returned 69 completed and five partial cases. Cppcheck returned 73 completed and one partial. Those states describe invocation/configuration completion, not every region.

| Cohort | Total diagnostic records | Primary diagnostic groups | Commands | Sum of per-source seconds |
| --- | ---: | ---: | ---: | ---: |
| Frozen baseline | 92 | 50 | 1,624 | 352.656 |
| GCC14 | 83 | 63 | 148 | 22.269 |
| GCC16 | 61 | 61 | 148 | 20.215 |
| Cppcheck | 47 | 47 | 148 | 14.653 |
| Tidy17 | 47 | 26 | 148 | 26.318 |

These are **not recall numerators**. Notes/path events are context; SARIF can put them inside code flows rather than separate records. Within reviewed units GCC14 has ten additional same-root evidence records, GCC16 eleven, baseline five. Cross-tool overlaps are merged by reviewed root identity, not raw message text or line proximity. The flattened [normalized_findings.json](outputs/normalized_findings.json) retains all 238 external records with tool/version/configuration, source binding, confidence, eligibility, provenance and explicit review linkage. Unmatched evidence stays unknown, not false.

The baseline has more probes/stages than individual candidates, and child startup/cache/platform conditions differ. These timings do not establish analyzer speed superiority. New public adapters normally use three commands (version, isolated capability, source analysis), bounded separately. GCC object output is private/deleted; no source is compiled and executed as a C program.

Failures were investigated rather than skipped:

- Initial baseline batch reached its 300-second external deadline after 61 saved reports whose own times total 298.328 seconds. This was an undersized batch budget, not evidence the next holdout hung. Those results were retained; 13 missing cases finished under separate 30/45-second limits before the baseline was frozen.
- Restricted Windows temporary-directory permissions caused three initial cleanup-state test failures. Elevated targeted execution confirmed the safeguards; four inspected, task-owned leftover directories were explicitly removed. No source/protected directory was deleted.
- A live test found Cppcheck requires its build-cache directory to exist. The harness now creates the private directory; tests were not relaxed.
- CodeBlocks' separate Clang-Tidy timed out during discovery. GCC16's obsolete JSON setting was rejected during capability probing, then replaced by its actually supported SARIF format. Neither is hidden as a successful source analysis.

## Regression and preservation

**433 tests passed; 0 failures, 0 errors, 0 skips**, in **352.500 seconds** (external supervisor 353.157 seconds; 480-second limit). This includes every prior 413 tests plus 20 v7 tests. Targeted tests ran first; final parser/adapter checks passed before full regression. See [tests.json](outputs/tests.json), [full.txt](outputs/full.txt), [full.supervision.json](outputs/full.supervision.json).

Additional supervised CLI checks confirm: GCC14 reports the allocation gap; the Cppcheck adapter returns the 24 benchmark groups; original `analyze_c.py --compiler gcc` still uses GCC6.3 and succeeds on valid input; supplying GCC6 to the pinned GCC14 profile is explicitly rejected rather than substituted. See [cli_checks.json](outputs/cli_checks.json).

All **1,025 pre-v7 protected files**, **87 new frozen-baseline files**, and **17 historical CSVs** retain their bytes. The legacy performance test writes a CSV; its prior bytes were restored in `finally` and the write is disclosed in [preservation_full.json](outputs/preservation_full.json). Timestamps are not claimed unchanged. No v1–v6 implementation/reference/report was modified and no earlier acceptance runner regenerated output.

All new implementation files are under v7: `__init__.py`, `protocol.py`, `experiment.py`, `run_comparison.py`, `evaluation.py`, `benchmark_review.py`, `adapter.py`, `__main__.py`, `run_validation.py`, `test_external.py`; configuration/reference/input/integration JSON; 12 holdout C files; audit/README/report; and versioned baseline/comparison/review/test/preservation outputs. [added_files.json](outputs/added_files.json) is the exact non-bytecode inventory; [acceptance_summary.json](outputs/acceptance_summary.json) records final verification. No commit or push was performed.

## Remaining gaps and proposed Milestone 8 evaluation

Independent human review is still necessary. Tool versions, library/header models, suppressed/unexplored configurations, macro contexts and target ABI can change results. Candidate process success does not prove full C/type validity or complete path coverage; Cppcheck's handling of malformed input is independent abstraction/recovery, not a guarantee it interpreted every construct correctly. Public findings remain unverified and original-source-only; conditioned external mapping is deliberately unsupported.

Recommended next evaluation, **not implemented**: human-adjudicated and separately frozen real-project holdouts; adversarial valid padded allocations and custom allocator/alias/realloc cases; additional compiler/OS/model configurations with explicit contracts; parser-error robustness with source-reviewed local facts; quantitative review burden rather than warning-count recall; and CBMC only after approved installation plus justified harnesses/unwind/precondition design. Preserve the historical references and current safety gates instead of weakening them to improve benchmark totals.
