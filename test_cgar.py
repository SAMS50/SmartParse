import unittest
from smartparse import Parser, tokenize
from cgar import search

class CGARTests(unittest.TestCase):
    def parse(self, source, **kwargs):
        parser = Parser(tokenize(source), validate_repairs=False,
                        adaptive_recovery=True, **kwargs)
        parser.parse()
        return parser

    def test_three_edit_case(self):
        p = self.parse('if (x > 1 ; , ] { x = 2; }')
        edits = [(r['operation'], r['from']) for r in p.repairs if r.get('adaptive_recovery')]
        self.assertEqual(edits, [('delete', ';'), ('delete', ','), ('substitute', ']')])
        self.assertEqual(p.adaptive_stats['accepted'], 1)

    def test_two_edit_case(self):
        p = self.parse('if (x > 1 ; ] { x = 2; }')
        self.assertEqual(len([r for r in p.repairs if r.get('adaptive_recovery')]), 2)

    def test_budget_limit(self):
        p = self.parse('if (x > 1 ; , ] { x = 2; }', recovery_max_edits=2)
        self.assertEqual(p.adaptive_stats['accepted'], 0)

    def test_source_preserved(self):
        source='if (x > 1 ; , ] { x = 2; }'
        tokens=tokenize(source)
        before=tuple(t.value for t in tokens)
        p=Parser(tokens, adaptive_recovery=True)
        p.parse()
        self.assertEqual(before,tuple(t.value for t in tokens))

    def test_does_not_delete_identifiers(self):
        p=self.parse('if (x > 1 y ] { x = 2; }')
        self.assertEqual(p.adaptive_stats['accepted'],0)

    def test_no_edit_valid(self):
        p=self.parse('if (x > 1) { x = 2; }')
        self.assertEqual(p.repairs,[])

    def test_reject_invalid_budgets(self):
        with self.assertRaises(ValueError):
            Parser(tokenize('int x;'),adaptive_recovery=True,recovery_max_edits=0)

if __name__=='__main__': unittest.main()
