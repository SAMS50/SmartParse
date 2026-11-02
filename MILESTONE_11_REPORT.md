# Milestone 11: intent-preserving syntax recovery

## Outcome and scope

Implemented an opt-in, deterministic recovery ranker in the existing repository,
integrated into Studio's Recovery tab. It uses verified editing history and
conservative Clang AST projections, with explicit abstention and read-only
comparisons. Existing CLI, panic baseline, recovery, isolation and tabs remain.

On the 20-case reconstructed/synthetic evaluation, full scoring produced 7 exact
recommendations, 1 incorrect recommendation and 12 abstentions. Same-pool old
heuristic scoring produced 5 exact, 12 incorrect and 3 abstentions. The original
parser repair plan exactly restored 2/20. This demonstrates a narrow improvement
in selection/abstention, not established general research superiority. The valid
but misleading snapshot case still causes a wrong recommendation. There are no
recorded human editing sessions or independently adjudicated labels.

## Architecture and established techniques

See `phase6/v11/ARCHITECTURE_AUDIT.md`. Candidate generation reuses
`recovery.rank_candidates`, the custom parser's repair plan and existing Clang
fix-it parsing. Strict parsing cheaply filters bounded punctuation alternatives;
Clang validates complete candidate programs. All modes receive the same pool.
Full-C outside the custom grammar receives applicable compiler fix-its; there is
no new general C repair search. Plans allow existing multi-error recovery.

Compiler diagnostics, strict parsing, ASTs, edit replay and weighted ranking are
established techniques. The proposed contribution here is their explicit
combination for intent-sensitive ranking and conservative recommendation
decisions, with separately inspectable evidence. No LLM selects a repair.

`smartparse_studio/api/worker.py` adds optional `report.intent_recovery`; existing
report consumers continue to work. The unified CLI is unchanged; a separate
`python -m phase6.v11` entry point exposes the new engine. Studio remains
loopback-only with one worker at a time. Worker deadline is 75 seconds, allowing
the existing 45-second engine and 15-second intent compiler budget plus cleanup.
The invocation count in `intent_recovery` is separate from existing engine usage.

## Candidate generation and validation

No candidate generator receives history or evaluator ground truth. Local repair
eligibility/heuristics come from existing code. Additional punctuation insertions,
deletions and substitutions at lexer token positions use a default 240-trial,
24-retained-program limit. Programs are deduplicated by complete repaired text;
the strongest reused heuristic evidence wins. Alternatives without a legacy
score receive a documented minimal single-edit score of 10; Clang fix-its use 35.
The existing parser plan uses its mean reported edit score. These are design
weights, not learned probabilities. Truncation and original validation status
are exposed. Search may miss intended repairs, especially late in large inputs.

Each candidate includes source, exact diff ranges and original code-point
line/column, generation origin, existing heuristic, validation, history and AST
evidence, score components, explanation and classification. IDs are SHA-256
prefixes of repaired text; tie-breaking is deterministic by ID. Compiler rejection
is INVALID; unavailable tools, fatal compilation environment errors, failed AST
loading and budget exhaustion are UNVERIFIED. Neither can be recommended.
Compiler acceptance is syntax/type evidence, not correctness.

The intent entry point caps source at 16384 Unicode code points; Studio's existing
128 KiB limit still applies to other analyses. Compiler calls have two-second
individual limits and a 15-second shared intent deadline. Parser trial counts and
source limits bound local work; this is not a hard real-time CPU guarantee.

## Editing history model

Studio records aggregate editor replacements per document in memory. Each event
has consecutive version, code-point offset, exact deleted text and inserted text.
Unicode conversion avoids confusing Monaco's UTF-16 offsets with Python offsets.
Undo is captured as an ordinary inverse edit. Rapid callbacks use the previous
captured source; explicit reset revisions invalidate earlier chains. Closed files
drop histories. No history is stored on disk or sent until opt-in Analyze.

The transport retains eight events by rolling older edits into a base snapshot;
large histories fall back conservatively. API models strictly validate event
types, sizes, offsets and allowed modes. Engine replay checks versions, exact
deleted slices, final text and final version. An inconsistent chain blocks all
recommendations, including the baseline ablation. The history window is
configurable through Python `Config`.

For verified snapshots, define changed-character mass D(a,b) as the sum of
max(deleted span length, inserted span length) over deterministic SequenceMatcher
opcodes (`autojunk=False`). This is explicitly not Levenshtein distance.

Let R indicate exact restoration of any retained preceding snapshot, delta be
D(current,last_previous)-D(candidate,last_previous), and d be minimum separation
between changed-span start offsets in the latest edit and candidate repair:

`H = 40 R + 10 clamp(delta,-2,2) + 5 max(0,1-d/40)`.

Missing history gives H=0 with explanation. Proximity uses latest pre/current
coordinate start positions and is only weak evidence; multiple disjoint edits can
make this approximate. Recent snapshot restoration can reflect an intentional
edit, so it is never proof of intent. Every feature and contribution is reported.

## Conservative structural and semantic-risk evidence

Only valid Clang JSON ASTs are projected. The newest valid historical snapshot
provides reference evidence; if unsupported, the analyzer returns UNKNOWN instead
of skipping it to claim preservation against an older reference. Invalid original
ASTs are never compared as complete programs. Valid candidates are additionally
compared to the highest ranked valid candidate, with distinct explanatory labels.

Supported subset: self-contained ASCII scalar C functions, local/parameter
declarations, arithmetic/literals, calls without pointer arguments, blocks,
if/else/for/while, return, break and continue. Preprocessing, globals, arrays,
pointer variables, records, casts, switch/goto, volatile/atomic, non-ASCII sources
and unrecognized AST kinds yield UNKNOWN. Macro rejection is intentionally broad.

Seven concrete projections track statement ownership, block boundaries, variable
scope, references resolved to declaration paths (including shadowing), expression
trees/literals, function signatures/boundaries and control-flow subtrees. AST IDs,
physical offsets and implicit builtin declarations do not enter equality.
Results are PRESERVED, CHANGED, UNKNOWN or NOT_APPLICABLE. Empty comparable
projections are NOT_APPLICABLE. PRESERVED means only equality of the supported
projection; it does not establish formal equivalence, undefined-behavior safety,
data-flow equivalence or intended behavior. This coarse whole-function comparison
can over-penalize benign changes. Unaffected-region proof is not implemented.

## Ranking, ablations and abstention

For syntactically VALID candidates:

`S = B + wH H - wC (# CHANGED checks) - wU (# UNKNOWN checks)`.

Defaults: wH=1, wC=18, wU=4; B is the reused heuristic as described above.
Evidence completeness has an explicit UNKNOWN penalty. `existing` uses B only;
`history` adds H; `semantic` adds AST penalties; `full` uses all components.
The semantic-only ablation still needs valid history snapshots as structural
references, but excludes edit-distance/restoration/proximity scores. Ranking is
deterministic for fixed inputs, toolchain and successful validation budget.
Resource exhaustion can change which candidates are verified and is exposed.

Default ambiguity margin is 12 score units. A second eligible candidate within
that margin triggers: "Multiple plausible repairs were found. Programmer
confirmation is recommended." This intentionally abstains even for equivalent
ties; it does not assume distinct text proves different runtime behavior.

Full/semantic recommendation requires reliable mappings, no UNKNOWN or CHANGED
checks on the best candidate, and a margin greater than 12 if alternatives exist.
History-only requires exact verified snapshot restoration and sufficient margin.
Existing scoring recommends its highest validated heuristic, to reproduce the
non-abstaining ranking comparison. Empty/invalid pools, unsupported analysis,
missing relevant evidence and unreliable mappings return explicit no-safe or
unsupported decisions. An already valid original has no proposed repair.

Classifications: recommended repair, alternative repair, ambiguous repair,
unsupported repair, no safe recommendation. No confidence percentages or
fabricated probabilities are used. A recommendation never auto-applies edits.

## Benchmark construction and results

`phase6/v11/benchmark.py` contains 20 reproducible cases: eight authored C
microprograms under verified/missing history (16), one misleading valid history,
one inconsistent version, and two mutations of existing repository fixtures
(`S01.c`, `C12_valid_full.c`). Delimiter, ownership, else/loop, shadowing,
expression, pointers, multiple-error and unsupported full-C cases are represented.
All ground truths are independently compiler-validated by the evaluator.

All edits are synthetic/reconstructed; **zero real human edit recordings** are
available. Histories legitimately contain pre-edit snapshots/deleted text,
frequently reconstructing the intended version; this is an optimistic and
explicit experimental condition. Hidden ground truth is used only by evaluator
metrics and is never passed as a candidate seed or scoring argument. Missing and
misleading history controls expose the limits of that assumption. This small,
development-time corpus is not an independent held-out evaluation.

Committed machine output: `phase6/v11/results/benchmark.json`. Numerators and
denominators below refer to shared-pool ranking; independent full-system reruns
gave the same decisions. No timing claim is statistically established.

| Metric | Existing score | + History | + Semantic | Full |
|---|---:|---:|---:|---:|
| Exact intended recommendation | 5/20 | 4/20 | 2/20 | 7/20 |
| Top-3 intended repair | 14/20 | 16/20 | 16/20 | 16/20 |
| Wrong recommendation | 12/20 | 1/20 | 1/20 | 1/20 |
| Compilable exact-intent mismatch | 12/20 | 1/20 | 1/20 | 1/20 |
| Abstention | 3/20 | 15/20 | 17/20 | 12/20 |
| Accuracy among recommendations | 5/17 | 4/5 | 2/3 | 7/8 |
| Intended candidate coverage | 18/20 | 18/20 | 18/20 | 18/20 |
| Structural mismatch among analyzable recommendations | 11/15 | 1/3 | 1/3 | 1/8 |
| Mean ranking ms | 2.83 | 2.11 | 2.01 | 1.79 |
| Mean full-system ms | 783.84 | 804.22 | 878.22 | 823.24 |

Mean candidate generation: 787.51 ms. Full-system overhead versus same-pool
existing-score mode: about 39.39 ms (5.0%) on this run. Fixed ordering, one run,
tool startup, filesystem and concurrent validation affect timings. The apparently
faster full ranker is measurement noise, not a speedup claim. Rank timing includes
evidence materialization; full-system timing includes generation and validation.

"Wrong" and "compilable incorrect" here operationally mean a selected VALID
program differs from the exact intended source. They do not prove different
observable behavior. Structural rates exclude UNKNOWN projections and expose
their smaller denominators. No repaired C program is executed by this benchmark.
Recommendation-independent behavioral test oracles remain future work.

The actual old Parser's repair plan exactly restored 2/20, separately from the
expanded-pool old-score ablation. Panic mode produces diagnostic continuation,
not repaired source, so exact-repair accuracy is not assigned to it.

GCC and Clang rejected 20/20 malformed inputs. GCC emitted zero applicable
machine-convertible fix-it sets, so its exact-repair denominator is 0. Clang
emitted applicable fix-it sets on 4/20 and exactly restored 2/4. Its diagnostic
coverage is not compared with repair accuracy; per-case diagnostics, fix-it
applicability and timing are in the JSON. Fix-it conversion applies nonoverlapping
physical stdin ranges, rather than interpreting diagnostic prose as a repair.

The misleading valid history restores a different if-block ownership and yields
the one incorrect full recommendation. Both programs compile and the historical
reference supports the wrong intent. The analyzer cannot infer that this valid
history is misleading. Missing histories all abstain in full mode. Unsupported
repository/full-C cases also abstain; there is no claim of full-C coverage.

## Demonstration and tests

`python -m phase6.v11.demo` starts with a valid function, reconstructs an accidental
closing-brace deletion and prints actual engine output for every ablation. The
old plan appends a brace at EOF, changing return ownership; full scoring restores
the deleted brace. Original text is preserved. Demo output is generated, not a
hardcoded expected decision. `browser_smoke.py` exercises real Monaco paste,
delimiter deletion, opt-in request history, recommendation, exact diff,
reanalysis preserving source, and ordinary editor undo.

Validation performed: repository unittest discovery, 523 tests with 28 optional
tool skips; subsequent final targeted suite, 11 tests passed; Studio Vitest,
69 tests passed; TypeScript/Vite production build passed (existing large-bundle
warning). The existing regression suite regenerates `results/verified_performance.csv`;
that test side effect was restored to its originally clean committed contents.
Historical outputs are excluded from milestone changes. Browser results are
recorded separately in the final validation record.

Tests cover replay, Unicode/version/offset consistency, candidates/deduplication,
validation, deterministic rank, history fallback, ambiguity, unsupported syntax,
ownership/control-flow/scope/binding/grouping/function/literal changes, strict API
models, frontend history and evidence rendering. These are structural regression
tests, not independent semantic correctness proofs.

## Reproduction in PowerShell

From repository root, use the existing environment and installed compilers:

```powershell
.\.studio-venv\Scripts\python.exe -m uvicorn smartparse_studio.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Set-Location studio
npm.cmd run dev
```

Enable **Analysis settings → Intent-aware recovery**, edit valid C, then Analyze.
History is session-only. To benchmark, demonstrate or test from root:

```powershell
.\.studio-venv\Scripts\python.exe -m phase6.v11.benchmark --full-system --output .studio-artifacts/m11/reproduced.json
.\.studio-venv\Scripts\python.exe -m phase6.v11.demo
.\.studio-venv\Scripts\python.exe -m phase6.v11 example.c --mode full
.\.studio-venv\Scripts\python.exe -m unittest discover
.\.studio-venv\Scripts\python.exe -m unittest discover -s phase6/v11 -t .
Push-Location studio
npm.cmd test
npm.cmd run build
Pop-Location
python -m phase6.v11.browser_smoke --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

The browser command uses system Python with existing Playwright; the Studio venv
does not contain Playwright. No package or browser installation was performed.
Clang is required for validation and supported semantic evidence. Existing
`SMARTPARSE_CLANG` and `SMARTPARSE_GCC` discovery overrides apply. Historical
benchmarks should be run in a disposable checkout if executing all legacy tests.

## Changed-file inventory

New files: this report; `phase6/v11/ARCHITECTURE_AUDIT.md`, `__init__.py`,
`__main__.py`, `history.py`, `semantics.py`, `engine.py`, `benchmark.py`, `demo.py`,
`browser_smoke.py`, `test_history.py`, `test_semantics.py`, `test_engine.py`,
`test_api.py`, `results/benchmark.json`, `results/demo.json`, `VALIDATION.md`;
`studio/src/lib/editHistory.ts`, `studio/src/lib/editHistory.test.ts`.

Modified: `README.md`; `smartparse_studio/api/models.py`, `worker.py`, `service.py`;
`studio/src/App.tsx`, `types/report.ts`, `components/SettingsPanel.tsx`,
`components/Inspector.tsx`, `components/Inspector.test.tsx`,
`components/CodeEditor.tsx`. No historical benchmarks or frozen fixtures changed.

## Limitations and next evidence needed

No formal semantic equivalence; conservative AST equality only. No general
multi-error candidate exploration beyond reused plans. No real edit recordings,
human labels, held-out corpus, behavioral execution oracle or broad real-world
repair evaluation. History can encode a prior intention that no longer holds.
Search/validation budgets reduce coverage; source contexts/includes are still
single-file Studio contexts. Source mappings are code-point physical ranges,
not general macro/source-map proofs. Whole-program whitespace differences count
against exact accuracy even when behavior might agree. Config weights are
initial hypotheses, not trained/calibrated confidence estimates. These limits
must be addressed before claiming general research superiority.
