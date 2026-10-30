# Phase 6 v7: controlled external-analyzer evaluation

V7 compares installed tools against frozen v6 evidence, then exposes only source-reviewed beneficial profiles. Earlier SmartParse/CGAR, Extended C, v1–v6, references, defaults and research artifacts are unchanged. New analysis is **opt-in**. No software is installed/upgraded and no user C program is executed.

## Selected usage

```powershell
# Disabled: no tool invocation.
python -m phase6.v7 "C:\my sources\input.c" --json

# Explicitly request the reviewed GCC 14.2 analyzer profile.
python -m phase6.v7 "C:\my sources\input.c" --external-analysis --tool gcc14 --json

# Explicitly request Cppcheck 2.16 on the original source.
python -m phase6.v7 "C:\my sources\input.c" --external-analysis --tool cppcheck --std c11 -I "C:\my headers" -D FEATURE=1 --json

# An executable override is explicit and still version/capability checked.
python -m phase6.v7 input.c --external-analysis --tool gcc14 --executable "C:\Program Files\CodeBlocks\MinGW\bin\gcc.exe" --json
```

```python
from phase6.v7.adapter import analyze_external
report = analyze_external("input.c", enabled=True, tool="gcc14")
```

Readable terminal output is default. Exit 0 means disabled analysis or completed analysis without primary warnings/errors; 1 means completed analysis with **unreviewed tool diagnostics**, not confirmed bugs; 2 means invalid arguments; 3 means partial/failed/unsupported/unavailable/timed-out/exhausted analysis. Completion never proves program safety or complete region coverage.

`--total-timeout` defaults to 30 seconds, `--timeout` to 10 per command, and `--max-invocations` to 4. Version, actual known-defect capability probe and source analysis normally use three commands. Maximums inherited from the bounded runner are 120 total seconds, 30 per command and 80 invocations. A timed-out call latches a stop. All waits are finite; finite cleanup grace and OS scheduling are not hard real-time guarantees or a hostile-input resource sandbox.

The selected profiles are pinned to audited versions. Missing tools/build changes are reported without automatically falling back to GCC 6, a different GCC release or another analyzer. The existing `analyze_c.py --compiler gcc` still uses the unchanged regular GCC workflow. There is no PATH/registry installation change; a tool's bin directory is prepended only in its child environment.

## Measured discovery and selection

| Candidate | Installed location/version | Result |
| --- | --- | --- |
| Existing GCC | `C:\MinGW\bin\gcc.exe`, 6.3.0 | Rejects `-fanalyzer`; retained as ordinary compiler baseline |
| GCC analyzer | CodeBlocks MinGW bin, 14.2.0 | **Selected**, actual analyzer probe and independent allocation/overlap gains |
| GCC analyzer | MSYS2 UCRT64 bin, 16.1.0 | Evaluated; same incremental reviewed roots as GCC14, comparison-only |
| Cppcheck | CodeBlocks MinGW bin, 2.16.0 | **Selected**, complementary overflow/overlap evidence and useful original erroneous-source findings |
| Clang-Tidy | NDK LLVM bin, 17.0.2 | Evaluated; incremental widening warning covered by Cppcheck, plus legitimate modular-control warning; comparison-only |
| Other Clang-Tidy | CodeBlocks MinGW bin | Version probes timed out; unusable in audited environment, version unknown |
| CBMC | Not discovered | Unsupported in this experiment; no installation or fabricated results |

Discovery covered PATH, common Windows roots and explicit locations with a time/depth bound. It is not a whole-disk/WSL absence proof. [tool_discovery.json](outputs/tool_discovery.json), [independent probes](outputs/independent_tool_probes.json), and GCC execution probes retain exact search scope/failures. A shared-budget initial probe was followed by independent tool probes so one timeout did not incorrectly hide other candidates.

GCC14 supports diagnostic JSON. GCC16 **rejects** that format and advertises SARIF-stderr, which was separately tested on an actual null-dereference probe. Both GCC builds use x86_64 MinGW-w64/UCRT configurations; per-tool target/predefined macro reports are retained. Cppcheck explicitly models `win64`; Clang/Clang-Tidy use their installed Windows configuration. Library/header models differ; comparison is explicit C11, not a hermetic identical-toolchain experiment. Version identity does not freeze every external header/model dependency.

CBMC would require an approved installation and separately designed harnesses, preconditions, unwind bounds and verification scope. Follow the [official installation guide](https://diffblue.github.io/cbmc/installation_guide.html) and [release instructions](https://github.com/diffblue/cbmc/releases) only after approval. A future Windows install can be checked with `cbmc --version`; bounded results must not be described as complete program verification. No install command was run here.

## Exact comparison profiles

- GCC14/GCC16: `-x c -std=c11 -Wall -Wextra -fmax-errors=20 -O0 -fanalyzer`, version-supported diagnostic format, `-c SOURCE -o PRIVATE/analysis.o`. Private objects are never linked/executed and are removed. A syntax-only flag-acceptance probe is not treated as analyzer execution. [GCC documents](https://gcc.gnu.org/onlinedocs/gcc/Static-Analyzer-Options.html) that analyzer availability depends on the build and analysis runs in the compiler pipeline.
- Cppcheck: `--xml --xml-version=2 --enable=warning --std=c11 --platform=win64 --max-configs=1 --error-exitcode=1 --cppcheck-build-dir=PRIVATE/cache SOURCE`. Default error checks plus warning checks are evaluated; style/performance/all/inconclusive classes are not enabled. One configuration is a deliberate coverage bound. Cache directories are created before invocation and removed afterward. See the [official manual](https://cppcheck.sourceforge.io/manual.html).
- Clang-Tidy: empty explicit config, `--checks=-*,` followed by the advertised correctness allowlist in [catalog.json](catalog.json); explicit C/standard/warning arguments after `--`. No fixes, build-system execution, compilation-database import, readability/modernize/style families or user `.clang-tidy` overrides. Its clang-analyzer checks reuse Clang's engine and are not algorithmically independent confirmations of existing CSA diagnostics.

Every actual command, version, PATH prefix, raw stdout/stderr, return code, source hash, timeout and invocation count is stored. Parser categories use known diagnostic identifiers; insufficient evidence stays `unknown`. XML DTD/entities are rejected. GCC JSON, GCC16 SARIF and Cppcheck XML preserve paths/context; Clang-Tidy text supports Windows paths and multiline notes. Related path events/notes do not create independent defects.

## Structured report and confidence

The adapter uses `schema: "smartparse.external_analysis"`, version `1.0`; experimental comparisons use `smartparse.external_comparison`. Setup errors are structured, not uncaught CLI tracebacks. Disabled/unsupported requests have no tool invocation.

| Field | Meaning |
| --- | --- |
| `tool`, `observed_version`, `configuration` | Audited ID/kind/path/version, live version and exact arguments/standard/includes/defines/child PATH. |
| `source` | Original path, byte SHA-256, final unchanged check. Sources are capped at 1 MiB. |
| `capability` | Actual private known-defect analyzer probe; not merely accepted flags. Probe caches/output are separate from user-analysis caches/output. |
| `status`, `reason`, `eligibility` | Process start, analyzer request, frontend blockers, operational completion and explicit unknown region/path coverage. |
| `diagnostics` | Identifier, severity, conservative category, reported file/line/column, source snippet when bound, column convention, context/path evidence, tool/configuration, provenance and review status. |
| `exact_duplicates`, `unique_primary_groups` | Exact diagnostic grouping only; **not distinct defect totals**. |
| `raw` | Full source-pass stdout/stderr and return code. |
| `usage`, `temporary_workspace_removed` | Counted commands, timing/limits and verified private cleanup. |
| `confirmed_defect_roots` | Null until a separate source/root review; warnings are not automatically true positives. |

`outputs/normalized_findings.json` supplies the flattened comparison records with tool names/versions, full eligibility, source identity and explicit source-review links. `observed_record_fingerprint` binds the enriched record to its original diagnostic; raw comparison records are not retroactively changed into human-confirmed findings.

Locations remain tool-reported. GCC byte columns and SARIF column conventions are retained rather than silently converted. Only the input source is read for snippets; foreign header paths are not arbitrarily opened. `#line`/presumed mappings are explicitly unverified, not claimed byte-accurate originals. Unknown/unbound locations cannot establish reviewed input roots.

This adapter supports **original-source files only**. Explicit repair/isolation provenance is rejected as unsupported without invoking a tool; it is never flattened into original-source findings. V2–v6 reports and guardrails are preserved. Candidate tools can independently analyze original malformed input using their own models; that does not mean Clang accepted it or every region was analyzed. No temporary punctuation repair or function exclusion was used in this comparison.

## Reproduction and evaluation

The 74-input manifest covers all v5/v6 C fixtures, twelve new positive/corrected/unknown controls and the unchanged benchmark. V6 baseline reports, input manifest and holdout bytes are frozen in [frozen_baseline/hashes.json](outputs/frozen_baseline/hashes.json). Earlier v6 results are separately protected. Existing baseline artifacts are verified/reused, never overwritten as new evidence.

```powershell
python -m unittest phase6.v7.test_external -v
python -m phase6.v7.run_comparison
python -m phase6.v7.evaluation
python -m phase6.v7.benchmark_review
python -m phase6.v7.run_validation
```

The full regression runner prepends the known installed Clang only in its test child environment. On another machine, tool paths/versions require a fresh capability audit; do not treat local catalog paths as installed everywhere. Live-test unavailability is explicitly reported as a skip, not a fabricated pass.

Comparisons have 20-second per-source internal and 35-second external deadlines, per-tool cohort limits of 180 seconds/160 command attempts, with explicit not-attempted states if exhausted. Runtime capability probes are added only to the selected public adapter. The full suite is externally bounded to 480 seconds. Historical performance CSV test writes are snapshotted/restored exactly and disclosed. No old acceptance runner regenerates protected reports.

Root evaluation is source/hash/identifier/meaning bound, with named agent-review rationales in [root_review.json](outputs/root_review.json). Identical v5/v6 source copies are aliases. Multiple warnings and backend versions supporting one root do not add roots. Conditional input/intent contracts remain conditional; unknown findings are not false positives by default. Human adjudication is pending; precision and recall remain null. See [MILESTONE_7_REPORT.md](MILESTONE_7_REPORT.md) for actual gains, allocation variants, benchmark review, control burden, failures, limitations and proposed next evaluation—not a claim of complete C coverage.
