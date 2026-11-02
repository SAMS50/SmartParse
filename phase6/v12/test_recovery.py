import unittest
from phase6.v11.history import reconstruct
from .history import assess
from .candidates import supplemental
from .engine import recover
from .semantics import Validator, projection, compare


class ReliabilityTests(unittest.TestCase):
    def test_incomplete_and_malformed(self):
        for h in ({}, {'events':[{}]}, {'base_source':'a','base_version':0,'source_version':2,'events':[]}):
            snapshots,r=assess('b',h)
            self.assertFalse(r['mapping_verified']);self.assertEqual(snapshots,[])
        self.assertTrue(assess('b',None)[1]['mapping_verified'])

    def test_lexical_delimiters_and_budget(self):
        self.assertEqual(supplemental('int f(){char *s="}"; /* } */ return 0;', '')[0][0],
                         'int f(){char *s="}"; /* } */ return 0;}')
        self.assertLessEqual(len(supplemental('int f(){if(1){return 0;', '')),4)
        self.assertEqual(supplemental('#define X {\nint f(){return 0;',''),[])


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        if not Validator().compiler:self.skipTest('Clang unavailable')

    def test_misleading_boundary_abstains(self):
        good='int f(int x){if(x){x++;}return x;}'
        stale='int f(int x){if(x){x++;return x;}}';bad=good.replace('}return','return')
        r=recover(bad,reconstruct(stale,bad))
        self.assertIsNone(r['recommendation']);self.assertIn('End-of-source',r['reason'])
        supported=recover(bad,reconstruct(good,bad))
        self.assertEqual(supported['decision'],'recommended repair')

    def test_reference_free_unique_repair(self):
        good='int sum(int x){int y=2;return x+y;}'
        bad=good.replace(';','')
        r=recover(bad)
        self.assertEqual(r['decision'],'recommended repair',r['reason'])
        c=next(c for c in r['candidates'] if c['id']==r['recommendation'])
        self.assertEqual(c['source'],good)
        self.assertTrue(all(x['status']=='UNKNOWN' for x in c['semantic'].values()))
        self.assertIn('consensus',r['evidence_basis'])

    def test_missing_history_ambiguity_and_pointer(self):
        self.assertIsNone(recover('int f(int x){if(x){x++;return x;}')['recommendation'])
        r=recover('int f(int *p){return *p;')
        self.assertTrue(any(c['source']=='int f(int *p){return *p;}' for c in r['candidates']))
        self.assertIsNone(r['recommendation'])

    def test_globals_binding_ownership_and_function_inventory(self):
        v=Validator()
        def p(s):return projection(s,v.inspect(s))
        a=p('int g=0;int f(int x){if(x)g++;return g;}')
        b=p('int g=0;int f(int x){if(x){}g++;return g;}')
        self.assertIsNotNone(a)
        for key in ('statement_ownership','control_flow','function_boundaries'):
            self.assertEqual(compare(a,b)[key]['status'],'CHANGED')
        self.assertEqual(compare(a,a)['variable_binding']['status'],'PRESERVED')
        self.assertIsNone(p('int *g;int f(){return 0;}'))

    def test_broad_contradictory_and_deterministic(self):
        good='int f(){return 1;}'
        bad='int f(){return 1'
        h=reconstruct('int obsolete(){return 99;}',bad)
        self.assertIsNone(recover(bad,h)['recommendation'])
        # An earlier restorable version cannot override a newer valid, different literal.
        h=dict(base_source=good,base_version=0,source_version=2,events=[
            dict(version=1,offset=15,deleted='1',inserted='2'),
            dict(version=2,offset=16,deleted=';',inserted='')])
        source='int f(){return 2}'
        a=recover(source,h);b=recover(source,h)
        self.assertEqual(a['recommendation'],b['recommendation'])
        if a['recommendation']:
            self.assertEqual(next(c['source'] for c in a['candidates'] if c['id']==a['recommendation']),'int f(){return 2;}')
        self.assertEqual(len(a['candidates']),len({c['source'] for c in a['candidates']}))
        self.assertTrue(a['original_unchanged'])


if __name__=='__main__':unittest.main()
