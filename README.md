# SmartParse — unified C analysis (0.9.0)

## SmartParse Studio (Milestone 10)

A local React/Monaco workbench now exposes the existing analysis engine through
FastAPI: edit C, choose analyzers, inspect attributed diagnostics and conditional
recovery/isolation evidence, and export the complete report. Original analysis
algorithms and historical evaluation evidence are unchanged. Independent human
adjudication remains pending.

See [Studio setup, PowerShell commands, security limits and demonstration](smartparse_studio/README.md).
The CLI below remains available independently; Studio requires its own Python
virtual environment and frontend dependencies. Run both servers on loopback only.

SmartParse combines its original restricted C-like syntax-recovery research with an optional compiler-backed C analysis pipeline. The unified interface analyzes one C translation unit, reports available diagnostics, and preserves original source files. It never runs the analyzed C program.

```powershell
python -m smartparse_cli --help
python -m smartparse_cli doctor
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C12_valid_full.c
```

The original `python smartparse.py`, `python analyze_c.py`, `python demo.py` and versioned `python -m phase6.vN` commands remain available with their existing behavior. The separate `smartparse_cli` name avoids replacing the original `smartparse.py` module or changing its imports.

## Requirements and PowerShell setup

- Python **3.12** is the tested interpreter; the analysis CLI uses the Python standard library only. Matplotlib is needed for historical research plots, not analysis.
- Install a working GCC or Clang toolchain **with target C headers** for compiler diagnostics. Clang is required for CSA, memory/semantic profiles, punctuation recovery and isolation.
- Optional external profiles currently retain the existing version constraints: GCC **14.2.0** analyzer and Cppcheck **2.16.0**. Different versions require a separately validated profile; they are not silently substituted.
- Windows 11/PowerShell is live-tested. Paths are quoted and passed as argument arrays without a shell. Python code and process supervision include POSIX support; this release's live tool models are Windows-specific. In particular, the existing Cppcheck profile models `win64`.

Put tools on PATH, supply executable options, or configure child discovery through `SMARTPARSE_GCC`, `SMARTPARSE_CLANG`, `SMARTPARSE_GCC14` and `SMARTPARSE_CPPCHECK`. `doctor` searches PATH, existing selected-profile locations and bounded common Windows installations, including LLVM/MinGW and a limited Android SDK NDK search. It performs version probes without installing anything. Analysis separately validates capabilities; a discovered version does not prove checker availability or compatible headers.

```powershell
python --version
python -m smartparse_cli --version
python -m smartparse_cli doctor --format json
# If needed, specify an installed Clang without changing machine PATH:
python -m smartparse_cli doctor --clang "C:\Program Files\LLVM\bin\clang.exe"
```

## Unified analysis commands

Default analysis runs **compiler syntax/type diagnostics only**. Choose a comma-separated analyzer list explicitly:

| Analyzer | Implementation and scope |
|---|---|
| `compiler` | GCC/Clang frontend diagnostics; syntax/type errors and available warnings |
| `static` | Clang Static Analyzer defaults, with independent completion |
| `memory` | Existing v5 capability-probed memory/resource/bounds profile |
| `semantic` | Existing v6 semantic facts/review suggestions; includes the memory profile |
| `gcc14` | Existing v7 pinned GCC static-analyzer profile |
| `cppcheck` | Existing v7 pinned Cppcheck profile, original-source only |
| `smartparse` | Original restricted-grammar context-aware recovery suggestions |
| `panic` | Original restricted-grammar panic-mode baseline |

```powershell
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C09_repair_null.c --compiler gcc
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers static
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C02_leak.c --analyzers memory
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C05_bounds.c --analyzers semantic
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers gcc14,cppcheck
python -m smartparse_cli analyze .\phase6\v8\fixtures\syntax\S03.c --analyzers smartparse
```

For your own build, use `--compiler auto|gcc|clang|"PATH"`, `--clang "PATH"`, `--std c11`, repeatable `-I "include directory"` and `-D NAME=VALUE`. External analyzer paths can be overridden with `--gcc14` and `--cppcheck`. A selected compiler/analyzer is not replaced silently when missing. The tool does not invoke build scripts or import a compilation database; dependencies/configuration must be supplied explicitly.

## Recovery, isolation and provenance

```powershell
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C09_repair_null.c --recovery
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C10_isolate_null.c --isolation
```

These flags explicitly opt into the existing bounded, conservative temporary-source workflows and add the memory pipeline when needed. They are disabled by default. Recovery inserts only supported, high-confidence semicolons; isolation excludes functions only when existing AST/dependency/preprocessing safeguards permit. They abstain on unsafe inputs. Identifiers, expressions, types and programmer intent are not repaired speculatively.

Original compiler evidence remains separate from `repair-conditioned`, `isolation-conditioned`, or jointly conditioned findings. Full edit/source-map/exclusion/dependency provenance remains in JSON. Report locations identify original mapped versus variant-reported coordinates. A conditioned finding is not an unconditional original-source defect. Optional GCC14/Cppcheck always analyze the original source, even when Clang-based variants are requested.

## Reports, budgets and exit codes

```powershell
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory --format json
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory --format markdown
# Choose a new destination: existing files are deliberately never overwritten.
python -m smartparse_cli analyze .\phase6\v8\fixtures\c\C01_null.c --analyzers memory --format json -o .\smartparse-report.json
```

Terminal output is the default. JSON schema `smartparse.unified_analysis` **1.0** retains all raw analyzer reports, normalized records, tool versions, source hash, limitations and conservative evidence groups. Exact same-backend diagnostic/source/provenance identity may be grouped; cross-backend warnings and same-line warnings are not automatically equated. Group counts are not root-defect counts. See [schema and API](smartparse_cli/README.md) and [JSON Schema](smartparse_cli/schema.json).

Each tool call defaults to 10 seconds (maximum 30); the shared runtime budget defaults to 120 seconds (maximum 240), with 256 tool invocations (maximum 512). Configure `--timeout`, `--total-timeout` and `--max-invocations`. Existing tighter per-profile limits still apply. Timeout cleanup has finite extra grace; this is not a hostile-input sandbox or hard real-time guarantee. Inputs are bounded to 1 MiB. Empty files are supported; their zero findings do not establish program safety.

| Exit | Meaning for the unified CLI |
|---|---|
| 0 | Requested analysis completed without primary warnings/errors; or doctor/help/version completed |
| 1 | Requested analysis completed with source diagnostics or potential findings, including compiler warnings |
| 2 | Invalid CLI arguments/configuration |
| 3 | Tool/input/output failure, unavailable requested analyzer, timeout, exhausted budget or incomplete requested analysis |

Incomplete analysis takes precedence over findings. Existing `analyze_c.py` retains its prior exit-code policy, including its handling of ordinary compiler warnings.

## Limits and validation

SmartParse is not a complete C compiler or a replacement for established industrial analyzers. Compiler diagnostics belong to GCC/Clang; CSA findings belong to Clang Static Analyzer; optional tool findings retain their names. They are not CGAR discoveries. The original parser supports a restricted C-like grammar, not arbitrary C. Semantic facts and suspicious operations may require programmer review, and potential runtime/logic issues are not necessarily reachable or confirmed defects. No analyzer process completion certifies all functions/paths; missing dependencies or frontend errors can block later analysis.

Independent human adjudication remains pending. No TP/FP/FN, precision, recall or F1 is inferred by the release CLI. The author-created v8 evaluation and its known matching/reference gaps remain unchanged.

```powershell
python -m unittest test_smartparse_cli -v
# Supervised full suite, installed Clang made available only to child tests,
# with historical CSV final bytes restored after the legacy performance test:
python -m phase6.v9.validate
python -m phase6.v9.smoke
```

The historical 452-test baseline was rerun before integration. Exact final regression/smoke results and preservation evidence are in [Milestone 9 report](phase6/v9/MILESTONE_9_REPORT.md). No commit, push or GitHub release is performed automatically.

Release reproducibility uses the separate [portable release manifest](phase6/v9/release_manifest.json) and [validation guide](phase6/v9/REPRODUCIBILITY.md). The archived Milestone 8/9 snapshots and results remain historical evidence, not requirements to possess another workstation's untracked files. Scoped Git attributes retain frozen byte hashes; legacy Python compatibility compares canonical content while still rejecting non-line-ending changes. New validation writes isolated run folders and checks actual checkout bytes before/after testing. See the [reproducibility verification report](phase6/v9/REPRODUCIBILITY_REPORT.md) for measured checkout results and publication limitations.

---

## Historical Phase 5H and earlier acceptance documentation

The following preserved narrative describes earlier milestones and measurements; its test counts are historical, not the current unified release total.

# SmartParse — Final project release (Phase 5H)

**Start here:** [Final release and evaluation guide](FINAL_RELEASE.md). This is a research prototype for a **restricted C-like grammar**, not a complete C compiler. The optional CGAR mode supplies bounded whole-program grammar-verified *suggestions* with conservative abstention; it does not guarantee programmer intent.

## Extended C Analysis CLI

Install Python 3.12 and an external Clang or GCC toolchain, then run from this
checkout. The analysis CLI uses only Python's standard library; Matplotlib is
needed only for the original research plots. Put `clang`/`gcc` on PATH or pass an
explicit executable. For Clang installation, see the
[official getting-started guide](https://clang.llvm.org/get_started.html) and
[toolchain configuration guide](https://clang.llvm.org/docs/Toolchain.html).
The compiler also needs the target C headers used by your source.

For real C programs, use the separate compiler-backed pipeline:

```powershell
python analyze_c.py "C:\My Project\program.c"
python analyze_c.py program.c --compiler gcc --std c11 -I "include folder" -D COUNT=10 --json
python analyze_c.py program.c --static-analysis --timeout 60
```

`analyze_c.py` attributes syntax/type diagnostics and warnings to external
GCC/Clang, and optional static-analysis findings to Clang Static Analyzer.
SmartParse/CGAR remains the original restricted-grammar research mode. The CLI
does not run the C program or edit its source. A completed check does not prove
absence of runtime or logic bugs.

Exit codes: **0** completed without errors or analyzer findings (compiler warnings
may remain); **1** source errors or potential analyzer findings; **2** invalid CLI
arguments; **3** failed/incomplete requested analysis, including missing compilers,
missing headers, or timeout. Incomplete analysis takes precedence over findings.

See [Extended C usage, reporting schema, and limitations](extended_c/README.md).

Acceptance evidence: [Milestone 5 report](acceptance/FINAL_ACCEPTANCE_REPORT.md).
The supplied 500-line numbered sample was found in Downloads and checked using a
separate line-preserving cleaned copy: GCC 6.3 reported 6 errors, 14 warnings, and
3 notes. These include cascades and are not independent bug counts. A later Windows
search found Clang 17.0.2 bundled with the Android NDK, outside PATH: all **237 tests
now pass, with no skips**, including live memory-analyzer checks. Clang reports
7 errors, 12 warnings, and 11 notes on the unchanged cleaned sample; its frontend
errors prevent a completed sample static-analysis pass. Final acceptance remains
pending user review. The original Phase 5H research release and its results remain
separate.

Quick start for the original research modes (from the repository directory):

```powershell
python -m unittest discover -v
python demo.py --example multiple --mode cgar
python phase5g_eval.py --repeats 5
```

The latest four-mode comparison is in `PHASE5G_NOTES.md` and `FINAL_RELEASE.md`. Historical results and conclusions below describe **earlier experiments** and must not be treated as a head-to-head exact-repair accuracy comparison with CGAR.

---


# SmartParse
### A Context-Aware Error Recovery System for Improved Compiler Diagnostics

SmartParse is a lightweight compiler-front-end research project that investigates how context-aware syntax-error recovery can improve compiler diagnostics compared with traditional panic-mode recovery.

It uses a hand-written recursive-descent parser for a restricted C-like programming language. When a syntax error occurs, SmartParse generates possible token-level corrections, ranks them using contextual heuristics, and optionally evaluates competing candidates through local grammar-based parsing.

The system reports suggested corrections and continues parsing without modifying the original source code.

## 1. Problem Statement

Traditional panic-mode error recovery typically skips input tokens until a synchronization point, such as a semicolon or closing brace.

Although this approach allows parsing to continue, it can discard valid tokens, miss subsequent errors, or produce cascading diagnostics.

SmartParse investigates whether localized, context-aware token repair can preserve more useful parsing information and produce more accurate syntax-error reports.

## 2. Objectives

- Implement lexical analysis and recursive-descent parsing for a restricted C-like language.
- Detect and report syntax errors with source locations.
- Generate candidate token insertions, deletions, and substitutions.
- Rank recovery candidates using surrounding token context.
- Validate competing candidates using local grammar-based probes.
- Continue parsing after recoverable syntax errors.
- Compare SmartParse against a panic-mode recovery baseline.
- Evaluate diagnostic accuracy, recovery behavior, and execution-time overhead.

## 3. System Architecture

```text
                 Source Program
                       |
                       v
                 Lexical Analyzer
                       |
                       v
                  Token Stream
                       |
                       v
             Recursive-Descent Parser
                       |
              Syntax Error Detected?
                  /          \
                No            Yes
                |              |
                v              v
         Continue Parsing  Context Analysis
                               |
                               v
                       Candidate Generation
                               |
                               v
                        Heuristic Ranking
                               |
                               v
                     Multiple Candidates?
                         /          \
                       No            Yes
                       |              |
                       |              v
                       |       Local Grammar Probes
                       |              |
                       +--------------+
                               |
                               v
                      Select Recovery Action
                               |
                               v
                     Resume Parser Execution
                               |
                               v
                    Diagnostics and Repair Log
```

Grammar validation is optional and is used only when multiple recovery candidates are available.

## 4. Supported Language Features

SmartParse supports a restricted C-like grammar, including:

- Integer and floating-point declarations
- Function declarations and definitions
- Function parameters and calls
- Assignment and arithmetic expressions
- Comparison and logical expressions
- `if` and `else` statements
- `while` and `for` loops
- `return` statements
- Nested blocks
- Increment and decrement operations
- Line and block comments

SmartParse is not a complete C compiler. It focuses on syntax analysis and error recovery rather than semantic analysis or machine-code generation.

## 5. Error Recovery Methodology

### 5.1 Syntax Error Detection

The parser compares the next input token against the token expected by the grammar.

When they do not match, SmartParse records the error location and examines possible recovery actions.

### 5.2 Context Analysis

The recovery module examines:

- The expected token
- The current token
- The preceding token
- The following token
- Delimiter nesting context
- Statement boundaries

### 5.3 Candidate Generation

SmartParse supports three token-level recovery operations.

**Insertion:** Treat a required token as present without consuming an input token.

**Deletion:** Skip an unexpected token when the following token matches the expected token.

**Substitution:** Treat an incorrect closing delimiter as the expected delimiter.

Candidate generation is intentionally restricted to supported punctuation and delimiter patterns.

### 5.4 Candidate Ranking

Recovery candidates receive heuristic scores based on contextual suitability.

The parser initially prioritizes higher-scoring candidates.

### 5.5 Local Grammar Validation

When multiple candidates are available, SmartParse can evaluate them by applying each candidate to a temporary token sequence and attempting a strict parse of the current statement.

Candidate selection considers:

1. Whether the local statement parses successfully
2. How far the probe progresses
3. The original heuristic score

The original source code and token sequence are preserved.

### 5.6 Parser Continuation

After choosing a supported recovery action, SmartParse resumes parsing and can report additional syntax errors.

When no local repair candidate is available, the parser falls back to panic-mode synchronization.

## 6. Recovery Modes

Three configurations are evaluated.

| Mode | Description |
|---|---|
| Panic mode | Strict parsing with token skipping to synchronization points |
| Heuristic | Context-aware local repairs selected by heuristic ranking |
| Grammar-validated | Context-aware repairs with local grammar probing when candidates compete |

The panic-mode baseline shares the lexer and grammar with SmartParse but does not perform local token repairs.

## 7. Experimental Evaluation

The project uses three evaluation groups.

### 7.1 Labelled Diagnostic Dataset

Twelve curated C-like programs containing eleven labelled syntax-error locations.

Diagnostic matching is based on expected-token and source-line anchors.

Metrics:

- True positives
- False positives
- False negatives
- Precision
- Recall
- F1 score

### 7.2 Ambiguous Recovery Benchmark

Six cases designed to produce multiple recovery candidates.

The benchmark records:

- Selected recovery operation
- Whether the operation matches the intended correction
- Whether the corrected reference parses strictly
- Number of grammar probes

### 7.3 Stress Evaluation

Six scenarios examine:

- Multiple errors in one program
- Errors inside nested blocks
- Parsing continuation after an error
- Nested missing delimiters
- Valid nested programs
- Mixed recovery situations

Stress-test checks include diagnostic minimums and whether parsing reaches EOF.

These tests do not establish semantic equivalence or full statement preservation.

## 8. Research Results

### Diagnostic Accuracy

Results on the twelve-program labelled dataset:

| Metric | Panic mode | Heuristic | Grammar-validated |
|---|---:|---:|---:|
| True positives | 10 | 11 | 11 |
| False positives | 5 | 0 | 0 |
| False negatives | 1 | 0 | 0 |
| Precision | 66.67% | 100% | 100% |
| Recall | 90.91% | 100% | 100% |
| F1 score | 76.92% | 100% | 100% |

These results apply only to the curated diagnostic dataset and its matching criteria.

### Ambiguous Recovery

Both heuristic and grammar-validated modes selected the intended recovery operation in all six ambiguous cases.

Grammar validation executed additional probes but did not change the selected operation in these experiments.

Therefore, the current evaluation does not demonstrate an accuracy advantage for grammar validation over heuristic ranking.

### Stress Evaluation

Both SmartParse modes met the defined test criteria across all six stress scenarios.

### Performance

Rotated performance benchmarks measure complete workload execution times, including tokenization and parsing.

Grammar validation introduces additional overhead when multiple recovery candidates require probing.

Results are machine-dependent exploratory measurements rather than universal performance guarantees.

## 9. Results and Visualizations

The `results/` directory contains detailed evaluation outputs.

The `results/final/` directory contains summary tables and graphs:

- `01_diagnostic_accuracy.png`
- `02_error_analysis.png`
- `03_performance_comparison.png`
- `04_stress_robustness.png`
- `accuracy_summary.csv`
- `performance_summary.csv`
- `benchmark_summary.csv`

The final graphs are generated using `final_results.py`.

## 10. Project Files

| File | Purpose |
|---|---|
| `smartparse.py` | Lexer, parser, diagnostics, and recovery integration |
| `recovery.py` | Context analysis and candidate ranking |
| `local_validation.py` | Local grammar-based recovery probing |
| `baseline.py` | Panic-mode comparison parser |
| `dataset.py` | Labelled diagnostic test programs |
| `metrics.py` | Diagnostic evaluation metrics |
| `research_eval.py` | SmartParse versus baseline evaluation |
| `ablation_eval.py` | Three-mode comparison |
| `ambiguous_benchmark.py` | Ambiguous candidate benchmark |
| `stress_eval.py` | Stress and performance evaluation |
| `verification_eval.py` | Recovery, baseline, and timing audits |
| `final_results.py` | Research graphs and summary exports |
| `test_*.py` | Automated unit and regression tests |

## 11. Requirements

- Python 3.12 or compatible Python 3 version
- Matplotlib for graph generation
- Standard Python libraries for the parser and evaluation scripts

Install Matplotlib:

```bash
python -m pip install matplotlib
```

## 12. How to Run

Clone the repository:

```bash
git clone https://github.com/SAMS50/SmartParse.git
cd SmartParse
```

Analyze a sample source program:

```bash
python smartparse.py example.c
```

Run the panic-mode baseline:

```bash
python baseline.py example.c
```

Run the complete test suite:

```bash
python -m unittest discover -v
```

Run the research evaluation:

```bash
python research_eval.py
```

Run the ablation study:

```bash
python ablation_eval.py
```

Run the ambiguous benchmark:

```bash
python ambiguous_benchmark.py
```

Run stress and performance experiments:

```bash
python stress_eval.py
```

Run the technical verification:

```bash
python verification_eval.py
```

Generate final graphs:

```bash
python final_results.py
```

## 13. Limitations

- Supports only a restricted C-like language.
- Candidate generation covers selected punctuation and delimiter errors.
- Some syntax errors require panic-mode fallback.
- Local grammar probes do not guarantee globally valid repairs.
- Diagnostic F1 does not measure semantic correctness.
- The evaluation datasets are small and curated.
- Grammar validation has not demonstrated better candidate-selection accuracy than heuristics on the current benchmark.
- Performance measurements are sensitive to workload and execution environment.

## 14. Future Scope

Potential extensions include:

- Larger and more diverse syntax-error datasets
- Grammar-aware candidate generation for additional token categories
- More sophisticated recovery candidate scoring
- Validation using larger syntactic contexts
- AST-based checks of recovered program structure
- Comparison against additional parser recovery strategies
- Integration into an IDE diagnostic interface

## 15. Conclusion

SmartParse demonstrates how localized, context-aware syntax-error recovery can improve diagnostic reporting compared with a simple panic-mode baseline.

On the curated twelve-program evaluation dataset, SmartParse achieved a diagnostic F1 score of 100%, compared with 76.92% for the implemented panic-mode baseline.

The experiments also reveal an important trade-off: local grammar validation incurs additional computational cost, while its accuracy benefit remains unproven on the current ambiguous benchmark.

The project provides a reproducible foundation for studying syntax-error recovery, diagnostic quality, and parser continuation.
