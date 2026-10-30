"""Build-context and coverage accounting, separate from defect detection.

All compiler invocations are preprocessing, syntax-only AST, metadata queries,
or the user's explicitly requested existing analyzer pass. No source is edited.
"""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from extended_c import analyze_file, to_report
from extended_c.backend import _run, _decode, _timeout
from extended_c.configuration import configuration_args
from extended_c.static_analysis import _command as analyzer_command
from .regions import functions_from_ast


def probe(command, timeout, data=None):
    record = {'command':list(command), 'status':'failed', 'returncode':None, 'stderr':'', 'stdout_sha256':None, 'stdout_bytes':0}
    output = b''
    try:
        process = _run(list(command), timeout, data)
        output = process.stdout
        record.update(status='completed' if process.returncode==0 else 'failed', returncode=process.returncode,
                      stderr=_decode(process.stderr))
    except subprocess.TimeoutExpired as error:
        output = error.stdout or b''
        record.update(status='timed_out', stderr=_decode(error.stderr), issue=f'Probe exceeded {timeout} seconds')
    except (OSError,subprocess.SubprocessError) as error:
        record['issue']=str(error)
    if isinstance(output,str): output=output.encode('utf-8')
    record.update(stdout_sha256=hashlib.sha256(output).hexdigest(),stdout_bytes=len(output))
    return record, output


def parse_macros(text):
    values = {}
    for line in text.splitlines():
        match = re.fullmatch(r'#define\s+(__STDC_VERSION__|__STDC__|__STRICT_ANSI__|__SIZEOF_POINTER__)\s+(.+)',line)
        if match: values[match[1]]=match[2]
    return values


def parse_includes(text):
    paths, active, complete = [], False, False
    for line in text.splitlines():
        if line.strip() in ('#include "..." search starts here:','#include <...> search starts here:'):
            active=True
        elif active and line.strip()=='End of search list.':
            complete=True; break
        elif active and line.startswith(' ') and line.strip():
            paths.append(line.strip())
    return paths if complete else None


def parse_checkers(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or 'Enabled Checkers' not in lines[0]:
        return None
    names = lines[1:]
    if not names or any(not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+',name) for name in names):
        return None
    return names


def context(compiler, config, standard, timeout, *, analyzer=False):
    metadata = {'compiler':asdict(compiler), 'requested_standard':standard,
                'standard_selection':'explicit' if standard else 'compiler_default',
                'target':None, 'target_basis':'driver -dumpmachine, no target override supported by this mode',
                'standard_macros':{}, 'system_include_paths':None, 'enabled_default_checkers':None,
                'checker_selection':'driver_defaults' if analyzer else 'not_requested', 'probes':{}}
    item, output = probe([compiler.path,'-dumpmachine'],timeout)
    value = _decode(output).strip()
    if item['status']=='completed' and not item['stderr'].strip() and re.fullmatch(r'[A-Za-z0-9_.+-]+',value):
        metadata['target']=value
    else: item['interpretation']='unknown target; unsupported or malformed query result'
    metadata['probes']['target']=item
    item, output=probe([compiler.path,'-x','c','-E','-dM',*config,'-'],timeout,b'\n')
    if item['status']=='completed' and not item['stderr'].strip():
        metadata['standard_macros']=parse_macros(_decode(output))
    metadata['probes']['standard_macros']=item
    item, output=probe([compiler.path,'-x','c','-E','-v',*config,'-'],timeout,b'\n')
    if item['status']=='completed': metadata['system_include_paths']=parse_includes(item['stderr'])
    metadata['probes']['include_search']=item
    if analyzer:
        try:
            with tempfile.TemporaryDirectory(prefix='smartparse-eligibility-') as directory:
                base=analyzer_command(compiler,'-',Path(directory)/'checkers.txt',config)
                item, output=probe([*base[:-1],'-Xclang','-analyzer-list-enabled-checkers','-'],timeout,b'int metadata_probe(void){return 0;}\n')
                if item['status']=='completed' and not item['stderr'].strip():
                    metadata['enabled_default_checkers']=parse_checkers(_decode(output))
                metadata['probes']['enabled_checkers']=item
        except OSError as error:
            metadata['probes']['enabled_checkers']={'status':'failed','issue':str(error)}
    return metadata


def classify_diagnostic(diagnostic, preprocessing_failed=False):
    if diagnostic.severity not in ('error','fatal error'): return None
    message=diagnostic.message.lower()
    if re.search(r'file not found|no such file|cannot (?:find|open)|#error|encoding|utf-16',message):
        return 'preprocessing/configuration'
    if diagnostic.category=='syntax': return 'syntax'
    if diagnostic.category=='semantic/type': return 'semantic/type'
    if preprocessing_failed: return 'preprocessing/configuration'
    return 'analyzer limitations'  # Unknown reason, never guessed syntax/type.


def pass_blockers(result, role, preprocessing_failed=False):
    if result is None: return []
    blockers=[]
    for diagnostic in result.diagnostics:
        category=classify_diagnostic(diagnostic,preprocessing_failed)
        if category:
            blockers.append({'stage':role,'category':category,'message':diagnostic.message,
                             'location':{'file':diagnostic.file,'line':diagnostic.line,'column':diagnostic.column},
                             'basis':'compiler-reported error; not a new independent defect'})
    for issue in result.issues:
        category=('timeout' if 'timed out' in issue.lower() or 'timeout' in issue.lower()
                  else 'preprocessing/configuration' if role=='compiler' and result.compiler is None
                  else 'analyzer limitations')
        blockers.append({'stage':role,'category':category,'message':issue,'location':None,'basis':'tool completion issue'})
    if result.unrecognized_output:
        blockers.append({'stage':role,'category':'analyzer limitations', 'message':'Unrecognized tool output prevents a reliable completion/coverage claim',
                         'location':None,'basis':'malformed or unsupported diagnostic layout'})
    return blockers


def coverage(result, role, *, reliable_function=False, frontend_accepted=False):
    if result is None:
        return {'status':'not_attempted','reason':'Pass was not requested.'}
    errors=any(d.severity in ('error','fatal error') for d in result.diagnostics)
    if errors:
        return {'status':'blocked','reason':'Translation-unit frontend errors prevent a complete claim, including regions without nearby diagnostics.'}
    if result.status=='unavailable' or not result.command:
        return {'status':'not_attempted','reason':'No usable tool invocation was available; see blockers.'}
    if result.status in ('failed','partial','timed_out'):
        return {'status':'unknown','reason':'Interrupted or unrecognized execution; per-region work is not established.'}
    if role=='analyzer':
        return {'status':'unknown','reason':'Analyzer invocation completed but text output supplies no per-function exploration certificate.'}
    if result.status=='completed' and result.returncode==0 and frontend_accepted:
        return {'status':'completed','reason':'Configured frontend accepted this translation unit'+(' and the validated AST contains this body.' if reliable_function else '; not a static-analysis or all-configurations claim.')}
    return {'status':'unknown','reason':'Frontend acceptance for this region is not established.'}


def build_report(source, result, *, standard=None, include_dirs=(), defines=(), metadata_timeout=5.0):
    """Report existing pass results plus explicitly labeled metadata/AST probes."""
    _timeout(metadata_timeout)
    path=Path(source).resolve()
    issues=[]
    try:
        data=path.read_bytes()
        source_info={'path':str(path),'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data),
                     'physical_lines':len(data.splitlines()),'encoding':'UTF-8' if _valid_utf8(data) else 'unknown/non-UTF-8',
                     'original_source_unchanged':None}
    except OSError as error:
        data=b''; source_info={'path':str(path),'sha256':None,'original_source_unchanged':None}; issues.append(str(error))
    config=configuration_args(standard,include_dirs,defines)
    contexts={}
    if result.compiler: contexts['compiler']=context(result.compiler,config,standard,metadata_timeout)
    analyzer=result.static_analysis
    if analyzer and analyzer.compiler: contexts['analyzer']=context(analyzer.compiler,config,standard,metadata_timeout,analyzer=True)
    preprocess={'status':'not_attempted','reason':'No usable compiler or source.'}
    if result.compiler and source_info['sha256'] is not None:
        preprocess,_=probe([result.compiler.path,'-x','c','-E',*config,str(path)],metadata_timeout)
    blockers=pass_blockers(result,'compiler',preprocess['status']=='failed')+pass_blockers(analyzer,'analyzer',preprocess['status']=='failed')
    if preprocess['status'] in ('failed','timed_out'):
        blockers.append({'stage':'preprocessing_probe','category':'timeout' if preprocess['status']=='timed_out' else 'preprocessing/configuration',
                         'message':preprocess.get('issue') or preprocess.get('stderr') or 'Preprocessing could not complete', 'location':None,
                         'basis':'independent preprocessing-only invocation'})
    accepted=result.status=='completed' and result.returncode==0 and not any(d.severity in ('error','fatal error') for d in result.diagnostics)
    inventory={'status':'not_attempted','regions':[],'exclusions':[], 'basis':'translation-unit fallback; no guessed function boundaries', 'probe':None}
    if result.compiler and result.compiler.backend=='clang' and source_info['sha256'] is not None:
        base=[result.compiler.path,'-x','c','-fsyntax-only',*result.compiler.flags,*config,'-Xclang','-ast-dump=json']
        capability,raw=probe([*base,'-'],metadata_timeout,b'int metadata_probe(void){return 0;}\n')
        inventory['capability_probe']=capability
        try:
            if capability['status']!='completed': raise ValueError('AST JSON invocation capability unavailable')
            functions_from_ast(json.loads(raw),str(path),b'int metadata_probe(void){return 0;}\n')  # validates envelope only; stdin bodies may be excluded
            actual,raw=probe([*base,str(path)],metadata_timeout)
            inventory['probe']=actual
            regions,excluded=functions_from_ast(json.loads(raw),str(path),data)
            inventory.update(status='completed' if actual['status']=='completed' else 'partial', regions=regions,exclusions=excluded,
                             configured_definitions_complete=actual['status']=='completed' and not excluded,
                             basis='Clang AST offsets verified against main-file bytes; partial AST never establishes analysis coverage')
        except (ValueError,TypeError,UnicodeError) as error:
            inventory.update(status='unknown',reason=str(error))
    elif result.compiler:
        inventory.update(status='unsupported',reason='This adapter has no verified GCC function-region inventory; use translation-unit fallback.')
    regions=[{'id':'translation_unit','kind':'translation_unit','name':None,'start_line':1 if source_info.get('physical_lines',0)>0 else None,
              'end_line':source_info.get('physical_lines'), 'mapping':'original physical file; configured preprocessing only',
              'compiler_coverage':coverage(result,'compiler',frontend_accepted=accepted),
              'analyzer_coverage':coverage(analyzer,'analyzer')}]
    for region in inventory['regions']:
        regions.append({**region,'compiler_coverage':coverage(result,'compiler',reliable_function=True,frontend_accepted=accepted and inventory['status']=='completed'),
                        'analyzer_coverage':coverage(analyzer,'analyzer')})
    if source_info['sha256'] is not None:
        try: source_info['original_source_unchanged']=hashlib.sha256(path.read_bytes()).hexdigest()==source_info['sha256']
        except OSError: source_info['original_source_unchanged']=False
    if source_info['original_source_unchanged'] is False:
        blockers.append({'stage':'source_integrity','category':'preprocessing/configuration','message':'Source changed during eligibility metadata collection', 'location':None,'basis':'before/after SHA-256'})
        for region in regions:
            region['compiler_coverage']=region['analyzer_coverage']={'status':'unknown','reason':'Source snapshot changed during analysis.'}
    for message in issues:
        blockers.append({'stage':'source','category':'preprocessing/configuration','message':message,'location':None,'basis':'source read failure'})
    return {'schema':'smartparse.analysis_eligibility','schema_version':'1.0',
            'manifest':{'source':source_info,'working_directory':str(Path.cwd()),'requested_standard':standard,
                        'include_directories':[{'provided':str(p),'resolved':str(Path(p).resolve())} for p in include_dirs],
                        'quote_include_root':str(path.parent),'macro_definitions':list(defines),
                        'locale':{'LC_ALL':'C','LANG':'C'},
                        'include_environment':{key:os.environ.get(key) for key in ('CPATH','C_INCLUDE_PATH','INCLUDE','SDKROOT')},
                        'tool_contexts':contexts,
                        'warning_options':{'compiler':[v for v in result.command if v.startswith('-W')],
                                           'analyzer':[v for v in analyzer.command if v.startswith('-W')] if analyzer else []},
                        'checker_options':'driver defaults; observed enabled list in analyzer context, unknown if query unavailable'},
            'stages':{'compiler':{'completion':result.status,'returncode':result.returncode,'frontend_accepted':accepted},
                      'analyzer':{'completion':analyzer.status if analyzer else 'not_attempted','returncode':analyzer.returncode if analyzer else None},
                      'preprocessing_probe':preprocess},
            'blockers':blockers,'region_inventory':inventory,'regions':regions,
            'mapping':{'source_edits_applied':False,'function_locations':'physical byte offsets and lines in hashed main file',
                       'diagnostic_locations':'compiler-reported; #line/presumed filenames are retained without unverified physical remapping',
                       'macros':'macro-generated/ambiguous bodies excluded; inactive branches are not claimed covered',
                       'headers':'header diagnostics retained in original analysis; main-file inventory is not header coverage'},
            'analysis':to_report(result)}


def _valid_utf8(data):
    try: data.decode('utf-8-sig'); return True
    except UnicodeError: return False


def analyze_eligibility(source, *, metadata_timeout=5.0, **options):
    _timeout(metadata_timeout)
    before=None
    try: before=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    except OSError: pass
    result=analyze_file(source,**options)
    report=build_report(source,result,metadata_timeout=metadata_timeout,
                        standard=options.get('standard'),include_dirs=options.get('include_dirs',()),defines=options.get('defines',()))
    if before is not None and report['manifest']['source']['sha256']!=before:
        report['manifest']['source']['original_source_unchanged']=False
        for region in report['regions']:
            region['compiler_coverage']=region['analyzer_coverage']={'status':'unknown','reason':'Source changed between initial snapshot and analysis.'}
        report['blockers'].append({'stage':'source_integrity','category':'preprocessing/configuration',
                                  'message':'Source changed between initial snapshot and analysis','location':None,'basis':'SHA-256 mismatch'})
    report['manifest']['source']['pre_analysis_sha256']=before
    for role, ctx in report['manifest']['tool_contexts'].items():
        ctx['capabilities']={'syntax_only':'verified by existing compiler discovery',
                             'validated_optional_flags':ctx['compiler']['flags'],
                             'target_query':'observed' if ctx['target'] else 'unknown',
                             'standard_metadata':'observed' if ctx['standard_macros'] else 'unknown',
                             'include_search':'observed' if ctx['system_include_paths'] is not None else 'unknown',
                             'enabled_checker_list':'observed' if ctx['enabled_default_checkers'] else 'unknown' if role=='analyzer' else 'not requested',
                             'ast_inventory':report['region_inventory']['status'] if role=='compiler' else 'not requested'}
    return report,result
