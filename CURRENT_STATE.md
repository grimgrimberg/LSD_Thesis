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
- Full `run-everything` completed on 2026-05-05.
- Publication figure rendering and publication package rebuild completed on 2026-05-05.
- Current final validation after follow-up: 103 pytest tests passed, Ruff passed, mypy passed.

## Current Generated Result State

- Stage summaries were regenerated on branch `refactor/research-audit-prototype-upgrade`.
- The regenerated summaries include commit `53c3977adc80f8a2c19dc58a150b0ce778c71eef` and `worktree_status: dirty`, because local follow-up changes were in progress during the run.
- Condition benchmark best model: `temporal_cnn`.
- Multitask benchmark best classification model: `multitask_temporal_cnn`.
- Multitask benchmark best regression model: `hist_gradient_multitask`.
- Degenerate FC/entropy warning paths were hardened after this regeneration; rerun stages again if you need generated summaries produced by the exact latest code.

## Read First

1. `GOAL.md`
2. `EXECUTIVE_SUMMARY.md`
3. `THESIS_CONCEPT_AUDIT.md`
4. `AUDIT.md`
5. `COMMANDS.md`
6. `NEXT_STEPS.md`
