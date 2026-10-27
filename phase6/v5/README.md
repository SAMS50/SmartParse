# Phase 6 v5: evidence-based memory, resource and bounds profile

This separate opt-in pipeline configures the installed Clang and evaluates evidence using the unchanged Phase 6 v1 model. It does not replace SmartParse/CGAR, change earlier compiler/reporting APIs, or relax v3 recovery/v4 isolation. No user C program is executed, no sanitizers or external analyzers are added, and no source is rewritten. There are no custom defect detectors in this milestone: existing capabilities provide the measured gains; remaining gaps are reported rather than guessed.

## Usage

Python 3.12 and an installed Clang are required for the memory profile. GCC 6.3 remains supported for baseline syntax/type analysis, not for these Clang checkers. Auto discovery prefers Clang on PATH; an explicit executable path works when Clang is elsewhere. Nothing installs software.

```powershell
# Disabled by default: existing baseline only.
python -m phase6.v5 "C:\my sources\program.c" --compiler gcc --json

# Explicit opt-in, using installed and successfully probed checks only.
python -m phase6.v5 "C:\my sources\program.c" --compiler "C:\Program Files\LLVM\bin\clang.exe" --memory-analysis --std c11 -I "C:\my headers" -D FEATURE=1 --json

# Default analyzer/source-warning comparison profile, not the additional checks.
python -m phase6.v5 program.c --compiler clang --memory-analysis --profile baseline --json

# Independently request prior experimental stages, retaining their safeguards.
python -m phase6.v5 program.c --compiler clang --memory-analysis --punctuation-recovery --isolate-unaffected --json
```

Without `--json`, observations print with checker identity and confidence/adjudication class. Exit 0 means no baseline compiler errors and requested invocation completed; warnings can still exist. Exit 1 preserves original compiler rejection even if conditioned analysis succeeds. Exit 2 means invalid arguments/configuration; exit 3 means unavailable/failed/incomplete analysis, budget exhaustion, or unverified preservation/cleanup. Status must be read alongside compiler errors and provenance. A completed analyzer process does not prove all functions/paths were checked or the program is safe.

```python
from phase6.v5.engine import run_detection, DetectionLimits
report = run_detection("input.c", enabled=True, compiler="clang",
                       limits=DetectionLimits())
```

## Capability audit and selection

The audit requests the installed driver's normal and alpha checker help and actual enabled-default list. It independently probes a fixed four-checker allowlist using valid C, then tests each optional warning flag. A zero exit code accompanied by an unknown-option warning is **not** accepted. Inventory absence/failure is reported, not silently assumed supported. Cached audits are bound to compiler path/version/default flags and build arguments; mismatches are rejected. Inventory text, return codes and stderr are retained.

Installed Clang 17.0.2 advertises 142 checkers across languages/platforms and enables 44 in the probed C configuration. This is an advertisement inventory, not live validation of all 142 checkers. Null dereferences, malloc/free lifetime/leaks, stack escapes and malloc/sizeof diagnostics already exist in defaults. Additional requested checkers are:

| Checker | Installed status | Interpretation |
| --- | --- | --- |
| `alpha.security.ArrayBoundV2` | Advertised, clean invocation probe | Experimental bounds evidence; measured new heap overrun finding |
| `alpha.unix.cstring.OutOfBounds` | Advertised, clean invocation probe | Experimental string bounds; no new root credit over compiler evidence in paired corpus |
| `alpha.unix.Stream` | Advertised, clean invocation probe | Experimental stream resources; measured new leak finding |
| `alpha.security.MallocOverflow` | Advertised, clean invocation probe | Experimental; no measured incremental root in this corpus, no effectiveness claim |

Clang labels all four alpha checks **“Enable only for development!”**. They are isolated in this opt-in experimental profile. Their observations are review suggestions, never automatic confirmed defects. No claim that these are stable production checks is made. Actual emitted checker IDs establish finding provenance; a probe establishes availability, not detection capability or recall.

Optional compiler warnings are `-Warray-bounds`, `-Wsizeof-pointer-memaccess`, `-Wreturn-stack-address`, and `-Walloc-size`. The first three pass on installed Clang; `-Walloc-size` produces an unknown-option warning and is omitted. Some accepted warnings are already implied by `-Wall` or compiler defaults: enabling them explicitly is not credited as a new detection. Compiler warnings and analyzer records stay separate. Diagnostic normalization preserves the existing unknown category rather than inferring memory semantics from English alone.

## Evidence and integration

The new envelope has `schema: "smartparse.memory_analysis"`, `schema_version: "1.0"`. Consumers should permit additional fields; setup errors may return `failure` with exit 3.

| Field | Meaning |
| --- | --- |
| `source` | Exact original bytes' SHA-256, resolved path, final preservation result. |
| `enabled`, `profile`, `status`, `reason` | Explicit request, baseline/memory configuration and independent analyzer operational result. |
| `upstream` | Unmodified v4 report, nested v3 compiler baseline/provenance and v2-compatible eligibility. |
| `capabilities` | Probed inventories, default checker list, per-checker/flag support, compiler/build binding and raw audit output. |
| `baseline_analyzer` | Original-source default analyzer report; never replaced with conditioned results. |
| `analysis` | Existing Extended C compiler report plus independently completed/partial/failed static-analysis result; raw stderr/stdout retained. |
| `eligibility` | v2-compatible snapshot eligibility; manifest `memory_profile` records requested additional checker/warning options and audit binding. Base manifest flags plus these options specify the effective profile; execution commands are authoritative. |
| `provenance` | Original/snapshot hashes, source map, repair/isolation flags, corresponding variant IDs and excluded spans. |
| `observations` | Unique primary analyzer warnings with mapped evidence, notes, provenance, and unknown adjudication. |
| `review_suggestions` | IDs of experimental-checker observations requiring review. |
| `unrecognized_or_unmapped_findings` | Unusable primary location evidence, excluded from observation counts. Raw unrecognized output also remains in embedded reports. |
| `usage`, `temporary_workspace_removed` | Combined subprocess/analyzer counts, elapsed time, detailed additional command records, limits and cleanup. |

Generic analyzer warnings are `backend_supported_potential`, not confirmed defects; alpha warnings are `review_suggestion`. Every observation starts `adjudication: unknown`, `confirmed_defect: false`. Notes are context, not new defects. Same-checker/message/location primary duplicates collapse; root-level compiler/analyzer duplicates require reviewed evaluation. No programmer intent is inferred from names.

Physical lines and byte columns are one-based, byte offsets zero-based. Existing v3 insertion mappings and v4 exclusion masks compose to original locations. Private VFS overlays keep original virtual filenames/include roots; neither recovery nor isolation is silently enabled. Excluded-region observations/traces are not admitted. Conditional evidence retains flags at report and finding level.

`export_v1_run(report, source_id)` supplies source/hash bindings and invocation-level coverage to the existing v1 evaluator. It **refuses** repair/isolation-conditioned evidence, unverified source preservation/cleanup, and failed/timed-out/exhausted runs. Conditioned cohorts remain separately reportable with their v2–v4 provenance; they cannot be flattened into unconditional baseline metrics. Successful frontend/analyzer invocation is operational eligibility, not full function/path coverage.

## Budgets, baseline freeze and reproducibility

Defaults/hard ceilings: combined compiler invocations **80/120**, analyzer driver invocations **16/20**, additional checkers **4/4**, total deadline **120/120 seconds**, per-process deadline **10/30 seconds**. All upstream probes and analyzer inventory/probe calls count. CLI overrides are `--max-invocations`, `--max-analyzer-invocations`, `--max-checkers`, `--total-timeout`, `--timeout`. Too-small checker budgets abstain rather than silently truncate. Capabilities may be cached only with matching build context. Private files are cleaned on success/error/timeout. Finite process cleanup grace can extend the deadline; Python/filesystem operations are not a hard real-time/resource sandbox.

`usage.compiler_invocations` counts recorded command attempts; `completed_subprocesses` distinguishes returned processes. Analyzer counters include actual recorded `--analyze` commands, including inventory/probes; `analyzer_slots_used` additionally captures reserved slots on interrupted/preflight paths. Source-analysis passes must not be inferred by subtracting or interpreting these as function counts.

```powershell
python -m phase6.v5.run_validation --stage targeted --compiler "C:\Program Files\LLVM\bin\clang.exe"
# Run once on a new v5 checkout: existing frozen baseline is never overwritten.
python -m phase6.v5.run_validation --stage freeze --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v5.run_validation --stage compare --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v5.run_validation --stage benchmark --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v5.run_validation --stage full --compiler "C:\Program Files\LLVM\bin\clang.exe"
```

Frozen baseline reports, source fixtures and reference are hash-bound. Freeze refuses an existing baseline directory; comparison verifies hashes and writes a separate configured directory. Baseline source passes use default compiler flags/checkers, although checker support probes on a valid separate input are recorded during audit. Stored results are tied to the measured compiler/target/build context, not portable claims about every Clang release.

Targeted tests run under external deadlines; freeze/compare batches have 240-second deadlines, benchmark cases 135 seconds each, full regression 420 seconds. Every source also has internal budgets. Stage failures/timeouts stop and are not silently skipped. Regression snapshots/restores the historical CSV test's writes in `finally`; preservation is explicitly reported. Old runners are not called, so their acceptance outputs are not regenerated.

The paired oracle `reference.json` contains nine atomic operation roots and corrected counterparts, plus malformed and unknown-contract fixtures. `evaluation.py` uses v1 matching, explicit named source-review rationales, scope fingerprints and duplicate adjudications. Unmatched findings stay unknown, including warnings on corrected programs; they do not automatically become false positives. Its lineage is local to this new fixture corpus and does not replace the original 68/76-entry references. Precision/recall values describe only this small, authored, agent-reviewed corpus; independent human oracle review and broader holdouts remain necessary.

See [MILESTONE_5_REPORT.md](MILESTONE_5_REPORT.md), [outputs/comparison.json](outputs/comparison.json) and [outputs/execution_summary.json](outputs/execution_summary.json) for measured gains, missed issues, false-positive burden and runtime. The 500-line benchmark still has frontend blockers; no memory-detection gain or complete coverage is claimed there.
