"""Review-aware adapter to the unchanged v1 evidence evaluator."""
import copy
from phase6.v1.evaluation import normalize_runs,admissible,evaluate,fingerprint
from phase6.v5.engine import export_v1_run


def export_run(report,sid):
    if any(report['provenance'][key] for key in ('repair_conditioned','isolation_conditioned')):
        raise ValueError('conditioned semantics cannot enter unconditional v1 evidence')
    if not report['source']['original_unchanged'] or not report['temporary_workspace_removed'] or report['status'] in ('failed','timed_out','budget_exhausted'):
        raise ValueError('unverified semantic evidence')
    run=export_v1_run(report['upstream'],sid);run=copy.deepcopy(run);run['id']='v6-'+sid
    for finding in report['findings']:
        if not finding['duplicate_of_existing']:
            run['report']['diagnostics'].append(finding['evidence'])
            # Independent backend support for the same source fact is retained,
            # then reviewed as a duplicate root rather than a new detection.
            run['report']['static_analysis']['findings'].extend(d for d in finding['backend_witnesses'] if d['backend']=='clang-static-analyzer')
    return run


def evaluate_reports(dataset,reports,semantic=False):
    runs=[export_run(r,sid) if semantic else export_v1_run(r,sid) for sid,r in reports.items()]
    evidence,_,_=normalize_runs(dataset,runs)
    review={'scope':{'dataset':fingerprint(dataset),'runs':fingerprint(runs)},'review_kind':'Agent-reviewed authored fixture bindings; independent human review pending.',
            'matches':[],'adjudications':[],'contracts':{}}
    for defect in dataset['defects']:
        candidates=sorted((eid for eid,item in evidence.items() if admissible(defect,item)))
        if not candidates:continue
        first=candidates[0]
        review['matches'].append({'defect_id':defect['id'],'evidence_id':first,'decision':'match','reviewer':'Codex-source-review',
                                  'rationale':defect['review_provenance']['rationale']})
        for eid in candidates[1:]:review['adjudications'].append({'evidence_id':eid,'decision':'duplicate','duplicate_of':first,
                                  'reviewer':'Codex-source-review','rationale':'Same source-bound structural root/conditional target; not an independent defect.'})
    return evaluate(dataset,runs,review)
