# Milestone 13 preregistered research protocol

Written before acquiring case contents or examining final evaluation outcomes.
Base: Milestone 12 `d48270d`. Branch: `feature/milestone-13-real-world-validation`.
No recovery algorithm, weights, thresholds, or Studio layout will be changed.

## Questions

* RQ1: Does intent-aware recovery improve intended-repair accuracy over existing
  SmartParse scoring on previously unseen C errors?
* RQ2: Does it reduce incorrect recommendations while maintaining useful coverage?
* RQ3: Does editing history add benefit beyond syntax and semantic-risk scoring?
* RQ4: How does it compare with applicable GCC/Clang fix-its?
* RQ5: How do runtime and failures vary by error category and source complexity?

## Source audit and acquisition plan

Primary candidate: [TEGCER](https://github.com/umairzahmed/tegcer), revision
`0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5`, `data/input/dataset.zip`.
The maintainers describe student error/correction pairs and source/target times.
The repository contains a GPL-3.0 license; inspect archive notices too. Its paired
snapshots supply correction labels, not a preceding editing session. Retain only
code and necessary provenance; exclude identifying metadata. Do not redistribute
student source or the external archive in Git. Commit acquisition instructions,
hashes, sampling metadata and aggregate/evidence records without source excerpts.

Other sources audited: [DeepFix](https://github.com/aar-gee/DeepFix) documents
Apache-2.0 student data but raw compilation failures alone do not establish a
paired intended correction. [DrRepair](https://github.com/michiyasunaga/DrRepair)
separates raw errors from synthetic perturbations; model-generated corrections
are not human ground truth. These are not automatically category A.

## Sampling, grouping and separation

Use UTF-8 strict decoding, optional UTF-8 BOM removal and LF normalization while
preserving raw source hashes and normalized source hashes. Do not strip code,
headers, or comments from engine inputs. Reject NULs, oversized code, obvious
credentials/identifying text and unsafe preprocessing directives/includes.
No source executes. Network acquisition is bounded and pinned; archives are read
without executing their code or extracting arbitrary paths.

Deterministically scan the released CSV, normalize C token identifiers/literals
for grouping, remove identical/near-identical pairs and assign inferred source
families (exact structural match or 64-bit token-shingle SimHash distance <=3).
These are inferred program families, not verified assignments/student identities.
Use seed `smartparse-v13-2026-11-03`; rank families by SHA-256(seed,family).
Select up to 100 distinct families: first 20 development, next 80 final. Select
one deterministic representative per family. No compiler-outcome resampling or
replacement. Sample count can fall if available eligible families are fewer.
Record all filters and realized counts. The same source family cannot cross
splits. No deliberate overlap with prior synthetic benchmarks; additionally
check canonical hashes against v11/v12 available cases.

The engine remains frozen even on development. Final outcomes are examined only
after protocol, acquisition and harness tests are committed. Any harness bug fix
must be documented and rerun consistently, never used to tune repair selection.

## Provenance categories and primary denominator

A: maintainer-documented human error/correction pair, source rejected and target
accepted by at least one **same** available compiler under frozen settings.
This verifies compilation of the intended dataset correction, not its behavior.
B: genuine reported error without a locally verified compatible correction.
C: synthetic/reconstructed errors; never counted as real-world primary accuracy.
D: excluded/unsupported inputs, unavailable validation, or no current compilation
failure. Keep these categories separate and report reasons and denominators.
Only final-split A cases contribute to primary exact-intended-repair metrics.
All selected cases remain in availability/compatibility accounting.

## History and leakage controls

Conditions are recorded real events, partial genuinely chronological **prior**
snapshots, no history, and explicitly synthetic/reconstructed history. Do not
create engine history by reversing the future corrected target. TEGCER endpoints
alone cannot supply a history before the buggy source; default is **no history**.
Only authenticated earlier events/snapshots, matching the submitted source with
timestamps no later than its time, can enter history. Reject target/future
snapshots and any reference-bearing engine input. Keep correction loading and
metrics separate from the source/history-only recovery request.
If there are no eligible real histories, RQ3 is not identifiable; do not simulate
a history advantage or relabel reconstructed data as observed human edits.

## Frozen systems and compiler settings

Compare v12 `existing`, `history`, `semantic`, `full` with one identical bounded
candidate pool per input. Retain margin 12, 24 candidates, 240 original trials
and existing 15-second intent compiler budget. Hash frozen v11/v12 modules before
and after evaluation. Size/unsupported inputs produce explicit abstention.
Measure both complete engine evidence construction and per-mode ranking time.

GCC/Clang identity/version and flags are recorded. Invoke only syntax checking,
stdin source, C11, no diagnostic colors, parseable fix-its when capability-probed;
never link/run programs. Use existing bounded runner, private temporary working
directories and finite per-call deadlines. Do not claim OS-level sandboxing.
Reject arbitrary includes/directives before compiler use and mark portability
failures separately. No diagnostics from corrected programs enter recovery.
Capture original diagnostics/exit/runtime, reliable physical machine fix-its,
applicability reasons, nonoverlapping edit bundle, repaired compilation and
reference match. Do not extract repairs from diagnostic prose. GCC/Clang lacking
applicable fix-its have zero repair-output coverage, not bad diagnostic accuracy.

## Metrics and analysis

Report exact normalized-source match, C-token match (ignoring whitespace/comments
only), compilation acceptance and behavioral equivalence as distinct outcomes.
Behavioral equivalence is **not assessed**. Wrong recommendation means exact
reference mismatch; compilable mismatch may be behaviorally equivalent.
Report exact/top-3 intended coverage, wrong/abstention/recommendation rates,
accuracy conditional on recommendation, compilable mismatch, validation status,
compiler repair-output coverage and runtime distributions. Show every numerator
and denominator, including N=0 as unavailable, not zero accuracy.

Break down by diagnostic category, source lines/tokens, diagnostic error count
(not a claimed independent-defect count), history condition, valid candidate
count, compiler compatibility, semantic UNKNOWN/CHANGED status and family/source.
Use seeded 2,000-replicate family bootstrap percentile intervals and paired
case/family differences where denominators permit. Report Wilson intervals for
observed proportions including zero-event uncertainty. Do not infer zero future
risk from a degenerate bootstrap. No significance or general-superiority claim
without suitable independent evidence. Selective-prediction analysis uses the
fixed primary policy plus explicitly labeled stricter post-hoc gap selectors;
no selectors are tuned on final outcomes or deployed to Studio.

## Deliverables and preservation

All reports must reflect actual acquisition, compiler and evaluation outcomes.
If acquisition/licensing is blocked, report counts as unavailable and deliver
tested ingestion/comparison infrastructure without fabricated real-world data.
Keep raw/normalized external data and diagnostics in ignored `.studio-artifacts/m13/`.
Commit only necessary manifests, safe per-case hashes/metrics and aggregate
research outputs. Preserve v11/v12 source/results and older frozen artifacts;
hash-check them and existing acceptance outputs around regressions. Run unit,
backend and frontend regressions/build. Do not push/merge without user approval.
