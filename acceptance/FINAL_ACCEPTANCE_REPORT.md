# Extended SmartParse acceptance report — 27 October 2026

**Disposition: live Clang validation completed; final release approval remains pending user review.**

The final-validation update below supersedes the earlier GCC-only environmental
limitations. The earlier measured GCC results remain recorded separately.

This report separates SmartParse/CGAR research from external compiler evidence.
No GCC or Clang findings below are attributed to CGAR. Compiler completion does
not establish that every bug was detected or that the program is safe to run.

## Final validation update: installed Clang located and exercised

A filename-only Windows search and registry inspection found two installations
outside PATH. No installation was needed and no permanent PATH setting changed:

| Installation | Measured version | Validation scope |
|---|---|---|
| `C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe` | Android NDK Clang **17.0.2**, default target `x86_64-w64-windows-gnu` | Selected for full tests and live analyzer validation |
| `C:\Program Files\CodeBlocks\MinGW\bin\clang.exe` | Clang **19.1.7**, default target `x86_64-w64-windows-gnu` | Version verified only; not claimed analyzer-validated |

See [discovery evidence](output/clang_discovery.json) and
[installation records](output/clang_installation_records.json). Broad filename
traversal found the two drivers on C:; further exhaustive disk enumeration was
stopped after a usable analyzer was verified. This is not an assertion that these
are the only Clang copies anywhere on the machine. Driver 17.0.2 successfully
resolved the tested C headers using its current environment; that does not prove
other targets or SDKs are configured.

The validation script prepends the selected driver directory to PATH only inside
its own process and validation children. The normal user's PATH remains unchanged.
Private analyzer temporary directories could not be traversed under the agent's
restricted Windows token. The live tests therefore ran with authorized execution
outside that sandbox; no compiler installation or C program execution occurred.

### Final test results and fixes exposed by live validation

- The **five previously skipped integration tests passed: 5/5, zero skips**.
- The **complete suite passed: 237/237, zero failures, zero errors, zero skips**.
- All **141 original SmartParse/CGAR tests** remain passing. GCC-specific tests
  also passed using the existing **MinGW GCC 6.3.0**.
- Live Clang exposed an unrecognized `incompatible result type` error phrase and
  inline assignment-fix decorations. The extended adapter now classifies that
  explicit type evidence, preserves Clang source indentation, and recognizes the
  narrow assignment-hint layout. Two new regression tests cover those cases.
- Additional compiler fix decorations in the sample are suppressed using
  capability-probed `-fno-diagnostics-fixit-info` when Clang supports it. Diagnostic
  notes remain visible and no fixes are applied. GCC flags/behavior are unchanged.
- One intermediate full-suite run had a five-second discovery-probe timeout during
  concurrent disk enumeration. It was reported as a tool failure. After stopping
  that enumeration, the full rerun passed without increasing or disabling timeouts.

These changes affect only the extended compiler adapters and their tests, not
SmartParse/CGAR or original evaluation scripts. Final logs:
[previously skipped tests](output/clang_validation/previously_skipped_tests.txt),
[full suite](output/clang_validation/tests.txt), and
[test counts](output/clang_validation/tests.json).

### Actual static-analysis findings

The independent fixtures completed under Clang Static Analyzer. Each emitted
**one warning**; path notes are supporting traces, not additional defects:

| Fixture | Line | Checker identifier | Measured warning | Path notes |
|---|---:|---|---|---:|
| null_pointer.c | 4 | core.NullDereference | Dereference of null pointer (loaded from variable 'pointer') | 2 |
| memory_leak.c | 7 | unix.Malloc | Potential leak of memory pointed to by 'pointer' | 4 |
| use_after_free.c | 7 | unix.Malloc | Use of memory after it is freed | 5 |
| double_free.c | 6 | unix.Malloc | Attempt to free released memory | 5 |

Exact locations/messages, emitted source snippets, and raw evidence are in the
[Clang comparison and inventory](output/clang_validation/comparison.md) and the
individual JSON/text reports in `output/clang_validation/`. The separate
`pointer_and_logic.c` acceptance program also produced **four analyzer warnings
and 16 path notes**, at lines 5, 12, 19, and 26. Its intentional assignment warning
stays an ordinary compiler diagnostic; the loop/contract bug at 32 was not detected.
These findings belong to **Clang Static Analyzer**, never to CGAR.

### Unmodified cleaned sample: compiler and analyzer results

| Pass | Completion | Errors | Warnings | Notes | CLI exit |
|---|---|---:|---:|---:|---:|
| GCC 6.3 syntax/type | completed | 6 | 14 | 3 | 1 |
| Clang 17 syntax/type | completed | 7 | 12 | 11 | 1 |
| Clang 17 analyzer frontend | partial | 7 | 0 | 2 | 3 when requested |

The Clang compiler categories were **2 syntax, 5 semantic/type, 12 compiler
warning, and 11 unknown** records. Analyzer findings are stored separately from
its **7 frontend errors and 2 frontend notes**. The sample analyzer emitted
**zero static findings because frontend errors prevented analysis from completing**.
This is not a clean memory-safety result. No syntax/type repair copy was created,
and the same unmodified cleaned source was used for GCC and Clang.

Reports: [Clang compiler JSON](output/clang_validation/sample.json),
[Clang compiler terminal](output/clang_validation/sample.txt),
[Clang analyzer JSON](output/clang_validation/sample_static.json), and
[case summary](output/clang_validation/cases.json). JSON contract and terminal
summary checks passed, including independent analyzer status and source attribution.

Different severities and cascades must not be counted as new defects:

- Clang adds a buffer-overflow warning at **74** that GCC syntax-only did not emit.
- Clang recovers the global declaration after the missing semicolon at 30; GCC's
  undeclared-global_label cascades at 432/438 are not two extra root defects.
- Clang reports mystery_value at 414 and 415, then reports a return conversion
  after suggesting last_value. That recovery is one undeclared-name root, not
  three independent bugs. No spelling correction was applied.
- The pointer-to-int return at 393 is a GCC warning and a Clang error. This is a
  severity difference for the same defect, not an extra detection.
- Both backends emit two warnings around the literal/comparison at 494. Notes
  are context, and repeated diagnostics are retained without adding references.

### Updated 68-entry reference comparison and matching rules

| Backend | Detected | Missed | Unsupported | Uncertain |
|---|---:|---:|---:|---:|
| GCC 6.3 | 15 | 1 | 37 | 15 |
| Clang 17 | 16 | 1 | 36 | 15 |

A match requires a relevant **non-note** diagnostic at the reviewed root line or
its documented reporting anchor. For the semicolons, GCC points to 31/83 while
Clang points to root lines 30/82. Message meaning and issue kind must agree: an
undeclared-name error at an allocation site does not diagnose its memory defect.
Multiple messages and multiple backends map to one reference entry, not extra bugs.

Detected means relevant evidence, not proven intent or an observed runtime crash.
Missed means a reviewed syntax/type issue had no relevant diagnostic in this run
(the nonvoid fallthrough at 405). Unsupported entries lack the needed general
logic/contract check or a completed analyzer pass on this malformed sample;
they separately record compiler_outcome=missed. Uncertain entries retain
unspecified contracts/preconditions/environment even if a warning exists. Floating
division at 382 remains uncertain: GCC warned, Clang did not, and no integer-UB
claim is made. The combined backend evidence matches **16** non-uncertain reference
entries, not 15+16. These list dispositions are not precision/recall or exhaustive
bug counts. See the [full 68-row comparison](output/clang_validation/comparison.md)
and [machine-readable mapping](output/clang_validation/reference_comparison.json).

### Preservation and remaining limitations

The final [hash manifest](output/clang_validation/preservation.json) confirms all
**17 historical CSVs**, original tracked parser/evaluation Python files, C fixtures,
the external numbered source, and the cleaned 500-line source are unchanged.
Legacy timing CSV writes were restored byte-for-byte in finally. No new build
artifacts appeared, and audited CLI subprocess commands contain only compiler
probes, syntax-only checks, or requested static analysis. No user's C binary was
built and executed. Only the extended adapter/test fixes, validation scripts,
documentation, and new measured artifacts changed.

The missing-Clang blocker is resolved. Remaining limitations are the sample's
frontend errors blocking its analyzer pass, default-checker/version dependence,
single-translation-unit/build-context limits, and incomplete logic/contract
analysis. Successful memory-fixture checks do not establish complete detection
on unfamiliar programs. **Final acceptance and release approval remain pending
user review.** No commit, push, software installation, or permanent PATH change
was performed.

Reproduce the live validation and comparison using the installed driver:

```powershell
python acceptance/validate_clang.py --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe"
python acceptance/summarize_clang.py
```

## Earlier GCC-only acceptance baseline (retained history)

The following sections record the earlier 235-test/5-skip baseline. Their
missing-Clang statements describe that earlier PATH-only validation and are
superseded by the measured final-validation update above.

## Environment and automated tests

- Windows workspace, PowerShell, Python **3.12.5**.
- Compiler: **gcc.exe (MinGW.org GCC-6.3.0-1) 6.3.0**, `C:\MinGW\bin\gcc.exe`.
- **235 tests run: 230 passed, zero failures, zero errors, five skips**.
- All **141 original SmartParse tests passed**. Existing restricted grammar,
  recovery, CGAR, and research evaluation Python files were preserved.
- Skips: the live Clang reporting test and the live null-pointer, leak,
  use-after-free, and double-free analyzer tests. Clang was unavailable on PATH.
  Common standalone LLVM and MinGW/MSYS2 Clang locations were also checked and
  absent. No live analyzer findings are claimed.
- Full [test log](output/tests.txt), [test summary](output/tests.json),
  [case summary](output/cases.json), and [preservation manifest](output/preservation.json).

The suite includes compiler-capability mocks, independent GCC/Clang diagnostic
text fixtures, failure/timeout/cleanup checks, schema/CLI tests, and generated
valid and invalid programs exceeding 620 lines. Mock success is not live Clang
validation. Acceptance added five tests for cleaning and independent report
contract validation; no parser or recovery implementation changes were required.

## The supplied 500-line sample

The file was located at `C:\Users\saami\Downloads\c_error_detection_500_lines.c`,
outside the checkout. Earlier milestone statements that it was absent from the
checkout were accurate but did not cover that Downloads location.

Every original row had a prefix such as `001 |`. A separate
[cleaned test copy](cleaned/c_error_detection_500_lines.c) removes only those
prefixes. It still has **500 physical lines**, preserving original line endings
and a one-to-one mapping to numbered original lines. There are no repairs to
syntax, types, or logic. The original source is untouched.

- Original SHA-256: `01fbad6a1e764207c8537efab725c73c6fb67e8d6430dbedae69ff24192a6367`.
- Cleaned SHA-256: `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`.
- [Provenance and mapping](output/sample_provenance.json).

The actual CLI checked the cleaned file using GCC, accepted preprocessing,
typedefs, structures, pointers, arrays, strings, and function definitions, and
reported issues through **line 494**. Result: **completed**, exit **1**, **6 errors,
14 warnings, 3 notes**, with **2 syntax**, **4 semantic/type**, **14 compiler
warning**, and **3 unknown** diagnostic records. Those category counts include
cascades and notes, not independent confirmed bugs.

All line numbers, columns, categories, identifiers, and exact messages are in the
[diagnostic inventory](output/diagnostics.md), [full JSON](output/sample.json),
and [terminal report](output/sample.txt). Detected examples include missing
semicolons (root lines 30 and 82, reported at 31 and 83), assignments in conditions
(104, 115, 149, 351), returning local addresses (129, 236), empty-body/indentation
warnings (164), format/type problems (292, 393, 421), an invalid call (409), an
undeclared name (414), and the multicharacter literal/comparison (494).

The errors at 432 and 438 concern `global_label` after the declaration at 31 was
rejected following the missing semicolon at 30. They are recorded compiler
cascades, **not** detection of allocation overflow or use-after-free at those
sites. Two warnings at 164 and two at 494 are not four separate root bugs.

## Reference comparison and missed issues

A manual, non-exhaustive [68-entry source reference](sample_reference.json) was
established before the acceptance CLI execution. The [entry-by-entry comparison](output/sample_comparison.md)
and [machine-readable comparison](output/sample_comparison.json) distinguish:

- **15 detected** reference issues with relevant compiler evidence.
- **1 missed** syntax/type reference: nonvoid fallthrough at 405 had no warning
  in this exact invocation. Earlier serious errors may suppress later warnings;
  absence is recorded without claiming a precise cause.
- **37 unsupported** reference assessments: missed by this compiler pass, with
  the appropriate analyzer unavailable or general contract/intent analysis absent.
- **15 uncertain** entries involving unspecified contracts, caller preconditions,
  threading assumptions, or floating-point environment. A warning may still exist.

These are review-list counts, **not recall, precision, independent bug counts, or
universal detection rates**. The comparison separately records each compiler
outcome, so unsupported assessments do not hide compiler misses. Examples missed
by GCC syntax-only checking include bounds errors at 55/202/245, use-after-free at
71/439, double-free at 252, a leak at 271, and contract-dependent arithmetic/loop
logic. The floating division at 382 is warned about, but is not described as
integer division-by-zero UB. The apparent threading concern at 427 is not proven
by a program that contains no threading.

## Three additional independent programs

These are newly authored acceptance programs with a [manual reference](REFERENCE.md),
not a blind third-party corpus. They complement the user's unfamiliar sample.

| Program | Measured CLI result | Reference comparison |
|---|---|---|
| `valid_inventory.c` | Completed; 0 errors/warnings/notes; exit 0 | Reviewed standard C structures, arrays, strings and loops accepted; no observed false alarm |
| `broken_records.c` | Completed; 4 errors, 2 notes; exit 1 | Both syntax defects (4, 9) and both semantic/type defects (13, 17) detected; notes are context |
| `pointer_and_logic.c` | Completed; 1 warning, no errors; exit 0 | Null dereference (5), leak (12), use-after-free (19), double-free (26), and contractual loop bug (32) missed by GCC syntax-only pass. Memory analyzer assessment unsupported. Assignment at 38 deliberately intentional: warning is useful suspicion, not a confirmed bug |

Additional checks reproduced the existing semantic fixture (3 errors, 1 warning,
2 notes; exit 1) and missing-header fixture (fatal error, partial; exit 3).
Generated large-file tests and preservation assertions remain in the full suite.

## JSON, terminal output, exit codes, and analyzer status

Saved JSON reports passed an independent dependency-free validation of schema
1.0 required fields, types, enums, diagnostic identifiers/locations, summary
counts, and analyzer subreport separation. This is validation against the
documented contract, not certification by an external JSON Schema engine.
Terminal outputs were captured independently and checked for status and count
agreement. All four CLI codes were exercised: clean/warnings-only 0, source
errors 1, invalid arguments 2, missing-header/incomplete analysis 3. The suite
also covers missing compilers, malformed bytes, missing files, and timeouts.

Explicit `--static-analysis` on the sample preserved all GCC diagnostics and
reported analyzer **unavailable**, with exit **3**, independently of compiler
status **completed**. See [JSON](output/sample_static.json) and
[terminal output](output/sample_static.txt). Zero recorded analyzer findings here
means the analyzer did not run; it is not a clean analyzer result. Even with a
working analyzer, unresolved syntax/type errors may prevent path analysis; any
future repaired copy must be separately labeled and must not replace this baseline.

## Preservation and execution evidence

All **17 historical research CSVs** are unchanged byte-for-byte. Legacy tests
rewrite a performance CSV; the acceptance runner snapshots and restores its
original bytes in `finally`. Original tracked Python files, existing C fixtures,
the new acceptance fixtures, and the external numbered original were hashed and
verified unchanged. Only a new cleaned source copy and acceptance artifacts were
written; no source repair was applied. No historical evaluation script changed.

Each live acceptance CLI run recorded Python subprocess audit events in
`output/*.processes.jsonl`. Child commands were compiler version probes,
syntax-only checks, or explicitly requested analyzer invocations. There was no
application-binary command, and no new `.exe`, `.o`, `.obj`, `.out`, or `.plist`
file appeared in accessible workspace directories. The audit covers Python's
direct subprocess boundary, not every compiler-internal OS descendant. Together
with `-fsyntax-only`/`--analyze` invocation checks, this verifies that this tool did
not build and execute the user's C program. It is not a security sandbox claim.

## Remaining release conditions

Live Clang/Clang Static Analyzer validation remains the exact environmental
blocker. Supply a usable Clang toolchain with its target C headers, rerun the live
tests and independent memory fixtures, and review their actual findings. No
installation or environment change was made automatically.

Other limits remain: one translation unit at a time, user-supplied build context,
compiler-dependent warnings and recovery, default analyzer checkers only, no
general logic/intent proof, and no exhaustive memory-safety guarantee. Documentation
and available acceptance evidence are ready for review; **final acceptance is not
declared**. No commit or push was made.

Reproduce from the repository root:

```powershell
python acceptance/run_acceptance.py --sample "C:\Users\saami\Downloads\c_error_detection_500_lines.c"
python acceptance/summarize_acceptance.py
```

The human conclusions in this report must be reviewed after a new run; measured
artifacts are refreshed by the commands. The prefix cleaner refuses nonsequential
or mixed numbering rather than silently changing source locations.
