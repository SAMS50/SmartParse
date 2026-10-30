"""Generate descriptive tables and review packets from immutable tool reports."""
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
from .prepare import HERE,ROOT,write_json,verify_freeze
from .evaluation import match,unavailable_metrics


def load(path):return json.loads(path.read_text(encoding='utf-8'))


def csv_write(name,rows):
    path=HERE/'tables'/name;path.parent.mkdir(exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(rows)


def flatten(report):
    """Keep immutable compiler baseline and conditioned current observations apart."""
    r=report['result'];diagnostics=[]
    if r.get('schema')=='smartparse.semantic_analysis':
        memory=r['upstream'];v4=memory['upstream'];v3=v4['recovery_report']
        diagnostics += [dict(d,_stage='compiler_baseline',_conditioned=False) for d in v3['baseline']['analysis']['diagnostics']]
        provenance=r['provenance'];conditioned=any(provenance.get(k) for k in ('repair_conditioned','isolation_conditioned'))
        stages=(memory.get('eligibility') or {}).get('stages',{})
        frontend=stages.get('compiler',{}).get('frontend_accepted',False)
        analyzer=stages.get('analyzer',{}).get('completion','not_attempted')
        for item in memory.get('observations',[])+r.get('findings',[]):
            d=dict(item['evidence'],_stage='analyzer_or_semantic',_conditioned=conditioned,
                   _blocked=not frontend or analyzer!='completed')
            d['related']=[n.get('original_location') or n for n in item.get('notes',[])]
            diagnostics.append(d)
        eligibility=dict(frontend_accepted=frontend,analyzer_completion=analyzer,
                         function_path_coverage_certified=False,conditioned=conditioned,
                         excluded_functions=v4.get('isolation',{}).get('excluded_functions',[]),
                         accepted_repairs=v3.get('recovery',{}).get('accepted_variants',[]))
    else:
        external=r.get('schema')=='smartparse.external_analysis'
        diagnostics=[dict(d,_stage='external' if external else 'compiler',_conditioned=False,
                          _blocked=external and r.get('status')!='completed') for d in r.get('diagnostics',[])]
        accepted=None if external else r.get('execution',{}).get('returncode')==0
        eligibility=dict(frontend_accepted=accepted,analyzer_completion=r.get('status') if external else 'not_attempted',
                         function_path_coverage_certified=False,conditioned=False)
    return diagnostics,eligibility


def main():
    verify_freeze();manifest=load(HERE/'manifest.json');config=load(HERE/'configurations.json')
    syntax=[]
    for name in config['syntax']:
        reports=[load(p) for p in sorted((HERE/'outputs/syntax'/name).glob('*.json'))]
        syntax.append(dict(configuration=name,cases=len(reports),completed=sum(r['status']=='completed' for r in reports),
            unsupported_lexer=sum(r['status']=='unsupported_lexer' for r in reports),
            proposed_roots=sum(len(c['roots']) for c in manifest['cases'] if c['cohort']=='syntax'),
            author_location_matches=sum(len(r.get('author_location_matches',[])) for r in reports),
            author_exact_repairs=sum(len(r.get('author_exact_repairs',[])) for r in reports),
            intended_stream_equal=sum(r.get('intended_token_stream_equal') is True for r in reports),
            strict_replay_valid=sum(r.get('replay_strictly_valid') is True for r in reports),
            reached_eof=sum(r.get('reached_eof') is True for r in reports),
            additional_diagnostics=sum(r.get('additional_diagnostics',0) for r in reports),
            invalid_intended_references=sum(r.get('intended_reference_valid') is False for r in reports),
            elapsed_seconds=round(sum(r['elapsed_seconds'] for r in reports),6),
            TP=None,FP=None,FN=None,precision=None,recall=None,F1=None,
            review_status='pending; author proposals only; context_default aliases validation_on'))
    csv_write('table_I_syntax.csv',syntax)
    allcases=[dict(c,absolute_path=str((ROOT/c['path']).resolve())) for c in manifest['cases'] if c['cohort']=='c']
    results=[];review=[];benchmark=[]
    for configuration in config['extended']:
        for case in allcases+[dict(id='benchmark',absolute_path=str(ROOT/'acceptance/cleaned/c_error_detection_500_lines.c'))]:
            path=HERE/'outputs/extended'/configuration/(case['id']+'.json')
            if not path.exists():continue
            report=load(path);r=report['result'];diagnostics,eligibility=flatten(report)
            row=dict(case=case['id'],configuration=configuration,status=r.get('status'),
                     elapsed_seconds=report.get('elapsed_seconds'),diagnostics=diagnostics,eligibility=eligibility,
                     compiler_invocations=r.get('usage',{}).get('compiler_invocations',0),
                     analyzer_invocations=r.get('usage',{}).get('analyzer_invocations'),
                     metrics=unavailable_metrics())
            if case['id']!='benchmark':row['evaluation']=match(case,Path(case['absolute_path']).read_bytes(),diagnostics)
            else:
                primary=[d for d in diagnostics if d.get('severity') in ('error','fatal error','warning') and not d.get('context_note')]
                fingerprint={(d.get('file'),d.get('line'),d.get('column'),d.get('diagnostic_id'),d.get('message')) for d in primary}
                benchmark.append(dict(configuration=configuration,status=r.get('status'),primary_diagnostics=len(primary),
                    exact_unique_diagnostics=len(fingerprint),exact_duplicate_diagnostics=len(primary)-len(fingerprint),
                    confirmed_roots=None,potential_root_count=None,frontend_accepted=eligibility['frontend_accepted'],
                    analyzer_completion=eligibility['analyzer_completion'],conditioned=eligibility['conditioned'],
                    historical_baseline='16/68 historical, separate; M7 nine locally reviewed potential incremental roots, not human-confirmed',
                    review_status='Fresh findings pending root review; raw warnings are not root totals'))
            for i,d in enumerate(diagnostics):
                if d.get('severity') in ('error','fatal error','warning') and not d.get('context_note'):
                    review.append(dict(case=case['id'],configuration=configuration,diagnostic=i,line=d.get('line'),
                        identifier=d.get('diagnostic_id'),message=d.get('message'),conditioned=d.get('_conditioned'),
                        human_decision=None,root_id=None,reviewer=None,review_date=None,disagreement=None))
            results.append(row)
    write_json(HERE/'outputs/evaluation.json',dict(schema='smartparse.descriptive_evaluation',schema_version='1.0',
        origin='author-created; not independent',metrics=unavailable_metrics(),results=results))
    write_json(HERE/'review/decisions.json',dict(status='pending_human_review',decisions=review))
    capabilities=[];adjudication=[];categories=[]
    for configuration in config['extended']:
        rows=[r for r in results if r['configuration']==configuration and r['case']!='benchmark']
        original={root for r in rows for root in r['evaluation']['original_supported_proposals']}
        conditional={root for r in rows for root in r['evaluation']['conditioned_supported_proposals']}
        capabilities.append(dict(configuration=configuration,cases=len(rows),expected_cases=len(allcases),
            statuses=json.dumps(dict(sorted(Counter(r['status'] for r in rows).items()))),
            original_supported_proposals=len(original),conditioned_supported_proposals=len(conditional),confirmed_roots=None,
            compiler_invocations=sum(r['compiler_invocations'] for r in rows),
            elapsed_seconds=round(sum(r['elapsed_seconds'] or 0 for r in rows),3),
            frontend_accepted=sum(r['eligibility']['frontend_accepted'] is True for r in rows),
            analyzer_completed=sum(r['eligibility']['analyzer_completion']=='completed' for r in rows),
            certified_function_path_coverage=False))
        adjudication.append(dict(configuration=configuration,TP=None,FP=None,FN=None,precision=None,recall=None,F1=None,
            pending_supported_proposals=len(original),conditional_supported_proposals=len(conditional),
            unobserved_proposals=sum(len(r['evaluation']['unobserved_proposals']) for r in rows),
            blocked_cases=sum(r['status'] in ('blocked','partial') for r in rows),
            unmatched_primary_records=sum(len(r['evaluation']['unmatched_primary_indices']) for r in rows),
            duplicate_support_records=sum(r['evaluation']['duplicate_support_records'] for r in rows),
            reason='Unobserved proposals are not confirmed false negatives; unmatched warnings are not confirmed false positives'))
        for category in sorted({root['category'] for c in allcases for root in c['roots']}):
            ids={root['id'] for c in allcases for root in c['roots'] if root['category']==category}
            categories.append(dict(configuration=configuration,category=category,author_proposals=len(ids),
                original_supported_proposals=len(ids&original),conditioned_supported_proposals=len(ids&conditional),confirmed_roots=None))
    # Union root sets, not warnings. No conditioned proposal enters this cohort.
    sets={name:{root for r in results if r['case']!='benchmark' and r['configuration']==name for root in r['evaluation']['original_supported_proposals']} for name in config['extended']}
    union=set().union(*sets.values())
    comparison=dict(original_sets={k:sorted(v) for k,v in sets.items()},combined_optional_original_only=sorted(union),
        exclusive={name:sorted(roots-set().union(*(s for k,s in sets.items() if k!=name))) for name,roots in sets.items()},
        all_configurations_intersection=sorted(set.intersection(*sets.values())),
        unobserved_by_all=sorted({root['id'] for c in allcases for root in c['roots']}-union),
        note='Pending author proposals, not verified defects. Conditional cohorts remain separate.',
        exclusive_claim_scope='Frozen matcher only, not unique detector capability; known allowlist and anchor omissions are documented in review/frozen_matching_limitations.json.')
    capabilities.append(dict(configuration='combined_optional',cases=len(allcases),expected_cases=len(allcases),
        statuses='{"derived_union_no_new_execution": 20}',original_supported_proposals=len(union),
        conditioned_supported_proposals=0,confirmed_roots=None,compiler_invocations=0,elapsed_seconds=None,
        frontend_accepted=None,analyzer_completed=None,certified_function_path_coverage=False))
    adjudication.append(dict(configuration='combined_optional',TP=None,FP=None,FN=None,precision=None,recall=None,F1=None,
        pending_supported_proposals=len(union),conditional_supported_proposals=0,unobserved_proposals=len(comparison['unobserved_by_all']),
        blocked_cases=None,unmatched_primary_records=None,duplicate_support_records=None,
        reason='Derived root union, not another execution; matching gaps and independent adjudication pending'))
    for category in sorted({root['category'] for c in allcases for root in c['roots']}):
        ids={root['id'] for c in allcases for root in c['roots'] if root['category']==category}
        categories.append(dict(configuration='combined_optional',category=category,author_proposals=len(ids),
            original_supported_proposals=len(ids&union),conditioned_supported_proposals=0,confirmed_roots=None))
    write_json(HERE/'outputs/root_comparison.json',comparison)
    # Reproduction of prior source-reviewed benchmark evidence is identity-based,
    # not a new adjudication. Keep the old provisional root relationships intact.
    prior=load(ROOT/'phase6/v7/outputs/benchmark_source_review.json')
    prior_report=load(ROOT/'phase6/v7/outputs/comparison/cppcheck/benchmark.json')
    old_by_id={d['id']:d for d in prior_report['diagnostics']}
    fresh=next((r for r in results if r['case']=='benchmark' and r['configuration']=='cppcheck'),None)
    signature=lambda d:(d.get('file'),d.get('line'),d.get('column'),d.get('diagnostic_id'),d.get('message'))
    signatures={signature(d) for d in fresh['diagnostics']} if fresh else set()
    reproduced=[]
    for review in prior['reviews']:
        d=old_by_id.get(review['evidence_id'])
        reproduced.append(dict(prior_review=review,exact_diagnostic_reproduced=bool(d and signature(d) in signatures),
                               independently_verified=False,review_status='pending_human_review'))
    write_json(HERE/'outputs/benchmark_prior_evidence_comparison.json',dict(
        source_sha256=prior['source_sha256'],historical_baseline_16_of_68_unchanged=True,
        prior_new_potential_roots=prior['new_source_supported_root_ids'],comparisons=reproduced,
        caveat='Exact reproduction is not an independent confirmation. No cascade or duplicate becomes a new root.'))
    csv_write('table_II_capabilities.csv',capabilities);csv_write('table_III_categories.csv',categories)
    csv_write('table_IV_adjudication.csv',adjudication);csv_write('table_V_benchmark.csv',benchmark)
    package=['# Human review package','',
        'No decisions are prefilled. Review source/contract and path evidence; do not confirm by line or warning count alone.',
        'Assign root IDs and TP/FP/uncertain/unsupported/blocked decisions in decisions.json; record reviewer/date and disagreements.',
        'The authored reference is a proposal, not an independently certified oracle. Corrected controls can also contain overlooked issues.',
        'For every warning, distinguish duplicate/cascade/real root/review suggestion. Repair/isolation conditions must remain attached.',
        'Inspect full raw per-configuration JSON under outputs/extended, including notes, exact commands and frontend status.','']
    for case in allcases:
        package += [f'## {case["id"]}',json.dumps(case['roots'],ensure_ascii=False,indent=2),'```c']
        package += [f'{i:03d} | {line}' for i,line in enumerate(Path(case['absolute_path']).read_text().splitlines(),1)]
        package += ['```','']
    (HERE/'review/REVIEW_PACKAGE.md').write_text('\n'.join(package),encoding='utf-8')
    print(json.dumps(dict(syntax=syntax,extended=capabilities,combined_provisional_roots=len(union),benchmark=benchmark),indent=2))


if __name__=='__main__':main()
