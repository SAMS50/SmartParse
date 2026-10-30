# Portable validation and historical audits

`release_manifest.json` is a separate release-payload manifest. Its relative paths enumerate every required distributed file; missing or changed files fail validation. It does not use the old workstation inventory as a list of files a clone must have. The manifest declares its own required, parseable path separately to avoid a self-referential hash.

The payload contains established Git-tracked files plus explicit v8, v9 and CLI additions. It excludes untracked legacy acceptance outputs, 147 empty v8 worker logs, redundant summaries/backups, bytecode, private snapshots and new runtime runs. Substantive analyzer JSON, supervisor records, figures, review evidence and the test-consumed golden reports remain included.

The older v1 regression additionally needs two raw acceptance reports. Exact-byte copies are now explicitly versioned under `fixtures/legacy_acceptance/`, with pinned hashes/source identity in `legacy_evidence.json`. The loader resolves those copies without rewriting their original paths or raw records. Original dataset/run fingerprints and all adjudication/evaluation rules remain unchanged. No original untracked acceptance output is required. The cleaned benchmark and older reference-bound C fixtures have explicit LF checkout policies matching their established reference hashes; the deliberate v3 CRLF fixture retains CRLF.

New frozen v8 artifacts and archived v9 outputs use exact-byte hashes and scoped `-text` attributes. Their actual mixed LF/CRLF bytes are retained. Ordinary existing Git text and new release code use canonical CRLF-to-LF content hashes, not whitespace, encoding or token normalization. Binary artifacts retain exact hashes. This permits the Git normalization already present in older history without rewriting that history. The three legacy implementation assertions bind canonical content to the established HEAD blobs and still reject every non-line-ending change.

```powershell
python -m phase6.v9.release
python -m unittest test_release_reproducibility test_smartparse_cli -v
python -m phase6.v9.validate --label portable
python -m phase6.v9.smoke
python -m phase6.v9.fresh_checkout
```

Validation writes unique directories under ignored `phase6/v9/reproducibility/runs/`; it does not overwrite archived M8/M9 evidence. Full validation checks the portable manifest before and after tests and checks exact actual-checkout bytes before/after. The legacy performance test's CSV bytes are restored in `finally`.

`fresh_checkout` creates a private Git object store and index, reads existing HEAD objects without changing them, adds only the explicit release payload in that private index, and uses Git `checkout-index` with both `core.autocrlf=true` and `false`. It creates no commits, does not touch the real index and copies no arbitrary untracked files. It checks the manifest and CLI in both checkouts and runs `python -m unittest discover -v` in the CRLF-configured checkout. Linux itself is not available in this Windows validation; the LF checkout and cross-platform path tests are not a fabricated Linux live run.

Source-repository queries disable optional Git lock/cache writes. The harness compares exact staged index entries before/after and separately reports the byte-cache hash, which can change when an IDE refreshes file statistics without staging. `--no-suite` runs the affected historical tests and compatibility tests in both checkout modes in addition to the CLI checks.

The archived `outputs/protected_hashes.json`, M8 freeze, old reports and pending human decisions remain unchanged. A strict original-workstation check remains available:

```powershell
python -m phase6.v9.validate --historical-audit
```

That audit intentionally fails when original local evidence is missing or authorized later release-tool files differ. It is not the portable release criterion and does not silently ignore missing files. Use the original snapshot plus the new task's explicit changed-file audit to assess historical preservation after these authorized fixes.

`python -m phase6.v9.release --build` is a maintainer operation after deliberately reviewing release membership/content. It updates only the new portable manifest, never a historical snapshot or evaluation result. Ordinary validation never rebuilds its oracle.

Archived reports contain personal Windows paths, installed versions and temporary paths. They provide provenance, not credentials or independent verification. Publish them unchanged only with informed approval; if paths should be hidden, generate a separately labeled derived publication edition and retain original frozen evidence unchanged. No derived redaction is performed automatically. No LICENSE is chosen by this task; project-owner approval is required.
