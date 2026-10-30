# Phase 6 Milestone 5: evidence-based memory/resource/bounds detection

Status: implementation and measured evaluation prepared for review. No commit, push, or Milestone 6 work. All additions are under `phase6/v5/`; earlier implementations and acceptance results remain separate.

## Capability audit

Measured compiler: installed **Clang 17.0.2**, Android build 11349228/r487747e, `C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe`, on Windows/Python 3.12. No software was installed. The audit uses the actual driver, not assumptions about newer documentation.

The driver advertises **142** normal/alpha checker names across supported languages/platforms; **44** are default-enabled for the probed C configuration. All advertised checkers are not claimed applicable or validated for C. The complete advertised/default inventories and original text are in [frozen_baseline/capability_audit.json](outputs/frozen_baseline/capability_audit.json); the preliminary inspection is retained in [initial_capabilities.json](outputs/initial_capabilities.json).

Already enabled: `core.NullDereference`, `unix.Malloc`, `core.StackAddressEscape`, `unix.MallocSizeof`, `core.VLASize`, uninitialized-value checks and related memory/string modeling. Thus ordinary null, malloc/free lifetime/leak, and stack-escape results are **baseline capabilities**, not new SmartParse findings. Current normalization separates compiler diagnostics from analyzer checker-ID findings and notes, retains raw output, and conservatively leaves semantic categories unknown. The new profile does not replace that normalization or attribute external findings to CGAR.

| Additional checker | Installed invocation probe | Increment in paired corpus |
| --- | --- | --- |
| `alpha.security.ArrayBoundV2` | Supported | One new concrete heap-buffer bounds root |
| `alpha.unix.cstring.OutOfBounds` | Supported | No additional unique root beyond compiler evidence |
| `alpha.unix.Stream` | Supported | One new stream-resource leak root |
| `alpha.security.MallocOverflow` | Supported | No measured incremental root; capability is not proof of effectiveness |

**All four are marked experimental/development-only by this Clang.** They run only in the explicit experimental memory profile. General observations from them are review suggestions, not automatic strong findings. A blank-input availability probe does not validate their recall or precision. No new custom defect-detection rule was added: configuring existing capabilities produced the measured gains; the remaining allocation-width gap is explicitly unresolved.

Warning probes accepted `-Warray-bounds`, `-Wsizeof-pointer-memaccess`, and `-Wreturn-stack-address`. Clang returns exit 0 **with an unknown-option warning** for `-Walloc-size`; it is rejected and never passed to source analysis. Accepted warnings may already be implied by defaults/`-Wall`; no new-root credit is given merely for explicitly requesting them.

## Frozen baseline and independent oracle

The comparison was frozen before the configured corpus run. [frozen_baseline/hashes.json](outputs/frozen_baseline/hashes.json) binds all baseline reports, the authored reference and all 22 fixture sources. Freeze refuses overwrite; comparison verifies hashes and writes separate results. Defaults are unchanged in baseline source passes; checker/flag availability probes use a separate valid input. Existing Phase 5 and v1 historical baselines are never replaced.

The independent corpus contains nine positive root-defect scenarios, nine corrected counterparts, semantic/syntax-malformed variants, a syntax-valid control, and an unknown-extent function whose caller contract cannot justify a concrete bounds claim. Its local lineage IDs are distinct from the original 68-entry/76-atom reference. Resource management is tagged separately but uses the v1 evaluator's existing `memory safety` category; this does not equate every resource leak with heap corruption.

Source inspection establishes each positive operation and its corrected contrast before comparison. Evidence matching requires exact source/hash binding, admissible anchor, checker/diagnostic identifier and message meaning. The unchanged v1 evaluator requires explicit named reviewer decisions and scope fingerprints. [reference.json](reference.json) and each evaluation's `review` store agent source-review rationales; **independent human oracle review remains pending**. This is not automatic semantic certainty.

| Root scenario | Default baseline | Configured profile | Evidence interpretation |
| --- | --- | --- | --- |
| Null dereference | Detected | Detected, already known | `core.NullDereference` |
| Double-free | Detected | Detected, already known | `unix.Malloc` |
| Use-after-free | Detected | Detected, already known | `unix.Malloc` |
| Heap leak | Detected | Detected, already known | `unix.Malloc` |
| Stack-address escape | Detected | Detected, already known | Compiler and analyzer are one root, not two |
| Fixed allocation bounds overrun | Missed | **New reviewed root** | `alpha.security.ArrayBoundV2` |
| String buffer overflow | Detected | Detected, already known | Existing compiler `-Wfortify-source`; no extra root credit |
| Stream leak | Missed | **New reviewed root** | `alpha.unix.Stream` |
| `malloc(1)` followed by an `int` store | Missed | **Still missed** | Enabled malloc/sizeof and overflow checks do not establish coverage of this allocation-width pattern |

Actual new evidence:

- `fixed_bounds_bad.c:2:72`: “Out of bound memory access (access exceeds upper limit of memory block)”. Source allocates four bytes, checks success, assigns constant index 4 and stores one byte there. Three notes support the single root. Its corrected counterpart uses index 3 and produces no warning.
- `stream_bad.c:2:74`: “Opened stream never closed. Potential resource leak”. Source opens a stream, returns if opening failed, and loses the handle on the successful-open path without closing it. Four notes support the single root. Its corrected counterpart closes the stream and produces no warning. This is a potential successful-open-path defect, not a claim that a particular file existed or was opened during execution.

No program was executed. These judgments concern local potential operation defects under the displayed success paths/standard library models, not guaranteed runtime manifestations or whole-program logic correctness.

## Root-based metrics and false-positive burden

Measured by [comparison.json](outputs/comparison.json), with separate frozen/configured v1-model evaluations and review decisions:

| Measure | Baseline | Configured |
| --- | ---: | ---: |
| Reviewed true root findings / authored roots | 6 / 9 | 8 / 9 |
| Corpus root recall | 66.7% | 88.9% |
| Memory-safety category, including resource tag | 5 / 6 | 6 / 6 |
| Bounds category | 1 / 3 | 2 / 3 |
| Confirmed false-positive groups | 0 | 0 |
| Unmatched primary observations in evaluated paired corpus | 0 | 0 |
| Warnings on nine corrected counterparts | 0 | 0 |
| Lost previously detected roots | — | 0 |

Adjudicated-only precision is 8/(8+0) for the configured corpus. **This is a small, authored, agent-reviewed measurement, not a general 100% precision claim.** Unknown findings would remain unknown, including warnings on corrected programs; tests explicitly prohibit converting unknowns into false positives. Supporting notes, compiler/analyzer duplicates and cascades do not create independent confirmed defects. There is no broad logic/UB coverage denominator in these nine scenarios, and no population-level recall estimate.

## Malformed input, eligibility and provenance

Twenty of the 22 original baseline/configured fixture invocations complete; both malformed variants remain partial with no admitted analyzer observations. The unknown-extent function produces no specific defect claim: no guess about caller bounds or naming is introduced.

Separately enabling the unchanged v4 policy on `malformed_semantic.c` excludes the unrelated bad function. The remaining function becomes analyzer-eligible and emits one bounds warning at physical line 3. The report remains **isolation-conditioned**, outside the unconditional 8/9 comparison. A live test likewise checks v3-repaired null-dereference evidence stays repair-conditioned. Another test covers Unicode/space-containing paths and JSON CLI output.

`export_v1_run` refuses conditioned, unverified or failed evidence. Thus neither repaired nor isolated results can silently inflate the original baseline or reference score. v2-compatible eligibility is embedded; v3/v4 edit/exclusion maps, source hashes, variant IDs and assumptions remain attached. Analyzer process completion does not establish complete function/path coverage.

## Cleaned 500-line benchmark

The original/cleaned source bytes and historical comparisons are unchanged. Cleaned SHA-256: `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`.

| Profile | Compiler diagnostics | Analyzer | New admitted memory observations |
| --- | --- | --- | ---: |
| Original default profile | 7 errors, 12 warnings, 11 notes | Partial | 0 |
| Original configured profile | Same | Partial | 0 |
| Explicit v3 recovery + requested v4 isolation + configured profile | 5 errors, 14 warnings, 12 notes, all repair-conditioned | Partial; isolation abstains on preprocessing whitelist | 0 |

The remaining type/call/identifier errors still prevent complete path analysis. Main-file macros/global context remain outside v4's initial whitelist. No safeguard was weakened to obtain more output. **No actual benchmark eligibility or confirmed-defect detection improvement was measured.** Notes and cascading type errors are not new roots.

The new original-source export was evaluated against the unchanged v1 76-atom reference with no stale reviews reused: 20 blocked, 22 conditional and 34 uncertain. Zero reviewed matches in this new *unreviewed* run is not a replacement 0/76 score, nor a loss of historical 16/68 results. All old review fingerprints and acceptance artifacts remain intact.

## Measured invocation counts and timing

Actual command/timing logs are recorded per report. Counts include metadata, capability probes and analyzer help/query invocations, not just source passes. [execution_summary.json](outputs/execution_summary.json) provides per-case values.

| Cohort | Reports | Combined compiler commands | Analyzer driver commands | Sum of per-report seconds |
| --- | ---: | ---: | ---: | ---: |
| Frozen baseline | 22 | 429 | 51 | 90.516 |
| Configured, including separate isolated malformed report | 23 | 459 | 56 | 69.189 |

External supervised batch times were 92.750 seconds (freeze) and 69.813 seconds (comparison). Different caching/scheduling conditions make these unsuitable as a speedup claim. Capability caching avoids repeating identical probes within a cohort. Baseline original/default analyzer evidence is retained separately from the source profile pass; those operational passes are not duplicate defect credit.

Benchmark original/default: 30 commands, including 9 analyzer driver commands, 5.016 seconds internally. Original/configured: 30/9, 4.734 seconds. Explicitly conditioned: 46/11, 8.656 seconds. Each has an external 135-second deadline and exits 3 for incomplete requested analysis.

Default source-workflow budgets are 80 total compiler commands, 16 analyzer driver commands, four additional checkers, 120 seconds overall and 10 seconds per process. Strict ceilings and CLI overrides are in [README.md](README.md). All upstream work counts. A timeout stops further work; outputs use file-backed capture and bounded cleanup. Python/filesystem/OS scheduling is not a hard real-time or hostile-input resource sandbox. No C executable is created for execution, no user binary runs, and no sanitizer/runtime instrumentation is used.

## Tests, preservation and files

Targeted policy, source/evidence evaluation, CLI, timeout/budget, malformed-output and live checks ran before the complete suite. The final suite passed **385 tests: 0 failures, 0 errors, 0 skips**, in **220.453 seconds** (external supervision 221.187 seconds, 420-second limit). This includes all 363 pre-v5 tests plus 22 new tests: 11 policy/evaluation/CLI tests and 11 live methods. Exact results are in [tests.json](outputs/tests.json), [full.txt](outputs/full.txt), and [full.supervision.json](outputs/full.supervision.json). Tests do not hardcode a positive-finding assertion for the experimental version-dependent checker set; the measurement report records actual outputs rather than fabricating unsupported findings. Live default null-check and installed-pipeline assertions are explicit tests.

Two additional 20-second-supervised checks used installed **GCC 6.3.0**: baseline valid-C analysis exited 0, while explicitly requested Clang-only memory analysis exited 3 with a clear availability reason. See [gcc_checks.json](outputs/gcc_checks.json). No validation stage timed out. Stored capability reports explicitly disclose unsupported options; no live test was silently omitted.

The preservation inventory covers **675 pre-v5 files**, including v1–v4 reports, fixtures, original numbered source outside the workspace, historical research/evaluation scripts and acceptance artifacts. All **17 historical CSVs** retain their exact bytes. The legacy full-suite performance test writes a CSV; the validation runner snapshots/restores those bytes in `finally` and discloses it. No old acceptance runner is invoked or output regenerated. Frozen v5 baseline hashes are checked separately.

Files added, all within v5: `engine.py`, `capabilities.py`, `evaluation.py`, `__main__.py`, `__init__.py`, `test_detection.py`, `run_validation.py`, `reference.json`, 22 independent `fixtures/*.c`, `README.md`, this report, and measured `outputs/` audits, frozen/configured evidence, comparison, benchmark/reference evaluation, supervision/test and preservation logs. No pre-existing implementation file was edited. A full file inventory and final verification are included with the output summaries.

## Remaining limitations

The allocation-width operation remains missed, and allocation-overflow effectiveness was not established by this small corpus. Experimental Clang checkers can be incomplete, version-dependent, or wrong on unfamiliar code; availability does not prove reliability. Resource findings rely on the modeled C library and success-path assumptions. Corrected fixtures do not substitute for diverse independent holdouts or human review.

Source evidence admits only narrowly justified operation claims. General ownership contracts, arbitrary pointer extents, unknown buffer capacities, general logic errors, concurrency and every possible UB class remain unsupported/unproven. Compiler diagnostics may exist when path analysis is blocked; failed/incomplete/zero-finding runs are never proof of safety. External header trees/environment are not frozen against concurrent changes. Historical research and CGAR claims remain unchanged and distinct from these Clang results.
