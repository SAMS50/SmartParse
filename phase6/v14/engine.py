"""Evidence-adaptive recovery API; analyzed C is never executed or overwritten."""
from dataclasses import asdict
import json
from pathlib import Path
import time
from phase6.v12.history import assess
from phase6.v12.engine import reference_for
from phase6.v12.semantics import Validator
from phase6.v13.ingest import sha,privacy_or_safety
from .providers import generate,select_pool
from .semantics import analyze
from .policy import Policy,decide


def prepare(source,history=None,standard='c11'):
    start=time.perf_counter();validator=Validator(standard,max_calls=32,seconds=15)
    pool,generation=generate(source,validator,standard)
    snapshots,reliability=assess(source,history)
    if any(privacy_or_safety(s) for s in snapshots):
        snapshots=[];reliability={**reliability,'mapping_verified':False,'intent_support':'unusable history',
                                  'reason':'A historical snapshot contains unsupported or unsafe input'}
        reference=None
    else:reference=reference_for(snapshots,validator)
    for c in pool:c['semantic_risk']=analyze(source,c,reference)
    valid=[c for c in pool if c['validation']['status']=='VALID']
    if reference is None and len(valid)>1 and all(c['semantic_risk']['status']=='UNKNOWN' and c.get('_projection') is not None and c['_projection']==valid[0].get('_projection') for c in valid):
        for c in valid:c['semantic_risk']=dict(status='NO_DETECTED_STRUCTURAL_CHANGE',
            reason='Supported valid alternatives have matching structural projections; original intent and behavior are not proved',checks={})
    return pool,snapshots,reliability,dict(generation=generation,
        compiler_invocations=validator.calls+generation.get('compiler_calls',0),elapsed_seconds=time.perf_counter()-start)


def deployed_policy():
    path=Path(__file__).with_name('selection.json')
    return Policy(max_edit_hunks=json.loads(path.read_text(encoding='utf-8'))['max_edit_hunks']) if path.exists() else Policy()


def recover(source,history=None,mode='full',standard='c11',policy=None,provider='combined'):
    if mode not in ('full','history','semantic','existing'):raise ValueError('Unknown adaptive evidence ablation')
    policy=policy or deployed_policy()
    pool,snapshots,reliability,usage=prepare(source,history,standard)
    result=decide(source,select_pool(pool,provider),snapshots,reliability,policy,
                  use_semantic=mode not in ('history','existing'),use_history=mode not in ('semantic','existing'))
    result.update(**usage,policy=asdict(policy),provider=provider,original_sha256=sha(source),original_unchanged=True)
    return result
