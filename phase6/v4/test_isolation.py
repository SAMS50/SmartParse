"""Independent policy and live integration checks, no benchmark tuning."""
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from extended_c import Diagnostic
from phase6.v2.validation import validate_eligibility
from phase6.v3.execution import LimitReached
from .engine import run_isolation,IsolationLimits
from .policy import inventory,plan,mask,preprocess_signature

HERE=Path(__file__).resolve().parent


def synthetic():
    data=b'int broken(void)\n{\n return missing;\n}\nint good(void)\n{\n return 1;\n}\n'
    nodes=[]
    for name in ('broken','good'):
        at=data.index(name.encode());start=data.rfind(b'int',0,at);left=data.index(b'{',at);end=data.index(b'}',left)
        nodes.append({'kind':'FunctionDecl','id':name,'name':name,'loc':{'file':'C:/a b/test.c','offset':at},
                      'range':{'begin':{'offset':start},'end':{'offset':end}},
                      'inner':[{'kind':'CompoundStmt','range':{'begin':{'offset':left},'end':{'offset':end}}}]})
    return data,{'kind':'TranslationUnitDecl','inner':nodes},'C:/a b/test.c'


class PolicyTests(unittest.TestCase):
    def test_physical_ast_boundaries(self):
        data,tree,path=synthetic();r=inventory(tree,path,data)
        self.assertEqual([f['name'] for f in r],['broken','good'])
        self.assertEqual(data[r[0]['end_byte_exclusive']-1:r[0]['end_byte_exclusive']],b'}')

    def test_boundary_spelling_mismatch_rejects(self):
        data,tree,path=synthetic();tree['inner'][0]['loc']['offset']+=1
        with self.assertRaisesRegex(ValueError,'name mismatch'):inventory(tree,path,data)

    def test_macro_boundary_rejects(self):
        data,tree,path=synthetic();tree['inner'][0]['range']['begin']={'expansionLoc':{'offset':0}}
        with self.assertRaisesRegex(ValueError,'macro'):inventory(tree,path,data)

    def test_global_initialization_rejects(self):
        data,tree,path=synthetic();tree['inner'].insert(0,{'kind':'VarDecl','loc':{'file':path}})
        with self.assertRaisesRegex(ValueError,'global'):inventory(tree,path,data)

    def test_shared_line_rejects(self):
        data,tree,path=synthetic();data=data.replace(b' return missing;',b' return missing;')
        start=tree['inner'][1]['range']['begin']['offset'];data=data[:start-1]+b';'+data[start:]
        with self.assertRaisesRegex(ValueError,'shares'):inventory(tree,path,data)

    def test_mask_preserves_bytes_lines_crlf_unicode(self):
        data='int f(void)\r\n{ /* é */\r\n}\r\n'.encode()
        r={'start_byte':0,'end_byte_exclusive':len(data)-2}
        result=mask(data,[r]);self.assertEqual(len(data),len(result))
        self.assertEqual([i for i,b in enumerate(data) if b in (10,13)],[i for i,b in enumerate(result) if b in (10,13)])
        self.assertTrue(all(b in b' \r\n' for b in result))

    def test_dependency_closure(self):
        data,tree,path=synthetic();r=inventory(tree,path,data)
        r[1]['references']=['broken']
        d=Diagnostic(path,3,9,'error','undeclared','clang','semantic/type')
        with self.assertRaisesRegex(ValueError,'no independent'):plan(r,[d],path,data,8)

    def test_exclusion_budget(self):
        data,tree,path=synthetic();r=inventory(tree,path,data);r[1]['references']=['broken']
        d=Diagnostic(path,3,9,'error','undeclared','clang','semantic/type')
        with self.assertRaisesRegex(ValueError,'budget'):plan(r,[d],path,data,1)

    def test_locationless_blocker_rejects(self):
        data,tree,path=synthetic();r=inventory(tree,path,data)
        d=Diagnostic(None,None,None,'error','unknown','clang','unknown')
        with self.assertRaisesRegex(ValueError,'mapped'):plan(r,[d],path,data,8)

    def test_signature_blocker_rejects(self):
        data,tree,path=synthetic();r=inventory(tree,path,data)
        d=Diagnostic(path,1,5,'error','type','clang','semantic/type')
        with self.assertRaisesRegex(ValueError,'body'):plan(r,[d],path,data,8)

    def test_preprocessing_guard(self):
        path='C:/a b/test.c';excluded=[{'start_line':2,'end_line':3}]
        a=b'# 1 "C:/a b/test.c"\nint kept;\nint removed;\nint removed2;\nint kept2;\n'
        b=b'# 1 "C:/a b/test.c"\nint kept;\n\n\nint kept2;\n'
        self.assertEqual(preprocess_signature(a,path,excluded),preprocess_signature(b,path,excluded))
        self.assertNotEqual(preprocess_signature(a,path,excluded),preprocess_signature(b.replace(b'kept2',b'changed'),path,excluded))

    def test_malformed_preprocessor_output_rejects(self):
        for output in (b'no markers',b'# strange\n',b'# 1 "bad\\q"\n'):
            with self.subTest(output=output),self.assertRaises(ValueError):preprocess_signature(output,'x.c',[])

    def test_hard_limits(self):
        for options in ({'variants':2},{'exclusions':17},{'invocations':81},{'analyzer_invocations':7},{'total_seconds':float('inf')}):
            with self.subTest(options=options),self.assertRaises(ValueError):IsolationLimits(**options).validate()


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler=shutil.which('clang')
        if not cls.compiler:raise unittest.SkipTest('Clang not on PATH; run validation with --compiler to enable live tests')

    def run_case(self,name,**options):
        p=HERE/'fixtures'/name;before=p.read_bytes()
        r=run_isolation(p,compiler=self.compiler,**options)
        self.assertEqual(before,p.read_bytes());self.assertTrue(r['source']['original_unchanged'])
        self.assertTrue(r['isolation']['temporary_workspace_removed'])
        self.assertLessEqual(r['isolation']['usage']['compiler_invocations'],r['isolation']['limits']['invocations'])
        self.assertLessEqual(r['isolation']['usage']['analyzer_invocations'],r['isolation']['limits']['analyzer_invocations'])
        return r

    def test_disabled_by_default(self):
        r=self.run_case('independent.c');self.assertEqual(r['isolation']['status'],'not_attempted')
        self.assertFalse(r['isolation']['variant']);self.assertIsNone(r['baseline_static_analysis'])

    def test_unrelated_error_allows_conditioned_finding(self):
        r=self.run_case('independent.c',isolate=True);i=r['isolation']
        self.assertEqual(i['status'],'completed',i['reason']);self.assertTrue(i['eligibility_improved'])
        self.assertEqual([f['name'] for f in i['excluded_functions']],['broken'])
        validate_eligibility(i['variant']['eligibility'])
        findings=r['isolation_conditioned_findings']
        if not findings:self.skipTest('Installed analyzer did not emit a null-dereference finding; no checker-specific finding assumed')
        self.assertEqual(len(r['unique_additional_findings']),1)
        self.assertTrue(all(f['isolation_conditioned'] and not f['confirmed_original_defect'] for f in findings))
        self.assertTrue(all(f['evidence']['line']>=5 for f in findings))
        self.assertFalse(i['function_path_coverage_certified'])

    def test_callers_excluded_without_stubs(self):
        r=self.run_case('dependent.c',isolate=True);i=r['isolation']
        self.assertEqual(i['status'],'completed',i['reason'])
        self.assertEqual([f['name'] for f in i['excluded_functions']],['broken','caller'])
        self.assertIn('depends on excluded',i['excluded_functions'][1]['exclusion_reasons'][0])

    def test_all_dependent_abstains(self):
        r=self.run_case('all_dependent.c',isolate=True)
        self.assertIn('no independent',r['isolation']['reason']);self.assertFalse(r['isolation']['variant'])

    def test_global_state_and_initialization_abstain(self):
        for name in ('global_initialization.c','global_blocker.c'):
            r=self.run_case(name,isolate=True);self.assertIn('global',r['isolation']['reason'])
            self.assertFalse(r['isolation_conditioned_findings'])

    def test_macro_and_indirect_dependencies_abstain(self):
        for name in ('macro.c','header_macro.c','indirect.c'):
            r=self.run_case(name,isolate=True);self.assertEqual(r['isolation']['status'],'abstained')
            self.assertFalse(r['isolation']['variant'])

    def test_malformed_source_abstains(self):
        r=self.run_case('malformed.c',isolate=True);self.assertEqual(r['isolation']['status'],'abstained')
        self.assertFalse(r['isolation_conditioned_findings'])

    def test_valid_source_does_not_isolate(self):
        r=self.run_case('valid.c',isolate=True);self.assertIn('already accepted',r['isolation']['reason'])

    def test_spaces_unicode_crlf_json_cli(self):
        from .__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory(prefix='isolation space ') as directory:
            p=Path(directory)/'é input.c';data=(HERE/'fixtures/independent.c').read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n');p.write_bytes(data)
            out=StringIO()
            with redirect_stdout(out):code=main([str(p),'--compiler',self.compiler,'--isolate-unaffected','--json'])
            r=json.loads(out.getvalue());self.assertEqual(code,1);self.assertEqual(r['isolation']['status'],'completed')
            self.assertEqual(p.read_bytes(),data)

    def test_budgets_stop_without_excess_calls(self):
        for limits in (IsolationLimits(invocations=1),IsolationLimits(analyzer_invocations=1),IsolationLimits(exclusions=1)):
            r=self.run_case('dependent.c',isolate=True,limits=limits)
            self.assertIn(r['isolation']['status'],('budget_exhausted','abstained'))

    def test_timeout_stops_isolation(self):
        from phase6.v4 import engine
        real=engine.ast
        def timeout(*args,**kwargs):raise LimitReached('compiler call timed out; test injection')
        with patch.object(engine,'ast',side_effect=timeout):r=self.run_case('independent.c',isolate=True)
        self.assertEqual(r['isolation']['status'],'timed_out');self.assertFalse(r['isolation']['variant'])

    def test_preprocessing_change_rejects_variant(self):
        from phase6.v4 import engine
        calls=[]
        def mismatch(output,*args):calls.append(output);return [len(calls)]
        with patch.object(engine,'preprocess_signature',side_effect=mismatch):r=self.run_case('independent.c',isolate=True)
        self.assertIn('preprocessing',r['isolation']['reason']);self.assertEqual(r['isolation']['variant']['status'],'rejected')
        self.assertFalse(r['isolation_conditioned_findings'])

    def test_malformed_ast_rejects(self):
        with patch('phase6.v4.engine.ast',return_value=({'kind':'Unknown'},1)):
            r=self.run_case('independent.c',isolate=True)
        self.assertEqual(r['isolation']['status'],'abstained');self.assertFalse(r['isolation']['variant'])

    def test_duplicate_and_excluded_findings_not_counted(self):
        from phase6.v4 import engine
        real=engine.analyzer_check
        def injected(*args,**kwargs):
            result=real(*args,**kwargs)
            if len(args)>4 and args[4]:
                warnings=[d for d in result.findings if d.severity=='warning']
                if warnings:
                    result.findings.extend([warnings[0],replace(warnings[0],line=3,column=5)])
            return result
        with patch.object(engine,'analyzer_check',side_effect=injected):r=self.run_case('independent.c',isolate=True)
        self.assertLessEqual(len(r['unique_additional_findings']),1)
        self.assertTrue(all(f['evidence']['line']!=3 for f in r['isolation_conditioned_findings']))

    def test_partial_analyzer_not_completed_coverage(self):
        from phase6.v4 import engine
        real=engine.analyzer_check
        def partial(*args,**kwargs):
            result=real(*args,**kwargs)
            if len(args)>4 and args[4]:result.status='partial';result.unrecognized_output=['malformed tool output']
            return result
        with patch.object(engine,'analyzer_check',side_effect=partial):r=self.run_case('independent.c',isolate=True)
        self.assertEqual(r['isolation']['status'],'partial');self.assertFalse(r['isolation']['eligibility_improved'])

    def test_invalid_finding_mapping_clears_eligibility_and_findings(self):
        from phase6.v4 import engine
        real=engine.analyzer_check
        def invalid(*args,**kwargs):
            result=real(*args,**kwargs)
            if len(args)>4 and args[4]:
                result.findings.append(Diagnostic(str(args[2]),999999,1,'warning','invalid mapped finding','clang-static-analyzer','unknown'))
            return result
        with patch.object(engine,'analyzer_check',side_effect=invalid):r=self.run_case('independent.c',isolate=True)
        self.assertEqual(r['isolation']['status'],'abstained');self.assertFalse(r['isolation']['eligibility_improved'])
        self.assertEqual(r['isolation']['variant']['status'],'rejected');self.assertFalse(r['isolation_conditioned_findings'])
