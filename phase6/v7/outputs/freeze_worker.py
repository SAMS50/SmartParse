"""Preintegration comparison baseline using unchanged v6 only."""
import json
import hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()))
from phase6.v6.engine import run_semantics
from phase6.v5.engine import DetectionLimits

here=Path('phase6/v7');out=here/'outputs/frozen_baseline'
out.mkdir(exist_ok=True);inputs=json.loads((here/'inputs.json').read_text());cap=None
assert not (out/'hashes.json').exists(),'refusing to overwrite a completed frozen baseline'
clang=r'C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe'
for sid,item in inputs['inputs'].items():
    source=Path(item['path']);assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
    if len(sys.argv)>1 and sid!=sys.argv[1]:continue
    target=out/(sid+'.json')
    if target.exists():
        r=json.loads(target.read_text());assert r['source']['sha256']==item['sha256'] and r['status'] in ('completed','blocked')
        cap=r['upstream']['capabilities'];continue
    if cap is None:
        saved=next(out.glob('v5-*.json'),None)
        if saved:cap=json.loads(saved.read_text())['upstream']['capabilities']
    print(sid,flush=True)
    r=run_semantics(source,enabled=True,compiler=clang,standard='c11',capability=cap,
                    limits=DetectionLimits(invocations=96,analyzer_invocations=20,total_seconds=30,call_seconds=5))
    assert r['status'] in ('completed','blocked'),r['reason']
    cap=r['upstream']['capabilities'];assert r['source']['original_unchanged'] and r['temporary_workspace_removed']
    (out/(sid+'.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
if all((out/(sid+'.json')).exists() for sid in inputs['inputs']):
    files=list(out.glob('*.json'))+[here/'inputs.json']+list((here/'fixtures').glob('*.c'))
    (out/'hashes.json').write_text(json.dumps({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
