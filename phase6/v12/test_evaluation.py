import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from .evaluate import main,fingerprint


class EvaluationIntegrityTests(unittest.TestCase):
    def test_changed_algorithm_refuses_heldout(self):
        with tempfile.TemporaryDirectory() as folder:
            selection=Path(folder)/'selection.json'
            selection.write_text(json.dumps(dict(algorithm_fingerprint='changed',margin=12)))
            with patch.object(sys,'argv',['evaluate','--split','heldout','--selection',str(selection),'--output',str(Path(folder)/'unused.json')]):
                with self.assertRaisesRegex(ValueError,'changed since development'):main()

    def test_records_reconcile_and_share_ablation_pool(self):
        root=Path(__file__).parent/'results'
        for name in ('development','heldout','historical'):
            data=json.loads((root/(name+'.json')).read_text(encoding='utf-8'))
            self.assertEqual(data['algorithm_fingerprint'],fingerprint())
            self.assertEqual(len(data['cases']),data['samples'])
            for summary in data['systems'].values():
                self.assertEqual(sum(summary[key]['numerator'] for key in ('exact','wrong','abstained')),data['samples'])
            for row in data['cases']:
                for version in ('v11','v12'):
                    pools=[{c['id'] for c in row['systems'][version+'-'+mode]['candidates']} for mode in ('existing','history','semantic','full')]
                    self.assertTrue(all(p==pools[0] for p in pools))
                    expected=row['systems'][version+'-full'];actual=row['full_system_decisions'][version]
                    self.assertEqual([expected[k] for k in ('exact','wrong','recommended')],[actual[k] for k in ('exact','wrong','recommended')])
