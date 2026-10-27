# Milestone 4 Phase 4 — independent synthetic evaluation

This phase adds `phase4_benchmark.py` and `test_phase4_benchmark.py` without modifying the parser's recovery rules. The evaluation uses held-out seeds 101/202/303 and new variable names, numeric values, punctuation and closing-delimiter combinations. **Important limitation:** these are newly generated cases, not a fully independent grammar/error family; the paired punctuation+wrong-closer pattern is the same class used to design the Phase 3 rule. Results must not be described as broad generalization to arbitrary C syntax.

The holdout measures exact operation/token/from sequences for 12 programs per seed. The scaling test injects 20 paired errors per program into 500/1,000/5,000-line synthetic programs. It counts `multi_token` repairs from the parser and reports wall-clock median and peak Python traced allocations (`tracemalloc`), not process RSS. Other modes do not emit `multi_token` repairs by definition; the `paired_edits` metric is therefore a **feature activation measure**, not a fair general exact-repair accuracy comparison across modes. Diagnostic count and total repairs are retained in the CSV for inspection.

Local verification (Linux Python runtime; user should rerun on Windows): 93/93 unit tests passed. With seeds 101/202, 2 repeats, heldout bounded-pair 48/48 intended edits across 24 cases; other modes 0/48 exact edits on this deliberately pair-focused dataset. The 5,000-line bounded-pair runs emitted 80/80 intended paired edits across two programs, median 71.037 ms and median peak 3152.4 KiB traced memory. These timing numbers are environment-specific and **must not be presented as Windows measurements**.

Run on Windows:

```powershell
python -m unittest discover -v
python phase4_benchmark.py --repeats 3 --sizes 500 1000 5000 --seeds 101 202 303
```

Outputs: `results/phase4_holdout.csv`, `results/phase4_scaling.csv`.

Before final Review 3 claims, add independently authored error classes, test non-triggering valid programs and false-positive repairs, and run repeated Windows measurements. No parser change was needed for this measurement milestone.
