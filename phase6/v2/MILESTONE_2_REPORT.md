# Phase 6 Milestone 2 — analysis eligibility and build context

Complete for review; work stops before repair/isolation/detection changes.
All implementation and new outputs are under `phase6/v2/`. This is the eligibility
feature namespace, not a replacement/version bump of the frozen v1 reference.

## Tests and preservation

**300 tests passed; zero failures, zero errors, zero skips**: all 265 existing
tests plus **35 new tests**, including seven live eligibility integrations. All
141 original SmartParse/CGAR tests remain passing. Compiler versions used:

- MinGW GCC **6.3.0**, `C:\MinGW\bin\gcc.exe`.
- Android NDK Clang **17.0.2**,
  `C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe`.

See [test log](outputs/tests.txt), [counts](outputs/tests.json),
[live case summary](outputs/cases.json), and [preservation](outputs/preservation.json).
Hash verification found **zero changes to 211 protected preexisting files**,
including Phase 6 v1 reference/reviews/results, all readable Phase 5 acceptance
artifacts, original parser/evaluation code, existing fixtures, cleaned benchmark,
and external original. All **17 historical CSVs** were preserved byte-for-byte;
the runner restored the legacy performance CSV write in finally. New holdout
sources/header were also unchanged. No old CLI, reporting API, README, reference,
or detector was edited. No compiled C binary was executed.

The first live run exposed a filename-elision case after a macro-generated
declaration. Inventory handling was corrected and a regression test added; the
generated body stays excluded, while the following ordinary body is recoverable.
Malformed nested AST location/child objects are explicitly rejected. The final
complete run and live cases passed after those changes.

## New files

- `eligibility.py`: source/build manifest, bounded metadata probes, blocker
  classification, independent pass completion, and conservative coverage.
- `regions.py`: Clang AST physical main-file range validation; no regex C parser.
- `__main__.py`, `__init__.py`: separate opt-in `python -m phase6.v2` CLI/package.
- `eligibility.schema.json`, `validation.py`: structural schema and independent
  semantic-invariant checks.
- `test_eligibility.py`: synthetic and live tests for contexts, errors, macros,
  headers, Unicode, Windows paths/spaces, AST failures, timeouts and coverage.
- `run_validation.py`: full-suite/live-case runner protecting old artifacts.
- `fixtures/`: six new C controls and one local header: valid configured C,
  missing header, syntax failure, semantic failure, required macro, macro regions.
- `README.md`, this report, and separate `outputs/` artifacts.

No dependencies were installed; Clang was selected explicitly/process-locally.
The existing analyzer requires normal private-directory access on Windows, so
authorized live testing ran outside the agent filesystem sandbox. This is not a
claim of compiler sandboxing or process-tree resource containment.

## Manifest evidence and a newly visible configuration difference

Reports include SHA-256/source stability, compiler versions, actual command
arguments, standard selection, observed standard macros, driver target, include
paths/environment, requested definitions, actual warning arguments, enabled
default checker names, and successful/failed/unknown capability queries. For
Clang 17, the enabled-default-checker query returned **44 names**; this inventory
does not certify that all checkers examined every region.

| Context | Observed driver target | Pointer-size macro | C-version macro |
|---|---|---:|---|
| GCC benchmark default | `mingw32` | 4 bytes | `201112L` |
| Clang benchmark default | `x86_64-w64-windows-gnu` | 8 bytes | `201710L` |
| Clang valid fixture with `--std c11` | `x86_64-w64-windows-gnu` | 8 bytes | `201112L`, strict ANSI defined |

These are measured build contexts, not equivalent-target claims. Historical
results are preserved; comparisons involving sizes, ABI, or dialect-sensitive
behavior must account for the difference. This milestone records target context
but adds no target-selection switch. Header dependencies are resolved by the
existing compiler and their search context is recorded, but they are not fully
snapshotted/content-hashed. Exact reproducibility requires stable build inputs.

## Benchmark results

The unchanged cleaned 500-line file was checked with both backends. Its existing
line mapping to the external numbered original remains identity. No cleaning,
repair, source rewrite, or function isolation was performed in this milestone.

| Pass | Execution completion | Frontend accepted | Inventory/coverage | Exit |
|---|---|---|---|---:|
| GCC syntax/type | completed, return 1 | No | Translation-unit fallback; compiler coverage blocked; analyzer not requested | 1 |
| Clang syntax/type | completed, return 1 | No | Partial AST inventory: 56 physical function ranges, one recovery-node exclusion | 3 with requested analyzer |
| Clang Static Analyzer | partial, return 1 | Blocked by frontend errors | All inventoried regions blocked; no completed function/path claims | 3 |

Clang reported the established **7 errors, 12 warnings and 11 notes** in its
ordinary pass. Its analyzer retained **7 frontend errors and 2 notes**, with zero
static findings because the pass did not complete. Blocker classes are syntax,
semantic/type, and analyzer completion limitations; preprocessing itself succeeds.
The recovery-node exclusion was `wrong_argument_count`. The 56 ranges are only
an inventory, not 56 analyzed functions or an assertion of exhaustive source
function coverage. No diagnostic-nearness inference was used.

Reports: [Clang benchmark](outputs/benchmark_clang.json),
[GCC benchmark](outputs/benchmark_gcc.json), and
[Clang terminal output](outputs/benchmark_clang.txt). Existing compiler cascades
remain raw evidence, not additional independent defect counts. This milestone
does not modify the Phase 6 reference comparison or reinterpret detection rates.

## Independent coverage cases

The controls were authored independently of the 68-entry matching rules. They
exercise eligibility behavior, not blind defect-detection performance.

| Case | Measured behavior |
|---|---|
| Valid header/Unicode/configured C | Compiler and analyzer complete; two physical main-file function ranges. Compiler frontend coverage completed; analyzer function coverage unknown because no exploration certificate exists. Header inline body excluded from main-file inventory |
| Missing header | Preprocessing fails; configuration blocker; compiler/analyzer partial; even the otherwise valid function remains blocked |
| Syntax failure | Preprocessing succeeds; syntax blocker; analyzer partial; no unaffected-looking function is certified analyzed |
| Semantic failure | Preprocessing succeeds; type/argument blocker; analyzer partial; recovery-node body excluded |
| Required macro absent | `#error` configuration failure plus a later semantic symptom; source rejected |
| Same source with `-DENABLE_FEATURE=1` | Frontend accepts, same source SHA-256, one configured function range; analyzer explicitly not requested |
| Macro-generated function | Source accepted; generated definition excluded from reliable physical ranges; ordinary following function mapped; no other-configuration coverage claimed |

All nine live reports passed envelope/invariant validation, JSON/terminal checks,
source hashes, and direct Python subprocess auditing. Process commands were only
compiler metadata queries, preprocessing, syntax-only checks, or explicit static
analysis; no application binary command was launched.

## Coverage contract and limitations

Four region states are explicit: `completed`, `blocked`, `not_attempted`, and
`unknown`. Successful compiler frontend acceptance can justify configured
syntax/type coverage. **Successful analyzer execution alone does not certify
function/path coverage**, so that coverage remains unknown without stronger
instrumentation. Frontend errors block complete analyzer coverage globally.

Ranges use original bytes and physical lines, with spelling/braces validated.
Macro expansions and ambiguous/recovery ranges are excluded. Header bodies are
not main-file regions; other preprocessor configurations are not claimed covered.
Diagnostic `#line`/presumed locations are kept as reported, separate from physical
AST locations. GCC has translation-unit coverage only in this adapter.

Unknown target/include/checker metadata stays unknown rather than guessed. AST
and preprocessing work are additional independently labeled queries with per-query
timeouts; there is no single global deadline, immutable transitive-header
snapshot, or exhaustive analyzer exploration certificate. A generic limitations
classification for unrecognized frontend evidence is not proof of a particular
analyzer defect. Blockers are not new defect-detection rules.

The structural JSON Schema is published, and the dependency-free validator checks
conservative invariants against live artifacts. No external schema engine was
installed or claimed as certification. Remaining work belongs to later approved
milestones; no automatic repair, function isolation, new checker, commit or push
has been performed. Stop here for review.
