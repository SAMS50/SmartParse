"""Multi-seed, clustered and dispersed mixed-error evaluation.

A cluster means erroneous six-line blocks are adjacent. This is NOT a
same-statement multi-edit benchmark. Results are synthetic and grammar-limited.
"""
import argparse
import csv
from pathlib import Path
from statistics import mean, median

from mixed_benchmark import make_program, run_case, MODES
from smartparse import StrictParser, tokenize


def build_case(lines, errors, seed, layout):
    """Generate a labelled case, with deterministic clustered or dispersed edits."""
    if layout not in ('clustered', 'dispersed'):
        raise ValueError('layout must be clustered or dispersed')
    # The existing generator chooses distinct blocks randomly. To control
    # positions without duplicating the source generator, reorder its six-line
    # blocks, carrying exact labels to the new positions.
    source, labels, reference = make_program(lines, errors, seed)
    source_lines = source.splitlines()
    ref_lines = reference.splitlines()
    blocks = (lines - 1) // 6
    original_error_blocks = { (item['line'] - 2) // 6 for item in labels }
    error_blocks = [i for i in range(blocks) if i in original_error_blocks]
    clean_blocks = [i for i in range(blocks) if i not in original_error_blocks]
    if layout == 'clustered':
        # Place erroneous blocks together in the middle of the program.
        left = len(clean_blocks) // 2
        order = clean_blocks[:left] + error_blocks + clean_blocks[left:]
    else:
        # Spread errors evenly across the program.
        order = []
        pending_error = error_blocks.copy()
        pending_clean = clean_blocks.copy()
        for position in range(blocks):
            should_error = (position * errors // blocks !=
                            (position + 1) * errors // blocks)
            if should_error and pending_error:
                order.append(pending_error.pop(0))
            elif pending_clean:
                order.append(pending_clean.pop(0))
            else:
                order.append(pending_error.pop(0))
        order.extend(pending_error)
    by_block = {(item['line'] - 2) // 6: item for item in labels}
    new_labels = []
    new_source = []
    new_reference = []
    for new_block, old_block in enumerate(order):
        new_source.extend(source_lines[old_block * 6:(old_block + 1) * 6])
        new_reference.extend(ref_lines[old_block * 6:(old_block + 1) * 6])
        if old_block in by_block:
            label = by_block[old_block].copy()
            label['line'] = new_block * 6 + 2
            new_labels.append(label)
    new_source.extend(source_lines[blocks * 6:])
    new_reference.extend(ref_lines[blocks * 6:])
    return '\n'.join(new_source) + '\n', new_labels, '\n'.join(new_reference) + '\n'


def evaluate(sizes=(500, 1000), seeds=(11, 22, 33), errors=40, repeats=2):
    rows = []
    for size in sizes:
        count = min(errors, 40, (size - 1) // 6)
        for layout in ('clustered', 'dispersed'):
            for seed in seeds:
                source, labels, valid = build_case(size, count, seed, layout)
                StrictParser(tokenize(valid)).parse()
                for mode in MODES:
                    result = run_case(source, labels, mode, repeats)
                    result.update(lines=size, seed=seed, layout=layout)
                    rows.append(result)
    return rows


def summarize(rows):
    groups = {}
    for row in rows:
        key = (row['lines'], row['layout'], row['mode'])
        groups.setdefault(key, []).append(row)
    summary = []
    for (lines, layout, mode), group in sorted(groups.items()):
        total = sum(r['injected_errors'] for r in group)
        tp = sum(r['tp'] for r in group)
        fp = sum(r['fp'] for r in group)
        repairs = sum(r['correct_repairs'] for r in group)
        summary.append(dict(lines=lines, layout=layout, mode=mode,
                            programs=len(group), injected_errors=total,
                            tp=tp, fp=fp, fn=total - tp,
                            detection_recall=round(tp / total, 4) if total else 0,
                            exact_repair_recall=round(repairs / total, 4) if total else 0,
                            median_ms=round(median(r['median_ms'] for r in group), 3),
                            error_cap_programs=sum(bool(r['error_cap_reached']) for r in group)))
    return summary


def save_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sizes', nargs='+', type=int, default=[500, 1000, 5000])
    ap.add_argument('--seeds', nargs='+', type=int, default=[11, 22, 33, 44, 55])
    ap.add_argument('--errors', type=int, default=40)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--out-dir', default='results')
    args = ap.parse_args()
    if args.repeats < 1 or args.errors < 1 or any(size < 12 for size in args.sizes):
        ap.error('Require repeats >= 1, errors >= 1 and sizes >= 12')
    rows = evaluate(args.sizes, args.seeds, args.errors, args.repeats)
    summary = summarize(rows)
    save_csv(Path(args.out_dir) / 'robust_trials.csv', rows)
    save_csv(Path(args.out_dir) / 'robust_summary.csv', summary)
    for row in summary:
        print(f"{row['lines']:>5} {row['layout']:<9} {row['mode']:<10} "
              f"detect={row['tp']}/{row['injected_errors']} "
              f"repair={row['exact_repair_recall']:.1%} "
              f"FP={row['fp']} cap={row['error_cap_programs']}/{row['programs']} "
              f"median={row['median_ms']:.2f}ms")
    print('Saved robust_trials.csv and robust_summary.csv')
    print('Caution: errors occupy adjacent blocks, not the same statement; '
          'panic mode cannot perform token repairs.')


if __name__ == '__main__':
    main()
