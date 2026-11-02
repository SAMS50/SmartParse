"""Render evaluation tables directly from recorded experiment output."""
from collections import Counter
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def fraction(metric):return f"{metric['numerator']}/{metric['denominator']}"


def main():
    dev=json.loads((ROOT/'results/development.json').read_text(encoding='utf-8'))
    held=json.loads((ROOT/'results/heldout.json').read_text(encoding='utf-8'))
    historical=json.loads((ROOT/'results/historical.json').read_text(encoding='utf-8'))
    lines=['# Milestone 12 evaluation','',
        'Frozen algorithm/dataset fingerprint: `'+held['algorithm_fingerprint']+'`. Development-selected margin: **12**. No algorithm or dataset change after the held-out run. The original 20 are historical comparisons, not development or held-out samples.','',
        '## Dataset and protocol','',
        '84 new deterministic cases: 32 development cases in 8 source families; 52 held-out cases in 13 families (12 authored routine families plus one repository-memory family containing 4 distinct C fixtures). All token-deletion histories are synthetic/reconstructed. There are zero recorded human editing sessions or independently adjudicated labels. Real Chrome events are integration tests, excluded from accuracy denominators.','',
        'Identifiers/numbers are normalized for deduplication; development and held-out share neither normalized malformed programs nor source-family IDs. Multiple mutations of a family remain correlated, so intervals resample families. This reduces leakage but does not establish independence across conceptual algorithm families. All valid reference programs are checked by an evaluator-owned compiler. The generator receives only malformed source, never truth or history. Legitimate history snapshots/deleted text can reconstruct the pre-edit program; that optimistic condition is explicitly labeled.','',
        'Both versions use margin 12 in primary results. All four modes within each version share a candidate pool. Cross-version pools and semantic coverage differ; generation coverage is reported rather than attributing all gains to ranking. `existing` denotes contextual heuristic ranking on that version’s pool, not a new claim about the old parser’s source reconstruction. V11 code/results are unchanged.','',
        '## Development versus held-out','',
        '| Split / system | Correct | Wrong | Abstained | Accuracy among recommendations | Top-3 | Intended candidate generated |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,data in (('Development',dev),('Held-out',held),('Historical',historical)):
        for system in ('v11-existing','v11-full','v12-existing','v12-history','v12-semantic','v12-full'):
            s=data['systems'][system]
            lines.append('| '+name+' / '+system+' | '+' | '.join(fraction(s[k]) for k in ('exact','wrong','abstained','accuracy','top3','candidate_coverage'))+' |')
    lines+=['','The initial development run exposed a merged identifier/control-keyword error and an implicitly declared function accepted by this Clang version. A bounded lexical-boundary candidate and C99+ declaration validation were added before the final development selection. All margins 0, 6, 12, 24 tied on the final development result; the predeclared tie rule retained 12. Thus the data did not identify a superior numeric margin. `d91f95c` froze this selection before held-out evaluation.','',
        '## Missing, misleading and incomplete history (held-out)','',
        '| History condition | N | V11 correct / wrong | V12 correct / wrong |','|---|---:|---:|---:|']
    for condition in sorted({r['history_condition'] for r in held['cases']}):
        rows=[r for r in held['cases'] if r['history_condition']==condition]
        values=[f"{sum(r['systems'][v]['exact'] for r in rows)} / {sum(r['systems'][v]['wrong'] for r in rows)}" for v in ('v11-full','v12-full')]
        lines.append(f"| {condition} | {len(rows)} | {' | '.join(values)} |")
    lines+=['','V12 full and semantic-only make the same held-out recommendations: no incremental benefit from history scoring is demonstrated on this set. History-only is more conservative. Reliability gates apply to all enhanced modes and are deliberately separate from the numerical history-score ablation. A valid replay is not a guarantee of current intent.','',
        '## Selective prediction','',
        'Primary margin sweeps 0, 6, 12, 24 are flat in both versions on held-out data: v11 stays at 20/52 coverage and 16/20 accuracy; v12 stays at 28/52 coverage and 28/28 accuracy. Fixed reliability/consensus gates dominate these decisions. This is a reported negative calibration result, not evidence that margin is irrelevant on other data.','',
        'The following **diagnostic-only** stricter score-gap selectors remove already-issued full-mode recommendations when a finite top-two gap falls below the listed threshold. Singleton pools have infinite gap. They do not enable withheld predictions, are not deployed Studio policies, and were not used for tuning. All thresholds are shown so coverage/accuracy is not compared under hidden selectors.','',
        '| Minimum gap | V11 recommendations / 52 | V11 correct / recommended | V12 recommendations / 52 | V12 correct / recommended |',
        '|---:|---:|---:|---:|---:|']
    curves=[]
    for threshold in (0,12,60,120,240):
        data=[]
        for version in ('v11-full','v12-full'):
            accepted=[r['systems'][version] for r in held['cases'] if r['systems'][version]['recommended'] and
                      (r['systems'][version]['margin'] is None or r['systems'][version]['margin']>=threshold)]
            data.extend([f'{len(accepted)}/52',f"{sum(r['exact'] for r in accepted)}/{len(accepted)}"])
        lines.append('| '+str(threshold)+' | '+' | '.join(data)+' |')
        curves.append(dict(minimum_gap=threshold,values=data))
    lines+=['','A large heuristic gap is not calibrated correctness confidence: misleading histories can have very large gaps. Stricter selection can discard correct repairs and retain incorrect ones. Exact-intent accuracy is not a behavioral equivalence metric.','',
        '## Uncertainty','',
        'Seeded 2,000-replicate source-family bootstrap percentile intervals (exploratory 95%, not formal significance tests):','',
        '| System | Exact recommendation rate | Wrong recommendation rate | Accuracy when recommending |','|---|---|---|---|']
    for system in ('v11-full','v12-full'):
        bounds=held['family_bootstrap'][system]['intervals']
        lines.append('| '+system+' | '+' | '.join(f'{bounds[k][0]:.3f}–{bounds[k][1]:.3f}' for k in ('exact_rate','wrong_rate','selective_accuracy'))+' |')
    upper=held['family_bootstrap']['v12-full']['zero_error_family_risk_upper95']
    lines+=['',f'V12’s zero-error bootstrap degenerates to zero observed error / perfect observed selective accuracy. It does **not** establish zero future risk. With 13 independently sampled families assumed, zero observed error families still permit a one-sided 95% upper bound of {upper:.3f} on the probability a family contains an error. These families are authored rather than randomly sampled, further limiting inference. No statistical significance, broad general superiority or non-inferiority claim is made.','',
        '## Runtime','',
        '| Split | V11 generation ms | V12 generation ms | V11 end-to-end ms | V12 end-to-end ms |','|---|---:|---:|---:|---:|']
    for split,data in (('Development',dev),('Held-out',held),('Historical',historical)):
        g=data['mean_generation_ms'];f=data['mean_full_system_ms']
        lines.append(f"| {split} | {g['v11']:.2f} | {g['v12']:.2f} | {f['v11']:.2f} | {f['v12']:.2f} |")
    delta=held['mean_full_system_ms']['v12']-held['mean_full_system_ms']['v11']
    mismatches=[(r['id'],v) for r in held['cases'] for v in ('v11','v12') if any(r['systems'][v+'-full'][key]!=r['full_system_decisions'][v][key] for key in ('exact','wrong','recommended'))]
    lines+=['',f'Held-out mean end-to-end overhead: {delta:.2f} ms ({100*delta/held["mean_full_system_ms"]["v11"]:.1f}%). Ranking-only and independent full-system recommendation decisions differed on {len(mismatches)} version/case pairs. Single-run timings include compiler startup and concurrent local validation; fixed ordering and cache/OS effects prevent a performance-significance claim. Rank timings and full evidence are in the JSON.','',
        '## Failure examples and remaining abstentions','',
        '| Held-out case | Intended candidate generated | V12 decision reason |','|---|---|---|']
    for row in held['cases']:
        obs=row['systems']['v12-full']
        if not obs['exact']:lines.append(f"| {row['id']} | {obs['coverage']} | {obs['reason']} |")
    lines+=['','`lcm-*` illustrates insufficient candidate exploration for multiple functions and merged/late boundaries. No post-held-out repair tuning was performed. Multi-error histories reconstructed as one broad replacement can trigger conservative abstention despite several tiny actual deletions. Candidate coverage and exactness remain limited by bounded search and formatting. Pointer/resource fixtures remain unsupported; these are appropriate abstentions rather than demonstrated recoveries. Historical scalar-global and unique punctuation cases improve, while a broad multi-edit history loses a previously correct recommendation.','',
        'Only syntax/type acceptance and structural projections are checked; no repaired program is executed, and undefined behavior, aliasing, data-flow equivalence and programmer intent are not proven. “Wrong” means compilable exact-source mismatch, which can include behaviorally equivalent text. All correct labels are evaluator-derived synthetic ground truths.','',
        '## Reproduction','',
        'From repository root in PowerShell:', '', '```powershell',
        '.\\.studio-venv\\Scripts\\python.exe -m phase6.v12.evaluate --split development --full-system --selection .studio-artifacts/m12/reproduced-selection.json --output .studio-artifacts/m12/reproduced-development.json',
        '.\\.studio-venv\\Scripts\\python.exe -m phase6.v12.evaluate --split heldout --full-system --selection .studio-artifacts/m12/reproduced-selection.json --output .studio-artifacts/m12/reproduced-heldout.json',
        '.\\.studio-venv\\Scripts\\python.exe -m phase6.v12.evaluate --split historical --full-system --output .studio-artifacts/m12/reproduced-historical.json',
        '.\\.studio-venv\\Scripts\\python.exe -m phase6.v12.report',
        '```','',
        'The report renderer reads committed results; reproduction commands write new run outputs outside tracked directories. The original v11 benchmark can be rerun independently with `python -m phase6.v11.benchmark --full-system --output .studio-artifacts/m12/reproduced-v11.json`.','']
    (ROOT/'EVALUATION_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':main()
