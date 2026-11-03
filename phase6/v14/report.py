"""Render frozen adaptive experiments without publishing external student code."""
from collections import Counter
import json
from pathlib import Path
from .evaluate import fingerprint

ROOT=Path(__file__).resolve().parent


def frac(value):return f"{value['numerator']}/{value['denominator']}"+(' (unavailable)' if not value['denominator'] else '')


def main():
    data={s:json.loads((ROOT/'results'/f'{s}.json').read_text(encoding='utf-8')) for s in ('development','exposed','independent')}
    if any(r['algorithm_fingerprint']!=fingerprint() for r in data.values()):raise ValueError('Experiment code changed after calibration')
    new=data['independent'];adaptive=new['systems']['adaptive-combined']
    lines=['# Milestone 14 evaluation: evidence-adaptive recovery','',
        '**Useful lower-assurance proposals are restored, but algorithmic superiority is not demonstrated.** New evaluation: adaptive combined makes 12 exact recommendations, zero exact mismatches, eight alternative-suggestion cases and 60 abstentions out of 80. Existing scoring makes 13 exact recommendations with zero mismatches. All adaptive recommendations originate from Clang. The four known mismatches remain on the exposed benchmark. Zero observed mistakes on the new set cannot establish acceptable error risk in general.','',
        '## Frozen methodology and provenance','',
        'The v13 baseline was reproduced and all 79 A abstentions audited before algorithm changes (`b735ce0`). The original 80 selected final records are **exposed** (79 A, 1 B). Twenty original development records alone calibrate the hunk cap. The next 80 pinned-TEGCER inferred source families form the new, previously unexamined evaluation; all 80 locally verify as category A. No compiler-outcome replacement or correction/history leakage. All 180 selected errors are maintainer-documented genuine student errors; no recorded preceding histories exist.','',
        'The underlying pinned archive, GPL-3.0 provenance and privacy/source policy are inherited from v13. Student code, corrections, raw compiler text and timestamps stay in ignored local storage. Public manifests contain hashes/metadata. Family separation uses inferred token/SimHash families, not assignment/student identifiers. This is a new split from one dataset, not independent cross-project evidence.','',
        'Policy choices 1/2 edit hunks were evaluated on development only. Both yield two exact recommendations and no wrong recommendations; the predeclared tie rule selects one hunk. Score margin stays 12. `f69e5a1` commits the final policy/development evidence before new outcomes. Algorithm fingerprint: `'+new['algorithm_fingerprint']+'`. No recovery policy tuning followed the new evaluation.','',
        '## Correctness amendment and rerun','', 'Final validation found a UTF-8 character/Clang-byte offset mismatch in the new structural-risk check. Commit `2e395c1` fixes it with a regression test. Two exposed sources contain non-ASCII text; development and new inputs are ASCII. The first-run records were preserved locally and all three evaluations rerun without policy tuning. Comparison of all 180 cases across eight systems found zero changes in recommendations, outcomes, selected hashes, candidate IDs, modes, origins or reasons. See `results/correctness-rerun.json`. The new set was unexamined before its first evaluation; the correctness rerun is not a pristine unseen test. Timings below are corrected-run measurements.','', '## Actual results','',
        '| Split / system | Exact | Token match | Wrong exact match | Recommended | Suggested alternatives | Abstained | Intended candidate coverage | Selective exact accuracy |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for split,result in data.items():
        for name,s in result['systems'].items():
            lines.append('| '+split+' / '+name+' | '+' | '.join(frac(s[k]) for k in ('exact','token_match','wrong','recommended','suggested_alternatives','abstained','candidate_coverage','accuracy_when_recommended'))+' |')
    lines+=['','Recommended / suggested alternatives / abstention are mutually exclusive v14 outcomes. A suggestion is not counted as an automatic recommendation or a wrong recommendation. Legacy systems have their original recommend/abstain outcomes. Nonrecommendation (alternatives + abstention) is also recorded to prevent a cosmetic category change from appearing as increased repair coverage. All issued recommendations have compiler-valid candidates; behavioral equivalence is not assessed.','',
        '## Candidate-provider attribution and ablations','',
        'Custom-only, compiler-only and combined arms use explicitly different provider pools. All combined-policy arms (adaptive, without positive semantic support, without positive history support and simple fallback) share the exact candidate pool. Positive-evidence ablations retain hard known-risk/mapping/failed-check vetoes; they do not pretend known hazards disappeared. No-history also withholds positive historical-reference agreement.','',
        '| Split | Custom-only exact recommendations | Compiler-only exact recommendations | Combined exact recommendations | Combined recommended origins | Combined decision modes |',
        '|---|---:|---:|---:|---|---|']
    for split,result in data.items():
        s=result['systems'];c=s['adaptive-combined']
        lines.append(f"| {split} | {frac(s['adaptive-custom']['exact'])} | {frac(s['adaptive-compiler']['exact'])} | {frac(c['exact'])} | {c['attribution']} | {c['modes']} |")
    lines+=['','All 12 new combined recommendations are Clang-derived, as are all 22 recommendations on the exposed set. Custom-only makes no recommendations. It supplies one exact intended candidate in development and none in the new or exposed evaluation sets (its new-set token-level top-3 coverage is 2/80). Combined and compiler-only make identical recommendations; custom adds three new-set alternative-suggestion cases. The demonstrated contribution is evidence routing, safety gates, explicit attribution and reviewable proposals, not an original C repair algorithm outperforming Clang.','',
        'Without positive semantic/history support, outcomes remain identical on this corpus because historical evidence is absent and whole-program preprocessing remains unsupported. Unit tests and actual Studio editing exercise other evidence modes; these are not relabeled genuine-history benchmark results.','',
        '## Simple fallback comparison and limits','',
        'The preregistered simple comparator chooses the highest existing heuristic among compiler-valid combined candidates without adaptive evidence/safety gates. On new data it makes 17 exact and three mismatched recommendations versus adaptive 12 exact and zero mismatches: five correct outputs are withheld to avoid those three. Existing v13 scoring is better on this particular set: 13 exact with no mismatches versus 12 exact with no mismatches.','',
        'Additional **post-hoc descriptive pool check**, not a tuned or deployed selector: the new compiler-only pools contain exactly 17 validated singletons and all match the reference. Thus a simple validated compiler-only selector would make 17 exact recommendations with zero observed mismatches. This further rules out an observed selection advantage for the adaptive policy. The four exposed semicolon mismatches are still recommended; the syntax-only gate cannot certify intent.','',
        '## Uncertainty and paired comparisons','',
        f"New adaptive exact rate {adaptive['exact']['estimate']:.3f}, Wilson 95% interval {adaptive['exact']['wilson95']}. Conditional exact accuracy 12/12 has interval {adaptive['accuracy_when_recommended']['wilson95']}. Zero wrong/80 has upper Wilson bound {adaptive['wrong']['wilson95'][1]:.3f}; zero events are not proof of zero future risk. Exact-source mismatch can include token-equivalent formatting, not a proven behavior change.",'',
        '| New evaluation comparison â†’ adaptive combined | Exact-rate difference | Paired family-bootstrap 95% interval | Adaptive-only / comparator-only successes |',
        '|---|---:|---|---|']
    for name,p in new['paired'].items():lines.append(f"| {name} | {p['mean_difference']:.4f} | {p['interval95']} | {p['right_only']} / {p['left_only']} |")
    lines+=['','Bootstrap uses 2,000 seeded paired family resamples. Inferred families can share assignments/templates; N=80 is small, no real histories exist, and one repository cannot establish cross-project generality. No significance, formal safety, equivalence or research-superiority claim is made.','',
        '## Runtime','',
        '| Split | V13 shared evidence mean / median / p95 ms | Adaptive shared preparation mean / median / p95 ms | Mean overhead |','|---|---|---|---|']
    for split,result in data.items():
        a=result['runtime_ms']['adaptive'];b=result['runtime_ms']['v13'];delta=a['mean']-b['mean']
        lines.append(f"| {split} | {b['mean']:.2f} / {b['median']:.2f} / {b['p95']:.2f} | {a['mean']:.2f} / {a['median']:.2f} / {a['p95']:.2f} | {delta:.2f} ms ({100*delta/b['mean']:.1f}%) |")
    lines+=['','Compiler capability probes, full-source validation and additional candidate rounds add material overhead. Timing is shared candidate/evidence preparation per case, not the sum of all policy variants, and excludes evaluator-only reference checks. Concurrent tests and two evaluation processes affect these one-run measurements; no performance-significance claim. Each compiler call and shared compiler-evidence deadline is bounded, but local parser CPU and cleanup are not a hard real-time guarantee.','',
        '## Case-level new-evaluation ledger','',
        '| Case | Class | Valid custom / compiler / combined | Intended generated | Mode | Outcome | Exact / wrong | Selected provider | Explanation |',
        '|---|---|---:|---|---|---|---|---|---|']
    for r in new['cases']:
        s=r['systems'];c=s['adaptive-combined']
        counts=' / '.join(str(s['adaptive-'+p]['valid_candidates']) for p in ('custom','compiler','combined'))
        lines.append(f"| {r['id']} | {r['category']} | {counts} | {c['candidate_coverage']} | {c['decision_mode']} | {c['outcome']} | {c['exact']} / {c['wrong']} | {c['provider']} | {c['reason']} |")
    lines+=['','## Exposed-case outcomes (not an unseen test)','',
        '| Case | Class | Adaptive outcome | Exact / wrong | Mode | Explanation |','|---|---|---|---|---|']
    for r in data['exposed']['cases']:
        c=r['systems']['adaptive-combined']
        lines.append(f"| {r['id']} | {r['category']} | {c['outcome']} | {c['exact']} / {c['wrong']} | {c['decision_mode']} | {c['reason']} |")
    lines+=['','All four exposed mismatches identified in `ROOT_CAUSE_ANALYSIS.md` remain; none was blacklisted by case ID. Their compiler-valid semicolon edits are insufficient to prove the reference intention. Missing validated candidates, unsupported structural checks, failed checks and unverified suggestions remain distinct in API records. Curated JSON includes all case metrics, provider sets, blocked/unverified counts and the calibration fingerprint, but no student source.','',
        '## Reproduction','',
        'See `MILESTONE_14_REPORT.md` for PowerShell setup, dataset preparation, explicit development/new/exposed commands, all milestone test commands and browser workflow. `python -m phase6.v14.report` regenerates this report from committed results. Raw sources and detailed candidate programs remain in ignored `.studio-artifacts/m14/`. Any further tuning needs new development data and another frozen evaluation split.','']
    (ROOT/'EVALUATION_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':main()
