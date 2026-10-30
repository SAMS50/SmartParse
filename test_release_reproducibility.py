"""Portable integrity checks without weakening historical byte snapshots."""
import json
from pathlib import Path
import tempfile
import unittest
from phase6.v9.release import canonical_bytes,digest,excluded,relative,verify,ROOT


class ReleaseReproducibilityTests(unittest.TestCase):
    def test_legacy_line_endings_equivalent(self):
        self.assertEqual(digest(b'int a;\r\n','git-text-lf'),digest(b'int a;\n','git-text-lf'))

    def test_canonical_comparison_detects_content_changes(self):
        self.assertNotEqual(digest(b'int a;\r\n','git-text-lf'),digest(b'int b;\n','git-text-lf'))

    def test_exact_comparison_retains_crlf_difference(self):
        self.assertNotEqual(digest(b'a\r\n'),digest(b'a\n'))

    def test_no_whitespace_or_encoding_normalization(self):
        self.assertEqual(canonical_bytes(b'\xef\xbb\xbf a \r\n'),b'\xef\xbb\xbf a \n')

    def test_windows_manifest_separators(self):
        self.assertEqual(relative(ROOT,'phase6\\v8\\freeze.json'),ROOT/'phase6/v8/freeze.json')

    def test_unsafe_manifest_paths_rejected(self):
        for name in ('../outside','C:\\outside','/outside'):
            with self.subTest(name=name),self.assertRaises(ValueError):relative(ROOT,name)

    def test_missing_release_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            r=verify(Path(directory),dict(files={'missing.json':dict(policy='exact',sha256='bad')}))
            self.assertFalse(r['preserved']);self.assertEqual(r['missing'],['missing.json'])

    def test_tampered_release_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data';path.write_bytes(b'changed')
            r=verify(Path(directory),dict(files={'data':dict(policy='exact',sha256=digest(b'original'))}))
            self.assertFalse(r['preserved']);self.assertEqual(r['changed'],['data'])

    def test_empty_logs_and_runtime_outputs_excluded(self):
        self.assertTrue(excluded('phase6/v8/outputs/extended/clang/case.log'))
        self.assertTrue(excluded('phase6/v9/reproducibility/runs/private/report.json'))
        self.assertFalse(excluded('phase6/v8/outputs/extended/clang/case.json'))

    def test_portable_manifest_has_no_local_acceptance_dependency(self):
        m=json.loads((ROOT/'phase6/v9/release_manifest.json').read_text())
        self.assertNotIn('acceptance/output/broken_records.json',m['files'])
        self.assertFalse(any(excluded(n) for n in m['files']))

    def test_frozen_manifest_unchanged_and_accessible(self):
        from phase6.v8.prepare import verify_freeze
        self.assertEqual(verify_freeze(),46)

    def test_manifest_includes_golden_reports_and_legacy_assertions(self):
        m=json.loads((ROOT/'phase6/v9/release_manifest.json').read_text())
        self.assertIn('phase6/v8/outputs/extended/extended_baseline/C01_null.json',m['files'])
        self.assertEqual(set(m['legacy_compatibility']),{'smartparse.py','baseline.py','analyze_c.py'})

    def test_historical_loader_fingerprints_unchanged(self):
        from phase6.v1.evaluate_saved import load_inputs
        from phase6.v1.evaluation import fingerprint
        index=json.loads((ROOT/'phase6/v9/legacy_evidence.json').read_text())
        data,runs=load_inputs()
        self.assertEqual(fingerprint(data),index['dataset_fingerprint'])
        self.assertEqual(fingerprint(runs),index['runs_fingerprint'])

    def test_legacy_copies_have_exact_original_hashes(self):
        index=json.loads((ROOT/'phase6/v9/legacy_evidence.json').read_text())
        for entry in index['reports'].values():
            self.assertEqual(digest((ROOT/entry['file']).read_bytes()),entry['sha256'])


if __name__=='__main__':unittest.main()
