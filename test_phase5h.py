import unittest
from demo import EXAMPLES, run

class FinalReleaseTests(unittest.TestCase):
    def test_demo_verified_multi_error(self):
        p = run(EXAMPLES['multiple'], verified=True)
        self.assertEqual(p.verified_cgar_status, 'verified_candidate')
        self.assertEqual(len(p.repairs), 2)
    def test_demo_unsupported_fallback(self):
        p = run(EXAMPLES['unsupported'], verified=True)
        self.assertEqual(p.verified_cgar_status, 'abstain')
        self.assertGreater(len(p.diagnostics), 0)
    def test_demo_default_unchanged(self):
        p = run(EXAMPLES['valid'])
        self.assertEqual(p.verified_cgar_status, 'not_attempted')
        self.assertEqual(len(p.diagnostics), 0)
    def test_demo_valid_ambiguous(self):
        p = run(EXAMPLES['ambiguous'], verified=True)
        self.assertEqual(p.verified_cgar_status, 'ambiguous_valid')
        self.assertEqual(len(p.repairs), 0)
if __name__ == '__main__': unittest.main()
