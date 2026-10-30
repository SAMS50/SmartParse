# Release reproducibility verification

Technical checkout blockers are resolved in the tested Windows environment. No analysis, recovery, isolation or diagnostic-detection algorithm was changed. Independent human adjudication remains pending. No real repository staging, commit, push, merge, tag or release was performed.

## Root causes and fixes

1. **Mixed bytes and automatic Git conversion.** Frozen v8 data includes LF C fixtures and CRLF JSON. Scoped `-text` rules now preserve those original bytes and archived v9 reports. Older reference-bound benchmark/v5/v6/v7 C sources have explicit LF policies matching their existing references. The deliberate v3 Unicode/CRLF fixture has an explicit CRLF policy. No historical file was rewritten merely to normalize endings.
2. **Workstation inventory used as a release oracle.** `release_manifest.json` now enumerates the intended distributed payload only. It excludes the 68 untracked acceptance outputs, 147 empty worker logs and redundant/local run files. Missing or altered required files fail. Historical inventories remain unchanged and available through `--historical-audit`; that strict local mode reports missing files and authorized later code changes rather than silently accepting them.
3. **Legacy raw-byte compatibility assertion.** The three legacy Python assertions use CRLF-to-LF canonical content bound to their established Git HEAD blobs. No whitespace, encoding, identifier or other content change is ignored. Exact-byte checks remain in place for frozen evidence and actual pre/post-test source preservation.
4. **Older regression evidence also depended on original paths.** The first genuine checkout exposed three legacy errors. Two exact raw acceptance reports are now explicitly versioned in `fixtures/legacy_acceptance/`, pinned by `legacy_evidence.json`. The v1 loader verifies their hashes, the actual cleaned-source hash and recorded source identity, without rewriting raw paths. Original dataset/run fingerprints remain identical; evaluation matching rules and historical results are unchanged.
5. **Validation output could overwrite old evidence.** New checks write unique ignored run directories. Archived M8/M9 results, snapshots and human-review evidence are not regenerated.

## Measured verification

| Check | Result |
|---|---|
| Working-tree complete suite | **516 passed; 0 failures/errors/skips**, 278.188 seconds |
| Genuine fresh Git checkout, complete suite | **516 passed; 0 failures/errors/skips**, 287.938 seconds |
| Focused compatibility/reference checks | **76 passed**, in both LF and CRLF checkout modes |
| Existing live unified-CLI smoke suite | **20/20 passed**; original inputs preserved |
| Fresh CLI commands | Version, doctor and valid-C analysis succeeded in both checkout modes |
| Portable manifest before/after full tests | No changed or missing release files |
| Exact checkout bytes before/after working-tree tests | Preserved; legacy CSV output restored in `finally` |
| Frozen v8 inputs | All 46 checksums retained |
| Original historical evidence | No artifact changes; authorized code/metadata changes are separately identified |

The fresh checkout was created by real Git `read-tree`/`checkout-index` operations using a private object store/index and the explicit intended payload. It copied no arbitrary untracked working files and created no commits. The 68 original local acceptance outputs and empty worker logs were absent. The full suite command was exactly `python -m unittest discover -v`, with installed Clang exposed only in the child PATH. No analyzed C binary was executed.

Representative Git blob/working-tree checks show the frozen C fixture retains LF and the frozen manifest retains its 855 CRLF lines under both `core.autocrlf=true` and `false`. Legacy Python files legitimately differ between LF/CRLF checkout bytes while canonical content remains identical.

The harness now seals both snapshots before starting long tests, avoiding late private Git reconfiguration. An earlier post-test harness error and the initial three legacy failures are retained in the local run evidence; none was skipped or represented as a successful full run. Exact staged index entries (modes/object IDs/stages/paths) remain unchanged. Git/IDE stat-cache byte refreshes are recorded separately and are not staging.

Local evidence, intentionally not part of the public payload:

- `reproducibility/runs/validation-20261030T145814-25452/`: working-tree 516-test run, exact before/after and portable preservation.
- `reproducibility/runs/validation-20261030T150856-24524/`: successful sealed-checkout full run and both CLI checkout modes.
- `reproducibility/runs/validation-20261030T110438-2964/`: both modes' focused 76-test compatibility checks.
- Other timestamped run directories preserve targeted, smoke, initial-failure and final documentation/payload rechecks.

The complete suite's source/fixture payload is unchanged by this final report addition. The portable manifest is rebuilt for the report, and a lightweight genuine checkout recheck verifies the final documentation/payload in both modes. Timings are execution records, not speed or accuracy claims.

## Exact changed-file scope

Existing files changed for this task:

- `.gitignore`: scoped local-only exclusions.
- `README.md`: portable validation guidance.
- `phase6/v1/evaluate_saved.py`: hash-verified relocation of historical evidence; matching logic untouched.
- `phase6/v8/prepare.py`: interpret Windows relative separators portably when checking the unchanged freeze.
- `phase6/v9/validate.py`: portable versus local audit modes, exact pre/post bytes, unique run output and tool discovery.
- `phase6/v9/smoke.py`: write new run output rather than archived reports.
- `test_smartparse_cli.py`: retain all three legacy assertions using explicit canonical-content hashes.

New distributed files:

- `.gitattributes`.
- `phase6/v9/release.py`, `release_manifest.json`, `fresh_checkout.py`.
- `phase6/v9/legacy_evidence.json` and the two exact JSON copies in `fixtures/legacy_acceptance/`.
- `phase6/v9/REPRODUCIBILITY.md` and this report.
- `test_release_reproducibility.py`: 14 new tests, including content-change rejection, exact frozen bytes, missing/tampered files, membership, unsafe paths, portable separators, unchanged historical fingerprints and raw-copy identity.

No original parser, CGAR, compiler backend, analyzer detector, reference dataset, research CSV, figure, frozen output or human-review decision changed. Historical inventory files remain byte-for-byte original; they are not relabeled as portable baselines.

## Publication and remaining limitations

No high-specificity credential pattern was found in the scanned release text. Archived outputs expose Windows usernames, installations and temporary paths. Keep essential raw evidence unchanged only with informed publication approval. If privacy requires redaction, publish a separately labeled derived edition and retain original frozen evidence; do not substitute redacted data for the hash-bound regression corpus. New runtime logs/private snapshots remain local.

No LICENSE exists or was selected. The owner should choose licensing terms before offering open-source reuse. No software was installed.

Both Git checkout EOL modes were tested on Windows 11/Python 3.12.5 with installed GCC/Clang/Cppcheck. This is not a native Linux execution result. The old historical evaluation runners still describe their recorded machine/tool configurations; the new release validator is the portable clean-checkout entry point. No universal C detection, complete path coverage or independently verified accuracy is claimed.
