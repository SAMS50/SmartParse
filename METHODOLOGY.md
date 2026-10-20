
# SmartParse — Architecture and Methodology

## 1. System Overview

SmartParse is a context-aware syntax-error recovery system implemented as a compiler front end for a restricted C-like language.

The system combines recursive-descent parsing, local token-repair candidate generation, heuristic ranking, optional grammar validation, and parser continuation.

Its purpose is to improve the usefulness of syntax-error diagnostics while reducing unnecessary token skipping.

## 2. Architecture

The system consists of six major components:

1. Lexical analysis
2. Recursive-descent parsing
3. Context-aware candidate generation
4. Candidate ranking and local grammar validation
5. Error recovery and parser continuation
6. Evaluation and reporting

### Overall Processing Pipeline

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
          v
    Syntax Error Detected?
       /          \
      No          Yes
      |            |
      v            v
    Continue   Context Analysis
      |            |
      |            v
      |       Candidate Generation
      |            |
      |            v
      |       Heuristic Ranking
      |            |
      |            v
      |       Grammar Validation
      |        (when required)
      |            |
      |            v
      |       Recovery Selection
      |            |
      +------------+
          |
          v
    Continue Parsing
          |
          v
    Diagnostics and Repair Log

## 3. Module Descriptions

### Module 1 — Lexical Analyzer

The lexical analyzer converts source text into tokens.

Each token contains information needed for parsing and diagnostic reporting, including its type, value, and source location.

The lexer recognizes keywords, identifiers, literals, operators, punctuation, and delimiters.

Comments and whitespace are handled during tokenization.

**Output:** A token stream ending with an EOF token.

### Module 2 — Recursive-Descent Parser

The parser implements the grammar through Python methods.

It recognizes declarations, expressions, control-flow statements, function definitions, function calls, and nested blocks.

When the current token does not match an expected grammar symbol, the parser initiates error recovery.

**Output:** Parsing progress, syntax diagnostics, and recovery metadata.

### Module 3 — Context-Aware Candidate Generation

When a recoverable mismatch occurs, SmartParse examines the expected token and nearby tokens.

It generates supported local recovery candidates:

- Insertion of a missing token
- Deletion of an unexpected token
- Substitution of an incorrect closing delimiter

These operations are constrained by the recovery rules implemented in the system.

**Output:** A set of candidate recovery actions.

### Module 4 — Candidate Ranking

The recovery module assigns contextual heuristic scores to candidates.

The score reflects the suitability of a proposed action given the expected token and surrounding syntax.

Candidates are ranked before a recovery action is selected.

**Output:** An ordered candidate list.

### Module 5 — Local Grammar Validation

When enabled and multiple candidates are available, SmartParse evaluates competing repairs using local grammar probes.

Each probe applies a candidate to a temporary token sequence and attempts strict parsing of the relevant local statement.

The candidate-selection process considers whether the probe succeeds, parsing progress, and heuristic ranking.

The original source code is not rewritten.

**Output:** Validation evidence supporting candidate selection.

### Module 6 — Recovery and Continuation

The selected repair is applied to the parser's internal token-processing state.

SmartParse records a diagnostic and repair action, then attempts to continue parsing.

When local repair is unavailable, synchronization-based recovery may be used.

**Output:** Continued parsing and structured diagnostics.

## 4. Recovery Algorithm

### Algorithm: Context-Aware Local Error Recovery

**Input:** Token stream, current parser position, expected grammar token, parser context

**Output:** Selected recovery action and diagnostic information

1. Detect a mismatch between the expected token and current token.
2. Collect nearby token and delimiter context.
3. Generate supported insertion, deletion, and substitution candidates.
4. Assign heuristic scores to the generated candidates.
5. If grammar validation is enabled and multiple candidates exist, evaluate candidates using local strict-parsing probes.
6. Select the preferred candidate using the available ranking and validation information.
7. Apply the recovery action to the parser's internal state.
8. Record the diagnostic and repair metadata.
9. Resume parsing from the resulting state.
10. If local recovery is unavailable, use synchronization-based fallback.

## 5. Panic-Mode Baseline

The baseline uses the same lexer and grammar as SmartParse but disables local token repair.

When a syntax error occurs, the parser skips tokens until a synchronization point such as `;` or `}` is reached.

This provides a simple reference implementation for comparing diagnostic accuracy and recovery behavior.

The baseline can lose structural context when a syntax error prevents successful entry into a block.

## 6. Evaluation Methodology

### 6.1 Labelled Diagnostic Evaluation

The labelled dataset contains 12 curated programs with 11 annotated syntax-error anchors.

Diagnostics are compared against these anchors to calculate true positives, false positives, and false negatives.

Precision, recall, and F1 score are derived from these counts.

### 6.2 Ablation Evaluation

Three recovery modes are compared:

- Panic-mode baseline
- Heuristic-only SmartParse
- Grammar-validated SmartParse

This comparison separates the effect of local contextual repair from the additional grammar-validation mechanism.

### 6.3 Ambiguous Candidate Evaluation

Six curated ambiguous cases test whether heuristic and grammar-validated modes choose the intended recovery operation.

The benchmark also records the number of grammar probes performed.

### 6.4 Stress Evaluation

Six stress scenarios examine parser continuation and diagnostic reporting under more complex inputs.

The checks include minimum diagnostic counts and whether parsing reaches EOF.

### 6.5 Performance Evaluation

Execution time is measured for complete workloads, including tokenization and parsing.

The rotated benchmark compares the three modes using repeated measurements.

Median and mean execution times are recorded.

## 7. Experimental Findings

On the labelled dataset, SmartParse achieved 100% diagnostic F1, compared with 76.92% for the implemented panic-mode baseline.

Both heuristic-only and grammar-validated SmartParse achieved identical diagnostic accuracy.

On the six ambiguous cases, both modes selected the intended recovery operations.

Grammar validation added computational overhead without changing candidate selection in these tests.

The results support the effectiveness of local contextual repair relative to the implemented baseline but do not establish an accuracy advantage for grammar validation.

## 8. Limitations

- Restricted C-like grammar
- Limited supported recovery operations
- Small curated evaluation datasets
- Local grammar probes cannot guarantee global syntactic correctness
- Diagnostic matching does not establish semantic correctness
- Recovery traces do not prove preservation of all original statements
- Performance results are exploratory and environment-dependent

## 9. Future Work

Future extensions may include:

- Larger syntax-error benchmarks
- More recovery candidate types
- Expanded grammar support
- AST-level recovery validation
- Alternative ranking methods
- Additional baseline recovery strategies
- Integration with developer tooling

## 10. Conclusion

SmartParse demonstrates a practical context-aware syntax-error recovery approach using localized token repairs and recursive-descent parsing.

The evaluation shows improved diagnostic accuracy over the implemented panic-mode baseline on curated test programs.

The project also identifies a trade-off between additional grammar-validation computation and observed recovery accuracy.
