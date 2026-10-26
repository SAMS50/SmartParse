"""Create two figures from mixed_benchmark.csv (requires matplotlib)."""
import argparse
import csv
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default='results/mixed_benchmark.csv')
    ap.add_argument('--out-dir', default='results')
    args = ap.parse_args()
    import matplotlib.pyplot as plt
    with open(args.csv, newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError('CSV is empty')
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    modes = ['panic', 'legacy', 'contextual', 'validated']
    sizes = sorted({int(r['lines']) for r in rows})
    for field, ylabel, filename in (
        ('recall', 'Detection recall (location)', 'mixed_detection.png'),
        ('repair_recall', 'Exact intended-repair recall', 'mixed_repairs.png'),
        ('median_ms', 'Median execution time (ms)', 'mixed_runtime.png'),
    ):
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for mode in modes:
            subset = {int(r['lines']): r for r in rows if r['mode'] == mode}
            ax.plot(sizes, [float(subset[s][field] or 0) for s in sizes],
                    marker='o', label=mode)
        ax.set(xlabel='Program lines', ylabel=ylabel)
        ax.set_xticks(sizes)
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / filename, dpi=170)
        plt.close(fig)
        print('Saved:', out / filename)
    print('Panic mode does not implement token repairs; its repair recall is zero by definition.')


if __name__ == '__main__':
    main()
