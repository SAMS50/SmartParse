"""Controlled original-source experiment. Does not enable any old CLI feature."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from phase6.v3.supervision import run_logged
from .experiment import run_case

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs'
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--tool');p.add_argument('--case');p.add_argument('--worker',action='store_true');a=p.parse_args()
    inputs=json.loads((HERE/'inputs.json').read_text())['inputs'];catalog=json.loads((HERE/'catalog.json').read_text())
    tools=[t for t in catalog if a.tool is None or t['id']==a.tool]
    if not tools:p.error('tool not in audited catalog')
    if a.worker:
        if a.case not in inputs:p.error('case not in frozen manifest')
        item=inputs[a.case];source=Path(item['path']);assert sha(source)==item['sha256']
        r=run_case(tools[0],source);write(OUT/'comparison'/tools[0]['id']/(a.case+'.json'),r)
        return 0
    frozen=json.loads((OUT/'frozen_baseline/hashes.json').read_text());assert all(sha(Path(name))==h for name,h in frozen.items())
    protected=json.loads((OUT/'protected_hashes.json').read_text());assert all(sha(Path(name))==h for name,h in protected.items())
    all_statuses=[]
    try:
        for tool in tools:
            folder=OUT/'comparison'/tool['id'];folder.mkdir(parents=True,exist_ok=True)
            started=time.monotonic();invocations=0
            for sid,item in inputs.items():
                target=folder/(sid+'.json')
                if target.exists():
                    old=json.loads(target.read_text())
                    if old.get('source',{}).get('sha256')==item['sha256'] and old.get('tool')==tool and old.get('source',{}).get('original_unchanged'):
                        all_statuses.append({'tool':tool['id'],'case':sid,'verified_reuse':True});continue
                if time.monotonic()-started>180 or invocations+2>160:
                    write(target,{'schema':'smartparse.external_comparison','schema_version':'1.0','tool':tool,'source':item,
                                  'status':'not_attempted_budget','reason':'Per-tool 180-second / 160-invocation cohort budget exhausted',
                                  'diagnostics':[],'usage':{'compiler_invocations':0}})
                    all_statuses.append({'tool':tool['id'],'case':sid,'status':'not_attempted_budget'});continue
                print(tool['id']+' '+sid,flush=True)
                status=run_logged([sys.executable,'-m','phase6.v7.run_comparison','--worker','--tool',tool['id'],'--case',sid],
                                  folder/(sid+'.log'),timeout=35,cwd=ROOT)
                all_statuses.append({'tool':tool['id'],'case':sid,**status})
                if status['timed_out'] or status['exit_code']!=0:
                    write(target,{'schema':'smartparse.external_comparison','schema_version':'1.0','tool':tool,'source':item,
                                  'status':'external_timeout' if status['timed_out'] else 'worker_failed','reason':status,
                                  'diagnostics':[],'usage':{'compiler_invocations':0}})
                else:
                    r=json.loads(target.read_text());invocations+=r['usage']['compiler_invocations']
                    assert sha(Path(item['path']))==item['sha256'],sid
                write(OUT/'comparison_supervision.json',all_statuses)
    finally:
        changed=[name for name,h in protected.items() if sha(Path(name))!=h]
        fchanged=[name for name,h in frozen.items() if sha(Path(name))!=h]
        write(OUT/'preservation_comparison.json',{'protected_files':len(protected),'changed':changed,'frozen_files':len(frozen),'changed_frozen':fchanged})
        assert not changed and not fchanged
    return 0


if __name__=='__main__':sys.exit(main())
