import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from extended_c import Compiler
from phase6.v3.execution import LimitReached
from phase6.v2.validation import validate_eligibility
from .capabilities import checker_names,selected_options,CHECKERS
from .engine import run_detection,DetectionLimits,Controller,export_v1_run

HERE=Path(__file__).resolve().parent


class PolicyTests(unittest.TestCase):
    def test_parse_actual_help_formats(self):
        self.assertEqual(checker_names('  alpha.unix.Stream    desc\n  continued text\n',True),['alpha.unix.Stream'])
        self.assertEqual(checker_names('OVERVIEW: text\ncore.NullDereference\n'),['core.NullDereference'])
    def test_limits(self):
        for kwargs in ({'checkers':5},{'invocations':121},{'analyzer_invocations':21},{'total_seconds':float('nan')},{'call_seconds':31}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):DetectionLimits(**kwargs).validate()
    def test_cache_binding_cannot_cross_configuration(self):
        with self.assertRaisesRegex(ValueError,'mismatch'):selected_options({'binding':'bad'},Compiler('clang','clang','17',()),[])
    def test_analyzer_budget_checked_before_invocation(self):
        c=Controller(DetectionLimits(analyzer_invocations=1),0,1,10)
        with self.assertRaisesRegex(LimitReached,'analyzer'):c.call('probe',['clang','--analyze'])
        self.assertEqual(c.budget.calls,[])
    def test_conditioned_export_refused(self):
        for kind in ('repair_conditioned','isolation_conditioned'):
            r={'provenance':{'repair_conditioned':False,'isolation_conditioned':False}};r['provenance'][kind]=True
            with self.assertRaisesRegex(ValueError,'conditioned'):export_v1_run(r,'source')
    def test_no_empty_export(self):
        with self.assertRaisesRegex(ValueError,'no analysis'):export_v1_run({'provenance':{'repair_conditioned':False,'isolation_conditioned':False},'analysis':None},'s')
    def fixture_report(self,sid,diagnostics,findings):
        from extended_c import Diagnostic
        p=(HERE/'fixtures'/(sid+'.c')).resolve()
        def d(message,backend,identifier,severity='warning'):
            return {'file':str(p),'line':1,'column':40,'severity':severity,'category':'unknown','backend':backend,
                    'message':message,'diagnostic_id':identifier,'source_snippet':None}
        import hashlib
        return {'profile':'memory','source':{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_unchanged':True},
                'temporary_workspace_removed':True,
                'provenance':{'repair_conditioned':False,'isolation_conditioned':False},'status':'completed',
                'analysis':{'status':'completed','diagnostics':[d(*args) for args in diagnostics],
                            'static_analysis':{'status':'completed','findings':[d(*args) for args in findings]}}}
    def test_compiler_analyzer_duplicates_are_one_reviewed_root(self):
        from .evaluation import evaluate_fixtures
        dataset=json.loads((HERE/'reference.json').read_text())
        r=self.fixture_report('stack_escape_bad',[('address of local stack memory returned','clang','-Wreturn-stack-address')],
                              [('address of local stack memory returned','clang-static-analyzer','core.StackAddressEscape'),
                               ('context only','clang-static-analyzer',None,'note')])
        result=evaluate_fixtures(dataset,{'stack_escape_bad':r})
        self.assertEqual(result['summary']['detected_root_cause_count'],1)
        self.assertEqual(result['summary']['finding_dispositions']['duplicate'],1)
        self.assertEqual(result['summary']['finding_dispositions']['context_note'],1)
    def test_corrected_counterpart_warning_remains_unknown_not_false_positive(self):
        from .evaluation import evaluate_fixtures
        dataset=json.loads((HERE/'reference.json').read_text())
        r=self.fixture_report('null_good',[('unclassified warning','clang','-Wunknown')],[])
        result=evaluate_fixtures(dataset,{'null_good':r})
        self.assertEqual(result['summary']['confirmed_false_positive_group_count'],0)
        self.assertEqual(result['bounded_fixture_metrics']['unknown_primary_observations'],1)
    def test_cli_invalid_arguments(self):
        from .__main__ import main
        from contextlib import redirect_stderr
        from io import StringIO
        for args in (['missing.c','--max-checkers','5'],['missing.c','--total-timeout','nan']):
            with self.subTest(args=args),redirect_stderr(StringIO()),self.assertRaises(SystemExit) as result:main(args)
            self.assertEqual(result.exception.code,2)
    def test_cli_missing_file_json(self):
        from .__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        out=StringIO()
        with redirect_stdout(out):code=main([str(HERE/'missing_input.c'),'--memory-analysis','--json'])
        self.assertEqual(code,3);self.assertIn('failure',json.loads(out.getvalue()))
    def test_unverified_source_cannot_export_evidence(self):
        r=self.fixture_report('null_good',[],[]);r['source']['original_unchanged']=False
        with self.assertRaisesRegex(ValueError,'unverified'):export_v1_run(r,'null_good')


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler=shutil.which('clang')
        if not cls.compiler:raise unittest.SkipTest('Installed Clang not on PATH; run v5 validation with --compiler')
        cls.capability=None
    def run_case(self,name,**options):
        p=HERE/'fixtures'/name;before=p.read_bytes()
        r=run_detection(p,compiler=self.compiler,capability=self.__class__.capability,**options)
        if r['capabilities']:self.__class__.capability=r['capabilities']
        self.assertEqual(p.read_bytes(),before);self.assertTrue(r['source']['original_unchanged']);self.assertTrue(r['temporary_workspace_removed'])
        self.assertLessEqual(r['usage']['compiler_invocations'],r['usage']['limits']['invocations'])
        self.assertLessEqual(r['usage']['analyzer_invocations'],r['usage']['limits']['analyzer_invocations'])
        return r
    def test_disabled_by_default(self):
        r=self.run_case('null_bad.c');self.assertEqual(r['status'],'not_attempted');self.assertEqual(r['observations'],[])
    def test_baseline_and_memory_have_same_default_null_checker(self):
        for profile in ('baseline','memory'):
            r=self.run_case('null_bad.c',enabled=True,profile=profile);self.assertEqual(r['status'],'completed',r['reason'])
            self.assertTrue(any(f['evidence']['diagnostic_id']=='core.NullDereference' for f in r['observations']))
            self.assertTrue(all(not f['confirmed_defect'] for f in r['observations']))
            validate_eligibility(r['eligibility'])
    def test_corrected_bounds_has_no_strong_claims(self):
        r=self.run_case('fixed_bounds_good.c',enabled=True)
        self.assertEqual(r['status'],'completed',r['reason']);self.assertFalse(r['observations'])
    def test_unknown_extent_no_naming_based_claim(self):
        r=self.run_case('unknown_extent.c',enabled=True);self.assertEqual(r['status'],'completed');self.assertFalse(r['observations'])
    def test_malformed_source_is_blocked(self):
        r=self.run_case('malformed_semantic.c',enabled=True)
        self.assertEqual(r['status'],'partial');self.assertFalse(r['observations'])
    def test_isolated_findings_cannot_export_unconditionally(self):
        r=self.run_case('malformed_semantic.c',enabled=True,isolate=True)
        self.assertTrue(r['provenance']['isolation_conditioned'],r['upstream']['isolation']['reason'])
        with self.assertRaises(ValueError):export_v1_run(r,'s')
    def test_invocation_budget(self):
        r=self.run_case('valid.c',enabled=True,limits=DetectionLimits(invocations=1))
        self.assertIn(r['status'],('failed','budget_exhausted'))
    def test_timeout_and_cleanup(self):
        with patch('phase6.v5.engine.analyzer_check',side_effect=LimitReached('compiler call timed out')):
            r=self.run_case('valid.c',enabled=True)
        self.assertEqual(r['status'],'timed_out');self.assertFalse(r['observations'])
    def test_malformed_ast_abstains_without_claim(self):
        with patch('phase6.v5.engine.ast',side_effect=ValueError('malformed JSON AST')):
            r=self.run_case('null_bad.c',enabled=True)
        self.assertEqual(r['status'],'failed');self.assertFalse(r['observations'])
    def test_repaired_evidence_stays_conditioned(self):
        p=HERE.parent/'v3/fixtures/positive_analyzer.c';before=p.read_bytes()
        r=run_detection(p,enabled=True,compiler=self.compiler,repair=True,capability=self.__class__.capability)
        self.assertEqual(p.read_bytes(),before);self.assertTrue(r['provenance']['repair_conditioned'])
        self.assertTrue(all(f['provenance']['repair_conditioned'] for f in r['observations']))
        with self.assertRaises(ValueError):export_v1_run(r,'s')
    def test_json_cli_space_unicode_path(self):
        from .__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        import tempfile
        with tempfile.TemporaryDirectory(prefix='memory profile space ') as work:
            p=Path(work)/'é input.c';data=(HERE/'fixtures/null_bad.c').read_bytes();p.write_bytes(data);out=StringIO()
            with redirect_stdout(out):code=main([str(p),'--memory-analysis','--compiler',self.compiler,'--json'])
            r=json.loads(out.getvalue());self.assertEqual(code,0);self.assertEqual(r['status'],'completed');self.assertEqual(p.read_bytes(),data)
