"""Deterministic integration tests; live tools are separately exercised by smoke tests."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from extended_c import AnalysisResult,Compiler,Diagnostic
from smartparse_cli.engine import analyze,exit_code
from smartparse_cli.__main__ import main
from smartparse_cli.diagnostics import normalize,group
from smartparse_cli.reporting import render

ROOT=Path(__file__).resolve().parent
CLANG=Compiler('mock-clang','clang','Clang test version',())


class UnifiedTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory(prefix='smartparse release tests ')
        self.path=Path(self.work.name)/'source unicode Ω.c';self.path.write_bytes(b'int value=7;\r\n')
        self.discovery=patch('smartparse_cli.engine.discover',return_value=CLANG);self.discovery.start()
        self.compiler=patch('smartparse_cli.engine.compiler_check',return_value=AnalysisResult('completed',CLANG,returncode=0));self.mock=self.compiler.start()

    def tearDown(self):
        self.compiler.stop();self.discovery.stop();self.work.cleanup()

    def diagnostic(self,message='bad type',severity='error',category='semantic/type',identifier='-Wint-conversion'):
        return Diagnostic(str(self.path),1,5,severity,message,'clang',category,None,identifier)

    def call(self,*args):
        out=io.StringIO();err=io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=main(list(args))
        return code,out.getvalue(),err.getvalue()

    def test_valid_input_exit_zero(self):
        r=analyze(self.path);self.assertEqual(exit_code(r),0);self.assertTrue(r['source']['original_unchanged'])

    def test_syntax_error_exit_one(self):
        self.mock.return_value=AnalysisResult('completed',CLANG,[self.diagnostic('expected ;',category='syntax')],returncode=1)
        r=analyze(self.path);self.assertEqual(exit_code(r),1);self.assertEqual(r['diagnostics'][0]['category'],'syntax')

    def test_warning_exit_one_is_documented(self):
        self.mock.return_value=AnalysisResult('completed',CLANG,[self.diagnostic(severity='warning')],returncode=0)
        self.assertEqual(exit_code(analyze(self.path)),1)

    def test_multiple_independent_findings_remain_separate(self):
        self.mock.return_value=AnalysisResult('completed',CLANG,[self.diagnostic('type A'),self.diagnostic('type B')],returncode=1)
        self.assertEqual(len(analyze(self.path)['groups']),2)

    def test_exact_duplicates_group_but_raw_records_survive(self):
        d=self.diagnostic();self.mock.return_value=AnalysisResult('completed',CLANG,[d,d],returncode=1)
        r=analyze(self.path);self.assertEqual(len(r['groups']),1);self.assertEqual(len(r['diagnostics']),2)
        self.assertEqual(len(r['runs'][0]['raw']['diagnostics']),2)

    def test_source_snippet_available(self):
        self.mock.return_value=AnalysisResult('completed',CLANG,[self.diagnostic()],returncode=1)
        self.assertEqual(analyze(self.path)['diagnostics'][0]['evidence']['source_snippet'],'int value=7;')

    def test_empty_input_is_not_a_crash_or_safety_claim(self):
        self.path.write_bytes(b'');r=analyze(self.path)
        self.assertTrue(r['source']['empty']);self.assertIn('not independently confirmed',r['summary']['limitation'])

    def test_missing_source(self):
        self.assertEqual(exit_code(analyze(self.path.with_name('missing.c'))),3)

    def test_invalid_extension(self):
        path=self.path.with_suffix('.txt');path.write_text('text')
        self.assertIn('.c extension',analyze(path)['tool_issues'][0]['message'])

    def test_missing_header_is_incomplete(self):
        self.mock.return_value=AnalysisResult('partial',CLANG,[self.diagnostic('header missing','fatal error','unknown')],returncode=1)
        self.assertEqual(exit_code(analyze(self.path)),3)

    def test_failed_compiler(self):
        self.mock.return_value=AnalysisResult('failed',CLANG,returncode=-1,issues=['crashed'])
        self.assertEqual(exit_code(analyze(self.path)),3)

    def test_unlocated_driver_error_is_not_a_source_defect(self):
        d=Diagnostic(None,None,None,'error','invalid standard','clang','unknown',None,None)
        self.mock.return_value=AnalysisResult('completed',CLANG,[d],returncode=1)
        r=analyze(self.path);self.assertEqual(exit_code(r),3)
        self.assertEqual(r['diagnostics'][0]['diagnostic_kind'],'driver_or_configuration_error')

    def test_malformed_output_preserved(self):
        self.mock.return_value=AnalysisResult('partial',CLANG,stderr='unparsed Ω',unrecognized_output=['unparsed Ω'])
        r=analyze(self.path);self.assertIn('unparsed Ω',r['runs'][0]['raw']['raw_output']['stderr'])

    def test_timeout_is_not_success(self):
        from phase6.v3.execution import LimitReached
        self.mock.side_effect=LimitReached('compiler timed out')
        r=analyze(self.path);self.assertEqual(r['runs'][0]['status'],'timed_out');self.assertEqual(exit_code(r),3)

    def test_invalid_timeout(self):
        for value in (0,-1,float('inf'),float('nan'),31):
            with self.subTest(value=value),self.assertRaises(ValueError):analyze(self.path,timeout=value)

    def test_invalid_analyzer(self):
        with self.assertRaises(ValueError):analyze(self.path,analyzers=['invented'])

    def test_source_preserved_with_unicode_path_and_crlf(self):
        before=self.path.read_bytes();analyze(self.path);self.assertEqual(self.path.read_bytes(),before)

    def test_json_format(self):
        code,text,_=self.call('analyze',str(self.path),'--format','json')
        self.assertEqual(code,0);self.assertEqual(json.loads(text)['schema_version'],'1.0')

    def test_terminal_format(self):
        code,text,_=self.call('analyze',str(self.path))
        self.assertEqual(code,0);self.assertIn('zero findings does not prove safety',text)

    def test_markdown_format(self):
        code,text,_=self.call('analyze',str(self.path),'--format','markdown')
        self.assertEqual(code,0);self.assertIn('# SmartParse analysis',text)

    def test_output_destination(self):
        target=Path(self.work.name)/'new report.json'
        code,_,_=self.call('analyze',str(self.path),'--format','json','-o',str(target))
        self.assertEqual(code,0);self.assertEqual(json.loads(target.read_text())['status'],'completed')

    def test_existing_source_never_overwritten_by_output(self):
        before=self.path.read_bytes();code,_,_=self.call('analyze',str(self.path),'-o',str(self.path))
        self.assertEqual(code,3);self.assertEqual(self.path.read_bytes(),before)

    def test_output_write_failure(self):
        code,_,err=self.call('analyze',str(self.path),'-o',str(Path(self.work.name)/'absent'/'report'))
        self.assertEqual(code,3);self.assertIn('failure',err)

    def test_help(self):
        with self.assertRaises(SystemExit) as stop:self.call('analyze','--help')
        self.assertEqual(stop.exception.code,0)

    def test_version(self):
        with self.assertRaises(SystemExit) as stop:self.call('--version')
        self.assertEqual(stop.exception.code,0)

    def test_invalid_cli_argument(self):
        with self.assertRaises(SystemExit) as stop:self.call('analyze',str(self.path),'--timeout','invalid')
        self.assertEqual(stop.exception.code,2)

    def test_invalid_cli_analyzer(self):
        with self.assertRaises(SystemExit) as stop:self.call('analyze',str(self.path),'--analyzers','madeup')
        self.assertEqual(stop.exception.code,2)

    def test_missing_optional_analyzer(self):
        r=analyze(self.path,analyzers=['cppcheck'],cppcheck=str(Path(self.work.name)/'absent.exe'))
        self.assertEqual(exit_code(r),3);self.assertIn(r['runs'][0]['status'],('unavailable','failed'))

    def test_doctor_missing_tools_is_inventory_not_finding(self):
        with patch('smartparse_cli.tools.locate',return_value=None):code,text,_=self.call('doctor','--format','json')
        self.assertEqual(code,0);self.assertTrue(all(t['status']=='unavailable' for t in json.loads(text)['tools']))

    def test_compiler_family_is_not_silently_substituted(self):
        r=analyze(self.path,compiler='gcc');self.assertEqual(exit_code(r),3)

    def test_legacy_parser_entry_unchanged(self):
        from phase6.v9.release import digest
        frozen=json.loads((ROOT/'phase6/v9/release_manifest.json').read_text())['legacy_compatibility']
        for name in ('smartparse.py','baseline.py','analyze_c.py'):
            self.assertEqual(digest((ROOT/name).read_bytes(),'git-text-lf'),frozen[name])

    def test_report_required_schema_fields(self):
        schema=json.loads((ROOT/'smartparse_cli/schema.json').read_text())
        r=analyze(self.path)
        self.assertTrue(set(schema['required'])<=set(r))

    def test_original_raw_record_not_changed_by_snippet_enrichment(self):
        self.mock.return_value=AnalysisResult('completed',CLANG,[self.diagnostic()],returncode=1)
        r=analyze(self.path);self.assertIsNone(r['diagnostics'][0]['raw_record']['source_snippet'])
        self.assertEqual(r['diagnostics'][0]['evidence']['source_snippet'],'int value=7;')


class EvidenceAndPipelineTests(unittest.TestCase):
    def d(self,backend='clang',provenance=None):
        return normalize(dict(file='C:/code.c',line=3,column=5,severity='warning',message='same',category='unknown',
            backend=backend,diagnostic_id='id'),run_id=backend,reference='/x',source_hash='a',provenance=provenance)

    def test_cross_backend_same_line_does_not_group(self):self.assertEqual(len(group([self.d(),self.d('gcc')])),2)
    def test_conditioned_never_groups_with_baseline(self):
        self.assertEqual(len(group([self.d(),self.d(provenance=dict(repair_conditioned=True))])),2)
    def test_joint_conditioning_explicit(self):
        self.assertEqual(self.d(provenance=dict(repair_conditioned=True,isolation_conditioned=True))['conditioning'],'repair-and-isolation-conditioned')
    def test_category_from_existing_checker_identifier(self):
        d=normalize(dict(diagnostic_id='core.NullDereference',category='unknown'),run_id='static',reference='/x',source_hash='a')
        self.assertEqual(d['category'],'memory safety');self.assertEqual(d['raw_record']['category'],'unknown')
    def test_unknown_checker_not_guessed_from_english(self):
        d=normalize(dict(diagnostic_id='future.check',message='null pointer memory leak'),run_id='static',reference='/x',source_hash='a')
        self.assertEqual(d['category'],'unknown')
    def test_unknown_location_does_not_group(self):
        a=self.d();b=self.d();b['id']='different';a['location']['column']=None;b['location']['column']=None
        self.assertEqual(len(group([a,b])),2)
    def test_terminal_control_characters_escaped(self):
        from smartparse_cli.reporting import safe
        self.assertNotIn('\x1b',safe('text\x1b[31m'))

    def saved(self,configuration,case):
        return copy.deepcopy(json.loads((ROOT/f'phase6/v8/outputs/extended/{configuration}/{case}.json').read_text())['result'])

    def pipeline(self,case,configuration='extended_baseline',recovery=False,isolation=False):
        path=ROOT/'phase6/v8/fixtures/c'/f'{case}.c'
        raw=self.saved(configuration,case)
        with patch('smartparse_cli.engine.run_semantics',return_value=raw):
            return analyze(path,analyzers=['semantic'],recovery=recovery,isolation=isolation)

    def test_null_pointer_evidence(self):
        r=self.pipeline('C01_null');self.assertTrue(any(d['diagnostic_id']=='core.NullDereference' for d in r['diagnostics']))
    def test_memory_leak_evidence(self):
        r=self.pipeline('C02_leak');self.assertTrue(any(d['diagnostic_id']=='unix.Malloc' for d in r['diagnostics']))
    def test_bounds_evidence(self):
        r=self.pipeline('C05_bounds');self.assertTrue(any(d['diagnostic_id']=='alpha.security.ArrayBoundV2' for d in r['diagnostics']))
    def test_repair_conditioning(self):
        r=self.pipeline('C09_repair_null','recovery_assisted',recovery=True)
        self.assertTrue(any(d['conditioning']=='repair-conditioned' and d['diagnostic_id']=='core.NullDereference' for d in r['diagnostics']))
        self.assertTrue(any(d['conditioning']=='original-source' and d['severity']=='error' for d in r['diagnostics']))
    def test_isolation_conditioning(self):
        r=self.pipeline('C10_isolate_null','isolation_assisted',isolation=True)
        self.assertTrue(any(d['conditioning']=='isolation-conditioned' for d in r['diagnostics']))
        self.assertFalse(r['coverage']['function_path_coverage_certified'])
    def test_raw_references_resolve_to_original_records(self):
        r=self.pipeline('C09_repair_null','recovery_assisted',recovery=True)
        raw=r['runs'][0]['raw']
        for record in r['diagnostics']:
            value=raw
            for part in record['raw_reference']['path'].strip('/').split('/'):
                value=value[int(part)] if isinstance(value,list) else value[part]
            self.assertEqual(value,record['raw_record'])
    def test_unsafe_isolation_abstention_preserved(self):
        r=self.pipeline('C11_missing_header','isolation_assisted',isolation=True)
        self.assertNotEqual(r['status'],'completed')
    def test_memory_dependency_not_run_twice(self):
        path=ROOT/'phase6/v8/fixtures/c/C01_null.c'
        with patch('smartparse_cli.engine.run_semantics',return_value=self.saved('extended_baseline','C01_null')),patch('smartparse_cli.engine.run_detection') as memory:
            r=analyze(path,analyzers=['memory','semantic']);memory.assert_not_called()
        self.assertEqual(r['effective_analyzers'],['semantic'])
    def test_original_smartparse_mode_needs_no_compiler(self):
        r=analyze(ROOT/'phase6/v8/fixtures/syntax/S03.c',analyzers=['smartparse'])
        self.assertTrue(r['diagnostics'][0]['suggestion']);self.assertEqual(exit_code(r),1)
    def test_unsupported_restricted_lexer_graceful(self):
        r=analyze(ROOT/'phase6/v8/fixtures/syntax/S12.c',analyzers=['smartparse'])
        self.assertEqual(exit_code(r),3)


if __name__=='__main__':unittest.main()
