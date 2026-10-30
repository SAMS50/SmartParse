"""Live CLI checks with per-command supervision and immutable fixture hashes."""
import hashlib
import json
from pathlib import Path
import sys
from phase6.v3.supervision import run_logged
from .validate import OUT,ROOT,write


def main():
    work=OUT/'smoke';work.mkdir(parents=True,exist_ok=True)
    c=ROOT/'phase6/v8/fixtures/c';s=ROOT/'phase6/v8/fixtures/syntax'
    cases=[
        ('doctor',['doctor','--format','json'],0),
        ('help',['analyze','--help'],0),('version',['--version'],0),
        ('valid',['analyze',str(c/'C12_valid_full.c'),'--format','json'],0),
        ('syntax',['analyze',str(c/'C09_repair_null.c'),'--compiler','gcc','--format','json'],1),
        ('type',['analyze',str(c/'C10_isolate_null.c'),'--format','json'],1),
        ('null',['analyze',str(c/'C01_null.c'),'--analyzers','memory','--format','json'],1),
        ('leak',['analyze',str(c/'C02_leak.c'),'--analyzers','memory','--format','json'],1),
        ('bounds',['analyze',str(c/'C05_bounds.c'),'--analyzers','memory','--format','json'],1),
        ('recovery',['analyze',str(c/'C09_repair_null.c'),'--recovery','--format','json'],1),
        ('isolation',['analyze',str(c/'C10_isolate_null.c'),'--isolation','--format','json'],1),
        ('static',['analyze',str(c/'C01_null.c'),'--analyzers','static','--format','json'],1),
        ('gcc14',['analyze',str(c/'C01_null.c'),'--analyzers','gcc14','--format','json'],1),
        ('cppcheck',['analyze',str(c/'C01_null.c'),'--analyzers','cppcheck','--format','json'],1),
        ('header',['analyze',str(c/'C11_missing_header.c'),'--format','json'],3),
        ('unavailable',['analyze',str(c/'C01_null.c'),'--analyzers','cppcheck','--cppcheck',str(work/'not-installed.exe'),'--format','json'],3),
        ('restricted',['analyze',str(s/'S03.c'),'--analyzers','smartparse','--format','json'],1),
        ('terminal',['analyze',str(c/'C01_null.c'),'--analyzers','memory'],1),
        ('markdown',['analyze',str(c/'C01_null.c'),'--analyzers','memory','--format','markdown'],1),
        ('combined',['analyze',str(c/'C01_null.c'),'--analyzers','compiler,static,memory,semantic,gcc14,cppcheck','--format','json'],1),
    ]
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in list(c.glob('*.c'))+list(s.glob('*.c'))}
    records=[]
    for name,args,expected in cases:
        suffix='.json' if 'json' in args else '.md' if 'markdown' in args else '.txt'
        output=work/(name+suffix)
        result=run_logged([sys.executable,'-m','smartparse_cli',*args],output,timeout=50,cwd=ROOT)
        result.update(name=name,expected_exit=expected,passed=result['exit_code']==expected and not result['timed_out'])
        if suffix=='.json':
            try:
                r=json.loads(output.read_text());result['schema']=r['schema']
                result['status']=r.get('status');result['summary']=r.get('summary')
                if r['schema']=='smartparse.unified_analysis':
                    result['source_preserved']=r['source']['original_unchanged']
                    result['passed'] &= result['source_preserved'] is True
                    if name=='recovery':result['passed'] &= any(d['conditioning']=='repair-conditioned' for d in r['diagnostics'])
                    if name=='isolation':result['passed'] &= any(d['conditioning']=='isolation-conditioned' for d in r['diagnostics'])
            except (ValueError,KeyError) as error:result.update(passed=False,parse_error=str(error))
        records.append(result);print(name,result['exit_code'],result['passed'],flush=True)
        write('smoke_results.json',dict(cases=records))
    preserved=all(hashlib.sha256(p.read_bytes()).hexdigest()==sha for p,sha in before.items())
    write('smoke_results.json',dict(cases=records,passed=sum(r['passed'] for r in records),total=len(records),
          sources_preserved=preserved,c_programs_executed=False,scope='Only Python CLI and installed compiler/analyzer tools; no C executable invocation.'))
    return 0 if preserved and all(r['passed'] for r in records) else 1


if __name__=='__main__':sys.exit(main())
