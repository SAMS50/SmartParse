# Phase 5C — Experimental grammar-verified repair planner

New `cgar_verified.py` adds a standalone bounded best-first search using the actual strict grammar. It proposes punctuation insertion, deletion, and substitution, with a configurable maximum number of edits and explored states. It restarts strict parsing after each candidate and accepts a plan only when the *entire* resulting token sequence parses under SmartParse's restricted C-like grammar.

This is deliberately **not integrated into the live Parser**. It is a separate research prototype to establish correctness and compare search policies before allowing automatic suggestions. Successful strict parsing does **not** establish programmer intent. It currently does not repair missing expressions, unknown identifiers, unsupported language constructs, or arbitrary lexical errors. Search can return None when the budget is exceeded. Token indices in edit records refer to the evolving candidate token sequence.

Run `python -m unittest discover -v` and experiment with:

```powershell
python -c "from cgar_verified import plan; r=plan('int x = 1 if (x > 0] { x = 2; }'); print(r.edits if r else 'no verified repair')"
```

Next: benchmark against generic bounded search and existing adaptive recovery on independently authored positive and negative cases; measure incorrect-but-grammar-valid repairs, search costs, and ambiguity. Only then integrate a conservative advisor into the parser.
