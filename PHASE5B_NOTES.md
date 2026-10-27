# Phase 5B — First CGAR integration (experimental)

Opt in with `Parser(tokenize(source), adaptive_recovery=True)`.

This phase adds a bounded local search over punctuation deletion and closing-delimiter substitution, allowing up to three edits at one expectation. It preserves the original token list and existing parser behavior by default. Unlike the old two-token pattern, search depth is configurable, but **it does not yet handle arbitrary syntax errors, missing expressions, or arbitrary insertion sequences**. It is not full grammar-validated search. It can suggest unintended repairs; no accuracy or superiority claims are made yet. The parser can continue to use panic-mode synchronization when it cannot recover.

Run: `python -m unittest discover -v`.
Next: evaluate adversarial cases, extend candidate generation to insertion and expression-level recovery, implement parser-progress validation and abstention, then compare fairly against baselines.
