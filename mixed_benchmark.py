"""Deterministic mixed-error benchmark for the supported C-like grammar.

Each injected edit has an exact intended inverse operation. Diagnostic detection
and repair-choice correctness are reported separately. These synthetic tests do
not establish superiority over production compiler recovery systems.
"""
import argparse
import csv
from pathlib import Path
import random
import statistics
import time

from baseline import PanicModeParser
from smartparse import Parser, StrictParser, tokenize

ERROR_TYPES = ('insert', 'substitute', 'delete')
MODES = ('panic', 'legacy', 'contextual', 'validated')


def make_program(lines=500, errors=20, seed=42):
    """Return source, exact edit labels, and the corresponding valid source.

    One error per distinct six-line block prevents overlapping labels. A final
    valid declaration pads the source to the requested line count.
    """
    if lines < 12 or errors < 0 or errors > min(40, (lines - 1) // 6):
        raise ValueError('Require lines >= 12 and 0 <= errors <= min(40, (lines - 1) // 6)')
    rng = random.Random(seed)
    block_count = (lines - 1) // 6
    selected = set(rng.sample(range(block_count), errors))
    types = list(ERROR_TYPES) * ((errors + 2) // 3)
    rng.shuffle(types)
    assigned = dict(zip(sorted(selected), types))
    original = []
    modified = []
    labels = []
    for n in range(block_count):
        name = f'v_{n}'
        chunk = [
            f'int {name} = {n + 2};',
            f'if ({name} > 0) {{',
            f'    while ({name} > 1) {{',
            f'        {name} = {name} - 1;',
            '    }',
            '}',
        ]
        edited = chunk.copy()
        if n in assigned:
            kind = assigned[n]
            if kind == 'insert':
                edited[0] = edited[0][:-1]
                # Parser expects ; at the beginning of the next if statement.
                anchor_line, col, token = len(modified) + 2, 1, ';'
            elif kind == 'substitute':
                edited[1] = edited[1].replace(') {', '] {')
                anchor_line = len(modified) + 2
                col = edited[1].index(']') + 1
                token = ')'
            else:
                edited[1] = edited[1].replace(') {', '; ) {')
                anchor_line = len(modified) + 2
                col = edited[1].index(';') + 1
                token = ')'
            labels.append({'line': anchor_line, 'column': col,
                           'operation': kind, 'token': token})
        original.extend(chunk)
        modified.extend(edited)
    while len(modified) < lines:
        pad = f'int pad_{len(modified)} = 1;'
        original.append(pad)
        modified.append(pad)
    return '\n'.join(modified) + '\n', labels, '\n'.join(original) + '\n'


def score_recovery(labels, repairs):
    """Exact match on line, column, operation and intended token."""
    unmatched = list(labels)
    correct = 0
    for repair in repairs:
        match = next((label for label in unmatched
                      if all(repair.get(key) == label[key]
                             for key in ('line', 'column', 'operation', 'token'))), None)
        if match is not None:
            correct += 1
            unmatched.remove(match)
    return correct


def score_detection(labels, diagnostics):
    """Location-level detection only (not repair correctness)."""
    unmatched = list(labels)
    tp = 0
    for diagnostic in diagnostics:
        match = next((label for label in unmatched
                      if diagnostic['line'] == label['line']
                      and diagnostic['column'] == label['column']), None)
        if match is not None:
            tp += 1
            unmatched.remove(match)
    return tp, len(diagnostics) - tp, len(unmatched)


def run_case(source, labels, mode, repeats=3):
    timings = []
    parser = None
    for _ in range(repeats):
        start = time.perf_counter()
        tokens = tokenize(source)
        if mode == 'panic':
            parser = PanicModeParser(tokens)
        else:
            parser = Parser(tokens, validate_repairs=(mode == 'validated'),
                            scoring_mode='legacy' if mode == 'legacy' else 'contextual')
        # The default 50-error cap is retained; label count is at most 40.
        parser.parse()
        timings.append((time.perf_counter() - start) * 1000)
    tp, fp, fn = score_detection(labels, parser.diagnostics)
    repairs = getattr(parser, 'repairs', [])
    correct = score_recovery(labels, repairs)
    return dict(mode=mode, injected_errors=len(labels), diagnostics=len(parser.diagnostics),
                tp=tp, fp=fp, fn=fn, precision=round(tp / (tp + fp), 4) if tp + fp else '',
                recall=round(tp / (tp + fn), 4) if tp + fn else '',
                correct_repairs=correct,
                repair_recall=round(correct / len(labels), 4) if labels else '',
                total_repairs=len(repairs),
                median_ms=round(statistics.median(timings), 3),
                error_cap_reached=len(parser.diagnostics) >= parser.max_errors)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sizes', nargs='+', type=int, default=[120, 500, 1000, 5000])
    ap.add_argument('--errors', type=int, default=40)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--out', default='results/mixed_benchmark.csv')
    ap.add_argument('--save-samples', action='store_true')
    args = ap.parse_args()
    if args.repeats < 1:
        ap.error('--repeats must be >= 1')
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for size in args.sizes:
        count = min(args.errors, 40, (size - 1) // 6)
        source, labels, valid = make_program(size, count, args.seed)
        # Verify that the unmodified reference is valid in our actual grammar.
        StrictParser(tokenize(valid)).parse()
        if args.save_samples:
            (path.parent / f'mixed_{size}_lines.c').write_text(source, encoding='utf-8')
            (path.parent / f'mixed_{size}_valid.c').write_text(valid, encoding='utf-8')
        for mode in MODES:
            row = run_case(source, labels, mode, args.repeats)
            row['lines'] = size
            rows.append(row)
            print(f'{size:>5} lines | {mode:<10} | detection {row["tp"]:>2}/{count:<2} '
                  f'| exact repairs {row["correct_repairs"]:>2}/{count:<2} '
                  f'| FP={row["fp"]:<2} | {row["median_ms"]:>8.3f} ms'
                  + (' | ERROR CAP' if row['error_cap_reached'] else ''))
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved: {path}')
    print('Detection = exact line/column; repair = exact line/column/operation/token.')
    print('Synthetic supported-grammar inputs only; this is not a full-C benchmark.')


if __name__ == '__main__':
    main()
