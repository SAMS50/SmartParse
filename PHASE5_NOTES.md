# Phase 5A — Conservative Repair Advisor

This incremental addition introduces `repair_advisor.py`, an **advisory-only**
interface. It classifies a parser expectation as `preferred`, `ambiguous`,
`review`, or `abstain` and includes ranked explanations. It does **not**
modify the parser, automatically apply repairs, or assert calibrated confidence.

`review` deliberately covers the bounded-pair pattern and single-candidate
situations: neither is automatically treated as trustworthy. `preferred`
means only that the heuristic score margin exceeds a threshold, **not** that
its probability of correctness is high.

Example from the project directory:

```python
from smartparse import tokenize
from repair_advisor import advise
source = 'if (x > 1 ; ] { x = 2; }'
tokens = tokenize(source)
index = next(i for i, t in enumerate(tokens) if t.value == ';')
print(advise(tokens, index, ')'))
```

Run all tests: `python -m unittest discover -v`.

## Not yet implemented

- Generalized edit-sequence search (the existing bounded-pair rule is narrow)
- Empirical confidence calibration on separate development data
- A real-programmer-error benchmark and precision/coverage curves
- Comparison against CPCT+ on a common grammar/dataset

These are necessary before claiming general improvement over published work.
