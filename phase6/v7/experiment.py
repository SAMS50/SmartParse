"""Internal controlled comparison harness, not an enabled product adapter."""
import json
import os
from pathlib import Path
import tempfile
from dataclasses import asdict
from phase6.v3.execution import Budget,Limits,LimitReached,bounded_run
from phase6.v1.evaluation import fingerprint
from .protocol import normalize


def command_for(tool,source,work,standard='c11',includes=(),defines=()):
    path=tool['path'];kind=tool['kind'];source=str(source)
    config=['-std='+standard,*['-I'+str(p) for p in includes],*['-D'+d for d in defines]]
    if kind=='gcc':return [path,'-x','c',*config,'-Wall','-Wextra','-fmax-errors=20','-O0','-fanalyzer',
                            '-fdiagnostics-format='+tool['diagnostic_format'],'-c',source,'-o',str(Path(work)/'analysis.o')]
    if kind=='cppcheck':return [path,'--xml','--xml-version=2','--enable=warning','--std='+standard,'--platform=win64',
                                '--max-configs=1','--error-exitcode=1','--cppcheck-build-dir='+str(Path(work)/'cache'),
                                *['-I'+str(p) for p in includes],*['-D'+d for d in defines],source]
    if kind=='tidy':return [path,'--config={}','--checks=-*,'+','.join(tool['checks']),'--warnings-as-errors=',
                            '--use-color=false',source,'--','-x','c',*config,'-Wall','-Wextra','-ferror-limit=20']
    raise ValueError('unsupported candidate kind')


def run_case(tool,source,*,timeout=20,invocations=3,standard='c11',includes=(),defines=(),capability_probe=False,call_timeout=10):
    from extended_c.configuration import configuration_args
    configuration_args(standard,includes,defines)
    limits=Limits(invocations=invocations,total_seconds=timeout,call_seconds=min(timeout,call_timeout));limits.validate()
    source=Path(source).resolve(strict=True);original=source.read_bytes()
    if source.suffix.lower()!='.c' or len(original)>1048576:raise ValueError('requires .c source up to 1 MiB')
    def execute(command,**kwargs):
        kwargs['env']['PATH']=str(Path(tool['path']).parent)+os.pathsep+kwargs['env'].get('PATH','')
        return bounded_run(command,**kwargs)
    budget=Budget(limits,execute=execute);directory=None
    result={'schema':'smartparse.external_comparison','schema_version':'1.0','tool':tool,
            'source':{'path':str(source),'sha256':__import__('hashlib').sha256(original).hexdigest()},
            'configuration':{'standard':standard,'include_dirs':list(map(str,includes)),'defines':list(defines),
                             'path_prepend':str(Path(tool['path']).parent),'shell':False},
            'status':'unavailable','reason':None,'diagnostics':[],'exact_duplicates':[],'raw':{},
            'eligibility':{'process_started':False,'analyzer_requested':True,'analyzer_phase_evidence':'unknown',
                           'region_coverage':'unknown; no per-function/path execution proof','function_path_coverage_certified':False},
            'provenance':{'original_source':True,'repair_conditioned':False,'isolation_conditioned':False}}
    try:
        with tempfile.TemporaryDirectory(prefix='smartparse external ') as work:
            directory=work
            version=budget.call('version',[tool['path'],'--version'])
            text=(version.stdout+version.stderr).decode('utf-8',errors='replace')
            result['observed_version']=text
            if version.returncode or tool['version'] not in text:
                result.update(status='unavailable',reason='tool unavailable or version changed; no silent substitution');return result
            if tool['kind']=='cppcheck':(Path(work)/'cache').mkdir()
            if capability_probe:
                probe_work=Path(work)/'capability';probe_work.mkdir()
                if tool['kind']=='cppcheck':(probe_work/'cache').mkdir()
                capsource=probe_work/'capability.c';capbytes=b'int capability(void){int *p=0;return *p;}\n';capsource.write_bytes(capbytes)
                # Never mix probe CTU/cache state or user macro definitions
                # into the program's analysis (or vice versa).
                probe=budget.call('analyzer_capability',command_for(tool,capsource,probe_work,standard))
                captext=(probe.stdout+b'\n'+probe.stderr).decode('utf-8',errors='replace') if tool['kind']=='tidy' else probe.stderr.decode('utf-8',errors='replace')
                caprows,_,_=normalize(tool['format'],captext,capsource,capbytes,tool,{})
                supported=probe.returncode in (0,1) and any(d['diagnostic_id'] in ('-Wanalyzer-null-dereference','nullPointer') for d in caprows)
                result['capability']={'supported':supported,'returncode':probe.returncode,'stdout':probe.stdout.decode('utf-8',errors='replace'),'stderr':probe.stderr.decode('utf-8',errors='replace')}
                if not supported:
                    result.update(status='unavailable',reason='Actual analyzer invocation/capability not verified');return result
            command=command_for(tool,source,work,standard,includes,defines);result['configuration']['command']=command
            process=budget.call('external_analysis',command)
            result['eligibility']['process_started']=True
            stdout=process.stdout.decode('utf-8',errors='replace');stderr=process.stderr.decode('utf-8',errors='replace')
            result['raw']={'stdout':stdout,'stderr':stderr,'returncode':process.returncode}
            text=stdout+'\n'+stderr if tool['kind']=='tidy' else stderr
            rows,duplicates,unknown=normalize(tool['format'],text,source,original,tool,result['configuration'])
            result.update(diagnostics=rows,exact_duplicates=duplicates,unrecognized_output=unknown)
            blockers=[d for d in rows if ((tool['kind']!='cppcheck' and d['severity'] in ('error','fatal error')) or
                        d['diagnostic_id'] in ('syntaxError','internalAstError','preprocessorErrorDirective','internalError','cppcheckError'))]
            analyzer_rows=[d for d in rows if d['diagnostic_id'] and (tool['kind']=='cppcheck' or 'analyzer' in d['diagnostic_id'] or d['diagnostic_id'].startswith('bugprone-'))]
            result['eligibility']['analyzer_phase_evidence']='diagnostic emitted, no exhaustive coverage inference' if analyzer_rows else 'no direct region exploration evidence'
            result['eligibility']['frontend_blockers']=[d['id'] for d in blockers]
            result['status']='partial' if blockers else 'completed' if process.returncode==0 or (process.returncode==1 and rows) else 'failed'
            result['eligibility']['analyzer_completion']='blocked_or_partial' if blockers else result['status']
            result['reason']='Tool returned; warnings require source/root review.' if result['status']=='completed' else 'Tool/frontend incomplete; inspect raw output and blockers.'
            for diagnostic in rows:
                diagnostic['analysis_eligibility']={'tool_completion':result['status'],'frontend_blockers':bool(blockers),'region_coverage':'unknown'}
    except LimitReached as error:result.update(status='timed_out' if 'timed out' in str(error) else 'budget_exhausted',reason=str(error))
    except FileNotFoundError as error:result.update(status='unavailable',reason=str(error))
    except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError) as error:result.update(status='failed',reason=str(error))
    finally:
        try:result['source']['original_unchanged']=source.read_bytes()==original
        except OSError:result['source']['original_unchanged']=False
        result['temporary_workspace_removed']=directory is None or not Path(directory).exists()
        result['usage']=budget.usage();result['usage']['limits']=asdict(limits)
        result['unique_primary_groups']=len([d for d in result['diagnostics'] if not d.get('context_note')])
        if not result['source']['original_unchanged'] or not result['temporary_workspace_removed']:
            result.update(status='failed',reason='Source preservation/cleanup unverified',diagnostics=[])
    return result
