import unittest
from .engine import recover, generate, rank, Config, MODES
from .semantics import Validator, projection
from .history import reconstruct as history


class EngineTests(unittest.TestCase):
    def setUp(self):
        if not Validator().compiler:self.skipTest('Clang unavailable')

    def test_restore_and_determinism(self):
        good='int f(int x){if(x){x++;}return x;}'
        bad=good.replace('}return','return')
        h=history(good,bad)
        a=recover(bad,h);b=recover(bad,h)
        self.assertEqual(a['recommendation'],b['recommendation'])
        self.assertEqual(a['decision'],'recommended repair')
        self.assertEqual(next(c['source'] for c in a['candidates'] if c['id']==a['recommendation']),good)
        self.assertTrue(a['original_unchanged'])
        self.assertEqual(len({c['source'] for c in a['candidates']}),len(a['candidates']))
        self.assertTrue(any(c['validation']['status']=='INVALID' for c in a['candidates']))

    def test_missing_unreliable_unsupported(self):
        bad='int f(){return 1;'
        self.assertIsNone(recover(bad)['recommendation'])
        self.assertIsNone(recover(bad,dict(base_source='',base_version=0,source_version=1,events=[]))['recommendation'])
        self.assertIsNone(recover('int f(int *p){return *p;',history('int f(int *p){return *p;}','int f(int *p){return *p;'))['recommendation'])

    def test_ambiguous_and_modes(self):
        v=Validator();source='int f(int x){if(x){x++;return x;}'
        candidates,_=generate(source,v)
        self.assertGreaterEqual(sum(c['validation']['status']=='VALID' for c in candidates),2)
        # Equal weights deliberately expose ties and exercise abstention.
        for c in candidates:c['heuristic']=10
        for mode in MODES:
            r=rank(source,candidates,[],None,mode)
            if mode!='existing':self.assertIsNone(r['recommendation'])
        self.assertEqual(rank(source,candidates,[],None)['decision'],'ambiguous repair')

    def test_misleading_history_is_evidence_not_correctness(self):
        intended='int f(int x){if(x){x++;}return x;}'
        stale='int f(int x){if(x){x++;return x;}}'
        bad=intended.replace('}return','return')
        r=recover(bad,history(stale,bad))
        self.assertTrue(all('does not prove correctness' in c['explanation'] for c in r['candidates']))
        self.assertIn(r['decision'],('recommended repair','ambiguous repair','no safe recommendation','unsupported repair'))

    def test_budget_and_valid_original(self):
        self.assertEqual(recover('x'*16385)['decision'],'unsupported repair')
        self.assertEqual(recover('int f(){return 0;}')['candidates'],[])


if __name__=='__main__':unittest.main()
