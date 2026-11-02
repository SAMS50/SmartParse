# Milestone 13 evaluation: genuine student C errors

**No measurable advantage for full intent-aware recovery is demonstrated on this sample.** The frozen full mode abstains on every primary case. Existing scoring and Clang machine fixes recover the same number of exact references. Reduced wrong recommendations are achieved by zero recommendation coverage, not useful selective recovery.

## Provenance and denominators

Pinned TEGCER archive: 21,995 upstream human-pair records; 100 deterministic inferred families selected, without compiler-outcome filtering. Development has 20 category-A pairs. The final sample has 79 category-A pairs and one category-B pair whose published correction is not accepted locally. No synthetic cases enter primary metrics. There are zero actual recorded prior histories or usable earlier snapshots; corrected endpoints are future information and are never recovery inputs. See `REAL_WORLD_DATASET.md` and the frozen manifest.

Primary intended-repair denominator is final category A only. A verifies source rejection and corrected compilation on the same compiler, not assignment/behavioral correctness. B remains in compatibility and qualitative records, never silently mixed into accuracy. Family deduplication is inferred from token structure, not verified assignment/student identity.

## Development outcomes (separate from final)

| System | Exact | Token match | Wrong exact match | Recommendations | Abstentions | Top-3 exact | Accuracy among recommendations |
|---|---:|---:|---:|---:|---:|---:|---:|
| existing | 3/20 | 3/20 | 0/20 | 3/20 | 17/20 | 3/20 | 3/3 |
| history | 0/20 | 0/20 | 0/20 | 0/20 | 20/20 | 3/20 | 0/0 (unavailable) |
| semantic | 0/20 | 0/20 | 0/20 | 0/20 | 20/20 | 3/20 | 0/0 (unavailable) |
| full | 0/20 | 0/20 | 0/20 | 0/20 | 20/20 | 3/20 | 0/0 (unavailable) |

No recovery tuning followed development outcomes. The preregistered engine, 24-candidate/240-trial budgets and margin 12 remain unchanged.

## Final primary outcomes

| System | Exact | Token match | Wrong exact match | Recommendations | Abstentions | Top-3 exact | Accuracy among recommendations |
|---|---:|---:|---:|---:|---:|---:|---:|
| existing | 20/79 | 21/79 | 4/79 | 24/79 | 55/79 | 20/79 | 20/24 |
| history | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 | 0/0 (unavailable) |
| semantic | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 | 0/0 (unavailable) |
| full | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 | 0/0 (unavailable) |

Every ablation receives the identical candidate pool. All 24 eligible candidate pools have one valid program, all with seven UNKNOWN semantic checks; full/semantic modes cannot certify supported structure. The other 55 A cases have no validated candidate. Exact intended-candidate coverage and top-3 coverage are both 20/79. These are pool limitations, not evidence that a different ranking of many candidates would solve them.

Existing-score recommendations compile independently in 24/24; compilable exact-intent mismatches are 4/79. One of the four exact mismatches is token-equivalent, three differ in tokens; none has established behavioral equivalence. Full-mode conditional accuracy and conditional compilation are undefined (0 recommendations), not perfect. No student program or compiled binary was executed.

## Research questions

* RQ1: no improved intended-repair accuracy: full 0/79 versus existing 20/79.
* RQ2: wrong exact-source recommendations fall from 4/79 to 0/79, but coverage falls from 24/79 to 0/79. Useful coverage is not maintained.
* RQ3: not identifiable without real prior editing history. Equal zero outcomes across enhanced modes do not establish that history is useless.
* RQ4: Clang produces 36/79 applicable edit bundles, 24/36 compile and 20/36 exactly match the correction. Existing scoring exactly matches on the same 20 cases. Installed GCC 6.3 has no supported machine fix-it mode; diagnostic rejection remains separately reported.
* RQ5: supported-subset and candidate-generation failures dominate; detailed category/length/diagnostic-count breakdowns follow. No claim generalizes to all C or all students.

## Generalization breakdowns

| Dimension | Group | N | Existing exact | Full exact | Full recommendations | Mean engine ms |
|---|---|---:|---:|---:|---:|---:|
| error_category | name/type | 13 | 1/13 | 0/13 | 0/13 | 132.44 |
| error_category | other | 8 | 1/8 | 0/8 | 0/8 | 106.71 |
| error_category | syntax/delimiter | 53 | 18/53 | 0/53 | 0/53 | 192.53 |
| error_category | type/expression | 5 | 0/5 | 0/5 | 0/5 | 111.86 |
| length | 21-50 lines | 38 | 10/38 | 0/38 | 0/38 | 155.79 |
| length | <=20 lines | 28 | 6/28 | 0/28 | 0/28 | 148.17 |
| length | >50 lines | 13 | 4/13 | 0/13 | 0/13 | 251.55 |
| error_diagnostics | multiple diagnostics | 36 | 3/36 | 0/36 | 0/36 | 179.33 |
| error_diagnostics | one | 43 | 17/43 | 0/43 | 0/43 | 160.07 |
| plausible_candidates | 0 | 55 | 0/55 | 0/55 | 0/55 | 148.48 |
| plausible_candidates | 1 | 24 | 20/24 | 0/24 | 0/24 | 215.52 |
| compiler_compatibility | gcc | 4 | 0/4 | 0/4 | 0/4 | 112.98 |
| compiler_compatibility | gcc,clang | 75 | 20/75 | 0/75 | 0/75 | 171.82 |
| semantic_unknown | 7 | 24 | 20/24 | 0/24 | 0/24 | 215.52 |
| semantic_unknown | None | 55 | 0/55 | 0/55 | 0/55 | 148.48 |
| history | none | 79 | 20/79 | 0/79 | 0/79 | 168.85 |

Error categories are deterministic diagnostic-keyword labels, not independent human annotations. Error counts are emitted error-diagnostic counts and may include cascades, not counts of independent defects. Each selected source family contributes one case; all are from TEGCER, so a second source-project comparison is unavailable.

## Uncertainty and paired comparisons

Existing exact rate: 0.253, Wilson 95% interval [0.170, 0.359]. Full exact and wrong rates are both zero, Wilson upper bound 0.046; zero wrong predictions with no recommendations provide no conditional safety guarantee.

Paired 2,000-replicate seeded family-bootstrap exact-rate differences:

| Left → right | Mean difference | 95% percentile interval | Right-only / left-only successes |
|---|---:|---|---|
| existing → history | -0.253 | [-0.35443037974683544, -0.16455696202531644] | 0 / 20 |
| existing → semantic | -0.253 | [-0.35443037974683544, -0.16455696202531644] | 0 / 20 |
| existing → full | -0.253 | [-0.35443037974683544, -0.16455696202531644] | 0 / 20 |
| gcc → full | 0.000 | [0.0, 0.0] | 0 / 0 |
| clang → full | -0.253 | [-0.35443037974683544, -0.16455696202531644] | 0 / 20 |
| semantic → full | 0.000 | [0.0, 0.0] | 0 / 0 |

Intervals describe this sampled family distribution under approximate independence. Inferred families may share assignments/templates, and the deterministic representative rule is not uniform sampling of all errors. No formal significance or population-wide superiority/non-inferiority claim is made. Degenerate zero/zero comparisons are not evidence of equivalence.

## Selective prediction

Diagnostic-only post-hoc selectors retain existing issued recommendations whose finite top-two score gap exceeds a threshold; singleton pools have infinite gaps. They never issue previously withheld predictions or tune the deployed policy.

| Minimum gap | Existing coverage | Existing selective accuracy | Full coverage | Full selective accuracy |
|---:|---:|---:|---:|---:|
| 0 | 24/79 | 20/24 | 0/79 | 0/0 (unavailable) |
| 12 | 24/79 | 20/24 | 0/79 | 0/0 (unavailable) |
| 60 | 24/79 | 20/24 | 0/79 | 0/0 (unavailable) |
| 120 | 24/79 | 20/24 | 0/79 | 0/0 (unavailable) |
| 240 | 24/79 | 20/24 | 0/79 | 0/0 (unavailable) |

The curve is flat because valid candidate pools are singletons. Margin calibration cannot recover missing candidates or resolve unsupported semantics. Abstention changes across the main policies are explicitly reported rather than treated as accuracy at equal coverage.

## Runtime and resources

| Measurement | N | Mean ms | Median ms | p95 ms |
|---|---:|---:|---:|---:|
| Shared SmartParse full evidence construction | 79 | 168.85 | 137.64 | 386.30 |
| gcc original diagnostics | 79 | 93.29 | 82.64 | 138.68 |
| clang original diagnostics | 79 | 98.18 | 93.47 | 135.30 |

SmartParse compiler calls per A input: mean 1.56, median 1, p95 2. Public records include retained candidate/source-byte counts and compiler stdout/stderr byte counts. Peak RSS and process-tree CPU are not instrumented on this Windows run (null, never assumed zero). End-to-end evidence time is shared across ablations; tiny per-mode ranking times are reported separately. Compiler diagnostic timing excludes fix-it validation, reference validation and capability probes; these scopes are not presented as equivalent work or a speedup claim. Single-run timings include startup, filesystem and concurrent test activity.

## Reproduction and limitations

Use the commands in `MILESTONE_13_REPORT.md`. Acquisition is pinned by revision and SHA-256. Raw original/corrected source and private diagnostics are kept locally; public reports contain only hashes, aggregates and safe metadata. Known threats: one novice dataset, screen/compatibility bias, inferred families, missing history, no behavioral oracle, old GCC profile, and an intentionally narrow recovery subset. Results falsify generalization on this sample rather than justify a claim of research superiority.
