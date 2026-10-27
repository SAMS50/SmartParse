# Phase 6 v3: bounded punctuation recovery for analysis

This experimental, separate entry point preserves SmartParse/CGAR, Extended C's existing API, Phase 6 v1/v2, and historical evaluation scores. Recovery is **disabled by default**. Compiler and analyzer observations belong to Clang/GCC, never CGAR. Temporary variants are hypotheses about punctuation, not corrected user programs or independently confirmed defects.

## Usage

Python 3.12 and an installed GCC or Clang are needed for baseline diagnostics. Recovery additionally requires a selected Clang with working machine-readable fix-its, JSON AST, and virtual-file overlay capabilities. Each capability is checked; unsupported configurations abstain. GCC 6.3 remains usable for baseline syntax/type checking; this prototype has no GCC repair adapter. No software is installed by these commands.

```powershell
# Baseline only: recovery remains disabled.
python -m phase6.v3 "C:\my sources\input.c" --compiler gcc --json

# Explicit opt-in; quote executable and source paths containing spaces.
python -m phase6.v3 "C:\my sources\input.c" --compiler "C:\Program Files\LLVM\bin\clang.exe" --std c11 -I "C:\my headers" -D FEATURE=1 --repair-for-analysis --static-analysis --json
```

`--compiler` accepts `auto`, `gcc`, `clang`, or an executable path. Auto searches PATH, preferring Clang. Static analysis is a separate opt-in and uses the selected Clang driver; it does not silently switch compilers. Without `--json`, the command prints baseline completion, candidate decisions, stop reason, and eligibility change. Existing `analyze_c.py` and `python -m phase6.v2` behavior is unchanged.

Exit codes: **0** baseline analysis completed without source errors; **1** baseline source errors remain the original result, even when a temporary variant is accepted; **2** invalid arguments/configuration; **3** tool failure, incomplete requested analyzer, exhausted budget, or unverified source preservation/cleanup. A rejected source does not become successful merely because recovery helped. Unavailable analysis and zero findings never establish bug freedom.

Python API:

```python
from phase6.v3.engine import run_recovery
from phase6.v3.execution import Limits
report = run_recovery("input.c", repair=True, compiler="clang",
                      static_analysis=True, limits=Limits())
```

## Admission and validation policy

Only a compiler-associated, machine-readable **zero-length `;` insertion** is considered. Diagnostic English is not a repair rule. A unique physical AST boundary must agree with the fix-it: a single-line builtin scalar declaration at translation-unit scope before another declaration, or a return statement directly within a compound statement before its closing brace. Macro expansion/recovery locations, headers, ambiguous nodes, presumed-line directives, unbraced control statements, and unsupported encodings abstain. Local declaration repair, arbitrary expression statements, typedef/pointer/array declarations, and multiline boundaries are outside this milestone's whitelist.

Each candidate is recompiled using the same selected compiler and configuration. Its mapped error set must be a **strict subset** of the preceding error set: any new error, including a newly exposed genuine error, rejects the candidate. Preprocessed output must differ only by one semicolon token, ignoring whitespace; string and character contents are retained. JSON AST/source mapping must remain usable. This is a deliberately conservative consistency check, not proof of semantic equivalence. No identifiers, types, expressions, arguments, conditions, allocation sizes, or loop bounds are edited.

Private temporary byte copies are exposed through a verified Clang VFS overlay retaining the original virtual filename, quote-include root, and `__FILE__`. Original files are never opened for writing by the recovery engine. Files are removed at scope exit and cleanup is recorded. Only syntax checks and optional static analysis run; no C executable is built or executed. An external compiler is trusted software, not a security sandbox.

## Budgets and timeout behavior

| Limit | Default | Hard ceiling |
| --- | ---: | ---: |
| Candidate records | 4 | 8 |
| Rounds | 3 | 4 |
| Compiler invocations, including all probes | 48 | 80 |
| Retained accepted variants | 4 | 4 |
| Cumulative insertions | 4 | 4 |
| Total compiler/recovery deadline, seconds | 90 | 120 |
| Individual compiler deadline, seconds | 10 | 30 |

CLI overrides are `--max-candidates`, `--max-rounds`, `--max-invocations`, `--max-variants`, `--max-edits`, `--total-timeout`, and `--timeout`. Source input is capped at 1 MiB. Each invocation timeout is clamped to the remaining deadline; a timeout latches a stop, preventing further compiler calls. File-backed binary capture avoids inherited-pipe EOF hangs. Timeout handling attempts to kill the owned process tree with finite waits; cleanup can take up to six additional seconds. Python processing, file I/O, OS scheduling, and serialization are not hard real-time guarantees. This is not a memory/resource sandbox.

## JSON contract, version 1.0

The new envelope has `schema: "smartparse.repair_for_analysis"`, `schema_version: "1.0"`. It does not replace older report schemas. Consumers should tolerate additional fields. Missing/unusable input may produce a failure envelope containing `schema`, `schema_version`, and `failure`, with exit 3.

| Field | Meaning |
| --- | --- |
| `source` | Resolved original path, SHA-256 of exact bytes, final `original_unchanged` check. |
| `baseline` | Immutable original `analysis`, its `analysis_sha256`, source hash, and v2-compatible `eligibility`; null if no baseline was obtainable. `metadata_incomplete` marks interrupted probes. |
| `recovery.enabled` | Whether the caller explicitly requested repair. |
| `recovery.limits`, `usage` | Limits, counted commands/roles/status/timings, stderr and output hashes. |
| `recovery.candidates` | Machine fix-it location/replacement/associated diagnostic, round, accepted/rejected decision and reason; accepted candidates link to variant and original byte offset. |
| `recovery.non_whitelisted_suggestions` | Ignored non-semicolon suggestions; never applied. |
| `recovery.accepted_variants` | Ordered cumulative variants with source/parent/original hashes, edits, mapping, preprocessing guard, eligibility, and cleanup result. |
| `recovery.stop_reason`, `budget_exhausted` | Explicit termination/abstention and budget state. |
| `recovery.temporary_workspace_removed` | Whether removal was verified; false precludes successful CLI exit. |
| `recovery.eligibility_change` | Baseline/final frontend acceptance, newly eligible frontend, newly completed analyzer, and explicit absence of function-path certification. |
| `repair_conditioned_findings` | Observations with variant ID, compiler/analyzer source, `repair_conditioned: true`, edit IDs, and mapped evidence. Includes supporting notes; entries are not counts of independent defects. |

Embedded `analysis` uses the existing Extended C report, including raw stdout/stderr and independent static-analysis status. Embedded eligibility uses the v2 schema; variant manifests explicitly identify `snapshot_kind: "private_vfs_variant"`, its hash, and `original_file_sha256`. Its physical AST regions refer to the snapshot, with the enclosing variant map providing original coordinates. `source_edits_applied: false` refers to the original file; `private_overlay_edits` records private changes.

Locations use **1-based physical lines and byte columns**, with **0-based byte offsets**. Source maps contain half-open variant/original byte spans. Inserted punctuation has null original span and an `anchor_original_offset`; it must not be represented as an original source token. No line breaks or existing bytes are rewritten, including UTF-8 and CRLF. Findings retain compiler locations and explicit mapped original locations; header/unmapped observations remain compiler-reported. Unsupported/non-UTF-8 inputs are not transcoded for repair.

Compiler-error reduction is recorded separately from eligibility. A rejected frontend blocks conservative function eligibility. A completed analyzer invocation does not certify every function/path; coverage remains unknown where the backend provides no reliable execution evidence. Intermediate variants with frontend errors do not trigger another analyzer run. Baseline analyzer diagnostics remain separate from all variant findings.

## Validation and limitations

First run `python -m phase6.v3.run_targeted` with the desired Clang on PATH: pure tests have a 20-second external timeout; live methods run in separate 30-second processes with captured logs. Then run:

```powershell
python -m phase6.v3.run_validation --compiler "C:\Program Files\LLVM\bin\clang.exe"
```

The validation runner bounds the complete suite to 240 seconds and each CLI case to 105 seconds, stops on failures/timeouts, validates reports, and records protected hashes. The legacy regression suite writes a historical performance CSV; the runner snapshots/restores its original bytes in `finally` and reports this explicitly. Do not use bare historical regression commands when preservation is required.

See [MILESTONE_3_REPORT.md](MILESTONE_3_REPORT.md) and [outputs/cases.json](outputs/cases.json) for measured results. AST/fix-it differences across Clang versions may cause safe abstention. Preprocessing consistency does not snapshot an entire external header tree; concurrent header/environment changes and time-dependent macros can cause rejection. No function isolation, semantic repairs, new detection rules, or historical reference rescoring are implemented. Repeated observations across variants/backends and analyzer notes must not be counted as independent defects.
