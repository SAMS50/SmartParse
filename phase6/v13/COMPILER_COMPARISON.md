# GCC/Clang comparison

No student binary is linked or executed. Source is copied to an evaluator-owned temporary `input.c`; only standard headers and simple numeric defines are allowed. The bounded runner has a three-second call limit and process-tree timeout cleanup. This is not an OS sandbox; trusted compilers can read local headers. Actual commands and raw diagnostics are private; public commands explicitly substitute `$COMPILER` and `<INPUT.C>` for local paths.

## Observed identities and capability probes

* gcc: `gcc.exe (MinGW.org GCC-6.3.0-1) 6.3.0`; status available; fix-its: unsupported.
  Arguments: `['-x', 'c', '-std=c11', '-fsyntax-only', '-fdiagnostics-color=never'] <INPUT.C>`.
* clang: `Android (11349228, based on r487747e) clang version 17.0.2 (https://android.googlesource.com/toolchain/llvm-project d9f89f4d16663d5012e5c09495f3b30ece3d2362)`; status available; fix-its: compiler parseable physical edits.
  Arguments: `['-x', 'c', '-std=c11', '-fsyntax-only', '-fdiagnostics-color=never', '-fdiagnostics-parseable-fixits'] <INPUT.C>`.

The parseable-fix-it flag was probed on valid test-owned C before corpus use. GCC 6.3 rejects the flag, so it is omitted; no GCC diagnostic prose is converted to a repair. Clang structured physical edit records are parsed by existing policy helpers. Diagnostics retain parsed severity/location/category plus private original messages and exact byte counts. Lack of JSON diagnostics does not turn prose into an applicable edit.

## Actual primary results

| Split / tool | Diagnostic rejection | Applicable bundles / A | Exact / A | Exact / applicable | Token match / applicable | Compiles / validated applicable |
|---|---:|---:|---:|---:|---:|---:|
| Development / gcc | 19/20 | 0/20 | 0/20 | 0/0 (unavailable) | 0/0 (unavailable) | 0/0 (unavailable) |
| Development / clang | 20/20 | 5/20 | 4/20 | 4/5 | 4/5 | 5/5 |
| Final / gcc | 78/79 | 0/79 | 0/79 | 0/0 (unavailable) | 0/0 (unavailable) | 0/0 (unavailable) |
| Final / clang | 79/79 | 36/79 | 20/79 | 20/36 | 21/36 | 24/36 |

Reference-compatibility-conditioned final results (rather than silently counting incompatible reference dialects as repair failures):

| Tool | A references accepted by this tool | Applicable outputs | Exact repairs |
|---|---:|---:|---:|
| gcc | 79 | 0/79 | 0/79 |
| clang | 75 | 35/75 | 20/75 |

Diagnostic rejection is a compatibility-specific compiler response, not human-rated message quality or automatic-repair accuracy. GCC accepts one final category-A source that Clang rejects under these settings. Exact intended accuracy for GCC conditioned on available repair output has denominator zero and is unavailable; 0/A output coverage does not penalize its diagnostic quality. A modern GCC may expose different capabilities, so these observations apply to the recorded installation only.

Fix-its must target the explicitly mapped physical input, have valid UTF-8 byte boundaries and nonoverlapping ranges, and fit a 24-edit bound. Duplicate/overlapping hints are rejected conservatively rather than guessed. Applicable means the extracted bundle can be applied, not that it compiles or is intended. On final A inputs, 36 Clang bundles apply, 24 compile, 20 exactly match, 21 are token-equivalent, and 12 still fail compilation. Four compiling outputs differ exactly from the reference; one is token-equivalent. Compilation, token match and behavioral equivalence are distinct.

Corrected-reference diagnostics never enter SmartParse. References are compiled only after the recovery boundary finishes, using separate compiler calls. Raw/normalized source hashes are verified on ingestion. Individual per-case application and compilation outcomes are in `results/final.json`; private raw diagnostics include source snippets and are intentionally excluded from Git.
