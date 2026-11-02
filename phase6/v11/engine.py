"""Bounded candidate pool independent of history; deterministic evidence ranking."""
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
import hashlib
import time
from smartparse import tokenize, StrictParser, ParseError, LexError, Parser
from recovery import rank_candidates
from phase6.v3.policy import fixits, point_offset
from .history import replay, score as history_score, HistoryConfig
from .semantics import Validator, projection, compare

MODES=('existing','history','semantic','full')
AMBIGUOUS='Multiple plausible repairs were found. Programmer confirmation is recommended.'


@dataclass(frozen=True)
class Config:
    history_window:int=8
    history_weight:float=1
    changed_penalty:float=18
    unknown_penalty:float=4
    ambiguity_margin:float=12
    max_candidates:int=24
    max_trials:int=240


def edits(original, repaired):
    return [dict(offset=a,end_offset=b,deleted=original[a:b],inserted=repaired[c:d],
                 line=original.count('\n',0,a)+1,column=a-original.rfind('\n',0,a))
            for tag,a,b,c,d in SequenceMatcher(None,original,repaired,autojunk=False).get_opcodes() if tag!='equal']


def generate(source, validator, config=Config()):
    """Reuse local candidates, parser plan and Clang fix-its; add bounded punctuation alternatives.

    Restricted grammar alternatives undergo StrictParser filtering before Clang.
    Real-C outside that grammar uses compiler fix-its only. No history input.
    """
    pool={};trials=0;truncated=False
    def add(text,heuristic,origin):
        if text==source:return
        if text in pool:
            if heuristic>pool[text]['heuristic']:pool[text]['heuristic']=heuristic
            return
        if len(pool)>=config.max_candidates:return
        pool[text]=dict(source=text,heuristic=heuristic,origin=origin)
    initial=validator.inspect(source)
    if initial['status']=='VALID':return [],dict(trials=0,truncated=False,original_status='VALID')
    try:
        tokens=tokenize(source)
        def offset(t):return sum(len(x) for x in source.splitlines(keepends=True)[:t.line-1])+t.col-1
        try:StrictParser(tokens).parse()
        except ParseError as error:
            index=next(i for i,t in enumerate(tokens) if t is error.token)
            if error.expected in (';',')','}',']'):
                for c in rank_candidates(tokens,index,error.expected):
                    at=offset(error.token);end=at if c.operation=='insert' else at+len(error.token.value)
                    add(source[:at]+('' if c.operation=='delete' else c.expected)+source[end:],c.score,'existing local candidate')
        parser=Parser(tokens);parser.parse()
        plan=[]
        for r in parser.repairs:
            at=sum(len(x) for x in source.splitlines(keepends=True)[:r['line']-1])+r['column']-1
            end=at if r['operation']=='insert' else at+len(r.get('from',''))
            plan.append((at,end,'' if r['operation']=='delete' else r['token']))
        repaired=source
        for a,b,value in sorted(set(plan),reverse=True):repaired=repaired[:a]+value+repaired[b:]
        if plan:add(repaired,sum(r.get('score') or 0 for r in parser.repairs)/len(plan),'existing parser repair plan')
        for token in tokens:
            at=offset(token)
            options=[(at,at,p) for p in ('}',')',';',']','{','(')]
            if token.value in '{}();,[]':
                options += [(at,at+len(token.value),p) for p in ('', '}',')',';',']','{','(')]
            for a,b,value in options:
                trials+=1
                if trials>config.max_trials:truncated=True;break
                text=source[:a]+value+source[b:]
                try:
                    StrictParser(tokenize(text)).parse()
                    add(text,10,'bounded punctuation alternative')
                except (ParseError,LexError,RecursionError):pass
            if truncated:break
    except (LexError,ParseError,RecursionError,StopIteration):pass
    # Clang diagnostic fix-its are parsed by the existing byte-oriented policy.
    # The diagnostic string is bounded; incomplete fix-its simply generate none.
    try:
        code=source.encode('utf-8')
        for f in fixits(initial.get('reason','').encode('utf-8')):
            a=point_offset(code,f['start_line'],f['start_column']);b=point_offset(code,f['end_line'],f['end_column'])
            add((code[:a]+f['replacement'].encode()+code[b:]).decode(),35,'Clang fix-it')
    except (ValueError,UnicodeError):pass
    # Preserve cheap old-score priority if the validation budget is reached.
    candidates=[]
    for item in sorted(pool.values(),key=lambda c:(-c['heuristic'],c['source'])):
        validation=validator.inspect(item['source'])
        item.update(id=hashlib.sha256(item['source'].encode()).hexdigest()[:16],
                    validation=dict(status=validation['status'],reason=validation['reason']),
                    changes=edits(source,item['source']),_projection=projection(item['source'],validation))
        candidates.append(item)
    return candidates,dict(trials=trials,truncated=truncated or len(pool)>=config.max_candidates,original_status=initial['status'])


def rank(source, candidates, snapshots, reference, mode='full', config=Config(), mapping=True):
    if mode not in MODES:raise ValueError('Unknown ablation mode')
    ranked=[]
    for raw in candidates:
        c={k:v for k,v in raw.items() if not k.startswith('_')}
        c['history']=history_score(source,c['source'],snapshots)
        c['semantic']=compare(reference,raw.get('_projection'))
        changed=sum(x['status']=='CHANGED' for x in c['semantic'].values())
        unknown=sum(x['status']=='UNKNOWN' for x in c['semantic'].values())
        components=dict(heuristic=c['heuristic'],history=config.history_weight*c['history']['score'] if mode in ('history','full') else 0,
                        structural_risk=-config.changed_penalty*changed if mode in ('semantic','full') else 0,
                        missing_evidence=-config.unknown_penalty*unknown if mode in ('semantic','full') else 0)
        c.update(components=components,score=round(sum(components.values()),6),
                 explanation=f'Score components: {components}; changed checks={changed}; unknown checks={unknown}. Syntax acceptance does not prove correctness.',
                 status='alternative repair' if c['validation']['status']=='VALID' else 'unsupported repair')
        ranked.append(c)
    ranked.sort(key=lambda c:(c['validation']['status']!='VALID',-c['score'],c['id']))
    eligible=[c for c in ranked if c['validation']['status']=='VALID']
    reason='No candidate satisfies syntax validation';recommendation=None;decision='no safe recommendation'
    if eligible:
        best=eligible[0];reason='Insufficient supported intent evidence'
        unknown=any(x['status']=='UNKNOWN' for x in best['semantic'].values())
        changed=any(x['status']=='CHANGED' for x in best['semantic'].values())
        ambiguous=len(eligible)>1 and best['score']-eligible[1]['score']<=config.ambiguity_margin
        if mode=='existing':recommendation=best['id'];reason='Existing heuristic maximum (research baseline)'
        elif mode=='history' and mapping and best['history']['restored_snapshot'] and not ambiguous:
            recommendation=best['id'];reason='Verified snapshot restoration; semantic analysis excluded in this ablation'
        elif mapping and not unknown and not changed and not ambiguous:
            recommendation=best['id'];reason='Supported structure preserved with a sufficient ranking margin'
        elif ambiguous:
            reason=AMBIGUOUS;decision='ambiguous repair'
            for c in eligible:
                if best['score']-c['score']<=config.ambiguity_margin:c['status']='ambiguous repair'
        elif unknown:decision='unsupported repair';reason='The behavioral impact could not be determined.'
        if not mapping:recommendation=None;decision='no safe recommendation';reason='Source mappings are unreliable'
        if recommendation:decision='recommended repair';best['status']='recommended repair'
    return dict(mode=mode,decision=decision,reason=reason,recommendation=recommendation,candidates=ranked)


def recover(source, history=None, mode='full', standard='c11', config=Config()):
    start=time.perf_counter();validator=Validator(standard,max_calls=config.max_candidates+config.history_window+2)
    candidates,generation=generate(source,validator,config)
    snapshots,mapping_reason=replay(source,history,HistoryConfig(window=config.history_window))
    reference=None
    for snapshot in reversed(snapshots[:-1]):
        reference=projection(snapshot,validator.inspect(snapshot))
        if reference is not None:break
    result=rank(source,candidates,snapshots,reference,mode,config,mapping=history is None or bool(snapshots))
    result.update(generation=generation,history_status=mapping_reason,config=asdict(config),
                  original_sha256=hashlib.sha256(source.encode()).hexdigest(),original_unchanged=True,
                  compiler_invocations=validator.calls,elapsed_seconds=time.perf_counter()-start)
    return result
