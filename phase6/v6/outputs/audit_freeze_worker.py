"""Preimplementation audit only: existing pipelines; no new detectors."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path.cwd()))
from phase6.v5.engine import run_detection
from phase6.v3.execution import Budget,Limits
from phase6.v3.engine import ast
from extended_c import Compiler

HERE=Path('phase6/v6');OUT=HERE/'outputs';FROZEN=OUT/'frozen_baseline'
CLANG=r'C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe'
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not FROZEN.exists(),'refusing to overwrite frozen baseline'
FROZEN.mkdir();cap=None;summary=[]
for p in sorted((HERE/'fixtures').glob('*.c')):
    print(p.stem,flush=True)
    r=run_detection(p,enabled=True,compiler=CLANG,capability=cap)
    assert r['status'] not in ('failed','timed_out','budget_exhausted'),r['reason']
    assert r['source']['original_unchanged'] and r['temporary_workspace_removed']
    cap=r['capabilities'];write(FROZEN/(p.stem+'.json'),r)
    summary.append({'case':p.stem,'status':r['status'],'compiler':r['analysis']['diagnostics'],
                    'analyzer':[f['evidence'] for f in r['observations']], 'usage':r['usage']})
write(FROZEN/'summary.json',summary)
b=Budget(Limits(invocations=30,total_seconds=45,call_seconds=5));audit={'tooling':{},'warning_probes':[],'allocation_ast':[],'ast_examples':{}}
for name in ('clang','clang-check','clang-tidy','llvm-config'):
    audit['tooling'][name]=shutil.which(name)
audit['tooling']['adjacent_libraries']=[p.name for p in Path(CLANG).parent.glob('*clang*.dll')]
for driver,flags in [(CLANG,['-Wtautological-overlap-compare','-Wconversion']),('gcc',['-Wlogical-op','-Wconversion'])]:
    for flag in flags:
        probe=b.call('warning_probe',[driver,'-x','c','-fsyntax-only',flag,'-'],b'int probe;\n')
        item={'driver':driver,'flag':flag,'probe_returncode':probe.returncode,'probe_stderr':probe.stderr.decode(errors='replace'),'cases':{}}
        if probe.returncode==0 and not probe.stderr.strip():
            for name in ('contradiction_bad','precision_review','scanf_width_bad','allocation_literal'):
                r=b.call('warning_experiment',[driver,'-fsyntax-only',flag,str((HERE/'fixtures'/(name+'.c')).resolve())])
                item['cases'][name]={'returncode':r.returncode,'stderr':r.stderr.decode(errors='replace')}
        audit['warning_probes'].append(item)
compiler=Compiler(cap['compiler']['path'],cap['compiler']['backend'],cap['compiler']['version'],tuple(cap['compiler']['flags']))
def walk(node):
    yield node
    for child in node.get('inner',[]):yield from walk(child)
for name in ('allocation_literal','scanf_width_bad','precision_review','contradiction_bad'):
    tree,code=ast(b,compiler,(HERE/'fixtures'/(name+'.c')).resolve(),[])
    audit['ast_examples'][name]={'returncode':code,'main_function_bodies':[n for n in tree['inner'] if n.get('kind')=='FunctionDecl' and n.get('name')=='f'],
        'library_declarations':[n for n in tree['inner'] if n.get('kind')=='FunctionDecl' and n.get('name') in ('malloc','scanf')]}
    if name=='allocation_literal':audit['allocation_ast']=audit['ast_examples'][name]
audit['usage']=b.usage();write(OUT/'preimplementation_audit.json',audit)
bound=list(FROZEN.glob('*.json'))+list((HERE/'fixtures').glob('*.c'))+[OUT/'preimplementation_audit.json']
write(FROZEN/'hashes.json',{str(p.resolve()):sha(p) for p in bound})
