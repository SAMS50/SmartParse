import unittest
from .dataset import manifest,canonical


class DatasetTests(unittest.TestCase):
    def test_split_dedup_and_determinism(self):
        data=manifest();self.assertEqual(data,manifest())
        self.assertGreaterEqual(sum(map(len,data.values())),70)
        self.assertFalse({c['family'] for c in data['development']}&{c['family'] for c in data['heldout']})
        for rows in data.values():
            self.assertEqual(len(rows),len({c['source_fingerprint'] for c in rows}))
        self.assertEqual(canonical('int alpha(int x){return x+1;}'),canonical('int beta(int y){return y+2;}'))
