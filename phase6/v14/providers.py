"""Bounded custom and Clang proposals with explicit origin and physical mappings."""
import re
import subprocess
import time
from phase6.v11.engine import generate as old_generate,Config,edits
from phase6.v12.candidates import supplemental
from phase6.v13.compiler import Compiler,apply_fixits
from phase6.v13.ingest import sha,privacy_or_safety,tokens


class BoundedCompiler(Compiler):
    def __init__(self,deadline):
        self.calls=0;self.deadline=deadline
        super().__init__('clang',timeout=2)
    def _call(self,args,data=None):
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise subprocess.TimeoutExpired('clang',0)
        self.timeout=min(2,remaining);self.calls+=1
        return super()._call(args,data)


def directive_lines(source):
    return {i for i,line in enumerate(source.splitlines(keepends=True)) if line.lstrip().startswith('#')}


def mask_directives(source):
    protected=directive_lines(source);lines=source.splitlines(keepends=True)
    masked=''.join(''.join(c if c in '\r\n' else ' ' for c in line) if i in protected else line for i,line in enumerate(lines))
    def restore(text):
        changed=text.splitlines(keepends=True)
        for i in protected:
            if i>=len(changed) or changed[i].strip():raise ValueError('Custom proposal changed a protected directive')
            changed[i]=lines[i]
        return ''.join(changed)
    return masked,restore


def normalized_edits(source,repaired):
    result=edits(source,repaired)
    protected=directive_lines(source)
    for e in result:
        e['start_byte']=len(source[:e['offset']].encode());e['end_byte']=len(source[:e['end_offset']].encode())
        if e['line']-1 in protected:raise ValueError('Edit touches a preprocessor directive')
    text=source
    for e in reversed(result):text=text[:e['offset']]+e['inserted']+text[e['end_offset']:]
    if text!=repaired:raise ValueError('Original-coordinate edit replay failed')
    return result


class ProposalValidator:
    """Validate restored full source; hide compiler hints from the custom provider."""
    def __init__(self,validator,restore):self.validator=validator;self.restore=restore
    def inspect(self,text):
        try:r=self.validator.inspect(self.restore(text))
        except ValueError:return dict(status='INVALID',reason='',tree=None)
        return {**r,'reason':''}


def custom_proposals(source,validator):
    masked,restore=mask_directives(source)
    proxy=ProposalValidator(validator,restore)
    pool,info=old_generate(masked,proxy,Config(max_candidates=20))
    result=[]
    for c in pool:
        try:result.append((restore(c['source']),c['heuristic'],'smartparse_custom',c['origin'],None))
        except ValueError:pass
    for text,origin,score in supplemental(masked,''):
        try:result.append((restore(text),score,'smartparse_custom',origin,None))
        except ValueError:pass
    return result[:24],info


def compiler_proposals(source,validator,standard='c11'):
    tool=BoundedCompiler(validator.deadline)
    tool.flags=[('-std='+standard if a.startswith('-std=') else a) for a in tool.flags]
    tool.identity['flags']=tool.flags[:]
    if tool.identity['status']!='available':return [],dict(status='unavailable',calls=tool.calls,identity=tool.identity)
    original=tool.check(source);hints=original.get('fixits',[]);result=[]
    def add(hs,base,origin):
        text,why=apply_fixits(base,hs)
        if text is not None and text!=source:
            try:normalized_edits(source,text)
            except ValueError:return None
            result.append((text,35,'clang_fixit',origin,hs if base==source else None));return text
        return None
    bundle=add(hints,source,'Clang nonoverlapping fix-it bundle')
    if len(hints)>1:
        for h in hints[:4]:add([h],source,'Clang individual machine fix-it')
    # One follow-up round addresses a failed partial bundle, never unlimited repair.
    if bundle and validator.inspect(bundle)['status']=='INVALID' and time.monotonic()<validator.deadline:
        follow=tool.check(bundle)
        add(follow.get('fixits',[]),bundle,'Clang two-round combined fix-its')
    return result[:6],dict(status=original['status'],calls=tool.calls,identity=tool.identity,
                          original_accepted=original.get('accepted'),machine_fixits=len(hints))


def generate(source,validator,standard='c11'):
    rejected=privacy_or_safety(source)
    if rejected:return [],dict(stop_reason=rejected,compiler_calls=0)
    original=validator.inspect(source)
    if original['status']=='VALID':return [],dict(stop_reason='Original source already compiler-valid',compiler_calls=0)
    custom,custom_info=custom_proposals(source,validator)
    clang,clang_info=compiler_proposals(source,validator,standard)
    pool={}
    # Keep compiler proposals reviewable even when custom search fills its budget.
    for text,score,provider,origin,physical in clang+custom:
        if text==source:continue
        try:changes=normalized_edits(source,text)
        except ValueError:continue
        key=sha(text)
        if key in pool:
            c=pool[key];c['origins']=sorted(set(c['origins']+[provider]));c['origin']='combined' if len(c['origins'])>1 else provider
            c['heuristic']=max(c['heuristic'],score);continue
        if len(pool)>=24:continue
        v=validator.inspect(text)
        pool[key]=dict(id=key[:16],source=text,heuristic=score,origins=[provider],origin=provider,
            provider_explanation=origin,machine_edits=physical,changes=changes,
            token_program_sha256=sha('\0'.join(tokens(text))),validation=dict(status=v['status'],reason=v['reason']),
            _tree=v.get('tree'))
    return list(pool.values()),dict(custom=custom_info,clang=clang_info,compiler_calls=clang_info.get('calls',0),
                                   retained=len(pool),retained_limit=24,original_validation=original['status'])


def select_pool(pool,provider):
    if provider not in ('custom','compiler','combined'):raise ValueError('Unknown candidate provider')
    name='smartparse_custom' if provider=='custom' else 'clang_fixit'
    return pool if provider=='combined' else [c for c in pool if name in c['origins']]
