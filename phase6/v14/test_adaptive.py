import unittest
from unittest.mock import patch
from copy import deepcopy
from phase6.v11.history import reconstruct
from phase6.v12.history import assess
from phase6.v12.semantics import Validator
from phase6.v13.ingest import sha
from .engine import recover,prepare
from .policy import decide,Policy,MODES
from .providers import mask_directives,normalized_edits,select_pool
from .semantics import analyze


def candidate(status='UNSUPPORTED',inserted=';'):
    text='int x'+inserted
    return dict(id=sha(text)[:16],source=text,heuristic=35,origins=['clang_fixit'],origin='clang_fixit',
                token_program_sha256=sha(text),changes=[dict(offset=5,end_offset=5,line=1,column=6,deleted='',inserted=inserted)],
                validation=dict(status='VALID',reason=''),semantic_risk=dict(status=status,reason='test structural evidence',checks={}))


class DecisionTests(unittest.TestCase):
    def test_explicit_evidence_modes(self):
        snapshots,r=assess('int x',reconstruct('int x;','int x'))
        for sem,history,expected in [('NO_DETECTED_STRUCTURAL_CHANGE',True,'FULL_EVIDENCE'),
                                      ('NO_DETECTED_STRUCTURAL_CHANGE',False,'SEMANTIC_EVIDENCE'),
                                      ('UNSUPPORTED',True,'HISTORY_EVIDENCE'),('UNSUPPORTED',False,'SYNTAX_ONLY')]:
            result=decide('int x',[candidate(sem)],snapshots if history else [],r)
            self.assertEqual(result['decision_mode'],expected)
            self.assertIsNotNone(result['recommendation'])

    def test_unavailable_is_not_failed_or_changed(self):
        _,r=assess('int x',None)
        for status in ('UNKNOWN','UNSUPPORTED'):
            self.assertEqual(decide('int x',[candidate(status)],[],r)['decision_mode'],'SYNTAX_ONLY')
        for status in ('VERIFIED_STRUCTURAL_CHANGE','CHECK_FAILED'):
            for semantic in (True,False):
                decision=decide('int x',[candidate(status)],[],r,use_semantic=semantic)
                self.assertIsNone(decision['recommendation']);self.assertIn('blocked',decision['reason'])

    def test_invalid_ambiguous_and_mapping_failure(self):
        _,r=assess('int x',None);a=candidate();b=candidate(inserted=',')
        result=decide('int x',[a,b],[],r)
        self.assertEqual(result['outcome'],'suggested alternatives');self.assertIsNone(result['recommendation'])
        a['validation']['status']='UNVERIFIED';result=decide('int x',[a],[],r)
        self.assertEqual(result['outcome'],'abstention');self.assertEqual(len(result['unverified_suggestions']),1)
        self.assertFalse(result['alternatives'])
        a=candidate();r['mapping_verified']=False
        self.assertIsNone(decide('int x',[a],[],r)['recommendation'])

    def test_missing_evidence_score_zero_and_bounded_policy(self):
        _,r=assess('int x',None);d=decide('int x',[candidate()],[],r)
        c=d['candidates'][0]
        self.assertEqual(c['components']['history'],0);self.assertEqual(c['components']['structural_agreement'],0)
        self.assertIsNone(decide('int x',[candidate(inserted='}')],[],r)['recommendation'])


class ProviderTests(unittest.TestCase):
    def setUp(self):
        if not Validator().compiler:self.skipTest('Clang unavailable')

    def test_real_header_recovery_origin_and_preservation(self):
        source='#include <stdio.h>\nint main(){return 0}\n'
        saved=source;r=recover(source)
        self.assertEqual(r['decision_mode'],'SYNTAX_ONLY',r['reason'])
        c=next(c for c in r['candidates'] if c['id']==r['recommendation'])
        self.assertIn('clang_fixit',c['origins']);self.assertEqual(c['source'],source.replace('0}','0;}'))
        self.assertEqual(source,saved);self.assertTrue(r['original_unchanged'])
        self.assertEqual(len(r['candidates']),len({c['source'] for c in r['candidates']}))

    def test_protected_header_and_edit_replay(self):
        original='#include <stdio.h>\nint x\n';masked,restore=mask_directives(original)
        self.assertEqual(restore(masked),original)
        with self.assertRaises(ValueError):restore('#oops\nint x\n')
        with self.assertRaises(ValueError):normalized_edits(original,original.replace('stdio','stdlib'))
        edits=normalized_edits(original,original.replace('int x','int x;'))
        self.assertEqual(edits[0]['line'],2);self.assertEqual(edits[0]['start_byte'],len(original[:edits[0]['offset']].encode()))

    def test_structural_veto_for_new_empty_body(self):
        # Clang accepts this repair, but it introduces an empty control body.
        source='int f(int x){if(x)\n}'
        repaired='int f(int x){if(x);\n}'
        v=Validator();checked=v.inspect(repaired)
        c=dict(source=repaired,changes=normalized_edits(source,repaired),validation={'status':checked['status']},_tree=checked['tree'])
        self.assertEqual(analyze(source,c)['status'],'VERIFIED_STRUCTURAL_CHANGE')

    def test_unsafe_prior_snapshot_is_not_compiled(self):
        source='int x';h=reconstruct('#include "/private/secret.h"\nint x;',source)
        with patch('phase6.v14.engine.reference_for') as reference:
            result=recover(source,h)
            reference.assert_not_called()
        self.assertIsNone(result['recommendation'])
        self.assertIn('historical snapshot',result['reason'])

    def test_valid_history_and_unknown_behavior(self):
        good='int f(int x){if(x){x++;}return x;}'
        bad=good.replace('}return','return');r=recover(bad,reconstruct(good,bad))
        self.assertEqual(r['decision_mode'],'FULL_EVIDENCE',r['reason'])
        _,_,_,_=prepare(bad)
        pool=[dict(origins=['clang_fixit']),dict(origins=['smartparse_custom']),dict(origins=['clang_fixit','smartparse_custom'])]
        self.assertEqual(len(select_pool(pool,'compiler')),2);self.assertEqual(len(select_pool(pool,'custom')),2)


if __name__=='__main__':unittest.main()
