import unittest
from .history import replay, score


class HistoryTests(unittest.TestCase):
    def test_replay_and_score(self):
        h=dict(base_source='a😀;',base_version=2,source_version=3,
               events=[dict(version=3,offset=2,deleted=';',inserted='')])
        snapshots,reason=replay('a😀',h)
        self.assertEqual(snapshots,['a😀;','a😀'])
        self.assertGreater(score('a😀','a😀;',snapshots)['score'],0)
        h['events'][0]['offset']=1
        self.assertEqual(replay('a😀',h)[0],[])

    def test_missing_and_version(self):
        self.assertEqual(score('a','b',[])['score'],0)
        self.assertEqual(replay('b',dict(base_source='a',base_version=0,source_version=2,
            events=[dict(version=2,offset=0,deleted='a',inserted='b')]))[0],[])


if __name__=='__main__':unittest.main()
