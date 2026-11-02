"""Conservative v12 decisions over bounded, history-independent candidate pools."""
from dataclasses import dataclass, asdict
import hashlib
import time
from phase6.v11.engine import Config as OldConfig, rank as old_rank, MODES, AMBIGUOUS
from phase6.v11.semantics import compare
from .semantics import Validator, projection
from .candidates import generate
from .history import assess


@dataclass(frozen=True)
class Config(OldConfig):
    # Candidate setting fixed before held-out evaluation; evaluated on development only.
    ambiguity_margin:float=12


def reference_for(snapshots,validator):
    for s in reversed(snapshots[:-1]):
        v=validator.inspect(s)
        if v['status']=='VALID':return projection(s,v)
    return None


def rank(source,candidates,snapshots,reference,reliability,mode='full',config=Config()):
    # Reuse the documented v11 score; change evidence eligibility, not fitted weights.
    result=old_rank(source,candidates,snapshots,reference,mode,config,mapping=reliability['mapping_verified'])
    result['algorithm']='milestone-12';result['reliability']=reliability
    valid=[c for c in result['candidates'] if c['validation']['status']=='VALID']
    supported=[raw.get('_projection') for raw in candidates if raw['validation']['status']=='VALID']
    unanimous=bool(supported) and all(p is not None and p==supported[0] for p in supported)
    # A missing-history recommendation needs one supported structure and only
    # non-brace punctuation edits. This does not label UNKNOWN historical checks preserved.
    local_punctuation=bool(valid) and all(
        1<=len(c['changes'])<=3 and all(set(e['deleted']+e['inserted'])<=set(';(),[] \t\r\n') for e in c['changes'])
        for c in valid)
    consensus=unanimous and local_punctuation
    conflicting=len({repr(p) for p in supported if p is not None})>1
    result['evidence_basis']='valid historical structural comparison' if reference is not None else 'no supported historical reference'
    if mode=='existing':return result
    reason=None
    if not reliability['mapping_verified']:reason='Source mappings are unreliable'
    elif reliability['broad_edit']:reason='Broad recent replacement provides insufficient intent evidence'
    elif reliability['boundary_deletion'] and conflicting:
        reason='End-of-source brace restoration conflicts with other valid statement-ownership structures; programmer confirmation is recommended.'
    # If historical structure changed, never let consensus override it.
    elif reference is None and consensus and mode in ('semantic','full'):
        result['recommendation']=valid[0]['id'];result['decision']='recommended repair'
        result['reason']='All validated candidates agree on one supported structure and use only local non-brace punctuation edits'
        result['evidence_basis']='bounded candidate structural consensus; historical preservation remains UNKNOWN'
    if reason:
        result['recommendation']=None;result['decision']='ambiguous repair' if conflicting else 'no safe recommendation';result['reason']=reason
    for c in result['candidates']:
        if c['status']=='recommended repair':c['status']='alternative repair'
        if c['id']==result['recommendation']:c['status']='recommended repair'
        c['evidence_reliability']=reliability['intent_support']
    return result


def recover(source,history=None,mode='full',standard='c11',config=Config()):
    if mode not in MODES:raise ValueError('Unknown ablation mode')
    if len(source)>16384:
        from phase6.v11.engine import recover as old
        return old(source,history,mode,standard,config)
    start=time.perf_counter();v=Validator(standard,max_calls=config.max_candidates+config.history_window+2)
    pool,generation=generate(source,v,config);snapshots,reliability=assess(source,history,config.history_window)
    ref=reference_for(snapshots,v)
    result=rank(source,pool,snapshots,ref,reliability,mode,config)
    result.update(generation=generation,history_status=reliability['reason'],config=asdict(config),
                  original_sha256=hashlib.sha256(source.encode()).hexdigest(),original_unchanged=True,
                  compiler_invocations=v.calls,elapsed_seconds=time.perf_counter()-start)
    return result
