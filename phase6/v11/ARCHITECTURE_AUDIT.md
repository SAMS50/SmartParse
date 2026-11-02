# Milestone 11 architecture audit

Starting point: Studio `4fa5b85`, branch `feature/smartparse-studio`, based on
the extended-C and phase6 release implementations. Local branches and remote
tracking refs were inspected. No tracked modifications existed; pre-existing
untracked `acceptance/output/` records are excluded from milestone commits.

* `smartparse.py`: custom lexer, recursive descent, StrictParser, local probing,
  bounded multi-edit and CGAR recovery. Grammar is intentionally restricted C.
* `recovery.py`: deterministic insertion/substitution/deletion eligibility and
  contextual score factors. Reuse for heuristic evidence, without changing it.
* `baseline.py`: same grammar, panic synchronization at semicolon/block boundary;
  diagnostic continuation, not a source-repair recommendation baseline.
* `extended_c/backend.py`, `static_analysis.py`: GCC/Clang syntax/type checking
  and static diagnostics. `phase6/v3/engine.py` adds bounded execution, physical
  AST inventory, VFS temporary variants and conservative semicolon fix-its.
* `smartparse_cli/engine.py`: unified report and analyzer orchestration;
  `analyze_c.py` retains the earlier real-C entry point.
* `smartparse_studio/api/`: strict Pydantic request, loopback-only FastAPI,
  serialized bounded worker, hash-verified source preservation and previews.
* `studio/src/`: React file workspace, Monaco per-document models/undo,
  Inspector Recovery tab and read-only exact diff. No edit-history transport.
* Root tests and `phase6/v*/test*`, Studio Vitest/browser smoke, historical
  benchmarks and METHODOLOGY document existing capabilities and limitations.
  Frozen outputs remain untouched. No existing intent-aware ranker or complete
  ownership/binding comparison was found.

Use `phase6/v11/` consistently with prior research milestones. Add an opt-in
worker result alongside existing report fields, a bounded history model, Clang
AST comparison of valid snapshots/candidates, transparent ranker and abstention.
Keep CLI/default behavior and all previous recovery engines intact. Candidate
generation must not consume evaluation ground truth or history snapshots.

Installed tools: Studio Python environment; Clang discovered through existing
bounded NDK lookup; GCC through MinGW. pycparser is absent, so use Clang JSON AST
instead of introducing another parser dependency. Compiler success is syntax/type
evidence only, never semantic correctness.
