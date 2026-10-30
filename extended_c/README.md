# Extended C Analysis: Milestones 1–5

This package invokes external Clang/GCC syntax and type checking. It does not
use or change SmartParse's restricted grammar, recovery algorithms, or CGAR.
Diagnostics belong to the named compiler backend.

## Installation and environment checks

1. Install Python 3.12 and open PowerShell in the repository root. No Python
   package installation is required for this CLI or its standard-library tests.
   The existing plotting scripts separately require Matplotlib.
2. Install an external C toolchain. Clang is preferred and also provides the
   optional analyzer. Use LLVM's [official getting-started instructions](https://clang.llvm.org/get_started.html)
   and [release downloads](https://llvm.org/releases/). An existing GCC toolchain
   can provide syntax/type checks; MinGW GCC 6.3 was verified here, with optional
   flags and requested dialects probed rather than assumed.
3. Make the driver available on PATH (reopen the shell if PATH changed), or pass
   its full path using `--compiler` or `--analyzer-executable`. Ensure the toolchain
   can find the target C standard-library headers. A driver installation alone
   does not ensure every target is configured; consult LLVM's
   [toolchain guide](https://clang.llvm.org/docs/Toolchain.html).
4. Verify discovery and a syntax-only check:

```powershell
python --version
Get-Command clang,gcc -ErrorAction SilentlyContinue
gcc --version
python analyze_c.py acceptance/fixtures/valid_inventory.c --compiler gcc
python analyze_c.py acceptance/fixtures/valid_inventory.c --compiler clang --static-analysis
```

The Clang command requires an installed, configured Clang driver; when absent the
CLI returns a tool-failure report rather than making claims about the source.
On other platforms use the same Python commands and their native shell's PATH
configuration. This workflow performs no compiler installation automatically.

```python
from extended_c import analyze_file, format_terminal, to_json

result = analyze_file('example.c', timeout=30)
print(format_terminal(result))
print(to_json(result))  # Returns a string; does not write any files.
```

Use `preference='clang'` or `'gcc'` to require a backend, or `executable=` for an
explicit driver path. Auto discovery prefers Clang, then GCC, on PATH. Discovery
checks the driver version, required syntax-only support, and each optional flag
on valid stdin C before enabling it. `discovery_timeout` bounds each probe;
`timeout` bounds the analysis invocation. Discovery takes multiple probes.

The invocation uses argument lists and no shell, linking, binary execution,
source edits, or compiler fix application. Source bytes are passed through the
original file. Compiler output is decoded as UTF-8 with replacement for malformed
bytes, and raw stdout/stderr are retained. Locale is set to C where supported.

Result status meanings:

- `completed`: the compiler finished checking, potentially reporting errors.
- `failed`: input, discovery, execution, or uninterpretable failure prevented checking.
- `timed_out`: analysis timed out without recognized findings.
- `partial`: findings survived a timeout, a fatal diagnostic prevented completion,
  or output/execution indicated an incomplete check. Read `issues` for the cause.

Completion is operational, not a guarantee that every line or bug was checked.
Compiler recovery can hide or cascade errors. Warnings indicate suspicious code,
not necessarily bugs. Missing headers or build configuration can prevent useful
analysis. This pipeline checks one translation unit with optional include paths,
macro definitions, and C standard selection. It does not detect all runtime or logic errors.
Static analysis is available only by explicit request, as described below.

Text diagnostic collection supports common GCC/Clang file/line/column and driver
messages, including Windows drive paths. Wrapped message prose and emitted
source snippets attach to the preceding diagnostic. Real integration tests use the installed backend;
Clang behavior cannot be claimed verified when only GCC is installed. A timeout
terminates the direct subprocess via Python's subprocess API; it is not a sandbox
or a cross-platform process-tree/resource limiter for compiler descendants.

Independent fixtures cover standard C constructs, independent syntax errors,
semantic/type failures, intentional assignments, and missing dependencies. Tests
also generate a larger program and verify source preservation and no build output.
The requested `c_error_detection_500_lines.c` was absent during Milestone 1.

## Reporting contract (schema version 1.0)

`to_report(result)` returns JSON-compatible data; `to_json(result, indent=2)`
serializes the same data with Unicode preserved. `format_terminal(result)` returns
readable text with terminal control characters escaped. These functions do not
print or write to source files. They report external compiler evidence only,
never SmartParse/CGAR recovery results.

The following keys are always present. Missing values use JSON `null`, not
invented locations, identifiers, or source snippets. A breaking schema change
requires a new major version; consumers should tolerate additive fields.

| Top-level key | Type and meaning |
|---|---|
| `schema_version` | String, currently `"1.0"` |
| `analysis_mode` | String, always `"extended_c"` |
| `status` | `completed`, `failed`, `timed_out`, or `partial`, as defined above |
| `compiler` | Object with string `path`, `backend`, `version`, and string-array `flags`; or null if discovery failed |
| `summary` | Object with integer `total_diagnostics`, `errors`, `warnings`, `notes`, and `categories` |
| `diagnostics` | Ordered array of diagnostic objects described below |
| `tool_issues` | String array of wrapper/discovery/execution/completion issues; excluded from diagnostic counts |
| `execution` | Object with integer-or-null `returncode` and string-array `command` |
| `raw_output` | Object with string `stdout` and `stderr`, retaining decoded compiler output including color escapes |
| `unrecognized_output` | String array of unrecognized stderr lines, with display color escapes removed |

Every diagnostic has exactly these version 1.0 fields:

| Field | Type and meaning |
|---|---|
| `file` | String or null; compiler-reported filename, not automatically resolved |
| `line`, `column` | Positive integer or null; compiler-reported coordinates (not converted to Unicode offsets) |
| `severity` | `fatal error`, `error`, `warning`, or `note` |
| `category` | `syntax`, `semantic/type`, `compiler warning`, or `unknown` |
| `message` | String; wrapped prose joined with newline; trailing warning identifier separated out |
| `source_snippet` | String or null; compiler-emitted source line, with display gutter removed |
| `backend` | String, `gcc` or `clang`; identifies the external producer |
| `diagnostic_id` | String or null; currently trailing `-W...` identifier when emitted |

Summary `errors` includes fatal errors. Notes count as diagnostics and use the
`unknown` category. `categories` always contains all four category keys with
integer counts, including zeros; their sum equals `total_diagnostics`. Warnings
remain `compiler warning` regardless of suspected syntax/type implications.
Only narrowly recognized error wording (expected punctuation/expression,
undeclared names, incompatible types, argument-count errors, etc.) receives
syntax or semantic/type classification. Other errors, including missing headers,
remain `unknown`. This categorization is explanatory, not compiler ground truth.

An input yielding unrecognized stderr alongside diagnostics is marked `partial`;
raw evidence is retained. Include-context lines, caret decorations, and compiler
summary lines are not extra diagnostics. Separate actual diagnostic headers,
including repeated identical ones, are preserved. Indented wrapped prose before
a source block attaches to its preceding message. Unsupported layouts may remain
unrecognized; a text adapter cannot disambiguate every possible compiler format.

Only compiler-emitted snippets are collected; no extra paths named by diagnostics
are opened. Snippets can be unavailable when the compiler omits them. Output is
decoded UTF-8 with replacement, so invalid byte sequences are not byte-exact raw
archives. Original source bytes remain untouched. GCC/Clang text fixtures test
both formats; actual Clang integration is explicitly skipped when unavailable.

## Optional Clang Static Analyzer (Milestone 3)

```python
from extended_c import analyze_file, analyze_static, format_terminal, to_json

# GCC can remain the regular syntax/type backend; Clang is discovered separately.
result = analyze_file('example.c', preference='gcc', static_analysis=True,
                      analyzer_timeout=30, analyzer_executable=None)
print(format_terminal(result))
print(to_json(result))

# Or explicitly request only the independent analyzer pass:
analyzer_result = analyze_static('example.c', timeout=30)
```

With the default `static_analysis=False`, no analyzer discovery or invocation
occurs. `analyzer_executable` selects an explicit Clang driver; there is no GCC
analyzer fallback. GCC 6.3 remains supported for regular diagnostics. A requested
analyzer pass runs independently even if the ordinary compiler rejects the file;
frontend errors may prevent useful analyzer results.

Discovery verifies Clang identity, syntax-checking capabilities, and the exact
`--analyze -Xanalyzer -analyzer-output=text` invocation on a valid stdin C probe.
It rejects nonzero exits and warning-only ignored/unsupported arguments. No
particular checker inventory or version is assumed: this milestone uses Clang's
default enabled checkers. Depending on version and platform these may find
potential null dereferences, leaks, use-after-free, and double-free. Detection
is not guaranteed, even for a program with one of these defects.

Both the capability probe and real pass place the `-o` output in their own private
`TemporaryDirectory`, cleaned on success, failure, and timeout. `analyze_static`
and `discover_analyzer` accept `temp_dir=` as an optional scratch parent. No
temporary copy or rewrite of the original source is needed. Output is text on
stderr; temporary artifacts are discarded. Execution uses the same no-shell,
timeout-controlled subprocess boundary as ordinary compiler checks; no compiled
user binary is executed. As with Milestone 1, this is not a compiler sandbox or
cross-platform process-tree/resource limiter.

### Additive reporting extension

Existing calls and ordinary reports retain the Milestone 2 schema and behavior.
When requested, `result.static_analysis` contains its independent `AnalysisResult`.
JSON adds a `static_analysis` subreport only for an explicitly requested pass;
the top-level status, diagnostics, compiler, and summary still describe ordinary
syntax/type checking. Consumers must inspect the analyzer subreport's status too.

Analyzer reports use the same version `1.0` envelope and diagnostic fields, with
`analysis_mode: "clang_static_analyzer"` and these additive fields:

| Field | Meaning |
|---|---|
| `diagnostics`, `summary` | Ordinary Clang frontend errors/warnings/notes from the analyzer invocation; backend `clang` |
| `findings` | Separate array of potential analyzer findings and path notes; backend `clang-static-analyzer` |
| `findings_summary` | Same count structure as `summary`, counting only `findings`; warning counts exclude path notes |

Checker-tagged warnings such as `[core.NullDereference]` establish analyzer
provenance, with the tag preserved in `diagnostic_id`. Following path notes are
attached to the analyzer source until the next ordinary diagnostic. Untagged
warnings remain ordinary frontend warnings; message keywords alone do not prove
an analyzer finding. Checkers with unsupported output layouts may remain in
ordinary/unrecognized output. No cross-source deduplication is performed.

Static findings use category `unknown`, preserving the four-category enum instead
of misleadingly classifying a potential runtime defect as a syntax/type error or
ordinary compiler warning. The separate findings array, backend, checker ID, and
terminal section identify their source. They are potential static-analysis issues,
not observed runtime failures or proof of programmer intent.

Analyzer status is independent:

- `completed`: invocation exited normally, with zero or more potential findings.
- `unavailable`: usable Clang or the required analyzer invocation could not be verified.
- `failed`: input, execution, or output handling prevented analysis without retained diagnostics/findings.
- `timed_out`: the analysis invocation exceeded its timeout without retained diagnostics/findings.
- `partial`: retained evidence from an interrupted/failed pass, or unrecognized output prevented a confident completion report.

Capability-probe failure/timeout means `unavailable`, with its cause in tool
issues. Analysis timeout with findings means `partial`, with the timeout cause
retained. Raw analysis stdout/stderr and execution metadata remain available in
the subreport. Terminal reporting explicitly warns that unavailable analysis or
zero findings does not establish that source code is bug-free.

Independent C fixtures cover the four memory/pointer cases. Unit tests use mocks
for capability, invocation, parsing, failure, timeout, separation, and cleanup.
Live tests skip when Clang is absent or the capability probe is unsupported. On
a usable installation they require normal completion, then skip a fixture with an
explicit explanation if default checkers emit no finding. They do not require
particular checker names or exact finding counts across versions. Live validation
was pending on the Milestone 3 development machine because Clang was absent.

## Command-line interface (Milestone 4)

Run from the repository with Python 3.12 (Windows PowerShell examples):

```powershell
python analyze_c.py "C:\Projects\My Application\program.c"
python analyze_c.py program.c --compiler gcc --std c11 -I "include directory" -D FEATURE=1
python analyze_c.py program.c --compiler "C:\Program Files\LLVM\bin\clang.exe" --json
python analyze_c.py program.c --static-analysis --analyzer-executable "C:\Program Files\LLVM\bin\clang.exe" --timeout 60
python analyze_c.py --help
```

The positional argument must name an existing regular `.c` file. Quote paths and
macro values containing spaces. Include paths are relative to the current working
directory, not automatically relative to the source directory. Source-local quoted
includes still follow compiler include rules. Options:

| Option | Meaning |
|---|---|
| `--compiler auto\|gcc\|clang\|PATH` | Default `auto` prefers Clang, then GCC; an explicit path never falls back to another executable |
| `--std`, `--standard` | C dialect such as `c11` or `gnu11`; otherwise compiler default. The selected compiler must pass a syntax-only capability probe for this spelling |
| `-I`, `--include-dir` | Repeatable include directories, including paths with spaces |
| `-D`, `--define` | Repeatable object-like macros, `NAME` or `NAME=VALUE`; function-like command-line macros are not supported |
| `--timeout` | Positive finite seconds per analysis pass, default 30 |
| `--discovery-timeout` | Positive finite seconds per capability probe, default 5; total discovery may take multiple probes |
| `--static-analysis` | Explicitly request the independent Clang analyzer pass |
| `--analyzer-executable` | Explicit Clang path for the analyzer; requires `--static-analysis`. Otherwise analyzer discovery uses Clang on PATH independently of `--compiler` |
| `--analyzer-timeout` | Analyzer timeout; defaults to `--timeout`; requires `--static-analysis` |
| `--json`, `--format json` | Emit only existing schema 1.0 JSON to stdout; default `--format terminal` |

Both passes receive the same standard/include/macro options, validated as separate
compiler arguments without a shell. Standards are checked independently on each
selected compiler. Unsupported standards become clear tool failures; no modern
standard support is assumed for GCC 6.3. No arbitrary compiler flags, linking,
fix-application, or binary execution options are exposed.

JSON retains the existing schema and independent `static_analysis` subreport when
requested. With no analyzer request the subreport is absent, and terminal output
explicitly says availability was not probed. Terminal reports show compiler
version, status, errors/warnings/notes, categories, and independent analyzer
status/findings. Existing Python APIs accept optional `standard`, `include_dirs`,
and `defines` arguments as well. Defaults preserve the earlier API behavior.

| Exit code | Meaning |
|---|---|
| `0` | All requested passes completed; no compiler errors and no potential analyzer findings. Compiler warnings/notes alone do not fail the command |
| `1` | Completed checks reported source errors or potential analyzer findings; analyzer path notes alone do not fail the command |
| `2` | Invalid command-line usage, unknown options, malformed macro/standard spelling, or nonpositive/nonfinite timeout. Argparse prints usage to stderr; help exits 0 |
| `3` | Any requested pass failed, was unavailable, timed out, or only partially completed; also input/output failures. This takes precedence over code 1 |

For example, missing headers produce incomplete analysis and code 3, even when
fatal compiler diagnostics are retained. Syntax/type rejection after normal
compiler completion produces code 1. With static analysis requested, frontend
errors may prevent analyzer completion and therefore yield code 3. Missing files,
wrong extensions, missing compilers, and unsupported dialects yield structured
tool-failure reports rather than tracebacks. Invalid CLI arguments yield argparse
text, even with `--json`. JSON is emitted to stdout only, with no report-file write
option that could overwrite a source file.

The CLI is a single-translation-unit checker, not a build system. Supply the same
include directories, defines, and dialect your project requires; compilation
databases, target selection, multi-file linking, and project-specific build flags
are not yet supported. Diagnostics may cascade or be suppressed after serious
errors. An unfamiliar large file is handled by the compiler rather than the
SmartParse lexer. Independent CLI tests generate valid and invalid programs over
620 lines, with real C constructs and errors distributed across the invalid file.
The user-provided 500-line sample was subsequently found outside the checkout in
Downloads during Milestone 5; see the acceptance record below.

## Acceptance status and supported checks (Milestone 5)

The [acceptance report](../acceptance/FINAL_ACCEPTANCE_REPORT.md) records the
initial GCC-only run and subsequent live Clang validation: **237 tests passed,
zero failures/errors/skips**, including all five previously skipped integration
tests. Clang 17.0.2 was found bundled with the Android NDK, outside PATH; no
installation or permanent PATH change was needed. Final acceptance awaits user
review. The unchanged sample still has frontend errors that block its path analysis.

| Analysis layer | What evidence it can provide | What the current results establish |
|---|---|---|
| Original SmartParse/CGAR | Restricted C-like syntax diagnostics, recovery and grammar-verified suggestions | Existing 141-test behavior preserved; no attribution of compiler findings to CGAR |
| GCC/Clang syntax-only | Backend syntax/type errors and enabled warnings, including invalid calls, names, returns, formats, suspicious conditions | Actual GCC 6.3 output collected, categorized, and reported; no full semantic or bug-freedom proof |
| Optional Clang Static Analyzer | Potential path-sensitive memory/pointer/resource problems under supported default checks | Live Clang 17 detected null dereference, leak, use-after-free, and double-free in independent fixtures; malformed sample analyzer pass is partial because frontend errors prevent completion |
| General runtime/logic analysis | Some suspicious constructs may produce warnings, but intent and all execution paths are not modeled | Reviewed bounds, ownership and logic defects can be missed; no program is executed |

The provided file contains display prefixes (`001 |`). The acceptance workflow
writes a new cleaned copy under `acceptance/cleaned/`, preserves all 500 physical
lines and original newlines, verifies that each prefix matches its physical row,
and records original/cleaned SHA-256 hashes. It refuses mismatched or mixed
numbering. This is an explicit test-copy transformation, not automatic source
repair by the CLI. Diagnostics refer to the cleaned filename; line N maps to
original numbered line N. The original in Downloads remains untouched.

```powershell
python acceptance/run_acceptance.py --sample "C:\Users\saami\Downloads\c_error_detection_500_lines.c"
python acceptance/summarize_acceptance.py
python analyze_c.py acceptance/cleaned/c_error_detection_500_lines.c --compiler gcc --json
```

Acceptance artifacts are separate from historical research outputs:
`acceptance/output/` contains full JSON, terminal reports, exact diagnostic
messages, source-reference comparison, test logs, subprocess audit events, and
preservation hashes. The acceptance runner snapshots/restores legacy CSVs because
some original tests rewrite performance data. Use this runner when protecting
historical results; plain `unittest discover` retains that legacy write behavior.

Measured sample results were 6 errors, 14 warnings, 3 notes, with diagnostics
through line 494. These include cascades from the missing semicolon at 30; the
undeclared-global_label errors at 432/438 do not detect allocation overflow or
use-after-free. A manual non-exhaustive 68-entry reference distinguishes detected,
missed, unsupported, and uncertain issues, separately from the backend category.
Neither that review nor the three new acceptance controls is a blind benchmark.
All 17 historical CSVs, original Python scripts, existing C fixtures, and the
external original were verified unchanged. No source fixes, commits, or pushes
were applied.

## Final Clang validation on Windows

Two previously installed off-PATH drivers were found: Android NDK Clang 17.0.2
and CodeBlocks MinGW Clang 19.1.7. Version 17.0.2 was selected and fully validated;
19.1.7 was version-checked only. The full search evidence and measured outputs
are in `acceptance/output/clang_discovery.json` and `acceptance/output/clang_validation/`.
The validation script uses a process-local PATH, leaving the user's environment
unchanged. Verify or invoke the selected installation explicitly:

```powershell
& "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --version
python analyze_c.py tests_fixtures/extended_c/null_pointer.c --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --static-analysis --analyzer-executable "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --json
python acceptance/validate_clang.py --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe"
python acceptance/summarize_clang.py
```

Live output exposed an explicit Clang result-type phrase and fix decorations
that needed extended-adapter handling. These have regression tests. Clang's
optional `-fno-diagnostics-fixit-info` is capability-probed before use to suppress
inline replacement decorations while retaining diagnostic notes. Source snippets
preserve Clang indentation. No suggested fix is applied, and the original
SmartParse/CGAR parser/recovery code is unchanged.

The sample compiler pass completed (7 errors, 12 warnings, 11 notes, exit 1).
Its analyzer pass retained 7 frontend errors and 2 notes, with **zero findings
and partial status**, making the combined CLI exit 3. This is not a negative
memory-safety result. Four independent fixtures each produced one analyzer
warning; the separate pointer/logic acceptance program produced four analyzer
warnings and 16 path notes. General intent-dependent logic remains unchecked.
Both compilers' evidence is matched once per reviewed reference root, rather
than summing diagnostic counts, cascades, or path notes. See the report's updated
68-entry comparison and matching criteria. Historical GCC-only measurements
remain available for comparison rather than being overwritten.
