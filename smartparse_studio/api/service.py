import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from fastapi import HTTPException
from phase6.v3.execution import bounded_run
from smartparse_cli.tools import doctor
from smartparse_cli.reporting import render
from .models import AnalysisRequest
from .views import editor_locations,recovered_previews

ROOT=Path(__file__).resolve().parents[2]
EXAMPLES=[
 ('valid','Valid C','C12_valid_full.c','Structs, strings and a bounded loop.','compiler'),
 ('semicolon','Missing semicolon','C09_repair_null.c','A syntax blocker before an unrelated pointer defect.','compiler'),
 ('null','Null pointer','C01_null.c','A local pointer initialized to null is dereferenced.','memory'),
 ('leak','Memory leak','C02_leak.c','An allocated buffer is not released on its successful path.','memory'),
 ('double-free','Double free','C03_double.c','An allocation is freed through two aliases.','memory'),
 ('use-after-free','Use after free','C04_uaf.c','A field is accessed after freeing its allocation.','memory'),
 ('bounds','Array bounds','C05_bounds.c','A fixed array is accessed beyond its extent.','memory'),
 ('logic','Contradictory condition','C08_contradiction.c','Integer constraints cannot all hold; intent still needs review.','semantic'),
 ('recovery','Recovery-assisted','C09_repair_null.c','Opt in to compiler-validated punctuation recovery.','memory'),
 ('isolation','Isolation-assisted','C10_isolate_null.c','Opt in to excluding a blocked helper when the policy permits.','memory'),
 ('research','SmartParse recovery','S03.c','Original restricted-grammar token repair with reported scores.','smartparse'),
]


def examples():
    result=[]
    for id,title,file,description,analyzer in EXAMPLES:
        path=ROOT/'phase6/v8/fixtures'/('syntax' if id=='research' else 'c')/file;data=path.read_bytes()
        result.append(dict(id=id,title=title,filename=file,description=description,source=data.decode('utf-8'),
            source_sha256=hashlib.sha256(data).hexdigest(),analyzers=[analyzer],recovery=id=='recovery',isolation=id=='isolation'))
    return result


_tools_lock=threading.Lock()
_tools_cache=None
_tools_checked=0.0


def tools():
    global _tools_cache,_tools_checked
    with _tools_lock:
        if _tools_cache is None or time.monotonic()-_tools_checked>30:
            _tools_cache=doctor(timeout=3);_tools_checked=time.monotonic()
        return _tools_cache


def perform(request:AnalysisRequest):
    code=request.source.encode('utf-8');source_hash=hashlib.sha256(code).hexdigest()
    work_path=None
    try:
        with tempfile.TemporaryDirectory(prefix='smartparse-studio-') as work:
            work_path=Path(work);path=work_path/request.filename;path.write_bytes(code)
            config=work_path/'request.json'
            options=request.model_dump(exclude={'source','filename'});options['path']=str(path)
            config.write_text(json.dumps(options),encoding='utf-8')
            env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
            env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
            process=bounded_run([sys.executable,'-m','smartparse_studio.api.worker',str(config)],capture_output=True,shell=False,env=env,timeout=55)
            try:report=json.loads(process.stdout)
            except (ValueError,UnicodeError) as error:raise HTTPException(502,'Analyzer worker returned unreadable output') from error
            if not isinstance(report,dict):raise HTTPException(502,'Analyzer worker returned an invalid report envelope')
            if process.returncode or report.get('worker_error'):
                raise HTTPException(502,report.get('worker_error','Analyzer worker failed'))
            if report.get('schema')!='smartparse.unified_analysis' or report.get('schema_version')!='1.0':
                raise HTTPException(502,'Unsupported analysis schema')
            if not isinstance(report.get('source'),dict) or not all(k in report for k in ('diagnostics','groups','runs','summary','usage')):
                raise HTTPException(502,'Analyzer worker returned an incomplete report envelope')
            if path.read_bytes()!=code or report['source'].get('original_unchanged') is not True or report['source'].get('sha256')!=source_hash:
                raise HTTPException(502,'Submitted-source preservation could not be verified')
            presentation=dict(request_id=str(uuid.uuid4()),filename=request.filename,submitted_sha256=source_hash,
                editor_locations=editor_locations(report,request.source),previews=recovered_previews(report,request.source),
                workspace_removed=False,limits=dict(source_bytes=128*1024,worker_seconds=55,engine_seconds=45,invocations=96),
                limitations=['Local trusted use only; compilers can read filesystem headers. Temporary files are not a security sandbox.',
                              'Stopping browser waiting does not terminate a running worker; its server deadline remains enforced.'])
            markdown=render(report,'markdown')
    except subprocess.TimeoutExpired as error:raise HTTPException(504,'Analysis worker timed out; no completed-analysis claim.') from error
    except OSError as error:raise HTTPException(503,'Local analyzer worker could not start or clean up.') from error
    except (KeyError,TypeError,ValueError) as error:raise HTTPException(502,'Analyzer report could not be interpreted safely') from error
    if work_path is None or work_path.exists():raise HTTPException(502,'Temporary workspace cleanup was not verified')
    presentation['workspace_removed']=True
    return dict(schema='smartparse.studio_response',schema_version='1.0',report=report,studio=presentation,markdown=markdown)


gate=threading.BoundedSemaphore(1)


def analyze_request(request):
    if not gate.acquire(blocking=False):raise HTTPException(429,'An analysis is already running. Wait for its bounded run to finish.')
    try:return perform(request)
    finally:gate.release()
