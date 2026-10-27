"""Phase 5G: same-case, clearly separated diagnostic and repair evaluation.

Diagnostic detection is comparable across parser modes. Exact reference recovery is
reported only for the standalone/integrated CGAR repair streams. No semantic
correctness or statistically generalizable superiority is claimed.
"""
import argparse
import csv
import tracemalloc
from pathlib import Path
from statistics import median
from time import perf_counter
from baseline import PanicModeParser
from smartparse import Parser, tokenize
from cgar_reliable import advise
from phase5d_eval import CASES, values

MODES = ('panic', 'smartparse', 'cgar_advisor', 'integrated_cgar')

def run_one(mode, source):
    if mode == 'cgar_advisor':
        a = advise(source)
        corrected = (tuple((t.kind,t.value) for t in a.result.corrected)
                     if a.result is not None and a.status in ('verified_candidate','unchanged') else None)
        return dict(status=a.status, detected=int(a.status in ('verified_candidate','abstain')),
                    diagnostics=None, suggestions=int(a.status=='verified_candidate'),
                    corrected=corrected, fallback=False)
    if mode == 'panic':
        p = PanicModeParser(tokenize(source))
    elif mode == 'smartparse':
        p = Parser(tokenize(source))
    elif mode == 'integrated_cgar':
        p = Parser(tokenize(source),verified_cgar=True)
    else:
        raise ValueError(mode)
    p.parse()
    status = p.verified_cgar_status if mode == 'integrated_cgar' else 'not_applicable'
    corrected = None
    if mode == 'integrated_cgar' and status in ('verified_candidate','unchanged'):
        a=p.verified_cgar_advice
        if a is not None and a.result is not None:
            corrected=tuple((t.kind,t.value) for t in a.result.corrected)
        elif status == 'unchanged':
            corrected=values(source)
    return dict(status=status,detected=int(bool(p.diagnostics)),
                diagnostics=len(p.diagnostics), suggestions=len(p.repairs),
                corrected=corrected, fallback=mode=='integrated_cgar' and status=='abstain')

def evaluate(repeats=5):
    if repeats<1: raise ValueError('repeats must be positive')
    rows=[]
    for case in CASES:
        # S07 has an intentionally different but grammatically valid reference.
        # The input itself is legal; this is not a syntax-error detection target.
        syntactically_invalid = case.name not in ('S07','S09','S10')
        for mode in MODES:
            timings=[]; peaks=[]; output=None
            for _ in range(repeats):
                tracemalloc.start()
                start=perf_counter()
                try: output=run_one(mode,case.broken)
                finally:
                    elapsed=(perf_counter()-start)*1000
                    _, peak=tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                timings.append(elapsed);peaks.append(peak/1024)
            exact = (int(output['corrected']==values(case.reference))
                     if output['corrected'] is not None else None)
            # False alarms on syntactically valid input only; ambiguous advisory
            # statuses are not treated as error detections.
            rows.append(dict(case=case.name,category=case.category,mode=mode,
                syntax_invalid=int(syntactically_invalid),detected=output['detected'],
                false_alarm=int(not syntactically_invalid and output['detected']),
                diagnostics=output['diagnostics'] if output['diagnostics'] is not None else 'N/A',
                suggestions=output['suggestions'],status=output['status'],
                exact_reference=exact if exact is not None else 'N/A',
                exact_available=int(exact is not None),
                fallback=int(output['fallback']),median_ms=round(median(timings),4),
                median_peak_kib=round(median(peaks),2)))
    return rows

def summary(rows):
    out=[]
    for mode in MODES:
        subset=[r for r in rows if r['mode']==mode]
        invalid=[r for r in subset if r['syntax_invalid']]
        valid=[r for r in subset if not r['syntax_invalid']]
        comparable=[r for r in subset if r['exact_available']]
        out.append(dict(mode=mode, cases=len(subset),
            detected_invalid=f"{sum(r['detected'] for r in invalid)}/{len(invalid)}",
            false_alarms_valid=f"{sum(r['false_alarm'] for r in valid)}/{len(valid)}",
            exact_reference=f"{sum(r['exact_reference'] for r in comparable)}/{len(comparable)}" if comparable else 'N/A',
            abstentions=sum(r['status']=='abstain' for r in subset),
            median_ms=round(median(r['median_ms'] for r in subset),4),
            median_peak_kib=round(median(r['median_peak_kib'] for r in subset),2)))
    return out

def save_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--repeats',type=int,default=5)
    args=p.parse_args()
    rows=evaluate(args.repeats); sums=summary(rows)
    save_csv(Path('results/phase5g_cases.csv'),rows)
    save_csv(Path('results/phase5g_summary.csv'),sums)
    for s in sums:
        print(f"{s['mode']:17} detected={s['detected_invalid']:5} false_alarms={s['false_alarms_valid']:3} exact_on_available={s['exact_reference']:5} abstain={s['abstentions']:2} median={s['median_ms']:.4f}ms peak={s['median_peak_kib']:.2f}KiB")
    print('CAUTION: exact_on_available has a conditional denominator; it is NOT overall accuracy.')
    print('Original SmartParse and panic-mode lack a comparable reconstructed edit stream (N/A).')
    print('S07 is valid under the grammar although its supplied reference removes an empty statement.')
    print('Timings and tracemalloc peaks are exploratory and environment-dependent.')
    print('Saved: results/phase5g_cases.csv and results/phase5g_summary.csv')
if __name__=='__main__': main()
