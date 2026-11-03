# Milestone 14 evaluation: evidence-adaptive recovery

**Useful lower-assurance proposals are restored, but algorithmic superiority is not demonstrated.** New evaluation: adaptive combined makes 12 exact recommendations, zero exact mismatches, eight alternative-suggestion cases and 60 abstentions out of 80. Existing scoring makes 13 exact recommendations with zero mismatches. All adaptive recommendations originate from Clang. The four known mismatches remain on the exposed benchmark. Zero observed mistakes on the new set cannot establish acceptable error risk in general.

## Frozen methodology and provenance

The v13 baseline was reproduced and all 79 A abstentions audited before algorithm changes (`b735ce0`). The original 80 selected final records are **exposed** (79 A, 1 B). Twenty original development records alone calibrate the hunk cap. The next 80 pinned-TEGCER inferred source families form the new, previously unexamined evaluation; all 80 locally verify as category A. No compiler-outcome replacement or correction/history leakage. All 180 selected errors are maintainer-documented genuine student errors; no recorded preceding histories exist.

The underlying pinned archive, GPL-3.0 provenance and privacy/source policy are inherited from v13. Student code, corrections, raw compiler text and timestamps stay in ignored local storage. Public manifests contain hashes/metadata. Family separation uses inferred token/SimHash families, not assignment/student identifiers. This is a new split from one dataset, not independent cross-project evidence.

Policy choices 1/2 edit hunks were evaluated on development only. Both yield two exact recommendations and no wrong recommendations; the predeclared tie rule selects one hunk. Score margin stays 12. `f69e5a1` commits the final policy/development evidence before new outcomes. Algorithm fingerprint: `4fe8a3fbb4dce8398cf9240273a3695423b098e36dfe013593dda4d0d03446f7`. No recovery policy tuning followed the new evaluation.

## Correctness amendment and rerun

Final validation found a UTF-8 character/Clang-byte offset mismatch in the new structural-risk check. Commit `2e395c1` fixes it with a regression test. Two exposed sources contain non-ASCII text; development and new inputs are ASCII. The first-run records were preserved locally and all three evaluations rerun without policy tuning. Comparison of all 180 cases across eight systems found zero changes in recommendations, outcomes, selected hashes, candidate IDs, modes, origins or reasons. See `results/correctness-rerun.json`. The new set was unexamined before its first evaluation; the correctness rerun is not a pristine unseen test. Timings below are corrected-run measurements.

## Actual results

| Split / system | Exact | Token match | Wrong exact match | Recommended | Suggested alternatives | Abstained | Intended candidate coverage | Selective exact accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| development / v13-existing | 3/20 | 3/20 | 0/20 | 3/20 | 0/20 | 17/20 | 3/20 | 3/3 |
| development / v13-full | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 | 20/20 | 3/20 | 0/0 (unavailable) |
| development / adaptive-custom | 0/20 | 0/20 | 0/20 | 0/20 | 2/20 | 18/20 | 1/20 | 0/0 (unavailable) |
| development / adaptive-compiler | 2/20 | 2/20 | 0/20 | 2/20 | 3/20 | 15/20 | 4/20 | 2/2 |
| development / adaptive-combined | 2/20 | 2/20 | 0/20 | 2/20 | 5/20 | 13/20 | 5/20 | 2/2 |
| development / without-semantic | 2/20 | 2/20 | 0/20 | 2/20 | 5/20 | 13/20 | 5/20 | 2/2 |
| development / without-history | 2/20 | 2/20 | 0/20 | 2/20 | 5/20 | 13/20 | 5/20 | 2/2 |
| development / simple-fallback | 5/20 | 5/20 | 2/20 | 7/20 | 0/20 | 13/20 | 5/20 | 5/7 |
| exposed / v13-existing | 20/79 | 21/79 | 4/79 | 24/79 | 0/79 | 55/79 | 20/79 | 20/24 |
| exposed / v13-full | 0/79 | 0/79 | 0/79 | 0/79 | 0/79 | 79/79 | 20/79 | 0/0 (unavailable) |
| exposed / adaptive-custom | 0/79 | 0/79 | 0/79 | 0/79 | 1/79 | 78/79 | 0/79 | 0/0 (unavailable) |
| exposed / adaptive-compiler | 18/79 | 19/79 | 4/79 | 22/79 | 3/79 | 54/79 | 21/79 | 18/22 |
| exposed / adaptive-combined | 18/79 | 19/79 | 4/79 | 22/79 | 4/79 | 53/79 | 21/79 | 18/22 |
| exposed / without-semantic | 18/79 | 19/79 | 4/79 | 22/79 | 4/79 | 53/79 | 21/79 | 18/22 |
| exposed / without-history | 18/79 | 19/79 | 4/79 | 22/79 | 4/79 | 53/79 | 21/79 | 18/22 |
| exposed / simple-fallback | 21/79 | 22/79 | 5/79 | 26/79 | 0/79 | 53/79 | 21/79 | 21/26 |
| independent / v13-existing | 13/80 | 13/80 | 0/80 | 13/80 | 0/80 | 67/80 | 13/80 | 13/13 |
| independent / v13-full | 0/80 | 0/80 | 0/80 | 0/80 | 0/80 | 80/80 | 13/80 | 0/0 (unavailable) |
| independent / adaptive-custom | 0/80 | 0/80 | 0/80 | 0/80 | 3/80 | 77/80 | 0/80 | 0/0 (unavailable) |
| independent / adaptive-compiler | 12/80 | 12/80 | 0/80 | 12/80 | 5/80 | 63/80 | 17/80 | 12/12 |
| independent / adaptive-combined | 12/80 | 12/80 | 0/80 | 12/80 | 8/80 | 60/80 | 17/80 | 12/12 |
| independent / without-semantic | 12/80 | 12/80 | 0/80 | 12/80 | 8/80 | 60/80 | 17/80 | 12/12 |
| independent / without-history | 12/80 | 12/80 | 0/80 | 12/80 | 8/80 | 60/80 | 17/80 | 12/12 |
| independent / simple-fallback | 17/80 | 17/80 | 3/80 | 20/80 | 0/80 | 60/80 | 17/80 | 17/20 |

Recommended / suggested alternatives / abstention are mutually exclusive v14 outcomes. A suggestion is not counted as an automatic recommendation or a wrong recommendation. Legacy systems have their original recommend/abstain outcomes. Nonrecommendation (alternatives + abstention) is also recorded to prevent a cosmetic category change from appearing as increased repair coverage. All issued recommendations have compiler-valid candidates; behavioral equivalence is not assessed.

## Candidate-provider attribution and ablations

Custom-only, compiler-only and combined arms use explicitly different provider pools. All combined-policy arms (adaptive, without positive semantic support, without positive history support and simple fallback) share the exact candidate pool. Positive-evidence ablations retain hard known-risk/mapping/failed-check vetoes; they do not pretend known hazards disappeared. No-history also withholds positive historical-reference agreement.

| Split | Custom-only exact recommendations | Compiler-only exact recommendations | Combined exact recommendations | Combined recommended origins | Combined decision modes |
|---|---:|---:|---:|---|---|
| development | 0/20 | 2/20 | 2/20 | {'clang_fixit': 2} | {'INSUFFICIENT_EVIDENCE': 18, 'SYNTAX_ONLY': 2} |
| exposed | 0/79 | 18/79 | 18/79 | {'clang_fixit': 22} | {'INSUFFICIENT_EVIDENCE': 57, 'SYNTAX_ONLY': 22} |
| independent | 0/80 | 12/80 | 12/80 | {'clang_fixit': 12} | {'INSUFFICIENT_EVIDENCE': 68, 'SYNTAX_ONLY': 12} |

All 12 new combined recommendations are Clang-derived, as are all 22 recommendations on the exposed set. Custom-only makes no recommendations. It supplies one exact intended candidate in development and none in the new or exposed evaluation sets (its new-set token-level top-3 coverage is 2/80). Combined and compiler-only make identical recommendations; custom adds three new-set alternative-suggestion cases. The demonstrated contribution is evidence routing, safety gates, explicit attribution and reviewable proposals, not an original C repair algorithm outperforming Clang.

Without positive semantic/history support, outcomes remain identical on this corpus because historical evidence is absent and whole-program preprocessing remains unsupported. Unit tests and actual Studio editing exercise other evidence modes; these are not relabeled genuine-history benchmark results.

## Simple fallback comparison and limits

The preregistered simple comparator chooses the highest existing heuristic among compiler-valid combined candidates without adaptive evidence/safety gates. On new data it makes 17 exact and three mismatched recommendations versus adaptive 12 exact and zero mismatches: five correct outputs are withheld to avoid those three. Existing v13 scoring is better on this particular set: 13 exact with no mismatches versus 12 exact with no mismatches.

Additional **post-hoc descriptive pool check**, not a tuned or deployed selector: the new compiler-only pools contain exactly 17 validated singletons and all match the reference. Thus a simple validated compiler-only selector would make 17 exact recommendations with zero observed mismatches. This further rules out an observed selection advantage for the adaptive policy. The four exposed semicolon mismatches are still recommended; the syntax-only gate cannot certify intent.

## Uncertainty and paired comparisons

New adaptive exact rate 0.150, Wilson 95% interval [0.08794040506163547, 0.24413228561323347]. Conditional exact accuracy 12/12 has interval [0.7575059933447592, 1]. Zero wrong/80 has upper Wilson bound 0.046; zero events are not proof of zero future risk. Exact-source mismatch can include token-equivalent formatting, not a proven behavior change.

| New evaluation comparison â†’ adaptive combined | Exact-rate difference | Paired family-bootstrap 95% interval | Adaptive-only / comparator-only successes |
|---|---:|---|---|
| v13-existing | -0.0125 | [-0.0375, 0.0] | 0 / 1 |
| v13-full | 0.1500 | [0.075, 0.225] | 12 / 0 |
| simple-fallback | -0.0625 | [-0.125, -0.0125] | 0 / 5 |

Bootstrap uses 2,000 seeded paired family resamples. Inferred families can share assignments/templates; N=80 is small, no real histories exist, and one repository cannot establish cross-project generality. No significance, formal safety, equivalence or research-superiority claim is made.

## Runtime

| Split | V13 shared evidence mean / median / p95 ms | Adaptive shared preparation mean / median / p95 ms | Mean overhead |
|---|---|---|---|
| development | 330.28 / 251.42 / 719.26 | 1212.50 / 1032.80 / 1755.53 | 882.22 ms (267.1%) |
| exposed | 419.87 / 281.29 / 709.73 | 1343.31 / 1285.01 / 2119.69 | 923.44 ms (219.9%) |
| independent | 318.88 / 265.87 / 533.18 | 1234.60 / 1123.20 / 1806.15 | 915.72 ms (287.2%) |

Compiler capability probes, full-source validation and additional candidate rounds add material overhead. Timing is shared candidate/evidence preparation per case, not the sum of all policy variants, and excludes evaluator-only reference checks. Concurrent tests and two evaluation processes affect these one-run measurements; no performance-significance claim. Each compiler call and shared compiler-evidence deadline is bounded, but local parser CPU and cleanup are not a hard real-time guarantee.

## Case-level new-evaluation ledger

| Case | Class | Valid custom / compiler / combined | Intended generated | Mode | Outcome | Exact / wrong | Selected provider | Explanation |
|---|---|---:|---|---|---|---|---|---|
| e3e7a6884c9c171c11f1e2fa | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 38f0c90253cd8d0e0c454449 | A | 2 / 0 / 2 | False | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Multiple plausible repairs remain; programmer confirmation is recommended. |
| e3c255e14f75e40744009585 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 51c78001365472dfef7eab0b | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| eca295b9f332e72970f9c194 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 40566d0ad3df48848aac99d3 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| f20060e4b2f9b3933045d478 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| c6cb77f278bbb287817aca14 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| f07dbe48b371bff7be7b1dac | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| ac535fdc290806ca5288377c | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 873e71ddd7943e33947439b5 | A | 0 / 1 / 1 | True | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Validated alternatives exist, but available evidence does not support choosing a repair. |
| af5d778fec3031f959d2dfc0 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| cf7c5bc2773846e287430e61 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 1d1ec0b6b0a0d237ba4b1a51 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 28255f566e95a17ec90bf4c0 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 31d24a14d1947416de243708 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 7c22775cf1d88543bfa02e74 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| c5338ee1f01a0772d8348583 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 67d69a41d675da1cd53a3ee5 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| a10aca046a54e6ab47beea2b | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 3d08db19a287eb46e9c383b5 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 31a2b7abcf87c5dd67229fdf | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| a7f123c66dc7cc7eb7aace7a | A | 0 / 1 / 1 | True | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Validated alternatives exist, but available evidence does not support choosing a repair. |
| ee202904597874fee5d9e7dd | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| c205ae50eaa55765aa73e396 | A | 0 / 1 / 1 | True | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Validated alternatives exist, but available evidence does not support choosing a repair. |
| 83c3a45aeb8fc61c0434aebf | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 79c26328aebf7b9bf40de164 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| e119cedcc5a20b33d2918072 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| fa6d46b9e3d0f4d2ec2aa39a | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 7bfa54f1963df9d0f1a60de8 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| acf465e815358e847e115ad9 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 5cbfc06acba16d5c32c86ce1 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 624cf9eca2f8a0a5ad7ed699 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 058f5110b6beaee7d79a50f2 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 4d70083a362bcc20755de0d5 | A | 0 / 1 / 1 | True | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Validated alternatives exist, but available evidence does not support choosing a repair. |
| 8a708d30b2fecbb586776770 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 8dd4493dea75622744da9287 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| a03d2a9153cf8760ad1aa35d | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 2d3ec9b038e3cf8fa2fbf35c | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| d94433aaf65c4acd760d8db5 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 9c5e2c20e5281238c1ac6743 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| a3ad2da209c542c550a8c554 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 2748bdb4ea12ee827f4b0b1d | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 1f096e37c65b156bb3c8a690 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 8116bf54c914b116f8a4ae85 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| b7078a70bcbb4a8cd92b0c69 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| d0df4c78c0ed5b5b11e09ab0 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| ebb5eb8b677126ece6e9080d | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 4ed549dc35cd3d16d1f800cc | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 032dea05022bea5ad52f7ad3 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| b2e334c9827e89959124b443 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 5ef083fdefb9c9a9286e4fd3 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| ec0547d041eafcf50f3a2ef6 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 7a3e1b9d69e5cb5f95c41a86 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| f7fb617721f13e81ea80f368 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| ce23186c0084157302d57518 | A | 2 / 0 / 2 | False | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Multiple plausible repairs remain; programmer confirmation is recommended. |
| b0b457c483053d6d84a3fc4d | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| beffb27d52a961ee82c20604 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| a5999587fb869a02d03d52a0 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 0387019e2e834a975a72336e | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| dec73da27b1478e9dfcb30b4 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 6b7cd05f440d4dde731361eb | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 9faf88b85d979e53b6666b2f | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 74a34d1082f76af2a2c4c251 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 53843022da26018d18fcf682 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| bfab4d0588ca428bd6d25647 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 0c5475600fb5cfcbe2aea689 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 5da31af54bfcf5b347eb0037 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| dff00b4ffea5866d9581d444 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 88cb5c2a92fef45744e6145e | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 29bff92166c387190623f383 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 4b25d407b7f636e75b7d1c6a | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 24d7389e3b7caaee04a2d815 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| d20fe2139cc65e4d2c054ed0 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| bb6423dbdf61c7049d4eb4a9 | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 4cf77fb18f4d4d386cf94b01 | A | 1 / 0 / 1 | False | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Validated alternatives exist, but available evidence does not support choosing a repair. |
| 13d8bf7961a59a57312c4a71 | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| d31500f4263a8605a0cb305f | A | 0 / 0 / 0 | False | INSUFFICIENT_EVIDENCE | abstention | False / False | None | No candidate completed compiler validation. |
| 1b600d2cb8bc8e585b76c0b6 | A | 0 / 1 / 1 | True | INSUFFICIENT_EVIDENCE | suggested alternatives | False / False | None | Validated alternatives exist, but available evidence does not support choosing a repair. |
| 9471ca2f5c995adf25900b2d | A | 0 / 1 / 1 | True | SYNTAX_ONLY | recommended repair | True / False | clang_fixit | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |

## Exposed-case outcomes (not an unseen test)

| Case | Class | Adaptive outcome | Exact / wrong | Mode | Explanation |
|---|---|---|---|---|
| 3db39a1a10f4cd0a5e6d42f3 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| a9ae9aea789b39a45a1fe1ae | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 2ae2817d0b8a70863745dce9 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 1a09ec4a316d51ab072d0670 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| d19bdbff34dbbd4c6d1f6535 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 5fd70bfa770da54050ed5658 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| b68a717b0bb663662a524b74 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| f8adeceeb45f269d553954d5 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| dd415587480a949de22a2201 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 804a5018996dbc96bd757eee | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| dabe1d75f3dc3df9883dd10e | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| ab866d4b308fe719c2312dac | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 52d9fe82e6a48de77dfb49e0 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 9fce7ec31171e0412e70f07e | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 295215b1636198187a1cf8ad | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 331173652ceab2f23f8c517f | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| da68feed9bc319e6a2475a1f | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| c23cde4be2a55ede8b3da081 | B | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| f633f80ea3d4d21bd3609437 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| b03e862de257e5ff77011979 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 56a96d003cf6b3c2cd7a6edd | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 24c4def1f11aab4b4e84978f | A | suggested alternatives | False / False | INSUFFICIENT_EVIDENCE | Multiple plausible repairs remain; programmer confirmation is recommended. |
| 6f67a55a4667f474d6f1d001 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| d0500ad7effa4f3c6ed37af2 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| e094eb7ece6f3e912a077025 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 650263c77dead603bfefe339 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 01e950795bb3e2f440ed622f | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 6b1e808b14c53edc1fe4dca6 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| d43660c3da53eade75ad5fca | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 3a49b8cd3127bac31f6fb79f | A | recommended repair | False / True | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 73f19c15332ac1eaa4daa977 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 1384ba97be222abf9aecd974 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| c51fab3abde843bad8c9e954 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 3352f6a69169c82fa6c1ea4a | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 2acba2c49b40982aaea415c2 | A | suggested alternatives | False / False | INSUFFICIENT_EVIDENCE | Validated alternatives exist, but available evidence does not support choosing a repair. |
| baac60b36d43bc0a34566abc | A | recommended repair | False / True | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| d7c5cb24a4f3de56df4e33cf | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 5efa83ff4c832b62b945253e | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 1a42840481a61092778b449c | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 6aefeeb5263ae69d8bb6f6ba | A | suggested alternatives | False / False | INSUFFICIENT_EVIDENCE | Validated alternatives exist, but available evidence does not support choosing a repair. |
| d41d4f6212bcf1486c79edf6 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 15da60b7b649d3c4d511cb9a | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 7c574c4767902ed40e9da9a6 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| c9468ffe90cc6731c4d1320f | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 0ded616efdc6a53ab7c692c2 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| b4c008aa112507a3983226ca | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 9ebf768e96fac12afcc679b2 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| edae0a568771c85fb2f01e01 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 73bebc8e733f3707d0a3dc3b | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 41358c2c9f600d64fd22aeaf | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 0befd7cf976216349383b318 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 6b97566afe5ac92773310e6c | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 8868f10a24286eeb2a71de63 | A | suggested alternatives | False / False | INSUFFICIENT_EVIDENCE | Validated alternatives exist, but available evidence does not support choosing a repair. |
| 47797a644243746ffaf3cc2b | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| d4486d76e11cc74cacd91ed3 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 8bf730761a0949ad5df97dbd | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 0dce2b05da61927d8e2784a1 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| c0c41e25b601c52f9ca9c869 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| d57c3fc5b8bec3c1b9abd002 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 9b50ae98a27dcf39936cdb87 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| a37cee98aec81cb9c4e3d018 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| a4bb70e0d77b8dbd3bcf6653 | A | recommended repair | False / True | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| f2ce1851dd1c844189e7181d | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| dcdf5402328d1f69d6625567 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| a125cabd7fefd3f8dbb95abc | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| fa20df242731979f9f8b26e5 | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| d0c8e27867f77176cdb1bd35 | A | recommended repair | False / True | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 5264170c8d5c8f1773844c2a | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 4373b47d4eb18c50e0d0cd75 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| e51dc0cca80e59f5c0c213f7 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| f179c4f09259453fa64ff9ea | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| d8b1d398ff37fd25843f5d31 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 3729d17d385c3743a733dfeb | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 10177366787df54c8ccc1b65 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 09f193cee0c8848765798a8d | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| bb96ef5455f26c985f1abc7b | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 1ffaad3e56ba9e260f66d4ff | A | recommended repair | True / False | SYNTAX_ONLY | A unique validated local punctuation repair is offered under the lower-assurance syntax policy. Intent and behavior remain unverified. |
| 08a5bacebc1effbb29e3f68d | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 3ecce859eacc822892d77e6e | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |
| 526a5a4984c6157c9e9ccc11 | A | abstention | False / False | INSUFFICIENT_EVIDENCE | No candidate completed compiler validation. |

All four exposed mismatches identified in `ROOT_CAUSE_ANALYSIS.md` remain; none was blacklisted by case ID. Their compiler-valid semicolon edits are insufficient to prove the reference intention. Missing validated candidates, unsupported structural checks, failed checks and unverified suggestions remain distinct in API records. Curated JSON includes all case metrics, provider sets, blocked/unverified counts and the calibration fingerprint, but no student source.

## Reproduction

See `MILESTONE_14_REPORT.md` for PowerShell setup, dataset preparation, explicit development/new/exposed commands, all milestone test commands and browser workflow. `python -m phase6.v14.report` regenerates this report from committed results. Raw sources and detailed candidate programs remain in ignored `.studio-artifacts/m14/`. Any further tuning needs new development data and another frozen evaluation split.
