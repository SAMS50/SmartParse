# Milestone 9: integration, CLI and release validation

Status: unified implementation complete for review; release publication requires user approval. Independent human adjudication remains pending. No commit, push, merge or GitHub release was performed.

## Audit and implementation

The repository was inspected before implementation: original parser/recovery and panic baseline, `analyze_c.py`, Extended C schemas, v2 eligibility, v3 bounded execution/recovery, v4 isolation, v5 memory capabilities, v6 semantics, v7 external adapters and v8 evaluation artifacts. The starting branch is `feature/phase6-recovery`, HEAD `9f8d005`. Milestone 8 remains present as uncommitted completed work; this milestone does not commit or rewrite it.

The actual pre-integration baseline was rerun: **452 passed, zero failures/errors/skips**, in **231.844 seconds**. The implementation builds on those modules rather than replacing them.

The new entry point is **`python -m smartparse_cli`**, version **0.9.0**. A separate package avoids shadowing or replacing `smartparse.py`. The original parser, recovery algorithms, CGAR, `analyze_c.py`, versioned pipelines and all earlier commands remain unchanged. Original CGAR research switches remain accessible through the existing demo/research commands; the unified restricted-grammar mode uses the original default parser.

`analyze` defaults to ordinary compiler diagnostics. Explicit selections support compiler, CSA defaults, memory, semantic (including memory), GCC14, Cppcheck, original SmartParse and panic. Recovery/isolation are opt-in and add the existing memory pipeline when required. Selecting both memory and semantic executes the semantic superset once. Optional external tools always analyze original sources, independently of Clang variants.

`doctor` performs bounded executable/version discovery without installing software or changing system PATH. It locates the available GCC **6.3.0**, SDK Clang **17.0.2**, GCC **14.2.0** and Cppcheck **2.16.0**. Analysis separately probes compiler/checker support. Explicit choices do not silently fall back, and pinned v7 versions remain enforced.

## Diagnostic and reporting contract

Unified JSON is `smartparse.unified_analysis` **1.0**, documented by `smartparse_cli/schema.json` and its README. It retains source identity, configuration, tool versions, requested/effective passes, independent pass status/eligibility, every complete raw pipeline report, normalized records, exact evidence groups, suggestions, provenance and limitations.

Normalized evidence contains reported/mapped locations, severity/category/message, backend and original ID, source snippets, raw-record references, repair suggestions where provided, conditioning, and completeness. Backend-supplied categories are retained; a narrow known-checker display taxonomy gives CSA null/malloc/bounds/stream diagnostics useful categories. Unknown IDs are not classified from English message guesses. Raw categories and all prior frozen evidence remain unchanged.

Baseline source diagnostics remain separate from repair/isolation-conditioned evidence. Both conditioning flags are retained when both apply. Unknown/variant-reported locations are explicitly labeled rather than falsely described as physically mapped originals. Function/path completeness stays uncertified. Raw intermediate compiler/analyzer reports, suppressed findings and notes remain available without counting excluded-region observations as detections.

Exact same-backend source/location/diagnostic/provenance identity can share an evidence group. Every contributing diagnostic remains in JSON. Same-line warnings, cross-backend warnings and different conditioned snapshots are not automatically merged. `root_id` and confirmed-defect totals remain null; evidence-group counts are not defect-root counts. No accuracy metrics or reviewer decisions are invented.

Terminal output shows diagnostics, tool versions/status, original-versus-conditioned provenance, summary categories, recovery/isolation outcomes and limitations. Markdown supplies a readable report. UTF-8 output files use exclusive creation: existing files, sources, hard links and research artifacts cannot be overwritten accidentally.

Exit codes are **0** completed/no primary findings, **1** completed with warnings/errors/potential findings, **2** invalid arguments, **3** unavailable/failed/incomplete requested analysis or input/output failure. The original compiler CLI retains its prior warnings policy. An unsupported `--std c999` check exposed an unlocated-driver-error classification issue; it was fixed and a deterministic regression test added. Actual Clang now returns CLI exit **3**, with raw rejection evidence retained, instead of treating it as a source defect.

## Safety and budgets

All new orchestration uses the existing bounded no-shell runner. Compiler-only checks are syntax-only. The GCC14 analyzer's private objects are neither linked nor executed. Recovery and isolation use their existing private variants, source mappings, dependency checks, preprocessing safeguards and abstention policies. No new detector, speculative repair or relaxed recovery/isolation safety rule was introduced.

Inputs are bounded to 1 MiB. Default limits are 10 seconds per tool call, 120 seconds overall and 256 invocations, configurable within 30/240/512 maxima; existing tighter per-profile ceilings remain in force. Shared accounting includes capability/discovery calls. Cleanup has finite extra grace, and parser/OS overhead is not a hard real-time sandbox guarantee.

Missing files, extension errors, empty files, malformed C, encoding problems in restricted parsing, unsupported driver arguments, unavailable analyzers, crashes, timeouts, parsing failures and output failures are handled without ordinary user-facing tracebacks. Source preservation is checked after analysis. Zero findings and process success do not certify safety.

## Ready-to-copy PowerShell demonstration

Run from the repository root:

```powershell
python -m smartparse_cli --help
python -m smartparse_cli --version
python -m smartparse_cli doctor
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C12_valid_full.c
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C09_repair_null.c --compiler gcc
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C09_repair_null.c --recovery
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C10_isolate_null.c --isolation
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers gcc14,cppcheck
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory --format json
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory --format markdown
# The destination must not already exist.
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory --format json -o .\smartparse-report.json
```

Observed null-pointer terminal excerpt (absolute path shortened here):

```text
SmartParse 0.9.0 — completed
Original source unchanged: True
memory: completed; ... clang version 17.0.2 ...
C01_null.c:3:16: warning (memory safety; Clang Static Analyzer; original-source): Dereference of null pointer (loaded from variable 'probe') [core.NullDereference]
Diagnostic records: 0 errors, 1 warnings, 2 notes
Categories: memory safety=1
Conditioning: original-source=1
```

The valid full-C fixture exits **0**. The GCC syntax fixture exits **1**. Null/leak/bounds/static/external analyzer examples exit **1** with attributed evidence. Recovery and isolation examples expose their respective conditional findings and retain baseline errors. Missing headers and a deliberately nonexistent Cppcheck path exit **3**. The Markdown, JSON, terminal and actual report-destination checks succeeded. Full observed reports and commands are retained under `outputs/smoke/`.

The unchanged 500-line benchmark also ran through compiler/semantic/Cppcheck with recovery and isolation enabled. It exits **3**, preserving compiler blockers and original Cppcheck evidence; it does not claim successful whole-program eligibility. The original compiler, parser and CGAR demonstration commands were separately exercised successfully. No analyzed C program was executed.

## Tests and preservation

All **50 new deterministic integration tests** pass. They cover valid/syntax/multiple findings, saved immutable null/leak/bounds evidence, duplicate handling, raw-record references, conditional findings, unknown locations/categories, driver errors, unavailable tools, all formats/output handling, source preservation, exit codes, help/version, restricted lexer errors, dependency reuse and legacy implementation hashes.

Live checks passed **20/20 unified smoke cases**, plus **5/5 additional checks** for the benchmark, actual report destination and three legacy commands. The real unsupported-standard check confirms the final exit-code fix. Missing optional tool behavior is deliberately exercised; it is not skipped or represented as a successful analyzer pass. Deterministic normalization tests reuse immutable saved analyzer reports; live smoke tests separately verify installed-tool execution.

The complete suite was rerun after the final driver-error fix under a 600-second supervisor with installed Clang added only to the child test PATH. **502/502 tests passed: zero failures, zero errors, zero skips**, in **214.797 seconds**. This includes all 452 baseline tests and 50 new integration tests. Exact final counts/timing are in `outputs/regression_final.tests.json` and `outputs/regression_final.supervisor.json`. The earlier **501/501** pre-fix integration pass is retained separately, not mislabeled as final. Timings are operational records, not evidence of a speed improvement.

Preservation covers **2,145 pre-existing files**, including every frozen v1–v8 result/reference/review artifact, existing source fixture, research figure and all **17 historical CSVs**. The one authorized pre-existing file change is the root README. The legacy performance test rewrites `results/verified_performance.csv`; previous bytes are restored in `finally` and disclosed. Final-byte preservation is claimed, not unchanged timestamps or absence of transient legacy test writes. No historical evaluation or adjudication decision was regenerated.

## Changed files

The exact generated-artifact inventory is `outputs/changed_files.json`. Implementation/documentation changes are:

| File | Purpose |
|---|---|
| `README.md` | Unified usage, installation/discovery, architecture, provenance, demonstration, formats, exit codes, tests and limitations; older narrative marked historical |
| `smartparse_cli/__init__.py` | Public analysis API and release-candidate version |
| `smartparse_cli/__main__.py` | `analyze`/`doctor` arguments, safe report destination and exit policy |
| `smartparse_cli/tools.py` | Bounded discovery, environment/explicit overrides and doctor inventory |
| `smartparse_cli/engine.py` | Existing-pipeline orchestration, shared budgets, source preservation and raw-evidence collection |
| `smartparse_cli/diagnostics.py` | Conservative normalization, known-ID presentation taxonomy, exact evidence grouping |
| `smartparse_cli/reporting.py` | Terminal/JSON/Markdown rendering |
| `smartparse_cli/schema.json` | Versioned unified JSON contract |
| `smartparse_cli/README.md` | API/schema, source mappings, grouping and safety semantics |
| `test_smartparse_cli.py` | 50 deterministic integration/regression tests |
| `phase6/v9/__init__.py` | New milestone validation namespace |
| `phase6/v9/validate.py` | Baseline/final suite supervision and preservation audit |
| `phase6/v9/smoke.py` | Reproducible live end-to-end checks |
| `phase6/v9/MILESTONE_9_REPORT.md` | This implementation/validation report |
| `phase6/v9/outputs/*` | Hash snapshots, original README copy, test logs/results, actual CLI reports/commands, audit and inventory |

## Release readiness and limitations

The unified implementation is suitable for the tested Windows university-project demonstration and review as a GitHub release candidate. Actual publishing remains pending user approval. No source/recovery/detection algorithms were redesigned. The CLI has no third-party Python dependency and is runnable directly from a repository checkout; no wheel/installer or IDE integration is claimed.

Live validation is Windows 11/Python 3.12.5 with the installed tool versions above. POSIX process support is inherited but this milestone has no separate Linux/macOS live matrix. Cppcheck retains its win64 model; GCC14/Cppcheck profiles are pinned. Target headers, libraries, macros and project configuration affect findings. No compilation-database import, arbitrary build execution, multi-translation-unit completeness or general C semantic solver was added.

Grouping intentionally leaves many cross-tool duplicates unresolved. Compiler cascades are retained, not counted as independently confirmed roots. Existing recovery/isolation restrictions can prevent eligibility gains on large malformed programs. Existing CSA alpha checks and semantic facts retain their experimental/assumption-dependent status. The v8 matching/reference limitations and pending human adjudication are unchanged; no research accuracy improvement is claimed by this integration release.

Work stops at Milestone 9 for review.
