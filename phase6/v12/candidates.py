"""History-independent additions justified by v11 failure analysis; cap stays 24."""
import hashlib
import re
from dataclasses import replace
from phase6.v11.engine import generate as old_generate, edits
from phase6.v3.policy import fixits, point_offset
from .semantics import projection

LEX=re.compile(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|\S')


def supplemental(source, diagnostic):
    """At most four complete programs: EOF closer, two block boundaries, fix-it bundle."""
    if re.search(r'^\s*#',source,re.M):return []
    stack=[];boundaries=[]
    for m in LEX.finditer(source):
        t=m.group()
        if t in ('(', '{', '['):stack.append(t)
        elif t in (')','}',']'):
            if stack and stack[-1]=={')':'(',']':'[','}':'{'}[t]:stack.pop()
        elif t in ('return','else'):boundaries.append(m.start())
    found=[]
    if 0<len(stack)<=3:
        closers=''.join({'(':')','{':'}','[':']'}[t] for t in reversed(stack))
        found.append((source+closers,'unmatched delimiter completion',20))
        if stack==['{']:
            for at in boundaries[-2:]:found.append((source[:at]+'}'+source[at:],'bounded block-boundary completion',10))
    try:
        code=source.encode();patches=[]
        for f in fixits(diagnostic.encode()):
            if f['file'] not in ('<stdin>','-'):continue
            patches.append((point_offset(code,f['start_line'],f['start_column']),point_offset(code,f['end_line'],f['end_column']),f['replacement'].encode()))
        patches=sorted(set(patches))
        if 1<len(patches)<=3 and all(b<=c and a!=c for (a,b,_),(c,d,__) in zip(patches,patches[1:])):
            for a,b,value in reversed(patches):code=code[:a]+value+code[b:]
            found.append((code.decode(),'nonoverlapping compiler fix-it bundle',35))
    except (ValueError,UnicodeError):pass
    return found[:4]


def generate(source,validator,config):
    pool,info=old_generate(source,validator,replace(config,max_candidates=max(1,config.max_candidates-4)))
    if info['original_status']=='VALID':return pool,info
    for c in pool:c['_projection']=projection(c['source'],validator.inspect(c['source']))
    for text,origin,heuristic in supplemental(source,validator.inspect(source).get('reason','')):
        if text==source or any(c['source']==text for c in pool) or len(pool)>=config.max_candidates:continue
        v=validator.inspect(text)
        pool.append(dict(source=text,heuristic=heuristic,origin=origin,id=hashlib.sha256(text.encode()).hexdigest()[:16],
                         validation=dict(status=v['status'],reason=v['reason']),changes=edits(source,text),_projection=projection(text,v)))
    info['supplemental_limit']=4;info['retained_limit']=config.max_candidates
    return pool,info
