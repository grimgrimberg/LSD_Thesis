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

## Rollback

- To inspect the safety baseline: `git show --stat 75218fc`.
- To compare current work against baseline: `git diff 75218fc`.
- Do not use destructive reset commands unless explicitly requested.
