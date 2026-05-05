# Current State

## Git

- Baseline commit: `75218fc`.
- Working branch: `refactor/research-audit-prototype-upgrade`.
- Local Git identity: `Codex <codex@local.invalid>`.
- History has not been rewritten.

## Repository State

- Source, configs, tests, docs, lockfiles, tooling, and small JSON/YAML summaries are tracked.
- Raw `/data/`, generated `/output/`, temp folders, local agent state, virtualenvs, generated figures, arrays, CSVs, and benchmark markdown reports are ignored.
- Core data-ingestion source under `src/lsd_thesis/data/` is trackable.
- Repo hygiene helper and test now guard against source paths becoming ignored again.

## Working Scientific State

- Implemented: 8-module stochastic graph surrogate, ds003059 extraction, sober fitting, perturbation ranking, ablation, dashboard, publication helpers, and training benchmarks.
- Present but broken: current perturbation effects do not cleanly match every intended macro signature.
- Proposed: robustness, atlas sensitivity, slow-test separation, and stronger figure package.

## Local Environment

- Windows `uv` available through `cmd.exe`.
- Python resolves to 3.13.13 through `uv`.
- Linux-shell `uv` is unavailable on `PATH`.
- Final validation passed with focused smoke tests, Ruff, mypy, and full pytest; see `TEST_REPORT.md`.

## Read First

1. `GOAL.md`
2. `EXECUTIVE_SUMMARY.md`
3. `THESIS_CONCEPT_AUDIT.md`
4. `AUDIT.md`
5. `COMMANDS.md`
6. `NEXT_STEPS.md`
