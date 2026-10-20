# SmartParse — implementation milestone 1

Python 3.12 compatible; no external dependencies.

## Run

```powershell
python smartparse.py example.c
python -m unittest -v
```

## Implemented
- Lexer with line/column positions
- Basic recursive-descent parser for a C-like subset
- Local insertion of missing `)`, `;`, `}` at selected boundaries
- Local substitution of `]` for expected `)` or `}`
- Panic-style fallback synchronization for other parse errors
- Diagnostics and internal repair log; source input is not rewritten
- Four automated unit tests

## Limitations
This is an early milestone, not the complete research system. It does not yet implement context-based candidate scoring, deletion candidate ranking, full `for` syntax, comprehensive function-call expressions, or comparative evaluation against a separately implemented panic-mode baseline. A local repair may not always be optimal.
