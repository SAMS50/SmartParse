"""Independent seeded evaluation of opt-in bounded-pair recovery.

Synthetic C-like grammar only. Holdout templates and seeds are not in the Phase 2
six-case development set. Exact labels refer to intended token edits.
"""
import argparse
import csv
import random
import statistics
import time
import tracemalloc
from pathlib import Path

from smartparse import Parser, StrictParser, tokenize
from mixed_benchmark import make_program

MODES = ('legacy', 'contextual', 'selective', 'bounded_pair')


def make_holdout(seed):
    rng = random.Random(seed)
    # Different names, numbers, loop/condition structures, punctuation and closers.
    # Cases are synthetic and share the same general error class as the training cases.
    cases = []
    for n in range(12):
        name = f'hold_{seed}_{n}'
        value = rng.randint(2, 99)
        keyword = rng.choice(('if', 'while'))
        punctuation = rng.choice((';', ','))
        closer = rng.choice((']', '}'))
        good = f'int {name} = {value};\n{keyword} ({name} > 1) {{ {name} = {name} - 1; }}\n'
        bad = good.replace(') {', f' {punctuation} {closer} {{', 1)
        expected = [('delete', ')', punctuation), ('substitute', ')', closer)]
        StrictParser(tokenize(good)).parse()
        cases.append((f'H{seed}-{n:02}', bad, expected))
    return cases


def make_scaling(lines, seed, count=20):
    source, _, valid = make_program(lines, 0, seed)
    StrictParser(tokenize(valid)).parse()
    rng = random.Random(seed)
    chunks = source.splitlines()
    eligible = [i for i, line in enumerate(chunks) if line.startswith('if (')]
    selected = rng.sample(eligible, min(count, len(eligible)))
    for idx in selected:
        chunks[idx] = chunks[idx].replace(') {', ' ; ] {', 1)
    return '\n'.join(chunks) + '\n', 2 * len(selected)


def parse_once(source, mode):
    parser = Parser(tokenize(source), validate_repairs=mode == 'selective' or mode == 'bounded_pair',
                    scoring_mode='legacy' if mode == 'legacy' else 'contextual',
                    validation_policy='selective', multi_token_recovery=mode == 'bounded_pair')
    parser.parse()
    return parser


def measure(source, mode, repeats, memory=False):
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        parser = parse_once(source, mode)
        samples.append((time.perf_counter() - start) * 1000)
    peak_kib = None
    if memory:
        tracemalloc.start()
        try:
            parse_once(source, mode)
            _, peak = tracemalloc.get_traced_memory()
            peak_kib = round(peak / 1024, 1)
        finally:
            tracemalloc.stop()
    return parser, round(statistics.median(samples), 4), peak_kib


def evaluate_holdout(seeds=(101, 202, 303), repeats=3):
    rows = []
    for seed in seeds:
        for case, source, intended in make_holdout(seed):
            for mode in MODES:
                parser, ms, _ = measure(source, mode, repeats)
                actual = [(r['operation'], r['token'], r['from']) for r in parser.repairs]
                rows.append(dict(case=case, seed=seed, mode=mode,
                                 correct_repairs=sum(x in actual for x in intended),
                                 expected_repairs=len(intended), exact_sequence=int(actual == intended),
                                 total_repairs=len(actual), diagnostics=len(parser.diagnostics),
                                 paired_accepted=parser.multi_token_stats['accepted'],
                                 median_ms=ms, actual=repr(actual), intended=repr(intended)))
    return rows


def evaluate_scaling(sizes=(500, 1000, 5000), seeds=(101, 202), repeats=2):
    rows = []
    for size in sizes:
        for seed in seeds:
            source, expected = make_scaling(size, seed)
            for mode in MODES:
                parser, ms, peak = measure(source, mode, repeats, memory=True)
                actual_pairs = sum(r.get('multi_token', False) for r in parser.repairs)
                rows.append(dict(lines=size, seed=seed, mode=mode, expected_repairs=expected,
                                 paired_repairs=actual_pairs, total_repairs=len(parser.repairs),
                                 diagnostics=len(parser.diagnostics),
                                 error_cap=int(len(parser.diagnostics) >= parser.max_errors),
                                 median_ms=ms, peak_tracemalloc_kib=peak))
    return rows


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--sizes', type=int, nargs='+', default=[500, 1000, 5000])
    ap.add_argument('--seeds', type=int, nargs='+', default=[101, 202, 303])
    ap.add_argument('--out-dir', default='results')
    args = ap.parse_args()
    if args.repeats < 1 or not args.seeds or any(s < 12 for s in args.sizes):
        ap.error('Require repeats >= 1, at least one seed, sizes >= 12')
    holdout = evaluate_holdout(args.seeds, args.repeats)
    scaling = evaluate_scaling(args.sizes, args.seeds[:2], args.repeats)
    write_csv(Path(args.out_dir) / 'phase4_holdout.csv', holdout)
    write_csv(Path(args.out_dir) / 'phase4_scaling.csv', scaling)
    for mode in MODES:
        subset = [r for r in holdout if r['mode'] == mode]
        print(f'{mode:12} holdout={sum(r["correct_repairs"] for r in subset)}/{sum(r["expected_repairs"] for r in subset)} exact_cases={sum(r["exact_sequence"] for r in subset)}/{len(subset)}')
    for size in args.sizes:
        for mode in MODES:
            subset = [r for r in scaling if r['lines'] == size and r['mode'] == mode]
            print(f'{size:5} {mode:12} paired_edits={sum(r["paired_repairs"] for r in subset)}/{sum(r["expected_repairs"] for r in subset)} median_ms={statistics.median(r["median_ms"] for r in subset):.3f} median_peak_KiB={statistics.median(r["peak_tracemalloc_kib"] for r in subset):.1f}')
    print('Saved phase4_holdout.csv and phase4_scaling.csv')
    print('Memory uses Python tracemalloc (not full process RSS); synthetic grammar-limited results.')


if __name__ == '__main__':
    main()
