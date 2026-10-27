import unittest
from smartparse import Parser, tokenize

class Phase5FIntegrationTests(unittest.TestCase):
    def parse(self, source, **kwargs):
        p = Parser(tokenize(source), verified_cgar=True, **kwargs)
        p.parse()
        return p

    def test_two_distant_errors(self):
        p = self.parse('int x = 1 if (x > 0] { x = 2; }')
        self.assertEqual(p.verified_cgar_status, 'verified_candidate')
        self.assertEqual(len(p.repairs), 2)
        self.assertTrue(all(r['verified_cgar'] for r in p.repairs))

    def test_operator_repair(self):
        p = self.parse('int x == 1;')
        self.assertEqual(p.verified_cgar_status, 'verified_candidate')
        self.assertIn('=', p.repairs[0]['token'])

    def test_source_not_mutated(self):
        tokens = tokenize('int x = 1 if (x > 0] { x = 2; }')
        snapshot = tuple(tokens)
        p = Parser(tokens, verified_cgar=True)
        p.parse()
        self.assertEqual(tuple(tokens), snapshot)

    def test_unsupported_falls_back(self):
        p = self.parse('int x = ;')
        self.assertEqual(p.verified_cgar_status, 'abstain')
        self.assertGreater(len(p.diagnostics), 0)

    def test_valid_code(self):
        p = self.parse('int x = 1;')
        self.assertEqual(p.verified_cgar_status, 'unchanged')
        self.assertEqual(p.repairs, [])
        self.assertEqual(p.diagnostics, [])

    def test_ambiguous_valid_code_unchanged(self):
        p = self.parse('int x = 1;;')
        self.assertEqual(p.verified_cgar_status, 'ambiguous_valid')
        self.assertEqual(p.repairs, [])

    def test_default_mode_unaffected(self):
        p = Parser(tokenize('int x = 1;'))
        p.parse()
        self.assertEqual(p.verified_cgar_status, 'not_attempted')

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            Parser(tokenize('int x;'), verified_cgar=True, verified_max_nodes=0)

if __name__ == '__main__': unittest.main()
