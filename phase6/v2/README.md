# Phase 6 Milestone 2 — analysis eligibility and build context

This is a separate opt-in mode. The original `analyze_c.py`, `extended_c` API,
SmartParse/CGAR, Phase 6 v1 data/reviews, and Phase 5 acceptance outputs are
unchanged. No automatic source repair, function isolation, or new defect check
is implemented. Additional invocations collect compiler metadata, preprocess the
unchanged input, and obtain syntax-only AST locations.

## Run

From the repository root, using Python 3.12:

```powershell
python -m phase6.v2 "C:\My Project\program.c" --compiler gcc --json
python -m phase6.v2 phase6/v2/fixtures/valid_context.c --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --std c11 -DINITIAL_VALUE=9 --json
python -m phase6.v2 acceptance/cleaned/c_error_detection_500_lines.c --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --static-analysis --analyzer-executable "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --json
```

The command inherits the established source/compiler/standard/include/macro/
timeout/static-analysis arguments. `--metadata-timeout` adds a positive finite
timeout per metadata, preprocessing, or AST query (default five seconds).
The total workflow can include several independent probes, so this is not a
single overall deadline. `--static-analysis` remains an explicit opt-in; metadata
queries do not silently analyze the user's source with the static analyzer.
The enabled-checker query uses valid stdin probe code, only when static analysis
was requested and its driver was usable. Probes use argument arrays and no shell.

No install or persistent PATH change is performed. The existing installed Clang
may be selected explicitly without PATH discovery. Private analyzer temporary
directories require a normal user token; the restricted agent sandbox cannot
traverse their Windows ACLs. The authorized live checks use execution outside
that sandbox, with no compiled C binary execution.

Old exit codes are retained: 0 for completed checks without source errors or
analyzer findings, 1 for source errors/potential findings, 2 for CLI usage errors,
3 for failed/partial/unavailable/timed-out requested analysis. A source-integrity
failure also yields 3. Missing optional metadata alone does not change an otherwise
successful analysis to failure: unknown capability/context remains explicit.

Python entry point:

```python
from phase6.v2.eligibility import analyze_eligibility

eligibility, original_result = analyze_eligibility(
    "example.c", preference="gcc", standard="c11", metadata_timeout=5
)
```

The returned `AnalysisResult` and nested existing report keep the previous API
and schema. The new envelope is intentionally distinct from the legacy report.

## Schema and manifest

`eligibility.schema.json` documents structural schema **1.0**. The dependency-free
`validation.validate_eligibility` also checks conservative semantic invariants.
Live artifacts were checked with that validator; this is not certification by
an external JSON Schema engine. Additional fields are permitted for forward
compatibility; breaking interpretation requires a new schema version.

| Top-level field | Meaning |
|---|---|
| `schema`, `schema_version` | `smartparse.analysis_eligibility`, `1.0` |
| `manifest` | Source snapshot/hash, build configuration, compiler identity, metadata and capabilities |
| `stages` | Independent compiler/analyzer completion and explicit preprocessing-probe execution |
| `blockers` | Classification and provenance of errors/tool limitations; not an independent-defect counter |
| `region_inventory` | AST probe status, trusted physical function ranges, exclusions, and reasons |
| `regions` | Translation-unit fallback plus reliable main-file functions, each with separate compiler/analyzer coverage |
| `mapping` | Original physical byte mapping, macro/header/#line limitations, and `source_edits_applied: false` |
| `analysis` | Existing schema 1.0 compiler/static-analysis report, unchanged in meaning |

Manifest details:

- SHA-256 of source bytes, pre-analysis SHA-256, byte/line counts, UTF-8 or unknown
  encoding, and before/after stability. No source decoding/re-encoding is applied.
- Compiler path, family and version, requested C standard, whether default or
  explicit, and observed standard macros (`__STDC__`, `__STDC_VERSION__`,
  `__STRICT_ANSI__`, `__SIZEOF_POINTER__`). No dialect name is invented when
  metadata is unavailable. These macros are probed on valid stdin with the same
  command-line definitions; source-defined macros remain in the hashed source.
- Driver-default target from `-dumpmachine`. This mode does not add target
  selection or silently change ABI/SDK configuration.
- Supplied and resolved include directories, source-local quoted-include root,
  observed system include search paths, and selected include-related environment
  variables. Only include-related variables are recorded, not the full environment.
- Actual enabled warning-option arguments, requested object-like definitions,
  and observed default checker names when the enabled-checker query is supported.
  Names represent the driver defaults for that invocation, not proof that each
  checker ran on every function.
- Per-query commands, return codes, timeout/failure state, raw stderr, stdout
  byte count and SHA-256. Large preprocessed/AST output is hashed, not embedded.
  Raw ordinary/analyzer diagnostic stdout/stderr remain in the nested analysis.
- Validated optional compiler flags and observed/unknown metadata capabilities.
  Missing or malformed metadata is not assumed supported.

Header dependencies are **not snapshotted or content-hashed** by this milestone.
The manifest records their resolution context, not an immutable full project
snapshot. Source hash checks cannot rule out every concurrent filesystem change.
The caller should keep headers/build inputs stable during analysis.

## Completion versus coverage

Compiler `completion: completed` can include source errors. Separate
`frontend_accepted` is true only after normal zero-exit checking without compiler
errors. Static-analyzer completion is independent and never inferred from that
compiler result. The preprocessing invocation is another labeled probe, not a
replacement for either measured pass.

Region coverage has exactly four states:

| State | Claim |
|---|---|
| `completed` | Configured compiler frontend accepted the translation unit; for a function, a successful syntax-only AST probe also contains a validated body range |
| `blocked` | Translation-unit frontend errors prevent complete coverage, even for a function without a nearby diagnostic |
| `not_attempted` | Pass was not requested, or no usable invocation could be launched |
| `unknown` | Interrupted/malformed output or insufficient per-region evidence; includes successful analyzer invocations without exploration certificates |

**No function-level analyzer `completed` claim is made in this implementation.**
Clang text output provides no exhaustive per-function/path certificate. A warning
near a function, or even a path note inside it, is not used to certify coverage.
A successful analyzer stage therefore coexists with `unknown` function coverage.
If frontend errors stop analysis, all inventoried regions report analyzer
`blocked`. Unaffected-looking functions are not isolated or analyzed separately.

The GCC adapter has no verified function AST inventory; it reports the exact
translation-unit region rather than guessing C boundaries with regexes. This
does not mean GCC cannot analyze C functions; it is a limitation of this inventory
adapter. Clang inventory status can be partial even when some ranges are reliable.
Those ranges are an inventory, not evidence that the analyzer checked them.

## Locations, macros, headers, and blockers

Function ranges use physical **byte offsets**, with an exclusive end, validated
against the source name spelling and body braces. Physical line numbers are
computed from original bytes, not diagnostic proximity. Invalid/recovery ASTs,
macro-generated bodies, ambiguous identities, overlapping ranges, or malformed
JSON are excluded or downgraded. Clang's elided filenames after macro locations
are carried as context only; macro ranges themselves remain untrusted.

Header function bodies are not presented as main-file regions. Inactive branches
and other macro configurations are not claimed covered. Source encodings are
preserved; unsupported bytes remain compiler evidence rather than guessed text.
Compiler diagnostics keep their reported file/line/column. `#line` and presumed
filenames are **not** silently converted into physical locations. AST physical
offsets are separate. This is useful for generated code without claiming a
verified arbitrary source map.

Blocker categories are `preprocessing/configuration`, `syntax`, `semantic/type`,
`timeout`, and `analyzer limitations`. Known diagnostic categories are preserved;
preprocessing failure does not relabel a known type error. Unrecognized frontend
errors/layouts use the limitations category rather than guessed syntax/type.
The stage, message and basis explain that conservative fallback. Repeated frontend
messages from separate invocations are retained as evidence, not counted as
additional independent defects.

## Verification and scope

```powershell
python -m phase6.v2.run_validation --compiler "C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe"
```

The runner protects all **211 preexisting readable files**, including Phase 6 v1,
Phase 5 outputs, original C sources and the external numbered sample. It restores
legacy timing CSV writes in finally. It writes only new v2 artifacts, checks new
holdout source hashes, and audits direct compiler subprocess invocations. All
17 historical CSVs and old acceptance artifacts remain unchanged. Protected
scope excludes Git internals, bytecode caches, and inaccessible old temporary
directories, which are not traversed or changed.

New self-authored independent fixtures cover valid C with headers/Unicode/macros,
missing headers, required configuration, syntax errors, semantic errors, and
macro-generated functions. They are independent coverage tests, not a blind
defect-detection benchmark. Existing timeout/failure tests and new malformed-output
tests verify conservative states. See `MILESTONE_2_REPORT.md` and `outputs/` for
actual counts, blockers, and full benchmark evidence. No repair, isolation,
new checker, commit, push, or release approval is performed.
