import unittest
from .engine import recover, generate, rank, Config, MODES
from .semantics import Validator, projection


def history(before,after):
    from .engine import edits
    changes=edits(before,after)
    # One aggregate replacement supports any reconstructed edit.
    a=min(c['offset'] for c in changes);b=max(c['end_offset'] for c in changes)
    tail=len(before)-b
    return dict(base_source=before,base_version=0,source_version=1,
                events=[dict(version=1,offset=a,deleted=before[a:b],inserted=after[a:len(after)-tail if tail else len(after)])])


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


if __name__=='__main__':unittest.main()
