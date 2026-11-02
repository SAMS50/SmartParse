# Milestone 12 evaluation

Frozen algorithm/dataset fingerprint: `9322e5d40a504760b990033eae5f41dfbfe30f536912bcde3897f51dda750036`. Development-selected margin: **12**. No algorithm or dataset change after the held-out run. The original 20 are historical comparisons, not development or held-out samples.

## Dataset and protocol

84 new deterministic cases: 32 development cases in 8 source families; 52 held-out cases in 13 families (12 authored routine families plus one repository-memory family containing 4 distinct C fixtures). All token-deletion histories are synthetic/reconstructed. There are zero recorded human editing sessions or independently adjudicated labels. Real Chrome events are integration tests, excluded from accuracy denominators.

Identifiers/numbers are normalized for deduplication; development and held-out share neither normalized malformed programs nor source-family IDs. Multiple mutations of a family remain correlated, so intervals resample families. This reduces leakage but does not establish independence across conceptual algorithm families. All valid reference programs are checked by an evaluator-owned compiler. The generator receives only malformed source, never truth or history. Legitimate history snapshots/deleted text can reconstruct the pre-edit program; that optimistic condition is explicitly labeled.

Both versions use margin 12 in primary results. All four modes within each version share a candidate pool. Cross-version pools and semantic coverage differ; generation coverage is reported rather than attributing all gains to ranking. `existing` denotes contextual heuristic ranking on that version’s pool, not a new claim about the old parser’s source reconstruction. V11 code/results are unchanged.

## Development versus held-out

| Split / system | Correct | Wrong | Abstained | Accuracy among recommendations | Top-3 | Intended candidate generated |
|---|---:|---:|---:|---:|---:|---:|
| Development / v11-existing | 15/32 | 10/32 | 7/32 | 15/25 | 18/32 | 20/32 |
| Development / v11-full | 11/32 | 3/32 | 18/32 | 11/14 | 20/32 | 20/32 |
| Development / v12-existing | 16/32 | 8/32 | 8/32 | 16/24 | 22/32 | 25/32 |
| Development / v12-history | 9/32 | 0/32 | 23/32 | 9/9 | 25/32 | 25/32 |
| Development / v12-semantic | 18/32 | 0/32 | 14/32 | 18/18 | 25/32 | 25/32 |
| Development / v12-full | 19/32 | 0/32 | 13/32 | 19/19 | 25/32 | 25/32 |
| Held-out / v11-existing | 28/52 | 13/52 | 11/52 | 28/41 | 35/52 | 36/52 |
| Held-out / v11-full | 16/52 | 4/52 | 32/52 | 16/20 | 35/52 | 36/52 |
| Held-out / v12-existing | 28/52 | 13/52 | 11/52 | 28/41 | 39/52 | 40/52 |
| Held-out / v12-history | 15/52 | 0/52 | 37/52 | 15/15 | 38/52 | 40/52 |
| Held-out / v12-semantic | 28/52 | 0/52 | 24/52 | 28/28 | 38/52 | 40/52 |
| Held-out / v12-full | 28/52 | 0/52 | 24/52 | 28/28 | 38/52 | 40/52 |
| Historical / v11-existing | 5/20 | 12/20 | 3/20 | 5/17 | 14/20 | 18/20 |
| Historical / v11-full | 7/20 | 1/20 | 12/20 | 7/8 | 16/20 | 18/20 |
| Historical / v12-existing | 7/20 | 12/20 | 1/20 | 7/19 | 16/20 | 20/20 |
| Historical / v12-history | 4/20 | 0/20 | 16/20 | 4/4 | 18/20 | 20/20 |
| Historical / v12-semantic | 6/20 | 1/20 | 13/20 | 6/7 | 18/20 | 20/20 |
| Historical / v12-full | 8/20 | 0/20 | 12/20 | 8/8 | 18/20 | 20/20 |

The initial development run exposed a merged identifier/control-keyword error and an implicitly declared function accepted by this Clang version. A bounded lexical-boundary candidate and C99+ declaration validation were added before the final development selection. All margins 0, 6, 12, 24 tied on the final development result; the predeclared tie rule retained 12. Thus the data did not identify a superior numeric margin. `d91f95c` froze this selection before held-out evaluation.

## Missing, misleading and incomplete history (held-out)

| History condition | N | V11 correct / wrong | V12 correct / wrong |
|---|---:|---:|---:|
| incomplete | 3 | 0 / 0 | 0 / 0 |
| local | 33 | 16 / 0 | 17 / 0 |
| misleading | 4 | 0 / 4 | 0 / 0 |
| missing | 12 | 0 / 0 | 11 / 0 |

V12 full and semantic-only make the same held-out recommendations: no incremental benefit from history scoring is demonstrated on this set. History-only is more conservative. Reliability gates apply to all enhanced modes and are deliberately separate from the numerical history-score ablation. A valid replay is not a guarantee of current intent.

## Selective prediction

Primary margin sweeps 0, 6, 12, 24 are flat in both versions on held-out data: v11 stays at 20/52 coverage and 16/20 accuracy; v12 stays at 28/52 coverage and 28/28 accuracy. Fixed reliability/consensus gates dominate these decisions. This is a reported negative calibration result, not evidence that margin is irrelevant on other data.

The following **diagnostic-only** stricter score-gap selectors remove already-issued full-mode recommendations when a finite top-two gap falls below the listed threshold. Singleton pools have infinite gap. They do not enable withheld predictions, are not deployed Studio policies, and were not used for tuning. All thresholds are shown so coverage/accuracy is not compared under hidden selectors.

| Minimum gap | V11 recommendations / 52 | V11 correct / recommended | V12 recommendations / 52 | V12 correct / recommended |
|---:|---:|---:|---:|---:|
| 0 | 20/52 | 16/20 | 28/52 | 28/28 |
| 12 | 20/52 | 16/20 | 28/52 | 28/28 |
| 60 | 20/52 | 16/20 | 28/52 | 28/28 |
| 120 | 19/52 | 15/19 | 23/52 | 23/23 |
| 240 | 16/52 | 14/16 | 22/52 | 22/22 |

A large heuristic gap is not calibrated correctness confidence: misleading histories can have very large gaps. Stricter selection can discard correct repairs and retain incorrect ones. Exact-intent accuracy is not a behavioral equivalence metric.

## Uncertainty

Seeded 2,000-replicate source-family bootstrap percentile intervals (exploratory 95%, not formal significance tests):

| System | Exact recommendation rate | Wrong recommendation rate | Accuracy when recommending |
|---|---|---|---|
| v11-full | 0.212–0.423 | 0.019–0.135 | 0.667–0.944 |
| v12-full | 0.385–0.673 | 0.000–0.000 | 1.000–1.000 |

V12’s zero-error bootstrap degenerates to zero observed error / perfect observed selective accuracy. It does **not** establish zero future risk. With 13 independently sampled families assumed, zero observed error families still permit a one-sided 95% upper bound of 0.206 on the probability a family contains an error. These families are authored rather than randomly sampled, further limiting inference. No statistical significance, broad general superiority or non-inferiority claim is made.

## Runtime

| Split | V11 generation ms | V12 generation ms | V11 end-to-end ms | V12 end-to-end ms |
|---|---:|---:|---:|---:|
| Development | 385.94 | 451.32 | 434.61 | 438.08 |
| Held-out | 480.22 | 560.94 | 582.00 | 614.70 |
| Historical | 745.03 | 805.49 | 754.13 | 854.23 |

Held-out mean end-to-end overhead: 32.70 ms (5.6%). Ranking-only and independent full-system recommendation decisions differed on 0 version/case pairs. Single-run timings include compiler startup and concurrent local validation; fixed ordering and cache/OS effects prevent a performance-significance claim. Rank timings and full evidence are in the JSON.

## Failure examples and remaining abstentions

| Held-out case | Intended candidate generated | V12 decision reason |
|---|---|---|
| factorial-block | True | End-of-source brace restoration conflicts with other valid statement-ownership structures; programmer confirmation is recommended. |
| factorial-multiple | True | Source mappings are unreliable |
| power-multiple | False | Broad recent replacement provides insufficient intent evidence |
| fibonacci-multiple | True | Broad recent replacement provides insufficient intent evidence |
| clamp-block | True | End-of-source brace restoration conflicts with other valid statement-ownership structures; programmer confirmation is recommended. |
| clamp-multiple | True | Broad recent replacement provides insufficient intent evidence |
| collatz-multiple | True | Source mappings are unreliable |
| lcm-semicolon | False | No candidate satisfies syntax validation |
| lcm-parenthesis | False | Insufficient supported intent evidence |
| lcm-block | False | Multiple plausible repairs were found. Programmer confirmation is recommended. |
| lcm-multiple | False | Broad recent replacement provides insufficient intent evidence |
| primality-block | True | End-of-source brace restoration conflicts with other valid statement-ownership structures; programmer confirmation is recommended. |
| primality-multiple | False | Broad recent replacement provides insufficient intent evidence |
| largestdivisor-multiple | False | Broad recent replacement provides insufficient intent evidence |
| alternatingsum-multiple | True | Source mappings are unreliable |
| reverse_digits-block | False | End-of-source brace restoration conflicts with other valid statement-ownership structures; programmer confirmation is recommended. |
| reverse_digits-multiple | False | Broad recent replacement provides insufficient intent evidence |
| floor_sqrt-multiple | True | Broad recent replacement provides insufficient intent evidence |
| sum_squares-block | False | Insufficient supported intent evidence |
| sum_squares-multiple | False | Broad recent replacement provides insufficient intent evidence |
| repository-C01_null.c | True | The behavioral impact could not be determined. |
| repository-C02_leak.c | True | The behavioral impact could not be determined. |
| repository-C03_double.c | True | The behavioral impact could not be determined. |
| repository-C04_uaf.c | False | No candidate satisfies syntax validation |

`lcm-*` illustrates insufficient candidate exploration for multiple functions and merged/late boundaries. No post-held-out repair tuning was performed. Multi-error histories reconstructed as one broad replacement can trigger conservative abstention despite several tiny actual deletions. Candidate coverage and exactness remain limited by bounded search and formatting. Pointer/resource fixtures remain unsupported; these are appropriate abstentions rather than demonstrated recoveries. Historical scalar-global and unique punctuation cases improve, while a broad multi-edit history loses a previously correct recommendation.

Only syntax/type acceptance and structural projections are checked; no repaired program is executed, and undefined behavior, aliasing, data-flow equivalence and programmer intent are not proven. “Wrong” means compilable exact-source mismatch, which can include behaviorally equivalent text. All correct labels are evaluator-derived synthetic ground truths.

## Reproduction

From repository root in PowerShell:

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v12.evaluate --split development --full-system --selection .studio-artifacts/m12/reproduced-selection.json --output .studio-artifacts/m12/reproduced-development.json
.\.studio-venv\Scripts\python.exe -m phase6.v12.evaluate --split heldout --full-system --selection .studio-artifacts/m12/reproduced-selection.json --output .studio-artifacts/m12/reproduced-heldout.json
.\.studio-venv\Scripts\python.exe -m phase6.v12.evaluate --split historical --full-system --output .studio-artifacts/m12/reproduced-historical.json
.\.studio-venv\Scripts\python.exe -m phase6.v12.report
```

The report renderer reads committed results; reproduction commands write new run outputs outside tracked directories. The original v11 benchmark can be rerun independently with `python -m phase6.v11.benchmark --full-system --output .studio-artifacts/m12/reproduced-v11.json`.
