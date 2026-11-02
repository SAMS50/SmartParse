import json
from pathlib import Path
import unittest
from .evaluate import fingerprint


class FrozenEvaluationTests(unittest.TestCase):
    def test_new_families_are_not_exposed_or_development(self):
        root=Path(__file__).parent
        data=json.loads((root/'sample-manifest.json').read_text(encoding='utf-8'))['cases']
        old=json.loads((root.parent/'v13/sample-manifest.json').read_text(encoding='utf-8'))['cases']
        new=[r for r in data if r['split']=='independent']
        self.assertEqual(len(new),80)
        self.assertFalse({r['id'] for r in new}&{r['id'] for r in old})
        self.assertFalse({r['family'] for r in new}&{r['family'] for r in old})
        self.assertFalse({r['canonical_source_sha256'] for r in new}&{r['canonical_source_sha256'] for r in old})
        self.assertEqual(len({r['id'] for r in data}),len(data))

    def test_calibration_fingerprint_is_frozen(self):
        selection=json.loads(Path(__file__).with_name('selection.json').read_text(encoding='utf-8'))
        self.assertEqual(selection['algorithm_fingerprint'],fingerprint())
        self.assertIn(selection['max_edit_hunks'],(1,2));self.assertEqual(selection['development_primary'],20)
