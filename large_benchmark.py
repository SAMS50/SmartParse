"""Reproducible long-input benchmark for the existing SmartParse C-like subset.

The generated workload intentionally uses simple declarations; it tests length and
repeated missing-semicolon recovery, not full-C compatibility or nested syntax.
"""
import argparse
import csv
from pathlib import Path
import random
import statistics
import time

from baseline import PanicModeParser
from metrics import evaluate_diagnostics
from smartparse import Parser, tokenize


def make_program(lines, errors=0, seed=42):
    if lines < 2 or errors < 0 or errors >= lines:
        raise ValueError('Require lines >= 2 and 0 <= errors < lines')
    rng = random.Random(seed)
    # Exclude final line: each missing semicolon is anchored at the next 'int'.
    missing = set(rng.sample(range(1, lines), errors))
    source_lines = []
    truth = []
    for n in range(1, lines + 1):
        ending = '' if n in missing else ';'
        source_lines.append(f'int value_{n} = {n}{ending}')
        if n in missing:
            truth.append({'line': n + 1, 'expected': ';'})
    return '\n'.join(source_lines) + '\n', truth


def measure(source, truth, mode, repeats=3):
    durations = []
    last = None
    for _ in range(repeats):
        started = time.perf_counter()
        tokens = tokenize(source)
        parser = (PanicModeParser(tokens) if mode == 'panic'
                  else Parser(tokens, validate_repairs=(mode == 'validated')))
        parser.parse()
        durations.append((time.perf_counter() - started) * 1000)
        last = parser
    result = evaluate_diagnostics(truth, last.diagnostics)
    return {
        'mode': mode,
        'expected_errors': len(truth),
        'diagnostics': len(last.diagnostics),
        'tp': result['tp'], 'fp': result['fp'], 'fn': result['fn'],
        'precision': result['precision'], 'recall': result['recall'],
        'median_ms': round(statistics.median(durations), 3),
        'skipped_tokens': getattr(last, 'skipped_tokens', 0),
        'repairs': len(last.repairs),
        'hit_error_cap': len(last.diagnostics) >= last.max_errors,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sizes', type=int, nargs='+', default=[100, 500, 1000, 5000])
    ap.add_argument('--errors', type=int, default=20)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--out', default='results/large_benchmark.csv')
    ap.add_argument('--save-samples', action='store_true')
    args = ap.parse_args()
    if args.repeats < 1:
        ap.error('--repeats must be >= 1')
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for lines in args.sizes:
        errors = min(args.errors, lines - 1)
        source, truth = make_program(lines, errors, args.seed)
        if args.save_samples:
            sample = out.parent / f'generated_{lines}_lines.c'
            sample.write_text(source, encoding='utf-8')
        for mode in ('panic', 'heuristic', 'validated'):
            result = measure(source, truth, mode, args.repeats)
            result['lines'] = lines
            rows.append(result)
            print(f'{lines:>5} lines | {mode:<10} | TP={result["tp"]:>2} '
                  f'FP={result["fp"]:>2} FN={result["fn"]:>2} '
                  f'| {result["median_ms"]:>8.3f} ms'
                  + (' | ERROR CAP REACHED' if result['hit_error_cap'] else ''))
    with out.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved: {out}')
    print('Note: diagnostic anchor matching, not intended-edit accuracy; '
          'synthetic declarations only.')


if __name__ == '__main__':
    main()
