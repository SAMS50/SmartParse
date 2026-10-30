import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from .protocol import gcc_json,gcc_sarif,cppcheck_xml,tidy_text,normalize,uri_path
from .experiment import command_for,run_case

HERE=Path(__file__).resolve().parent
SOURCE='C:/folder with spaces/é.c'


class ProtocolTests(unittest.TestCase):
    def test_gcc_json_primary_and_notes(self):
        rows,_=gcc_json(json.dumps([{'kind':'warning','message':'null','option':'-Wanalyzer-null-dereference','locations':[{'caret':{'file':SOURCE,'line':2,'byte-column':7}}],
                                    'children':[{'kind':'note','message':'path event','locations':[]}]}]))
        self.assertEqual(rows[0]['column'],7);self.assertTrue(rows[1]['context_note']);self.assertEqual(rows[0]['category'],'memory safety')
    def test_sarif_windows_uri_and_codeflow(self):
        payload={'version':'2.1.0','runs':[{'results':[{'ruleId':'-Wanalyzer-out-of-bounds','message':{'text':'outside'},'locations':[{'physicalLocation':{'artifactLocation':{'uri':'file:///C:/folder%20with%20spaces/%C3%A9.c'},'region':{'startLine':2,'startColumn':1}}}],'codeFlows':[{'threadFlows':[]}]}]}]}
        rows,_=gcc_sarif(json.dumps(payload));self.assertEqual(rows[0]['file'],SOURCE);self.assertTrue(rows[0]['related'])
    def test_cppcheck_related_not_duplicate_primary(self):
        xml='<results version="2"><errors><error id="doubleFree" severity="error" msg="double"><location file="a.c" line="4"/><location file="a.c" line="2"/></error></errors></results>'
        rows,_=cppcheck_xml(xml);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['line'],4);self.assertEqual(len(rows[0]['related']),1)
    def test_tidy_windows_multiline_check_identifier(self):
        rows,_=tidy_text('C:\\folder with spaces\\é.c:2:4: warning: widening cast [bugprone-misplaced-widening-cast]\n  source\n  ^\nC:\\folder with spaces\\é.c:1:1: note: context\n')
        self.assertEqual(len(rows),2);self.assertEqual(rows[0]['diagnostic_id'],'bugprone-misplaced-widening-cast');self.assertTrue(rows[1]['context_note'])
    def test_duplicates_and_unicode_source_binding(self):
        d={'kind':'warning','message':'test','locations':[{'caret':{'file':SOURCE,'line':2,'column':1}}]}
        rows,duplicates,_=normalize('gcc-json',json.dumps([d,d]),SOURCE,'/* é */\r\nreturn 1;\r\n'.encode(),{'id':'gcc14'},{})
        self.assertEqual(len(rows),1);self.assertEqual(len(duplicates),1);self.assertEqual(rows[0]['source_snippet'],'return 1;')
    def test_unknown_identifier_not_guessed(self):
        rows,_=gcc_json('[{"kind":"warning","message":"leak-looking text","locations":[]}]')
        self.assertEqual(rows[0]['category'],'unknown');self.assertIsNone(rows[0]['line'])
    def test_line_directive_does_not_claim_physical_mapping(self):
        d={'kind':'warning','message':'location','locations':[{'caret':{'file':SOURCE,'line':2,'column':1}}]}
        rows,_,_=normalize('gcc-json',json.dumps([d]),SOURCE,b'#line 2\nint f;\n',{}, {})
        self.assertFalse(rows[0]['source_bound']);self.assertIsNone(rows[0]['source_snippet']);self.assertEqual(rows[0]['mapping_status'],'unverified_presumed_locations')
    def test_malformed_outputs_fail_closed(self):
        for format,text in [('gcc-json','{'),('gcc-sarif','[]'),('cppcheck-xml','<bad>'),('cppcheck-xml','<!DOCTYPE a><results version="2"/>')]:
            with self.subTest(format=format,text=text),self.assertRaises(ValueError):normalize(format,text,SOURCE,b'',{}, {})
    def test_sarif_no_location_still_preserved(self):
        rows,_=gcc_sarif('{"version":"2.1.0","runs":[{"results":[{"message":{"text":"global"}}]}]}')
        self.assertIsNone(rows[0]['file']);self.assertEqual(rows[0]['message'],'global')
    def test_command_never_links_or_fixes(self):
        catalog=json.loads((HERE/'catalog.json').read_text())
        for tool in catalog:
            command=command_for(tool,Path(SOURCE),Path('private space'))
            self.assertNotIn('--fix',command);self.assertNotIn('-o',command if tool['kind']!='gcc' else [])
            if tool['kind']=='gcc':self.assertIn('-c',command);self.assertTrue(command[-1].endswith('.o'))
    def test_missing_tool_clear_state(self):
        tool={'id':'missing','path':str(HERE/'missing.exe'),'version':'1','kind':'gcc','format':'gcc-json','diagnostic_format':'json'}
        r=run_case(tool,HERE/'fixtures/alloc_literal_good.c',timeout=2)
        self.assertEqual(r['status'],'unavailable');self.assertTrue(r['temporary_workspace_removed']);self.assertTrue(r['source']['original_unchanged'])
    def test_timeout_no_more_calls_and_cleanup(self):
        tool=json.loads((HERE/'catalog.json').read_text())[0]
        with patch('phase6.v7.experiment.bounded_run',side_effect=subprocess.TimeoutExpired('tool',1)):
            r=run_case(tool,HERE/'fixtures/alloc_literal_good.c',timeout=2)
        self.assertEqual(r['status'],'timed_out');self.assertEqual(r['usage']['compiler_invocations'],1);self.assertTrue(r['temporary_workspace_removed'])
    def test_version_change_not_silently_substituted(self):
        tool=json.loads((HERE/'catalog.json').read_text())[0]
        with patch('phase6.v7.experiment.bounded_run',return_value=subprocess.CompletedProcess([],0,b'Other Compiler 999',b'')):
            r=run_case(tool,HERE/'fixtures/alloc_literal_good.c')
        self.assertEqual(r['status'],'unavailable');self.assertEqual(r['usage']['compiler_invocations'],1)


class LiveTests(unittest.TestCase):
    def test_each_discovered_candidate_on_frozen_null(self):
        source=HERE.parents[1]/'phase6/v5/fixtures/null_bad.c'
        for tool in json.loads((HERE/'catalog.json').read_text()):
            if not Path(tool['path']).exists():self.skipTest('Recorded local tool unavailable: '+tool['path'])
            r=run_case(tool,source,timeout=15)
            self.assertEqual(r['status'],'completed',(tool['id'],r['reason'],r['raw']))
            self.assertTrue(r['temporary_workspace_removed']);self.assertTrue(r['source']['original_unchanged'])
            self.assertTrue(r['diagnostics'],tool['id'])


class AdapterTests(unittest.TestCase):
    def test_disabled_is_no_tool_execution(self):
        from .adapter import analyze_external
        with patch('phase6.v7.adapter.run_case',side_effect=AssertionError('must not invoke')):
            r=analyze_external('missing.c')
        self.assertEqual(r['status'],'not_attempted');self.assertEqual(r['usage']['compiler_invocations'],0)
    def test_conditioned_inputs_are_not_flattened(self):
        from .adapter import analyze_external
        for key in ('repair_conditioned','isolation_conditioned'):
            r=analyze_external('missing.c',enabled=True,provenance={key:True})
            self.assertEqual(r['status'],'unsupported');self.assertEqual(r['diagnostics'],[])
    def test_comparison_only_tools_rejected(self):
        from .adapter import analyze_external
        with self.assertRaisesRegex(ValueError,'comparison-only'):analyze_external('missing.c',enabled=True,tool='gcc16')
    def test_cli_invalid_args_and_missing_file(self):
        from .__main__ import main
        from io import StringIO
        from contextlib import redirect_stdout,redirect_stderr
        with redirect_stderr(StringIO()),self.assertRaises(SystemExit) as r:main(['missing.c','--timeout','31'])
        self.assertEqual(r.exception.code,2)
        out=StringIO()
        with redirect_stdout(out):code=main([str(HERE/'missing.c'),'--external-analysis','--json'])
        self.assertEqual(code,3);self.assertEqual(json.loads(out.getvalue())['status'],'failed')
    def test_runtime_capability_budget_and_private_cleanup(self):
        from .adapter import analyze_external
        for tool in ('gcc14','cppcheck'):
            r=analyze_external(HERE/'fixtures/alloc_literal_good.c',enabled=True,tool=tool,invocation_budget=1)
            self.assertEqual(r['status'],'budget_exhausted');self.assertEqual(r['usage']['compiler_invocations'],1);self.assertTrue(r['temporary_workspace_removed'])
    def test_live_selected_adapters_unicode_crlf_preservation(self):
        from .adapter import analyze_external
        with tempfile.TemporaryDirectory(prefix='external space ') as work:
            p=Path(work)/'é input.c';data=b'int probe(void)\r\n{ int *p=0; return *p; }\r\n';p.write_bytes(data)
            for tool in ('gcc14','cppcheck'):
                r=analyze_external(p,enabled=True,tool=tool)
                self.assertEqual(r['status'],'completed',r['reason']);self.assertEqual(p.read_bytes(),data)
                self.assertTrue(r['capability']['supported']);self.assertEqual(r['usage']['compiler_invocations'],3)
                self.assertTrue(r['diagnostics']);self.assertIsNone(r['confirmed_defect_roots'])
                self.assertTrue(all(d['provenance']['original_source'] and not d['provenance']['repair_conditioned'] for d in r['diagnostics']))
                if tool=='cppcheck':
                    commands=[c['command'] for c in r['usage']['calls'] if c['role'] in ('analyzer_capability','external_analysis')]
                    caches=[next(arg for arg in cmd if arg.startswith('--cppcheck-build-dir=')) for cmd in commands]
                    self.assertNotEqual(caches[0],caches[1])
