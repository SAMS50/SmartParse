# Phase 6 v4: experimental unaffected-region analysis

This separate experiment removes entire blocked function definitions from a private analysis snapshot, without inserting stubs, declarations, casts, values, or replacement bodies. It does not change SmartParse/CGAR or the existing Extended C, v2 eligibility, or v3 recovery APIs. All diagnostics remain attributable to their compiler/analyzer. **Isolation is disabled by default.**

## Usage

Python 3.12 and a working Clang installation are needed for isolation. GCC remains available for the existing baseline pipeline, but has no isolation adapter. Clang availability and analyzer/VFS/AST capabilities are tested, not assumed. Nothing installs software or runs the user's C binary.

```powershell
# Baseline only; neither isolation nor punctuation repair runs.
python -m phase6.v4 "C:\my sources\program.c" --compiler gcc --json

# Explicit experimental isolation, which requests Clang Static Analyzer.
python -m phase6.v4 "C:\my sources\program.c" --compiler "C:\Program Files\LLVM\bin\clang.exe" --isolate-unaffected --std c11 -I "C:\my headers" -D FEATURE=1 --json

# Separately enable the existing v3 punctuation-recovery stage first.
python -m phase6.v4 "program.c" --compiler clang --punctuation-recovery --isolate-unaffected --json
```

`auto` prefers Clang on PATH; an explicit executable path is supported. Paths with spaces must be quoted. Without `--json`, the terminal report gives isolation status, exclusions, unique additional conditioned warning count, and source preservation. Exit 0 means the original baseline was accepted with requested analysis completed (including when isolation was unnecessary); exit 1 preserves original source rejection even if a variant succeeds; exit 2 means invalid CLI/configuration; exit 3 means failed, incomplete, unavailable, exhausted, or conservatively abstained requested isolation. Read the independent compiler/analyzer stages in JSON to distinguish source errors from tool failures.

```python
from phase6.v4.engine import run_isolation, IsolationLimits
report = run_isolation("program.c", isolate=True, repair=False, compiler="clang",
                       limits=IsolationLimits())
```

## Admission policy and dependency decisions

Clang JSON AST physical main-file locations must agree with the function name and both compound-body braces. Definitions must occupy separate physical boundary lines. A body with recovery nodes can be excluded when its outer boundaries remain reliable; it cannot be claimed analyzed. Syntax errors require the separately enabled v3 recovery stage first; unknown locations, signature errors, header errors and unreliable boundaries abstain. Diagnostic location assigns blockers to bodies; it never proves analysis coverage.

All functions directly referring to an excluded definition are transitively excluded, including address-taking references. No prototype or opaque call is invented to replace that definition. Dependencies between retained functions stay intact. Unchanged explicit external function declarations/headers retain their existing contracts; this is a conditional source-level analysis, not whole-program equivalence. Header references back into main-file definitions cause rejection.

This initial whitelist rejects main-file global variables/initialization, persistent or external local state, references to header/global variables, indirect calls, assembly/computed control flow, unsupported attributes/declarations, main-file preprocessing directives other than includes, and macro-expanded function content. Includes within function ranges are rejected. Unused macro definitions also cause conservative abstention. Some otherwise safe real programs will therefore be unsupported.

One candidate variant masks every excluded definition with ASCII spaces, preserving every CR/LF byte and all offsets. Includes, other declarations, and retained function bytes remain unchanged. A private VFS overlay preserves the original virtual filename, quote-include root and `__FILE__`; capability checks verify that behavior. The variant must pass the selected compiler without errors. Preprocessor line markers identify excluded main-file lines; token streams outside exclusions must agree. A second physical AST inventory must contain exactly the retained functions at identical offsets and with identical function references. Any mismatch rejects the variant before analysis. Preprocessed output/AST validation is consistency evidence, not proof of original intent or whole-program behavior.

## Bounded execution

| Resource | Default | Hard maximum |
| --- | ---: | ---: |
| Excluded function definitions | 8 | 16 |
| Candidate isolation variants | 1 | 1 |
| Compiler invocations, including v3/probes | 64 | 80 |
| Analyzer driver invocations, including capability/checker probes | 5 | 6 |
| Combined recovery/isolation deadline, seconds | 120 | 120 |
| Per compiler/analyzer timeout, seconds | 10 | 30 |

CLI controls are `--max-exclusions`, `--max-invocations`, `--max-analyzer-invocations`, `--total-timeout`, and `--timeout`. The v3 source limit remains 1 MiB and its punctuation limits remain in effect. Every additional invocation uses the remaining combined compiler/time allowance. Analyzer slots are separately checked before probes and source analysis. A timeout stops further compiler calls. File-backed capture and finite owned-process-tree cleanup reuse v3's safe runner, without shell execution. Process cleanup has finite grace beyond the deadline; filesystem/Python processing is not a hard real-time OS guarantee or a hostile-input resource sandbox.

Temporary files are removed on success, rejection, timeout and exceptions; cleanup and final original-source hashes are reported. No original source is opened for writing. External header trees/environment are not frozen; concurrent build-context changes remain a limitation. This experiment does not execute a compiled C program.

## Versioned JSON contract

Envelope: `schema: "smartparse.unaffected_regions"`, `schema_version: "1.0"`. Additional fields may be added. Input/tool setup failures may return a failure envelope with `failure` and exit 3.

| Field | Meaning |
| --- | --- |
| `source` | Original resolved path, exact-byte SHA-256, final preservation result. |
| `recovery_report` | Unmodified v3 report, containing immutable original compiler diagnostics and any separately opted-in punctuation provenance. |
| `baseline_static_analysis` | Original-source Clang analyzer report, independent from compiler completion and isolation results; null if not attempted/available. |
| `analyzer_context` | Selected compiler/version/flags, queried enabled default checkers (null if unavailable), checker-query result; no extra detection rules/checkers enabled. |
| `isolation.enabled`, `experimental` | Explicit feature request and experimental status. |
| `isolation.status`, `reason` | `not_attempted`, `completed`, `partial`, `abstained`, `budget_exhausted`, `timed_out`, or `failed`, with reason. |
| `isolation.inventory` | Reliable physical boundary inventory and dependencies; inventory can remain empty when admission fails. |
| `isolation.excluded_functions` | Each actual planned exclusion, physical source range, original mapped range, reasons and dependency assumptions. A rejected plan need not create any exclusions. |
| `isolation.retained_functions` | Candidate retained definitions, references and dependency assumptions; analyzer coverage remains unknown. |
| `isolation.variant` | Null or I1: validating/rejected/accepted status, hashes, exclusion spans, optional punctuation IDs, source map, and embedded v2-compatible eligibility. |
| `isolation.eligibility_improved` | True only when a previously rejected frontend's isolated variant is accepted and its analyzer invocation completes. This does not certify per-function coverage. |
| `isolation.function_path_coverage_certified` | Always false: the backend provides no reliable evidence of complete function/path traversal. |
| `isolation.usage`, `limits` | Combined compiler count, actual/attempted analyzer slots, overall elapsed time and detailed additional commands/results. |
| `isolation.temporary_workspace_removed` | Verified cleanup result. |
| `isolation_conditioned_findings` | Primary analyzer warnings in retained main-file functions, with original mapped evidence, variant ID, notes, conditional provenance and unreviewed adjudication. |
| `unique_additional_findings` | IDs of unique conditioned warnings absent from original baseline and earlier recovery evidence; **not confirmed distinct original defects**. |
| `suppressed_findings` | Unmapped/header/excluded observations or findings whose trace reaches an excluded region; not counted. |

Source ranges are zero-based, half-open byte spans. Lines/columns are one-based physical byte coordinates. Masking preserves offsets; when v3 is enabled, `parent_to_original` composes the insertion map and excluded-function `original_source_range` maps original bytes. Generated punctuation has no original token. UTF-8, CRLF, Unicode paths and spaces are supported; unsupported encodings abstain. Embedded eligibility identifies `private_isolation_variant` and original hash; original sources remain unmodified.

A completed compiler/analyzer invocation never implies every retained function was analyzed. Excluded functions are `not_attempted`; retained function/path coverage is `unknown`. Original and variant findings never merge. Unique warning identity uses mapped original file, line, byte column, checker ID and diagnostic message; exact duplicates and supporting notes do not increase counts. Different messages/checkers can still describe the same underlying defect, so human adjudication is required. Missing findings, unsupported isolation and analyzer completion never prove bug freedom.

## Validation

With the desired installed Clang:

```powershell
python -m phase6.v4.run_validation --stage targeted --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v4.run_validation --stage full --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v4.run_validation --stage cases --compiler "C:\Program Files\LLVM\bin\clang.exe"
```

Targeted tests have external 20/35-second deadlines; full suite 300 seconds; CLI cases 135 seconds. Failures/timeouts stop that stage and are not silently skipped. Logs/results stay in v4. The historical suite writes a performance CSV; the runner snapshots/restores its exact previous bytes in `finally`, explicitly recording the write. Earlier v1–v3 validation runners are not invoked, preventing overwrites of their acceptance outputs.

See [MILESTONE_4_REPORT.md](MILESTONE_4_REPORT.md) for measured exclusions, benchmark results, tests, limitations and preservation evidence. No new defect-detection rules, external analyzers, semantic repairs or historical reference rescoring are part of this milestone.
