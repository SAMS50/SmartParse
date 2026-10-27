"""Source-reviewed fixture bindings using the unchanged Phase 6 v1 evaluator.

Mechanical bindings do not generalize beyond this hash-bound authored oracle.
Unmatched findings remain unknown; corrected-source warnings are not auto-FPs.
"""
from phase6.v1.evaluation import evaluate,normalize_runs,admissible,fingerprint
from .engine import export_v1_run


def evaluate_fixtures(dataset,reports):
    runs=[export_v1_run(report,sid) for sid,report in reports.items() if sid in dataset['sources'] and report['analysis'] is not None]
    evidence,_,_=normalize_runs(dataset,runs)
    review={'scope':{'dataset':fingerprint(dataset),'runs':fingerprint(runs)},
            'review_kind':'agent-assisted source-reviewed fixture bindings; independent human review pending',
            'matches':[],'adjudications':[],'contracts':{}}
    for defect in dataset['defects']:
        candidates=[(eid,e) for eid,e in evidence.items() if admissible(defect,e)]
        candidates.sort(key=lambda pair:(pair[1]['pass']!='compiler',pair[0]))
        if not candidates:continue
        first=candidates[0][0]
        rationale=defect['review_provenance']['rationale']+' Checker ID, diagnostic meaning and source/sink anchor agree; potential operation defect, not a whole-program execution claim.'
        review['matches'].append({'defect_id':defect['id'],'evidence_id':first,'decision':'match',
                                  'reviewer':'Codex-source-review','rationale':rationale})
        for eid,item in candidates[1:]:
            review['adjudications'].append({'evidence_id':eid,'decision':'duplicate','duplicate_of':first,
                                           'reviewer':'Codex-source-review','rationale':'Same reviewed fixture root; compiler/analyzer observations are not separate defects.'})
    result=evaluate(dataset,runs,review)
    tp=result['summary']['detected_root_cause_count'];fp=result['summary']['confirmed_false_positive_group_count']
    unknown=sum(f['disposition']=='unknown' and f['evidence']['diagnostic']['severity']!='note' for f in result['findings'])
    negatives=set(dataset['corrected_sources'])
    negative_warnings=[f for f in result['findings'] if f['evidence']['source_id'] in negatives and f['evidence']['diagnostic']['severity']=='warning']
    result['bounded_fixture_metrics']={'reviewed_true_root_findings':tp,'known_root_defects':len(dataset['defects']),
        'confirmed_false_positive_groups':fp,'unknown_primary_observations':unknown,'corrected_counterpart_warning_observations':len(negative_warnings),
        'root_recall_in_authored_fixture_corpus':tp/len(dataset['defects']),
        'adjudicated_only_precision':tp/(tp+fp) if tp+fp else None,
        'precision_is_incomplete':bool(unknown),'independent_human_review_pending':True,
        'generalization':'Small authored paired fixtures; no population recall/precision claim.'}
    return result


def compare(baseline,configured):
    left=set(baseline['summary']['detected_root_cause_ids']);right=set(configured['summary']['detected_root_cause_ids'])
    return {'baseline_root_count':len(left),'configured_root_count':len(right),'new_root_cause_ids':sorted(right-left),
            'already_detected_root_cause_ids':sorted(left&right),'lost_root_cause_ids':sorted(left-right),
            'baseline_metrics':baseline['bounded_fixture_metrics'],'configured_metrics':configured['bounded_fixture_metrics'],
            'baseline_categories':baseline['summary']['categories'],'configured_categories':configured['summary']['categories']}
