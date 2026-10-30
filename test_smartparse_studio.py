"""Thin-API tests plus real compiler/CSA smoke checks; no fabricated UI findings."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from smartparse_studio.api.main import app
from smartparse_studio.api import service
from smartparse_studio.api.views import editor_locations,recovered_previews
from smartparse_cli import analyze
from smartparse_cli.tools import locate

ROOT=Path(__file__).resolve().parent
CLIENT=dict(base_url='http://127.0.0.1',client=('127.0.0.1',51000),headers={'X-SmartParse-Studio':'1'})


class StudioApiTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app,**CLIENT);self.paths=[]
        def worker(command,**kwargs):
            config=json.loads(Path(command[-1]).read_text());path=Path(config['path']);self.paths.append(path)
            report=analyze(path,analyzers=['smartparse'])
            return subprocess.CompletedProcess(command,0,json.dumps(report).encode(),b'')
        self.mock=patch('smartparse_studio.api.service.bounded_run',side_effect=worker);self.worker=self.mock.start()

    def tearDown(self):
        self.mock.stop();self.client.close()

    def post(self,**options):return self.client.post('/api/analyze',json={'source':'int value=7;\r\n',**options})

    def test_health(self):self.assertEqual(self.client.get('/api/health').json()['status'],'ok')

    def test_tools_uses_real_inventory_interface(self):
        with patch.object(service,'tools',return_value={'tools':[{'name':'clang','status':'unavailable'}]}) as inventory:
            self.assertEqual(self.client.get('/api/tools').json()['tools'][0]['status'],'unavailable');inventory.assert_called_once()

    def test_gallery_reads_actual_fixtures(self):
        examples=self.client.get('/api/examples').json()['examples']
        self.assertEqual(len(examples),11)
        for e in examples:
            data=(ROOT/'phase6/v8/fixtures'/('syntax' if e['id']=='research' else 'c')/e['filename']).read_bytes()
            self.assertEqual(e['source'].encode('utf-8'),data)
            self.assertEqual(e['source_sha256'],hashlib.sha256(data).hexdigest())

    def test_valid_schema_and_cleanup(self):
        r=self.post();self.assertEqual(r.status_code,200);body=r.json()
        self.assertEqual(body['report']['schema'],'smartparse.unified_analysis')
        self.assertTrue(body['studio']['workspace_removed']);self.assertFalse(self.paths[0].parent.exists())

    def test_invalid_c_has_real_parser_diagnostic(self):
        r=self.post(source='int a=1\nint b=2;\n',analyzers=['smartparse'])
        self.assertTrue(r.json()['report']['diagnostics'])

    def test_unicode_crlf_submitted_bytes_preserved(self):
        code='// café\r\nint value=7;\r\n';body=self.post(source=code).json()
        self.assertEqual(body['studio']['submitted_sha256'],hashlib.sha256(code.encode()).hexdigest())
        self.assertTrue(body['report']['source']['original_unchanged'])
        response=self.client.post('/api/analyze',content=b'{"source":"\\ud800"}',headers={'Content-Type':'application/json'})
        self.assertEqual(response.status_code,422)
        self.assertIn('unicode',response.json()['detail'][0]['msg'].lower())

    def test_recovery_and_isolation_forwarded(self):
        captured=[]
        def worker(command,**kwargs):
            config=json.loads(Path(command[-1]).read_text());captured.append(config)
            report=analyze(config['path'],analyzers=['smartparse'])
            return subprocess.CompletedProcess(command,0,json.dumps(report).encode(),b'')
        self.worker.side_effect=worker
        self.assertEqual(self.post(recovery=True,isolation=True).status_code,200)
        self.assertTrue(captured[0]['recovery']);self.assertTrue(captured[0]['isolation'])

    def test_unknown_analyzer_rejected(self):self.assertEqual(self.post(analyzers=['shell']).status_code,422)
    def test_empty_analyzer_list_rejected(self):self.assertEqual(self.post(analyzers=[]).status_code,422)
    def test_extra_executable_or_output_fields_rejected(self):self.assertEqual(self.post(output='C:/secret.c',compiler='cmd.exe').status_code,422)

    def test_unsafe_filenames_rejected(self):
        for filename in ('../input.c','C:\\input.c','NUL.c','input.txt','bad?.c'):
            with self.subTest(filename=filename):self.assertEqual(self.post(filename=filename).status_code,422)

    def test_source_size_limit(self):self.assertEqual(self.post(source='a'*131073).status_code,422)
    def test_utf8_byte_limit(self):
        response=self.post(source='é'*70000)
        self.assertEqual(response.status_code,422)
        self.assertIn('UTF-8 limit',response.text)
    def test_raw_body_limit(self):self.assertEqual(self.post(source='a'*300000).status_code,413)
    def test_nul_rejected(self):self.assertEqual(self.post(source='int x;\0').status_code,422)
    def test_boolean_opt_ins_are_explicit(self):self.assertEqual(self.post(recovery='yes').status_code,422)
    def test_standard_allowlist(self):self.assertEqual(self.post(standard='-fplugin=evil').status_code,422)

    def test_nonloopback_client_rejected(self):
        with TestClient(app,base_url='http://127.0.0.1',client=('192.0.2.1',2000)) as client:
            self.assertEqual(client.get('/api/health').status_code,403)

    def test_rebinding_host_rejected(self):self.assertEqual(self.client.get('/api/health',headers={'Host':'evil.example'}).status_code,403)
    def test_untrusted_origin_rejected(self):self.assertEqual(self.post().status_code,200);self.assertEqual(self.client.get('/api/health',headers={'Origin':'https://evil.example'}).status_code,403)
    def test_custom_header_required(self):self.assertEqual(self.client.post('/api/analyze',json={'source':'int a;'},headers={'X-SmartParse-Studio':''}).status_code,403)
    def test_json_content_type_required(self):self.assertEqual(self.client.post('/api/analyze',content='int a;',headers={'Content-Type':'text/plain'}).status_code,415)

    def test_local_cors_preflight(self):
        r=self.client.options('/api/analyze',headers={'Origin':'http://127.0.0.1:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'Content-Type,X-SmartParse-Studio'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.headers['access-control-allow-origin'],'http://127.0.0.1:5173')

    def test_parallel_analysis_rejected(self):
        service.gate.acquire()
        try:self.assertEqual(self.post().status_code,429)
        finally:service.gate.release()

    def test_worker_timeout_and_cleanup(self):
        paths=[]
        def fail(command,**kwargs):paths.append(Path(command[-1]).parent);raise subprocess.TimeoutExpired(command,55)
        self.worker.side_effect=fail
        self.assertEqual(self.post().status_code,504);self.assertFalse(paths[0].exists())

    def test_worker_malformed_output(self):
        self.worker.return_value=subprocess.CompletedProcess([],0,b'not json',b'');self.worker.side_effect=None
        self.assertEqual(self.post().status_code,502)

    def test_worker_scalar_json_is_not_an_analysis(self):
        self.worker.side_effect=None;self.worker.return_value=subprocess.CompletedProcess([],0,b'[]',b'')
        self.assertEqual(self.post().status_code,502)

    def test_incomplete_worker_envelope_rejected(self):
        self.worker.side_effect=None;self.worker.return_value=subprocess.CompletedProcess([],0,b'{"schema":"smartparse.unified_analysis","schema_version":"1.0"}',b'')
        self.assertEqual(self.post().status_code,502)

    def test_worker_failure(self):
        self.worker.side_effect=OSError('missing worker')
        self.assertEqual(self.post().status_code,503)

    def test_nonmatching_worker_source_hash_rejected(self):
        original_worker=self.worker.side_effect
        def wrong_hash(command,**kwargs):
            result=original_worker(command,**kwargs);report=json.loads(result.stdout)
            report['source']['sha256']='wrong'
            return subprocess.CompletedProcess(command,0,json.dumps(report).encode(),b'')
        self.worker.side_effect=wrong_hash
        response=self.post()
        self.assertEqual(response.status_code,502)
        self.assertIn('preservation',response.text)


class PresentationTests(unittest.TestCase):
    def report(self,configuration,case):return json.loads((ROOT/f'phase6/v9/outputs/smoke/{configuration}.json').read_text())

    def test_actual_accepted_repair_preview_hash(self):
        report=self.report('recovery','C09');source=(ROOT/'phase6/v8/fixtures/c/C09_repair_null.c').read_bytes().decode()
        previews=recovered_previews(report,source);self.assertEqual(len(previews),1)
        self.assertEqual(hashlib.sha256(previews[0]['source'].encode()).hexdigest(),previews[0]['sha256'])
        self.assertIn('return 17;',previews[0]['source'])

    def test_actual_isolation_preview_hash(self):
        source=(ROOT/'phase6/v8/fixtures/c/C10_isolate_null.c').read_bytes().decode()
        p=recovered_previews(self.report('isolation','C10'),source);self.assertEqual(p[0]['conditioning'],'isolation-conditioned')

    def test_no_invented_preview_when_hash_differs(self):
        self.assertEqual(recovered_previews(self.report('recovery','C09'),'int different;\n'),[])

    def test_unicode_byte_mapping_to_utf16(self):
        r={'source':{'path':'a.c'},'diagnostics':[{'id':'d','location':{'file':'a.c','line':1,'column':8},'location_space':'mapped-original'}]}
        self.assertEqual(editor_locations(r,'// 😀\n')['d']['column'],6)

    def test_unknown_unicode_column_is_line_only(self):
        r={'source':{'path':'a.c'},'diagnostics':[{'id':'d','location':{'file':'a.c','line':1,'column':8},'location_space':'original-tool-reported'}]}
        self.assertEqual(editor_locations(r,'// 😀\n')['d']['precision'],'line')

    def test_line_directives_do_not_get_invented_physical_mapping(self):
        r={'source':{'path':'a.c'},'diagnostics':[{'id':'d','location':{'file':'a.c','line':1,'column':1},'location_space':'original-tool-reported'}]}
        self.assertEqual(editor_locations(r,'#line 20\n'),{})

    def test_variant_and_header_locations_not_projected_onto_original(self):
        r={'source':{'path':'a.c'},'diagnostics':[{'id':'d','location':{'file':'other.h','line':1,'column':1},'location_space':'original-tool-reported'}]}
        self.assertEqual(editor_locations(r,'int x;'),{})


@unittest.skipUnless(locate('clang'),'Clang unavailable; live Studio compiler/CSA integration pending')
class LiveStudioTests(unittest.TestCase):
    def test_real_valid_null_recovery_and_isolation(self):
        with TestClient(app,**CLIENT) as client:
            for name,options,expected in [
                ('C12_valid_full',{'analyzers':['compiler']},'completed'),
                ('C01_null',{'analyzers':['memory']},'completed'),
                ('C09_repair_null',{'analyzers':['memory'],'recovery':True},'completed'),
                ('C10_isolate_null',{'analyzers':['memory'],'isolation':True},'completed')]:
                with self.subTest(name=name):
                    path=ROOT/f'phase6/v8/fixtures/c/{name}.c';before=path.read_bytes()
                    response=client.post('/api/analyze',json={'source':before.decode(),'filename':name+'.c',**options})
                    self.assertEqual(response.status_code,200,response.text[:700]);body=response.json()
                    self.assertEqual(body['report']['status'],expected);self.assertEqual(path.read_bytes(),before)
                    self.assertTrue(body['studio']['workspace_removed'])
                    if name=='C01_null':self.assertTrue(any(d['diagnostic_id']=='core.NullDereference' for d in body['report']['diagnostics']))
                    if options.get('recovery'):self.assertTrue(body['studio']['previews']);self.assertTrue(any(d['conditioning']=='repair-conditioned' for d in body['report']['diagnostics']))
                    if options.get('isolation'):self.assertTrue(body['studio']['previews']);self.assertTrue(any(d['conditioning']=='isolation-conditioned' for d in body['report']['diagnostics']))


if __name__=='__main__':unittest.main()
