# Milestone 7 initial audit

Branch `feature/phase6-recovery`, checkpoint `08bc8d9`; v1–v6 implementations, reports, references, capability/provenance/evaluation models and frozen baselines were reviewed. They remain unchanged. A 1,025-file pre-v7 hash inventory includes prior acceptance artifacts and the external numbered benchmark. Legacy CSV test writes will be restored explicitly, not regenerated as research results.

Remaining gaps: the literal undersized allocation/scalar-int store, unknown extent/ownership contracts, syntax/type blockers on the 500-line program, and intentionally narrow semantic/region eligibility. Tool findings must be reviewed against source roots; v6's conditional input/precision targets are not confirmed bugs. No recovery/isolation safeguard is to be relaxed.

## Installed tools, actual probes

- Existing PATH GCC 6.3.0 rejects `-fanalyzer`; it must remain the existing baseline, not be silently upgraded.
- `C:\Program Files\CodeBlocks\MinGW\bin\gcc.exe`: GCC 14.2.0; actual `-c -O0 -fanalyzer` emits a null-dereference warning on a valid probe. Diagnostic JSON is supported.
- `C:\msys64\ucrt64\bin\gcc.exe`: MSYS2 GCC 16.1.0; per-process bin PATH is needed. Diagnostic `json` is **not supported** in this driver; advertised SARIF-stderr works and actual analyzer execution emits the known null warning. No inference of support from version alone.
- `C:\Program Files\CodeBlocks\MinGW\bin\cppcheck.exe`: Cppcheck 2.16.0, help captured.
- NDK `clang-tidy.exe`: LLVM 17.0.2. Actual check inventory includes correctness-oriented `bugprone-integer-division`, `bugprone-misplaced-widening-cast`, `bugprone-sizeof-expression`, and clang-analyzer checks. Style check families will not be enabled or counted.
- CodeBlocks' separate clang-tidy executable timed out on version probing and is excluded unless a bounded follow-up establishes usability. This is a tool failure, not a negative detection result.
- CBMC was not found on PATH, the bounded common-root search or explicit common install locations. Search was time-limited and not an exhaustive disk inventory. Installation is not authorized and will not be attempted.

Raw discovery/probe reports are under `outputs/`. Initial shared-budget discovery stopped after one timeout, so independent per-tool probes were performed; unattempted tools were not falsely marked unavailable. Common-root search cutoff and scope are recorded. No software was installed/upgraded or C binary executed.

GCC analyzer probes use private object output, not syntax-only mode: accepting a flag is not proof the analyzer ran. Objects are never linked/executed and are removed. GCC 14's MinGW-w64 UCRT and GCC 16's MSYS2 UCRT toolchains are explicit separate candidates; per-tool PATH changes are child-only. ABI/target differences and model configurations must accompany comparisons.

## Frozen experiment design before adapter integration

`inputs.json` includes all 22 v5 C fixtures, all 39 v6 fixtures, the unchanged cleaned benchmark and 12 new source-reviewed positive/negative/unknown controls. New allocation variants cover literal, variable-held, helper-returned, correct and unknown extents; corrected variable/helper counterparts are included. Additional unseen late-widening and overlapping-copy pairs test independent candidate capability, with a legitimate unsigned-modular control. No rule is tailored to benchmark line numbers.

Freeze fresh v6 results on every input using explicit C11 and selected existing Clang 17. Existing v6 historical reports are separately preserved by hash. Candidate runs use the same original files/standard; toolchain platform/header models differ and must be recorded. Prefer machine diagnostic formats with raw output retained. Suggested candidate configuration: GCC `-O0 -fanalyzer`, Cppcheck error/warning classes with explicit platform/standard, and an advertised correctness-only Clang-Tidy list. No style warning counts as a defect.

Only after reviewing measured incremental roots and corrected controls may an opt-in production adapter be added. A comparison-only negative result is valid. Unknown/conditioned findings cannot be promoted to unconditional baseline evidence, successful process exit cannot certify regions, and no independently verified precision/recall claim is justified by agent review.
