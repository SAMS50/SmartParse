# Milestone 14 evaluation protocol

Root-cause audit `b735ce0` was completed before adaptive implementation. Preserve
all v11/v12/v13 engines and outputs. The old 79 A cases were exposed in v13 and
inspected for this required diagnosis: report them only as an exposed benchmark.

Use the pinned TEGCER archive and v13 ingestion/safety/license policy. Rebuild
the deterministic family ranking with 180 requested families. Preserve the old
20 development and 80 exposed records; use the next up-to-80 families, with no
source/family overlap, as a new unexamined evaluation split. No replacement based
on compiler outcomes. Inferred families are not independently verified student or
assignment identities; this is a fresh split of one dataset, not external-project
validation. Student source stays local; commit only hashes/metadata/metrics.

Calibrate on the original 20 development pairs only. Candidate policy grid:
one versus two local punctuation-edit hunks. Require complete compiler validation,
reliable physical mappings, and no verified structural hazard or failed check.
Syntax-only recommendations must be unique token-level valid programs and insert
only semicolons/commas; braces, operator changes and unresolved alternatives are
suggestions rather than recommendations. Other evidence modes may support broader
repairs with explicit evidence. Missing signals contribute zero, never a numeric
penalty; verified structural change is a hard veto, never a fallback opportunity.
Choose minimum wrong exact-source recommendations, then maximum correct ones,
then the smaller hunk cap. Keep score margin 12; do not fit case identifiers.
Freeze engine/provider/semantic policy hashes and selected cap before opening new
evaluation outcomes. No post-evaluation policy tuning.

Compare v13 existing and full; adaptive custom-only, compiler-only, combined;
combined without positive semantic support and without positive history support;
and a simple highest-score validated-syntax fallback on the same combined pool.
All combined-pool policy ablations use identical candidates; different providers
have explicitly different pools. Hard known hazards/mapping failures remain vetoes
even when positive evidence is ablated. Track this safety distinction explicitly.

Custom proposals use existing lexer/parser rules with protected standard-header
lines masked only during proposal generation, never during actual compilation.
Clang proposals use machine physical-range fix-its: individual hints, nonoverlapping
bundles, and at most one additional fix-it round for a failed bundle. Bound candidate
retention to 24; retain provider origins through deduplication. Compiler-generated
repairs are credited to Clang, not a new SmartParse syntax-repair algorithm.

Semantic outcomes distinguish supported comparison agreement, verified structural
difference, unavailable reference, unsupported constructs and failed checks. An
inserted empty control body can be verified from the repaired AST and edit mapping
without assuming the invalid original AST was complete. No formal behavioral
equivalence claims. Preprocessor/macro edit mappings must not be guessed.

Primary metrics use A pairs (same-compiler broken source + compiling target), with
B/D cases separately recorded; reference text/diagnostics never enter generation
or policy. Report exact and token matches separately, wrong/abstention/alternative
outcomes, candidate coverage, compilation, provider/mode distributions and runtime.
Use seeded paired family bootstrap and Wilson intervals, acknowledging small N,
correlation and zero-event limits. Compare adaptive with simple fallback fairly;
if equal, explicitly decline superiority claims. No C programs execute. Finite
compiler deadlines, private files, no source overwrites, no OS-sandbox claims.

## Correctness amendment after first evaluation

A test-owned Unicode-comment regression exposed a byte/code-point mismatch in
the new empty-control-body check. Correct the Clang byte offsets, without changing
weights, thresholds, providers or selection rules, then rerun development and
both frozen evaluation splits. Preserve first-run records locally and verify
decision changes explicitly. Two of the 180 sampled erroneous sources contain
non-ASCII text; do not assume their decisions are unaffected. The new set was unexamined before its
first run, but is exposed for this correctness rerun; make no pristine-test or
strong generalization claim for the rerun. Do not use its outcomes to optimize.
