"""Resume checks: pure tests first, then one externally bounded live test at a time."""
import argparse
import json
import os
from pathlib import Path
import sys
import unittest

from .supervision import run_logged
from .test_recovery import LiveRecoveryTests

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--compiler',required=True,type=Path)
    args=parser.parse_args()
    env=os.environ.copy();env['PATH']=str(args.compiler.resolve(strict=True).parent)+os.pathsep+env.get('PATH','')
    batches=[('pure',['phase6.v3.test_recovery.PolicyTests','phase6.v3.test_recovery.BudgetTests'],20)]
    batches.extend((name,['phase6.v3.test_recovery.LiveRecoveryTests.'+name],30)
                   for name in unittest.defaultTestLoader.getTestCaseNames(LiveRecoveryTests))
    records=[]
    for name,names,timeout in batches:
        print('Checking '+name,flush=True)
        record=run_logged([sys.executable,'-m','unittest',*names,'-v'],HERE/'outputs'/('targeted_'+name+'.txt'),timeout=timeout,env=env)
        records.append(record)
        (HERE/'outputs/targeted_runs.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        print(f"  exit={record['exit_code']} elapsed={record['elapsed_seconds']}s timeout={record['timed_out']}",flush=True)
        if record['timed_out'] or record['exit_code']!=0:
            print(Path(record['log']).read_text(encoding='utf-8',errors='replace')[-3000:],flush=True)
            return 1
    return 0


if __name__=='__main__':sys.exit(main())
