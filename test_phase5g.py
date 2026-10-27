import unittest
from phase5g_eval import MODES, evaluate, summary, run_one

class Phase5GTests(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(len(MODES),4)
    def test_invalid_repeats(self):
        with self.assertRaises(ValueError): evaluate(0)
    def test_frozen_cases_all_modes(self):
        rows=evaluate(1)
        self.assertEqual(len(rows),64)
        self.assertEqual(len(summary(rows)),4)
    def test_valid_semicolons_not_an_error(self):
        for mode in MODES:
            r=run_one(mode,'int x = 1;;')
            self.assertEqual(r['detected'],0,mode)
    def test_verified_multiple_errors(self):
        r=run_one('integrated_cgar','int x = 1 if (x > 0] { x = 2; }')
        self.assertEqual(r['status'],'verified_candidate')
        self.assertIsNotNone(r['corrected'])
    def test_unsupported_fallback(self):
        r=run_one('integrated_cgar','int x = ;')
        self.assertTrue(r['fallback'])
        self.assertGreater(r['diagnostics'],0)

if __name__=='__main__': unittest.main()
