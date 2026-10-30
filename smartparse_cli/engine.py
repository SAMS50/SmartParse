"""Integrate unchanged analyzers with bounded work and explicit evidence lineage."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import time

from extended_c import to_report
from extended_c.configuration import configuration_args
from phase6.v3.execution import Budget, Limits, LimitReached
from phase6.v3.engine import discover, compiler_check, analyzer_check
from phase6.v5.engine import DetectionLimits, run_detection
from phase6.v6.engine import run_semantics
from phase6.v7.adapter import analyze_external
from . import __version__
from .diagnostics import normalize, group, summarize
from .tools import locate
from smartparse import LexError

ANALYZERS=('compiler','static','memory','semantic','gcc14','cppcheck','smartparse','panic')


def initial(source,selected):
    return dict(schema='smartparse.unified_analysis',schema_version='1.0',version=__version__,
        source=dict(path=str(Path(source).resolve()),sha256=None,bytes=None,original_unchanged=None),
        requested_analyzers=list(selected),effective_analyzers=list(selected),status='not_attempted',
        runs=[],diagnostics=[],groups=[],tool_issues=[],summary={},
        coverage=dict(function_path_coverage_certified=False,reason='Per-run eligibility is preserved; process completion is not exhaustive coverage.'),
        independent_human_adjudication='pending; no accuracy metrics are inferred')


def collect(report,run,hash_value):
    """Baseline compiler evidence stays distinct from all current-variant evidence."""
    records=[];runid=run['id'];result=run['raw'];status=run['status']
    def add(d,path,provenance=None,suggestion=None):
        snippet=None
        if not d.get('source_snippet') and not (provenance or {}).get('repair_conditioned') and not (provenance or {}).get('isolation_conditioned'):
            if str(d.get('file','')).replace('\\','/').casefold()==report['source']['path'].replace('\\','/').casefold():
                lines=Path(report['source']['path']).read_bytes().decode('utf-8',errors='replace').splitlines()
                if isinstance(d.get('line'),int) and 1<=d['line']<=len(lines):snippet=lines[d['line']-1]
        records.append(normalize(d,run_id=runid,reference=path,source_hash=hash_value,
                                 provenance=provenance,completeness=status,suggestion=suggestion))
        if snippet is not None:records[-1]['evidence']['source_snippet']=snippet
    def compiler_rows(result,path,provenance=None):
        for field in ('diagnostics','findings'):
            for i,d in enumerate(result.get(field,[])):
                add(d,f'{path}/{field}/{i}',provenance)
                records[-1]['completeness']=dict(pass_completion=result.get('status'),run_completion=status,
                    frontend_accepted=result.get('execution',{}).get('returncode')==0 if result.get('analysis_mode')=='extended_c' else None,
                    function_path_coverage_certified=False)
        if result.get('static_analysis'):compiler_rows(result['static_analysis'],path+'/static_analysis',provenance)
    if runid in ('smartparse','panic'):
        for i,d in enumerate(result.get('diagnostics',[])):
            snippet=None;line=d.get('line')
            if line and line<=len(result.get('source_lines',[])):snippet=result['source_lines'][line-1]
            repairs=[r for r in result.get('repairs',[]) if (r['line'],r['column'])==(d.get('line'),d.get('column'))]
            add(dict(d,file=report['source']['path'],severity='error',category='syntax',backend=runid,
                     source_snippet=snippet,diagnostic_id=None),f'/diagnostics/{i}',suggestion=repairs or None)
            records[-1]['raw_record']=d
    elif runid in ('compiler','static'):
        compiler_rows(result,'')
    elif runid in ('gcc14','cppcheck'):
        for i,d in enumerate(result.get('diagnostics',[])):
            add(dict(d,backend=runid),f'/diagnostics/{i}',result.get('provenance'))
            records[-1]['raw_record']=d
    else:
        semantic=runid=='semantic'
        memory=result['upstream'] if semantic else result
        prefix='/upstream' if semantic else ''
        isolation=memory['upstream'];recovery=isolation['recovery_report']
        base=recovery.get('baseline')
        if base:compiler_rows(base['analysis'],prefix+'/upstream/recovery_report/baseline/analysis')
        provenance=memory['provenance']
        # Accepted variants' complete compiler/analyzer outputs remain in raw;
        # expose the final current compiler snapshot when conditioning exists.
        conditioned=provenance.get('repair_conditioned') or provenance.get('isolation_conditioned')
        if conditioned and memory.get('analysis'):
            for i,d in enumerate(memory['analysis'].get('diagnostics',[])):
                add(d,prefix+f'/analysis/diagnostics/{i}',provenance)
        for i,item in enumerate(memory.get('observations',[])):
            add(item['evidence'],prefix+f'/observations/{i}/evidence',item['provenance'])
            for j,note in enumerate(item.get('notes',[])):add(note,prefix+f'/observations/{i}/notes/{j}',item['provenance'])
        if semantic:
            for i,item in enumerate(result.get('findings',[])):
                add(item['evidence'],f'/findings/{i}/evidence',item['provenance'])
        run['eligibility']=memory.get('eligibility')
        run['provenance']=provenance
        run['recovery']=dict(stop_reason=recovery['recovery']['stop_reason'],
            eligibility_change=recovery['recovery']['eligibility_change'],
            candidates=recovery['recovery']['candidates'],accepted_variants=recovery['recovery']['accepted_variants'])
        run['isolation']=isolation['isolation']
    return records


def analyze(source,*,analyzers=('compiler',),compiler='auto',clang=None,gcc14=None,cppcheck=None,
            standard='c11',include_dirs=(),defines=(),recovery=False,isolation=False,
            timeout=10,total_timeout=120,max_invocations=256):
    import math
    selected=list(dict.fromkeys(analyzers))
    if not selected or any(a not in ANALYZERS for a in selected):raise ValueError('Select one or more supported analyzers')
    if not math.isfinite(timeout) or not 0<timeout<=30:raise ValueError('timeout must be positive and at most 30 seconds')
    if not math.isfinite(total_timeout) or not 0<total_timeout<=240:raise ValueError('total-timeout must be positive and at most 240 seconds')
    if type(max_invocations) is not int or not 1<=max_invocations<=512:raise ValueError('max-invocations must be 1..512')
    config=configuration_args(standard,include_dirs,defines)
    report=initial(source,selected);start=time.monotonic();used=0
    if (recovery or isolation) and not any(a in selected for a in ('memory','semantic')):selected.append('memory')
    # The semantic pipeline already includes the memory profile.
    effective=[a for a in selected if not (a=='memory' and 'semantic' in selected)]
    report['effective_analyzers']=effective
    path=Path(source).resolve();original=None
    try:
        if not path.is_file():raise ValueError('Source file does not exist or is not a regular file: '+str(path))
        if path.suffix.lower()!='.c':raise ValueError('Source must have a .c extension')
        if path.stat().st_size>1048576:raise ValueError('Bounded analysis accepts source files up to 1 MiB')
        original=path.read_bytes();sha=hashlib.sha256(original).hexdigest()
        report['source'].update(sha256=sha,bytes=len(original),empty=not original)
        # Stable execution order gives compiler diagnostics first, regardless of flag ordering.
        for name in ANALYZERS:
            if name not in effective:continue
            remaining=total_timeout-(time.monotonic()-start);allowance=max_invocations-used
            run=dict(id=name,status='not_attempted',reason=None,raw={},elapsed_seconds=0,usage={},eligibility=None)
            report['runs'].append(run);tick=time.monotonic();budget=None
            try:
                if remaining<=0 or allowance<1:raise LimitReached('Overall runtime or invocation budget exhausted')
                if name in ('compiler','static'):
                    budget=Budget(Limits(invocations=min(80,allowance),total_seconds=min(120,remaining),call_seconds=min(timeout,remaining)))
                    choice=compiler if name=='compiler' else (locate('clang',clang) or 'clang')
                    if choice=='auto':choice=locate('clang') or locate('gcc') or 'auto'
                    elif choice in ('gcc','clang'):choice=locate(choice) or choice
                    selected_compiler=discover(budget,choice)
                    if name=='compiler' and compiler in ('gcc','clang') and selected_compiler.backend!=compiler:
                        raise ValueError('Selected executable does not match requested compiler family '+compiler)
                    if name=='static' and selected_compiler.backend!='clang':raise ValueError('Static analysis requires Clang; no fallback to GCC')
                    if name=='static':
                        probe=budget.call('analyzer_capability',[selected_compiler.path,'--analyze','-x','c','-o',__import__('os').devnull,'-'],b'int capability;\n')
                        if probe.returncode or probe.stderr.strip():raise RuntimeError('Clang analyzer capability probe failed: '+probe.stderr.decode('utf-8',errors='replace'))
                    raw=to_report((compiler_check if name=='compiler' else analyzer_check)(budget,selected_compiler,path,config))
                    raw['usage']=budget.usage()
                    run['eligibility']=dict(frontend_accepted=raw['execution']['returncode']==0 if name=='compiler' else None,
                        operational_completion=raw['status'],function_path_coverage_certified=False)
                elif name in ('memory','semantic'):
                    choice=locate('clang',clang) or (compiler if compiler not in ('auto','gcc') else 'clang')
                    limits=DetectionLimits(invocations=min(120,allowance),analyzer_invocations=20,
                        total_seconds=min(120,remaining),call_seconds=min(timeout,remaining))
                    raw=(run_semantics if name=='semantic' else run_detection)(path,enabled=True,compiler=choice,standard=standard,
                        include_dirs=include_dirs,defines=defines,repair=recovery,isolate=isolation,limits=limits)
                elif name in ('gcc14','cppcheck'):
                    executable=locate(name,gcc14 if name=='gcc14' else cppcheck)
                    if not executable:raise FileNotFoundError('Optional analyzer '+name+' is unavailable; provide an explicit executable')
                    raw=analyze_external(path,enabled=True,tool=name,executable=executable,standard=standard,
                        include_dirs=include_dirs,defines=defines,total_timeout=min(120,remaining),
                        timeout=min(timeout,remaining),invocation_budget=min(4,allowance))
                    run['eligibility']=raw.get('eligibility')
                else:
                    from smartparse import Parser,tokenize
                    from baseline import PanicModeParser
                    text=original.decode('utf-8-sig')
                    parser=(Parser if name=='smartparse' else PanicModeParser)(tokenize(text));parser.parse()
                    raw=dict(status='completed',diagnostics=parser.diagnostics,repairs=parser.repairs,
                             source_lines=text.splitlines(),reached_eof=parser.peek().kind=='EOF',
                             grammar='restricted C-like; no full-C/type/runtime analysis',
                             usage=dict(compiler_invocations=0))
                run.update(raw=raw,status=raw['status'],reason=raw.get('reason'),usage=raw.get('usage',{}))
                if name in ('compiler','static') and any(d.get('severity') in ('error','fatal error') and
                        not d.get('file') for d in raw.get('diagnostics',[])):
                    run.update(status='failed',reason='Unlocated driver/configuration error; no successful source-level analysis claim. Inspect raw diagnostics.')
                report['diagnostics']+=collect(report,run,sha)
                if name in ('memory','semantic') and not raw.get('temporary_workspace_removed',False):
                    raise RuntimeError('Temporary cleanup not verified')
            except (OSError,ValueError,RuntimeError,KeyError,TypeError,AttributeError,IndexError,RecursionError,LexError) as error:
                run.update(status='timed_out' if isinstance(error,LimitReached) and 'timed out' in str(error) else
                           'budget_exhausted' if isinstance(error,LimitReached) else 'unavailable' if isinstance(error,FileNotFoundError) else 'failed',
                           reason=f'{type(error).__name__}: {error}')
                if budget:run['usage']=budget.usage()
            finally:
                run['elapsed_seconds']=round(time.monotonic()-tick,6)
                used+=run['usage'].get('compiler_invocations',0)
            if run['status']!='completed':report['tool_issues'].append(dict(analyzer=name,status=run['status'],message=run['reason'] or 'Requested analysis incomplete; inspect raw evidence.'))
    except (OSError,ValueError) as error:report['tool_issues'].append(dict(analyzer='input',status='failed',message=str(error)))
    finally:
        if original is not None:
            try:report['source']['original_unchanged']=path.read_bytes()==original
            except OSError:report['source']['original_unchanged']=False
            if not report['source']['original_unchanged']:report['tool_issues'].append(dict(analyzer='input',status='failed',message='Source preservation could not be verified'))
        report['groups']=group(report['diagnostics']);report['summary']=summarize(report['diagnostics'],report['groups'])
        report['usage']=dict(elapsed_seconds=round(time.monotonic()-start,6),compiler_invocations=used,
                            total_timeout=total_timeout,call_timeout=timeout,max_invocations=max_invocations)
        report['configuration']=dict(standard=standard,include_dirs=list(include_dirs),defines=list(defines),
                                     compiler=compiler,clang=clang,recovery=recovery,isolation=isolation)
        report['status']='partial' if report['tool_issues'] and any(r['status']=='completed' for r in report['runs']) else 'failed' if report['tool_issues'] else 'completed'
    return report


def exit_code(report):
    if report['status']!='completed':return 3
    if any(d['severity'] in ('error','fatal error','warning') and not d['context_note'] for d in report['diagnostics']):return 1
    return 0
