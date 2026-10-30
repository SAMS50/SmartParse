import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from .detectors import contradiction,precision,input_capacity,scan
from .engine import run_semantics,CHECKER
from phase6.v5.engine import DetectionLimits
from phase6.v3.execution import LimitReached

HERE=Path(__file__).resolve().parent
def literal(value,type='int'):return {'kind':'IntegerLiteral','value':str(value),'type':{'qualType':type}}
def ref(id='x',type='int'):return {'kind':'DeclRefExpr','type':{'qualType':type},'referencedDecl':{'id':id,'kind':'ParmVarDecl','type':{'qualType':type}}}
def comparison(op,value,id='x'):return {'kind':'BinaryOperator','opcode':op,'inner':[ref(id),literal(value)]}
def conjunction(*items):
    n=items[0]
    for item in items[1:]:n={'kind':'BinaryOperator','opcode':'&&','inner':[n,item]}
    return n
def division(a,b):return {'kind':'ImplicitCastExpr','castKind':'IntegralToFloating','type':{'qualType':'double'},'inner':[{'kind':'BinaryOperator','opcode':'/','type':{'qualType':'int'},'inner':[a,b]}]}
def scanf(format,capacity=4):return {'kind':'CallExpr','inner':[{'kind':'DeclRefExpr','referencedDecl':{'id':'scanf'}},
    {'kind':'StringLiteral','value':json.dumps(format)},ref('buffer',f'char[{capacity}]')]}


class PolicyTests(unittest.TestCase):
    def test_empty_interval_and_boundary(self):
        self.assertIsNotNone(contradiction(conjunction(comparison('<',5),comparison('>',10)),{'x'}))
        self.assertIsNone(contradiction(conjunction(comparison('<=',5),comparison('>=',5)),{'x'}))
    def test_three_terms(self):
        proof=contradiction(conjunction(comparison('>=',5),comparison('<=',5),comparison('==',6)),{'x'})
        self.assertGreater(proof['intersection_lower'],proof['intersection_upper'])
    def test_different_declaration_ids_are_not_same_value(self):
        self.assertIsNone(contradiction(conjunction(comparison('<',5),comparison('>',10,'y')),{'x','y'}))
    def test_unsigned_and_volatile_abstain(self):
        for type in ('unsigned int','volatile int','_Atomic(int)'):
            a=comparison('<',5);a['inner'][0]=ref(type=type)
            self.assertIsNone(contradiction(conjunction(a,comparison('>',10)),{'x'}))
    def test_unsigned_conversion_abstains(self):
        a=comparison('<',5);a['inner'][1]=literal(5,'unsigned int')
        self.assertIsNone(contradiction(conjunction(a,comparison('>',10)),{'x'}))
    def test_side_effect_abstains(self):
        a=comparison('<',5);a['inner'][0]={'kind':'UnaryOperator','opcode':'++','inner':[ref()]}
        self.assertIsNone(contradiction(conjunction(a,comparison('>',10)),{'x'}))
    def test_term_budget(self):
        self.assertIsNone(contradiction(conjunction(*[comparison('==',i) for i in range(9)]),{'x'}))
    def test_precision_is_not_a_zero_or_exact_division_check(self):
        self.assertIsNotNone(precision(division(ref('a'),ref('b')),{'a','b'}))
        self.assertIsNone(precision(division(literal(6),literal(3)),set()))
        self.assertIsNone(precision(division(ref('a'),literal(0)),{'a'}))
    def test_explicit_division_cast_abstains(self):
        n=division(ref('a'),ref('b'));n['inner'][0]={'kind':'CStyleCastExpr','inner':n['inner']}
        self.assertIsNone(precision(n,{'a','b'}))
    def test_fixed_input_bounds_include_nul(self):
        self.assertEqual(input_capacity(scanf('%4s'),{'buffer'},{'scanf'})['maximum_required_bytes'],5)
        self.assertIsNone(input_capacity(scanf('%3s'),{'buffer'},{'scanf'}))
        self.assertIsNone(input_capacity(scanf('%4c'),{'buffer'},{'scanf'}))
    def test_unknown_capacity_and_callee_do_not_match(self):
        self.assertIsNone(input_capacity(scanf('%s'),{'buffer'},set()))
        n=scanf('%s');n['inner'][2]=ref('buffer','char *')
        self.assertIsNone(input_capacity(n,{'buffer'},{'scanf'}))
    def test_suppressed_and_zero_width_abstain(self):
        for fmt in ('%*s','%0s','%ls','%s%s'):
            self.assertIsNone(input_capacity(scanf(fmt),{'buffer'},{'scanf'}))
    def test_malformed_tree_is_rejected(self):
        with self.assertRaises((ValueError,KeyError)):scan({'kind':'Unknown'},'x.c',b'int x;')
    def test_invalid_cli_limits(self):
        from .__main__ import main
        from io import StringIO
        from contextlib import redirect_stderr
        with redirect_stderr(StringIO()),self.assertRaises(SystemExit) as r:main(['missing.c','--max-findings','129'])
        self.assertEqual(r.exception.code,2)
    def test_half_open_boundary_at_inserted_semicolon_maps_to_anchor(self):
        from .engine import original_boundary
        edits=[{'original_offset':10}]
        self.assertEqual(original_boundary(10,edits),10)
        self.assertEqual(original_boundary(11,edits),10)
        self.assertEqual(original_boundary(15,edits),14)
    def test_conditioned_evidence_export_rejected(self):
        from .evaluation import export_run
        for key in ('repair_conditioned','isolation_conditioned'):
            provenance={'repair_conditioned':False,'isolation_conditioned':False};provenance[key]=True
            with self.assertRaisesRegex(ValueError,'conditioned'):export_run({'provenance':provenance},'s')


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler=shutil.which('clang');cls.capability=None
        if not cls.compiler:raise unittest.SkipTest('Clang unavailable on test PATH; use validation --compiler')
    def run_case(self,name,**kwargs):
        p=HERE/'fixtures'/(name+'.c');before=p.read_bytes()
        r=run_semantics(p,compiler=self.compiler,capability=self.__class__.capability,**kwargs)
        if r['upstream']['capabilities']:self.__class__.capability=r['upstream']['capabilities']
        self.assertEqual(p.read_bytes(),before);self.assertTrue(r['source']['original_unchanged']);self.assertTrue(r['temporary_workspace_removed'])
        self.assertLessEqual(r['usage']['compiler_invocations'],r['usage']['limits']['invocations'])
        self.assertLessEqual(r['usage']['analyzer_invocations'],r['usage']['limits']['analyzer_invocations'])
        return r
    def test_disabled_by_default(self):
        r=self.run_case('contradiction_three_bad');self.assertEqual(r['status'],'not_attempted');self.assertFalse(r['findings'])
    def test_existing_condition_warning_not_new_root(self):
        r=self.run_case('contradiction_bad',enabled=True);self.assertEqual(r['status'],'completed',r['reason'])
        self.assertTrue(r['findings'][0]['duplicate_of_existing'])
    def test_three_term_proof_and_backend_evidence(self):
        r=self.run_case('contradiction_three_bad',enabled=True);self.assertEqual(r['status'],'completed',r['reason'])
        f=r['findings'][0];self.assertEqual(f['confidence'],'proven_predicate_false');self.assertFalse(f['duplicate_of_existing'])
        if r['checker_capability']['supported']:self.assertTrue(any(d['diagnostic_id']==CHECKER for d in f['backend_witnesses']))
    def test_corrected_conditions_and_value_controls(self):
        for name in ('contradiction_good','contradiction_three_good','contradiction_boundary_good','different_variables','volatile_control','side_effect_control','conversion_control','unsigned_control'):
            r=self.run_case(name,enabled=True);self.assertFalse(r['findings'],name)
    def test_macro_conditions_and_precision_abstain(self):
        for name in ('macro_control','precision_macro'):
            r=self.run_case(name,enabled=True);self.assertFalse(r['findings'])
    def test_scanf_evidence_and_safe_controls(self):
        for name,expected in (('scanf_unbounded',1),('scanf_width_bad',1),('scanf_good',0),('scanf_unknown',0),('scanf_suppressed',0),('scanf_character_good',0),('scanf_local_name',0)):
            r=self.run_case(name,enabled=True);self.assertEqual(len(r['findings']),expected,(name,r['reason']))
            if expected:self.assertEqual(r['findings'][0]['confidence'],'review_suggestion')
    def test_precision_context_is_suggestion(self):
        for name,expected in (('precision_review',1),('precision_literal_review',1),('precision_good',0),('precision_deliberate',0),('precision_exact',0),('precision_zero',0),('precision_integer_control',0)):
            r=self.run_case(name,enabled=True);self.assertEqual(len(r['findings']),expected,name)
            if expected:self.assertFalse(r['findings'][0]['confirmed_programmer_intent_bug'])
    def test_malformed_frontend_blocks_custom_scan(self):
        for name in ('malformed_semantic','malformed_syntax'):
            r=self.run_case(name,enabled=True);self.assertEqual(r['status'],'blocked');self.assertIsNone(r['inventory']);self.assertFalse(r['findings'])
    def test_isolation_provenance_retained(self):
        r=self.run_case('malformed_semantic',enabled=True,isolate=True)
        self.assertTrue(r['provenance']['isolation_conditioned'],r['reason']);self.assertTrue(r['findings'])
        self.assertTrue(all(f['provenance']['isolation_conditioned'] for f in r['findings']))
    def test_timeout_and_budget_stop(self):
        with patch('phase6.v6.engine.ast',side_effect=LimitReached('compiler call timed out')):
            r=self.run_case('valid',enabled=True)
        self.assertEqual(r['status'],'timed_out');self.assertFalse(r['findings'])
        r=self.run_case('valid',enabled=True,limits=DetectionLimits(invocations=1))
        self.assertFalse(r['findings']);self.assertIn(r['status'],('failed','budget_exhausted'))
    def test_missing_checker_does_not_fabricate_backend_witness(self):
        from phase6.v6 import engine
        with patch.object(engine,'CHECKER','alpha.nonexistent.Test'):
            r=self.run_case('contradiction_three_bad',enabled=True)
        self.assertFalse(r['checker_capability']['advertised']);self.assertIsNone(r['additional_backend'])
        self.assertEqual(r['findings'][0]['backend_witnesses'],[])
    def test_json_unicode_spaces_crlf(self):
        from .__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory(prefix='semantic space ') as work:
            p=Path(work)/'é input.c';data=('/* é */\r\n'+(HERE/'fixtures/precision_review.c').read_text()).replace('\r\r\n','\r\n').encode();p.write_bytes(data);out=StringIO()
            with redirect_stdout(out):code=main([str(p),'--compiler',self.compiler,'--semantic-analysis','--json'])
            r=json.loads(out.getvalue());self.assertEqual(code,0);self.assertEqual(p.read_bytes(),data)
            self.assertEqual(r['findings'][0]['evidence']['original_location']['line'],2)
