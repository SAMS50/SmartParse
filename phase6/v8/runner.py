"""Frozen evaluation runner. Each tool case has an independent external deadline."""
import argparse
import json
from pathlib import Path
import sys
import time
from .prepare import HERE,ROOT,digest,write_json,verify_freeze


def configs():return json.loads((HERE/'configurations.json').read_text())


def run_one(source, configuration):
    if configuration not in configs()['extended']:raise ValueError('Unknown frozen configuration')
    from phase6.v3.execution import Budget,Limits
    from phase6.v3.engine import discover,compiler_check
    from extended_c import to_report
    from phase6.v6.engine import run_semantics
    from phase6.v5.engine import DetectionLimits
    from phase6.v7.adapter import analyze_external
    paths={t['id']:t['path'] for t in configs()['tools']}
    started=time.monotonic()
    if configuration.startswith('compiler_'):
        budget=Budget(Limits(invocations=20,total_seconds=30,call_seconds=5))
        compiler=discover(budget,paths['gcc6' if configuration=='compiler_gcc6' else 'clang17'])
        report=to_report(compiler_check(budget,compiler,Path(source).resolve(),['-std=c11']))
        report['usage']=budget.usage()
    elif configuration in ('gcc14','cppcheck'):
        report=analyze_external(source,enabled=True,tool=configuration,executable=paths[configuration],
                                total_timeout=30,timeout=5,standard='c11')
    else:
        report=run_semantics(source,enabled=True,compiler=paths['clang17'],standard='c11',
            repair=configuration=='recovery_assisted',isolate=configuration=='isolation_assisted',
            limits=DetectionLimits(invocations=96,analyzer_invocations=20,total_seconds=30,call_seconds=5))
    return dict(configuration=configuration,source_sha256=digest(Path(source).read_bytes()),
                elapsed_seconds=round(time.monotonic()-started,6),result=report)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',nargs=3,metavar=('SOURCE','CONFIGURATION','OUTPUT'))
    p.add_argument('--limit',type=int,help='Only first N C cases; resumable subset, never final completeness')
    p.add_argument('--syntax-only',action='store_true')
    args=p.parse_args();verify_freeze()
    if args.worker:
        source,configuration,output=args.worker
        try:report=run_one(source,configuration)
        except Exception as error:report=dict(configuration=configuration,result=dict(status='failed',reason=f'{type(error).__name__}: {error}'))
        write_json(Path(output),report);return
    from .evaluation import syntax_case
    from phase6.v3.supervision import run_logged
    manifest=json.loads((HERE/'manifest.json').read_text())
    for case in manifest['cases']:
        if case['cohort']!='syntax':continue
        source=(ROOT/case['path']).read_text(encoding='utf-8')
        intended=(ROOT/case['intended_path']).read_text(encoding='utf-8') if case.get('intended_path') else None
        for configuration in configs()['syntax']:
            output=HERE/'outputs'/'syntax'/configuration/(case['id']+'.json')
            if output.exists() and json.loads(output.read_text()).get('matching_protocol')!='1.1':
                archive=HERE/'outputs/syntax_protocol_1_0'/configuration/output.name
                archive.parent.mkdir(parents=True,exist_ok=True)
                if not archive.exists():archive.write_bytes(output.read_bytes())
            if not output.exists() or json.loads(output.read_text()).get('matching_protocol')!='1.1':
                write_json(output,syntax_case(case,source,configuration,intended))
    if args.syntax_only:return
    cases=[c for c in manifest['cases'] if c['cohort']=='c']
    cases.append(dict(id='benchmark',path='acceptance/cleaned/c_error_detection_500_lines.c'))
    if args.limit is not None:cases=cases[:args.limit]
    for case in cases:
        for configuration in configs()['extended']:
            output=HERE/'outputs'/'extended'/configuration/(case['id']+'.json')
            supervisor=output.with_suffix('.process.json');log=output.with_suffix('.log')
            if output.exists() and supervisor.exists():continue
            output.parent.mkdir(parents=True,exist_ok=True)
            command=[sys.executable,'-m','phase6.v8.runner','--worker',str(ROOT/case['path']),configuration,str(output)]
            status=run_logged(command,log,timeout=45,cwd=ROOT)
            write_json(supervisor,status)
            if not output.exists():write_json(output,dict(configuration=configuration,result=dict(status='timed_out' if status['timed_out'] else 'failed',reason='Worker did not produce report; see supervisor/log')))
            print(case['id'],configuration,status['exit_code'],status['elapsed_seconds'],flush=True)
    verify_freeze()


if __name__=='__main__':main()
