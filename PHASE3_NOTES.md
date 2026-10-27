# Review 3 — Milestone 4, Phase 3

This phase adds an **opt-in, bounded two-edit recovery pattern** to `Parser` via `multi_token_recovery=True`.

When the parser expects a closing delimiter and encounters a redundant `;` or `,` immediately followed by a *different* closing delimiter, it can delete the punctuation and substitute the incorrect closer in one bounded operation. The search examines only two tokens (constant lookahead) and preserves the original token stream. Both edits appear separately in `parser.repairs`, with `multi_token=True` metadata and `parser.multi_token_stats` counters.

The default is **False** for backwards compatibility. This is a targeted pattern, **not** a general two-edit beam search; it does not solve arbitrary multi-token syntax errors. It has not been tuned or tested on independent real-world C programs.

Run:

```powershell
python -m unittest discover -v
python phase2_benchmark.py --repeats 5
python phase3_benchmark.py --repeats 5
python robust_benchmark.py --sizes 500 1000 5000 --seeds 11 22 33 --repeats 2
```

On the six existing, previously-labelled Phase 2 cases, contextual selective mode improves from **7/11** intended edits and **4/6** exact repair sequences to **11/11** and **6/6** with the new option enabled. These cases directly motivated the targeted rule; this is an in-sample result, not evidence of generalization. Phase 3 does not enable the option in the older large-program benchmark by default, so separate performance testing of the new option on long programs is still needed.

`results/phase3_repair_choices.csv` contains per-case comparisons. Timing is exploratory and environment-dependent.
