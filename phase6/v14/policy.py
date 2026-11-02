"""Transparent evidence selection. Missing signals contribute zero, not penalties."""
from dataclasses import dataclass
from phase6.v11.history import score as history_score
from phase6.v13.ingest import tokens

MODES=('FULL_EVIDENCE','SEMANTIC_EVIDENCE','HISTORY_EVIDENCE','SYNTAX_ONLY','INSUFFICIENT_EVIDENCE')


@dataclass(frozen=True)
class Policy:
    max_edit_hunks:int=1
    margin:float=12


def syntax_eligible(candidate,policy):
    changes=candidate['changes']
    return 1<=len(changes)<=policy.max_edit_hunks and all(not e['deleted'].strip() and
        bool(e['inserted'].strip()) and set(e['inserted'].strip())<=set(';,') for e in changes)


def decide(source,pool,snapshots,reliability,policy=Policy(),use_semantic=True,use_history=True):
    ranked=[]
    history_available=bool(use_history and len(snapshots)>1 and reliability['mapping_verified'] and not reliability['broad_edit'])
    for raw in pool:
        c={k:v for k,v in raw.items() if not k.startswith('_')}
        if not use_history and c['semantic_risk']['status']=='NO_DETECTED_STRUCTURAL_CHANGE' and snapshots:
            c['semantic_risk']={**c['semantic_risk'],'status':'UNKNOWN','reason':'Positive historical-reference comparison withheld in the no-history ablation'}
        h=history_score(source,c['source'],snapshots if history_available else [])
        sem=c['semantic_risk'];supported=use_semantic and sem['status']=='NO_DETECTED_STRUCTURAL_CHANGE'
        components=dict(heuristic=c['heuristic'],history=h['score'] if history_available else 0,
                        structural_agreement=20 if supported else 0,edit_cost=-2*len(c['changes']))
        c.update(history=h,components=components,score=round(sum(components.values()),6),
            explanation='Explicit ranking components: '+str(components)+'. Missing evidence adds no penalty. Compilation does not prove intent.',
            semantic={k:dict(status='UNKNOWN',explanation=sem['reason']) for k in ('statement_ownership','block_boundaries','variable_scope','variable_binding','expression_grouping','function_boundaries','control_flow')},
            status='alternative repair' if c['validation']['status']=='VALID' else 'unverified suggestion')
        if sem.get('checks') and isinstance(next(iter(sem['checks'].values())),dict):c['semantic']=sem['checks']
        ranked.append(c)
    def blocked(c):return c['semantic_risk']['status'] in ('VERIFIED_STRUCTURAL_CHANGE','CHECK_FAILED') or c['semantic_risk'].get('mapping_reliable') is False
    ranked.sort(key=lambda c:(c['validation']['status']!='VALID',blocked(c),-c['score'],c['id']))
    all_valid=[c for c in ranked if c['validation']['status']=='VALID']
    valid=[c for c in all_valid if not blocked(c)]
    distinct={c['token_program_sha256'] for c in valid}
    missing=[]
    if not history_available:missing.append('reliable recent editing-history support')
    available=['compiler-validated syntax'] if valid else []
    if history_available:available.append('verified edit-history replay')
    recommendation=None;mode='INSUFFICIENT_EVIDENCE';reason='No candidate completed compiler validation.';outcome='abstention'
    if not valid and all_valid:reason=all_valid[0]['semantic_risk']['reason']+' Automatic fallback is blocked.'
    if valid:
        best=valid[0];sem=best['semantic_risk'];positive_semantic=use_semantic and sem['status']=='NO_DETECTED_STRUCTURAL_CHANGE'
        if positive_semantic:available.append('supported structural comparison')
        else:missing.append('verified structural preservation; '+sem['status'])
        strong_history=history_available and best['history']['restored_snapshot']
        # These are negative or failed checks, not merely missing evidence. Never downgrade them.
        hard_risk=sem['status'] in ('VERIFIED_STRUCTURAL_CHANGE','CHECK_FAILED')
        failed_alternatives=any(c['validation']['status']=='UNVERIFIED' for c in ranked)
        close=len(valid)>1 and len(distinct)>1 and best['score']-valid[1]['score']<=policy.margin
        boundary_ambiguity=strong_history and reliability['boundary_deletion'] and len({c['token_program_sha256'] for c in all_valid})>1
        if not reliability['mapping_verified']:reason='Editing-history evidence is not usable: '+reliability['reason']+'. Confirmation is required.'
        elif hard_risk:reason=sem['reason']+' Automatic fallback is blocked.'
        elif sem.get('mapping_reliable') is False:reason='Macro source mapping is uncertain; confirmation is required.'
        elif failed_alternatives:reason='Some alternatives remain unverified; confirmation is required.'
        elif boundary_ambiguity or close:reason='Multiple plausible repairs remain; programmer confirmation is recommended.'
        elif strong_history or positive_semantic:
            mode='FULL_EVIDENCE' if strong_history and positive_semantic else 'HISTORY_EVIDENCE' if strong_history else 'SEMANTIC_EVIDENCE'
            recommendation=best['id'];reason='The repair is compiler-valid and supported by '+('recent edits and structural checks.' if mode=='FULL_EVIDENCE' else 'recent edit evidence; structural impact remains unverified.' if mode=='HISTORY_EVIDENCE' else 'supported structural checks; original intent is still not proved.')
        elif len(distinct)==1 and syntax_eligible(best,policy):
            recommendation=best['id'];mode='SYNTAX_ONLY'
            reason='A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified.'
        else:reason='Validated alternatives exist, but available evidence does not support choosing a repair.'
        if recommendation:outcome='recommended repair'
        else:outcome='suggested alternatives'
    for c in ranked:
        if c['validation']['status']=='UNVERIFIED':c['status']='unverified suggestion'
        elif c['validation']['status']!='VALID':c['status']='rejected repair'
        elif c['id']==recommendation:c['status']='recommended repair'
        elif blocked(c):c['status']='blocked repair'
    return dict(algorithm='milestone-14',decision=outcome,outcome=outcome,decision_mode=mode,reason=reason,
        recommendation=recommendation,available_evidence=available,missing_evidence=missing,
        evidence_reliability=dict(history=reliability['intent_support'],syntax='compiler validation, not an intent guarantee'),
        evidence_basis='Evidence-adaptive decision; '+mode,candidates=ranked,
        recommended_repairs=[recommendation] if recommendation else [],
        alternatives=[c['id'] for c in ranked if c['status']=='alternative repair'],
        unverified_suggestions=[c['id'] for c in ranked if c['status']=='unverified suggestion'],
        blocked_repairs=[c['id'] for c in ranked if c['status']=='blocked repair'],reliability=reliability,
        history_status=reliability['reason'])
