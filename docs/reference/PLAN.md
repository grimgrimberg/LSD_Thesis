# Audit And Upgrade Execution Plan

## Phase 0 - Safety Baseline

- Fixed `.gitignore` so `/data/` is root-anchored and `src/lsd_thesis/data/` is trackable.
- Excluded local agent state, raw data, virtualenvs, temp folders, generated figures, NPY/NPZ caches, CSV outputs, and generated reports.
- Created initial baseline commit `75218fc` on `codex/whole-brain-surrogate`.
- Created working branch `refactor/research-audit-prototype-upgrade`.

## Phase 1 - Documentation Audit

- Create root-level audit documents that summarize repo inventory, thesis concept, architecture, commands, security, tests, metrics, visuals, roadmap, and next actions.
- Keep claims grounded in observed files, tests, and result summaries.
- Use the evidence taxonomy from `GOAL.md`.

## Phase 2 - Low-Risk Hardening

- Add a regression test that prevents source directories from being accidentally ignored by Git.
- Normalize command documentation for Windows `uv` and this WSL/Codex shell.
- Update `README.md` and `AGENTS.md` with the new audit entrypoints and safety rules.

## Phase 3 - Verification And Handoff

- Run targeted smoke tests, lint, and type checks.
- Run full tests if feasible in the available local environment.
- Update `TEST_REPORT.md`, `CURRENT_STATE.md`, `NEXT_STEPS.md`, `REFACTOR_LOG.md`, `CHANGELOG.md`, and `EXECUTIVE_SUMMARY.md`.
- Commit the audit and hardening phase with a clear message.
