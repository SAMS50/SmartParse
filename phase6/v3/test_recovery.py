"""Independent recovery policy, mapping, budget and live integration tests."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from unittest.mock import patch

from extended_c import AnalysisResult,Compiler,Diagnostic
from phase6.v2.validation import validate_eligibility
from phase6.v3.execution import Budget,Limits,LimitReached,bounded_run
from phase6.v3.engine import run_recovery,error_keys
from phase6.v3.policy import (fixits,unescape,point_offset,original_offset,apply_edits,source_map,
                             only_inserted_semicolon,boundary_candidate)

HERE=Path(__file__).resolve().parent
FAKE_PATH='C:/folder with spaces/input.c'


def policy_fixture(data=b'int value = 1\nint other = 2;\n'):
    end=data.index(b'1')
    tree={'kind':'TranslationUnitDecl','inner':[{'kind':'VarDecl','loc':{'file':FAKE_PATH,'offset':data.index(b'value')},
         'range':{'begin':{'offset':0,'tokLen':3},'end':{'offset':end,'tokLen':1}},'inner':[]}]}
    fix={'file':FAKE_PATH,'replacement':';','start_line':1,'end_line':1,'start_column':end+2,'end_column':end+2,
         'diagnostic':{'severity':'error'}}
    return data,tree,fix


class PolicyTests(unittest.TestCase):
    def test_machine_fixits_decode_windows_paths_and_octal_utf8(self):
        raw=b'x.c:1:2: error: syntax\nfix-it:"C:\\\\folder with spaces\\\\input.c":{1:2-1:2}:";"\n'
        found=fixits(raw)
        self.assertEqual(found[0]['file'],'C:\\folder with spaces\\input.c')
        self.assertEqual(unescape(b'caf\\303\\251'),'café'.encode())

    def test_insertion_requires_machine_range_and_ast(self):
        data,tree,fix=policy_fixture()
        self.assertEqual(boundary_candidate(fix,tree,FAKE_PATH,data)['offset'],13)
        tree['inner']=[]
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_non_semicolon_and_nonzero_range_rejected(self):
        for kind in ('identifier','range'):
            data,tree,fix=policy_fixture()
            if kind=='identifier':fix['replacement']='missing_identifier'
            else:fix['end_column']+=1
            with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_header_fixit_is_not_main_file_repair(self):
        data,tree,fix=policy_fixture();fix['file']='C:/headers/input.c'
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_macro_range_is_not_trusted(self):
        data,tree,fix=policy_fixture()
        tree['inner'][0]['range']['end']={'expansionLoc':{'offset':12},'spellingLoc':{'offset':12}}
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_duplicate_ast_boundary_is_ambiguous(self):
        data,tree,fix=policy_fixture();tree['inner']*=2
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_unknown_encoding_is_not_reencoded(self):
        data,tree,fix=policy_fixture();data+=b'/*\xff*/'
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_presumed_line_directive_abstains(self):
        data,tree,fix=policy_fixture();data+=b'#line 200 "alias.c"\n'
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_unbraced_return_is_not_whitelisted(self):
        data=b'int f(int x) { if(x) return 1\n}\n'
        start=data.index(b'return');end=data.index(b'1')
        node={'kind':'ReturnStmt','range':{'begin':{'offset':start,'tokLen':6},'end':{'offset':end,'tokLen':1}}}
        tree={'kind':'TranslationUnitDecl','inner':[{'kind':'IfStmt','loc':{'file':FAKE_PATH},'inner':[node]}]}
        fix={'file':FAKE_PATH,'replacement':';','start_line':1,'end_line':1,'start_column':end+2,'end_column':end+2,'diagnostic':{'severity':'error'}}
        with self.assertRaises(ValueError):boundary_candidate(fix,tree,FAKE_PATH,data)

    def test_preprocessing_guard_requires_only_one_semicolon_token(self):
        self.assertTrue(only_inserted_semicolon(b'int a=1\nint b;',b'int a=1;\nint b;'))
        for value in (b'int a=2; int b;',b'int a=1;; int b;',b'int a=1; int c;'):
            self.assertFalse(only_inserted_semicolon(b'int a=1\nint b;',value))
        self.assertFalse(only_inserted_semicolon(b'char*x="a";',b'char*x="a;";'))

    def test_crlf_unicode_mapping_is_byte_accurate(self):
        original='/* café */\r\nint n=1\r\nint f(void){return n;}\r\n'.encode()
        offset=point_offset(original,2,8)
        edits=[{'original_offset':offset}]
        variant=apply_edits(original,edits)
        self.assertEqual(variant.count(b'\r\n'),original.count(b'\r\n'))
        self.assertEqual(original_offset(offset,edits),None)
        self.assertEqual(original_offset(offset+1,edits),offset)
        self.assertEqual(original_offset(len(variant),edits),len(original))
        spans=source_map(original,edits)
        self.assertEqual(spans[1]['generated'],';')
        self.assertEqual(spans[-1]['original_end_exclusive'],len(original))

    def test_overlapping_edits_rejected(self):
        with self.assertRaises(ValueError):apply_edits(b'int n=1', [{'original_offset':7},{'original_offset':7}])

    def test_invalid_machine_coordinates_rejected(self):
        with self.assertRaises(ValueError):point_offset(b'int n;\n',2,1)
        with self.assertRaises(ValueError):point_offset(b'int n;\n',1,999)

    def test_new_semantic_error_is_not_an_old_error_match(self):
        original=b'int n=1\nint x=2;\n';variant=apply_edits(original,[{'original_offset':7}])
        compiler=Compiler('clang','clang','test',())
        before=AnalysisResult('completed',compiler,[Diagnostic(FAKE_PATH,1,8,'error',"expected ';'",'clang','syntax')],returncode=1)
        after=AnalysisResult('completed',compiler,[Diagnostic(FAKE_PATH,2,5,'error','undeclared identifier x','clang','semantic/type')],returncode=1)
        self.assertFalse(error_keys(after,FAKE_PATH,variant,original,[{'original_offset':7}])<error_keys(before,FAKE_PATH,original,original,[]))


class BudgetTests(unittest.TestCase):
    def test_real_timeout_does_not_wait_for_inherited_output_pipe(self):
        # Harmless Python control processes, never a user C program. The child
        # inherits output and would keep a PIPE open after its parent dies.
        code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print('started',flush=True); time.sleep(30)"
        started=time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            bounded_run([sys.executable,'-c',code],timeout=0.4)
        self.assertLess(time.monotonic()-started,8)

    def test_file_capture_preserves_binary_output(self):
        completed=bounded_run([sys.executable,'-c',"import sys; sys.stdout.buffer.write(b'\\xffout'); sys.stderr.write('err')"],timeout=5)
        self.assertEqual(completed.stdout,b'\xffout');self.assertEqual(completed.stderr,b'err')

    def test_all_calls_count_and_use_no_shell(self):
        seen=[]
        def execute(args,**kwargs):seen.append(kwargs);return subprocess.CompletedProcess(args,0,b'',b'')
        budget=Budget(Limits(invocations=1),execute=execute)
        budget.call('probe',['clang','--version'])
        with self.assertRaises(LimitReached):budget.call('probe',['clang','--version'])
        self.assertFalse(seen[0]['shell']);self.assertEqual(len(budget.calls),1)

    def test_total_deadline_stops_before_spawn(self):
        clock=[0.0];calls=[]
        budget=Budget(Limits(total_seconds=1),clock=lambda:clock[0],execute=lambda *a,**k:calls.append(a))
        clock[0]=2
        with self.assertRaises(LimitReached):budget.call('probe',['clang'])
        self.assertEqual(calls,[])

    def test_call_timeout_latches_stop(self):
        def execute(*args,**kwargs):raise subprocess.TimeoutExpired('clang',1,stderr=b'partial')
        budget=Budget(Limits(),execute=execute)
        with self.assertRaises(LimitReached):budget.call('probe',['clang'])
        with self.assertRaises(LimitReached):budget.call('probe',['clang'])
        self.assertEqual(len(budget.calls),1)

    def test_call_timeout_clamped_to_remaining_total(self):
        clock=[0.0];seen=[]
        def execute(args,**kwargs):seen.append(kwargs['timeout']);return subprocess.CompletedProcess(args,0,b'',b'')
        budget=Budget(Limits(total_seconds=2,call_seconds=10),clock=lambda:clock[0],execute=execute)
        clock[0]=1.25;budget.call('probe',['clang'])
        self.assertEqual(seen,[0.75])

    def test_policy_has_hard_ceilings(self):
        for options in ({'candidates':9},{'rounds':5},{'retained_variants':5},{'invocations':81},{'total_seconds':float('nan')}):
            with self.assertRaises(ValueError):Limits(**options).validate()


class LiveRecoveryTests(unittest.TestCase):
    def clang(self):
        value=shutil.which('clang')
        if not value:self.skipTest('Clang unavailable; live machine-fixit/VFS validation pending')
        return value

    def run_fixture(self,name,**options):
        source=HERE/'fixtures'/name;before=source.read_bytes()
        report=run_recovery(source,compiler=self.clang(),**options)
        self.assertEqual(source.read_bytes(),before)
        self.assertTrue(report['source']['original_unchanged'])
        self.assertTrue(report['recovery']['temporary_workspace_removed'])
        if report['baseline']:validate_eligibility(report['baseline']['eligibility'])
        for variant in report['recovery']['accepted_variants']:
            validate_eligibility(variant['eligibility']);self.assertTrue(variant['temporary_files_removed'])
        return report

    def test_disabled_by_default_captures_no_variant_or_fixit(self):
        report=self.run_fixture('positive_return.c')
        self.assertFalse(report['recovery']['enabled'])
        self.assertEqual(report['recovery']['accepted_variants'],[])
        self.assertNotIn('machine_fixit_capture',[c['role'] for c in report['recovery']['usage']['calls']])

    def test_declaration_frontend_becomes_eligible(self):
        report=self.run_fixture('positive_declaration.c',repair=True)
        self.assertTrue(report['recovery']['eligibility_change']['frontend_newly_eligible'],report['recovery'])
        self.assertEqual(len(report['recovery']['accepted_variants']),1)
        self.assertEqual(report['baseline']['analysis']['summary']['errors'],1)

    def test_return_frontend_becomes_eligible(self):
        report=self.run_fixture('positive_return.c',repair=True)
        self.assertTrue(report['recovery']['eligibility_change']['frontend_newly_eligible'],report['recovery'])

    def test_analyzer_findings_are_only_repair_conditioned(self):
        report=self.run_fixture('positive_analyzer.c',repair=True,static_analysis=True)
        self.assertTrue(report['recovery']['eligibility_change']['analyzer_newly_completed'],report['recovery'])
        self.assertEqual(report['baseline']['analysis']['static_analysis']['findings'],[])
        self.assertTrue(any(f['source']=='analyzer' and f['evidence']['severity']=='warning' for f in report['repair_conditioned_findings']))
        self.assertTrue(all(f['repair_conditioned'] for f in report['repair_conditioned_findings']))

    def test_negative_unbraced_macro_and_header_abstain(self):
        for name in ('negative_unbraced.c','negative_macro.c','negative_header.c'):
            report=self.run_fixture(name,repair=True)
            self.assertEqual(report['recovery']['accepted_variants'],[],name)
            self.assertTrue(report['recovery']['candidates'],name)

    def test_expression_semantic_and_legal_code_not_rewritten(self):
        for name in ('negative_expression.c','negative_semantic.c','negative_legal.c'):
            report=self.run_fixture(name,repair=True)
            self.assertEqual(report['recovery']['accepted_variants'],[],name)

    def test_crlf_and_unicode_preserved(self):
        report=self.run_fixture('unicode_crlf.c',repair=True)
        self.assertEqual(len(report['recovery']['accepted_variants']),1,report['recovery'])
        self.assertTrue(report['recovery']['eligibility_change']['frontend_newly_eligible'])

    def test_two_rounds_and_edit_budget(self):
        report=self.run_fixture('positive_two.c',repair=True)
        self.assertEqual(len(report['recovery']['accepted_variants']),2,report['recovery'])
        limited=self.run_fixture('positive_two.c',repair=True,limits=Limits(edits=1))
        self.assertEqual(len(limited['recovery']['accepted_variants']),1)
        self.assertIn('edit budget',limited['recovery']['stop_reason'])

    def test_retained_variant_budget(self):
        report=self.run_fixture('positive_two.c',repair=True,limits=Limits(retained_variants=1))
        self.assertEqual(len(report['recovery']['accepted_variants']),1)
        self.assertIn('retained-variant budget',report['recovery']['stop_reason'])

    def test_candidate_and_round_budgets(self):
        for limits,word in [(Limits(candidates=1),'candidate budget'),(Limits(rounds=1),'round budget')]:
            report=self.run_fixture('positive_two.c',repair=True,limits=limits)
            self.assertEqual(len(report['recovery']['accepted_variants']),1)
            self.assertIn(word,report['recovery']['stop_reason'])

    def test_windows_spaces_unicode_filename(self):
        source=HERE/'outputs'/('new café source '+uuid.uuid4().hex+'.c')
        source.write_bytes((HERE/'fixtures/positive_return.c').read_bytes())
        try:
            report=run_recovery(source,compiler=self.clang(),repair=True)
            self.assertTrue(report['recovery']['eligibility_change']['frontend_newly_eligible'],report['recovery'])
        finally:source.unlink()

    def test_validation_rejects_injected_new_error(self):
        from phase6.v3 import engine
        original_check=engine.compiler_check
        def changed(budget,compiler,path,config,overlay=()):
            checked=original_check(budget,compiler,path,config,overlay)
            if overlay and Path(path).name=='positive_return.c':
                checked.returncode=1
                checked.diagnostics.append(Diagnostic(str(path),1,5,'error','synthetic newly revealed type error','clang','semantic/type'))
            return checked
        with patch('phase6.v3.engine.compiler_check',side_effect=changed):
            report=self.run_fixture('positive_return.c',repair=True)
        self.assertEqual(report['recovery']['accepted_variants'],[])
        self.assertIn('new errors',report['recovery']['candidates'][0]['reason'])

    def test_validation_rejects_changed_preprocessing_tokens(self):
        from phase6.v3 import engine
        original_pp=engine.preprocess
        def changed(budget,compiler,path,config,overlay=()):
            text=original_pp(budget,compiler,path,config,overlay)
            return text+b'\nint unexpected_token;\n' if overlay and Path(path).name=='positive_return.c' else text
        with patch('phase6.v3.engine.preprocess',side_effect=changed):
            report=self.run_fixture('positive_return.c',repair=True)
        self.assertEqual(report['recovery']['accepted_variants'],[])
        self.assertIn('preprocessing changed',report['recovery']['candidates'][0]['reason'])


if __name__=='__main__':unittest.main()
