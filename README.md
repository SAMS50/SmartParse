# SmartParse — Final project release (Phase 5H)

**Start here:** [Final release and evaluation guide](FINAL_RELEASE.md). This is a research prototype for a **restricted C-like grammar**, not a complete C compiler. The optional CGAR mode supplies bounded whole-program grammar-verified *suggestions* with conservative abstention; it does not guarantee programmer intent.

Quick start (from `smartparse_work`):

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
