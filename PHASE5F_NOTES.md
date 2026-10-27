# Phase 5F: Opt-in CGAR parser integration

Use `Parser(tokenize(source), verified_cgar=True).parse()`. The opt-in parser invokes the Phase 5E conservative advisor, verifies the proposed whole-program repair with StrictParser, and records grammar-verified suggestions using the original token positions. It does **not** rewrite the source. If the advisor abstains or the input is already valid, the existing parser runs unchanged. `verified_cgar_status` exposes `verified_candidate`, `abstain`, `unchanged`, or `ambiguous_valid`.

Important limitations: this is a whole-program preflight integrated into `Parser.parse()`, not yet an incremental grammar-context search at each error. Grammar-valid suggestions are not proof of author intent. Diff-based reporting may group multiple adjacent token edits into one diagnostic. The planner has strict edit/node budgets and may abstain on long or unsupported programs. The original parser is the fallback.

Run: `python -m unittest discover -v`
