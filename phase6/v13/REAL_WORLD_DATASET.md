# Real-world dataset provenance and realized sampling

## Source audit

| Source | License/provenance audit | Suitability |
|---|---|---|
| [TEGCER](https://github.com/umairzahmed/tegcer) | Repository GPL-3.0 file; maintainer-documented CS1 student pairs; pinned archive contains one CSV and no separate license notice | Selected: genuine same-student broken/fixed endpoints, not a full preceding edit session |
| [DeepFix](https://github.com/aar-gee/DeepFix) | Maintainers explicitly state Apache-2.0 for their Prutor release | Raw errors alone do not establish per-error intended corrections; not mixed into primary pairs |
| [DrRepair](https://github.com/michiyasunaga/DrRepair) | Repository MIT; upstream datasets have their own provenance | Distinguishes raw errors and seeded training corruptions; generated fixes are not human reference corrections; not selected |

The TEGCER README attributes its data to a 2015–2016 introductory C course,
collected through Prutor. It describes compiler-failing programs subsequently
corrected by the same student on one line. This is maintainer-provided human
provenance, not independent adjudication. Compilation and correction suitability
are verified separately by this evaluation. Model/classification claims in that
README are not imported as repair-accuracy baselines.

Use/credit: Ahmed, Sindhgatta, Srivastava and Karkare, *Targeted Example Generation
for Compilation Errors*, ASE 2019; Das, Ahmed, Karkare and Gulwani, *Prutor: A
system for tutoring CS1 and collecting student programs for analysis* (2016).
References: [TEGCER paper](https://arxiv.org/abs/1909.00769) and
[Prutor paper](https://arxiv.org/abs/1608.03828).
The upstream README requests citation of both works. No external student source,
archive or license text is redistributed in this feature branch. Code retrieval
is reproducible via `acquire.py` and the hash-locked manifest.

## Pinned acquisition

Revision: `0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5`.

[Archive](https://raw.githubusercontent.com/umairzahmed/tegcer/0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5/data/input/dataset.zip),
[license](https://raw.githubusercontent.com/umairzahmed/tegcer/0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5/LICENSE),
[collection/schema documentation](https://github.com/umairzahmed/tegcer/blob/0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5/README.md).

Compressed archive: 9,651,167 bytes, SHA-256
`5bfc7485b7c7dc79d5fe55e530ba62fa2d4bc448f02df0ded0ea7e4d1bce3868`.
Its only member, `dataset.csv`, is 88,942,404 uncompressed bytes. Exact README and
license hashes are in `acquisition-lock.json`. Local archive/code live only under
ignored `.studio-artifacts/m13/`. No upstream scripts or student code are run.

## Ingestion, privacy and sampling (before compiler outcomes)

The actual CSV has 21,995 paired rows. Source/target text and timestamps are used;
submission IDs, free-form old compiler reports and other fields are ignored.
Raw UTF-8 source-field hashes and normalized LF hashes are retained separately.
Original and normalized code remain locally available. The frozen public
`sample-manifest.json` contains only necessary case hashes/metadata and CSV
ordinals, never student code or raw timestamps. IDs are derived hashes rather
than submission identifiers.

| Preparation step | Observed count |
|---|---:|
| CSV rows scanned | 21,995 |
| Unsupported includes/directives | 172 |
| Unsupported preprocessing forms | 11 |
| Privacy/credential-screen exclusions | 5 |
| Normalized duplicate pairs removed | 1,400 |
| Unique eligible normalized pairs | 20,407 |
| Inferred corrected-program families | 18,563 |
| Deterministic selected families/pairs | 100 |
| Development / final | 20 / 80 |
| Selected cases with known dataset correction endpoints | 100 |
| Actual recorded prior editing sessions | 0 |
| Usable partial history before the erroneous endpoint | 0 |

Grouping masks identifiers/literals, then combines matching or close 64-bit
token-shingle SimHashes (Hamming distance <=3). Family ordering uses the fixed
protocol seed; each family contributes one deterministic representative. A second
deduplication pass prevents near-identical erroneous sources crossing splits.
No compiler acceptance, SmartParse outcome or error category influenced sampling.
No selected family was replaced after validation. Assignment/student grouping
metadata is absent from the published schema; inferred families reduce leakage
but cannot certify assignment independence or eliminate distant template copies.

All sampled pairs are genuine errors according to upstream provenance. They
remain **unclassified for primary accuracy until local verification**: A requires
a broken source and compiling correction on the same available compiler, B
retains unverified corrections for qualitative analysis, and D records unsupported
environments/currently compiling sources. No synthetic examples are substituted.
Actual A/B/D counts and correction compilation results are added by the reports
after experiments, separately from the pre-outcome sample manifest.

## Chronology and limits

Source and target timestamps are strictly increasing in every retained pair.
The corrected target is in the future relative to the erroneous input. It is
never passed as a snapshot or reverse-generated edit history to the engine.
The primary condition is no history. RQ3 cannot be answered for real recorded
editing sessions with this release. The ingestion API can validate provenance-
bearing older snapshot/event evidence, but no such evidence is invented here.

This is one public novice-student dataset and a limited deterministic sample,
not production C, all CS1 assignments, or a statistically random sample of all
human syntax errors. Code screening and current compiler compatibility further
limit generality. Known corrected endpoints establish intended textual edits,
not functional correctness or behavioral equivalence.

## Realized verification (after frozen experiments)

| Split | Selected human pairs | A: verified correction | B: unverified correction | C: synthetic | D: excluded after sampling | Actual prior histories |
|---|---:|---:|---:|---:|---:|---:|
| Development | 20 | 20 | 0 | 0 | 0 | 0 |
| Final | 80 | 79 | 1 | 0 | 0 | 0 |
| Total selected | 100 | 99 | 1 | 0 | 0 | 0 |

Reference compatibility: 94 targets compile on both installed compilers; five
compile on GCC only; one is rejected by both. Known published correction endpoints
therefore number 100; **locally verified corrections number 99**. The final primary
denominator is 79, not 80 or 100. Category B case
`c23cde4be2a55ede8b3da081` is retained in the case ledger and raw local evidence,
without replacement or an accuracy label. No reference diagnostics or future
target snapshots entered the recovery boundary.
