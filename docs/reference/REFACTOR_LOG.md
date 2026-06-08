# Refactor Log

## 2026-05-05 - Safety Baseline

- Changed `.gitignore` so root `/data/` is ignored without ignoring `src/lsd_thesis/data/`.
- Ignored local agent state, virtualenvs, raw data, temp outputs, generated publication outputs, generated figures, arrays, CSVs, and benchmark markdown reports.
- Staged and committed lean baseline as `75218fc` with message `chore: establish baseline before audit refactor`.
- Created branch `refactor/research-audit-prototype-upgrade`.
- Set repository-local Git identity to `Codex <codex@local.invalid>` because no local identity was configured.

## 2026-05-05 - Audit Documentation

- Added root-level audit, architecture, command, roadmap, security, test, metric, visual, BioRender brief, current state, next steps, and executive summary documents.
- Kept all scientific wording at macro-scale surrogate/proxy level.

## 2026-05-05 - Repo Hygiene And Validation

- Added `src/lsd_thesis/repo_hygiene.py` and `tests/test_repo_hygiene.py` to catch source paths hidden by Git ignore rules.
- Verified the hygiene test red-green cycle: it first failed because the helper did not exist, then passed after minimal implementation.
- Fixed lint issues in `src/lsd_thesis/data/ds003059.py` that were revealed once the data source package became tracked.
- Added `.coverage` to `.gitignore` after full pytest generated the coverage data file.
- Ran focused smoke tests, Ruff, mypy, and full pytest successfully; details are in `TEST_REPORT.md`.

## 2026-05-05 - Full Workflow And Metric Hardening

- Ran `uv run python scripts/run_pipeline.py run-everything` through the Windows `cmd.exe` wrapper.
- Stages 1-4 completed, training windows exported, condition benchmark completed, and multitask benchmark completed.
- Added finite-correlation handling for constant/degenerate time-series inputs.
- Added tests covering finite degenerate summary metrics and constant-window FC eigenspectrum targets without RuntimeWarnings.
- Verified and adopted `scripts/render_publication_figures.py` plus its tests as a lightweight publication-figure rendering command.
- Rebuilt the publication package with `scripts/build_publication_package.py`.
- Final validation after these changes: focused metric/script tests passed, Ruff passed, mypy passed, and full pytest passed with 103 tests.

## Rollback

- To inspect the safety baseline: `git show --stat 75218fc`.
- To compare current work against baseline: `git diff 75218fc`.
- Do not use destructive reset commands unless explicitly requested.
