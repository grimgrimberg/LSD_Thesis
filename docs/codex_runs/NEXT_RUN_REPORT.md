# Next Run Report

## Current state

The prompt pack has been executed through Stage 06. The repository now has:

- Legacy Stages 1-4 preserved as the baseline path.
- A model-zoo interface with a registered `receptor_gradient_neural_mass` / `rgg_nmm` model.
- Parcellation support for `harvard_oxford_8` and metadata-only `schaefer_100_yeo_7`.
- Literature-aligned metrics and Stage 2b target validation outputs.
- A Stage 5 literature-weighted objective and quick perturbation leaderboard.
- Supervisor-facing docs, proposal notes, open-source demo notes, a 10-slide outline, and a reproducibility runbook.

Key current artifacts:

- `docs/codex_runs/06_final_summary.md`
- `docs/codex_runs/master_prompt_pack_execution.md`
- `docs/reproducibility_runbook.md`
- `docs/stage_reports/stage_2b.md`
- `docs/stage_reports/stage_5.md`
- `results/stage_2b/target_reliability_summary.json`
- `results/stage_5/literature_weighted_fit_summary.json`
- `results/stage_5/ablation_leaderboard.csv`

## Verified so far

Freshest reliable evidence from the last run:

- Full `uv run pytest` passed earlier in the continuation: `136 passed`, coverage `86.51%`.
- Full Ruff passed through `.venv\Scripts\ruff.exe check .` after final cleanup.
- Focused changed-area tests passed after final cleanup: `35 passed`.
- Stage 2b smoke command passed after final cleanup.
- Stage 5 quick smoke command passed after final cleanup.

Commands that passed after final cleanup:

```powershell
.venv\Scripts\ruff.exe check .
.venv\Scripts\python.exe -m pytest tests\test_receptor_gradient_neural_mass.py tests\test_metrics_literature.py tests\test_literature_fitting.py tests\test_cli.py tests\test_parcellations.py -q -o addopts= -o cache_dir=codex_logs\pytest-cache
.venv\Scripts\python.exe scripts\run_pipeline.py stage-2b-target-validation --parcellation harvard_oxford_8
.venv\Scripts\python.exe scripts\run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass --quick
```

## Known verification blockers

These are environment/tooling issues observed in this Windows session:

- `uv run ...` can fail inside sandboxed shell runs because `C:\Users\yuval\AppData\Local\uv\cache\sdists-v9\.git` is access denied.
- Direct `.venv` mypy currently exits with status 1 and no diagnostics, even with `--show-traceback --no-incremental --cache-dir codex_logs\mypy-cache-final`.
- Direct full pytest can fail before or during tests because:
  - coverage cannot remove locked `.coverage`,
  - pytest cannot scan `C:\Users\yuval\AppData\Local\Temp\pytest-of-yuval`,
  - Git subprocesses may need `git -c safe.directory=D:/LSD_Thesis`,
  - sklearn/joblib may fail to create Windows pipes.
- Several local temp directories are permission-locked and show up in `git status` warnings:
  - `codex_logs/cli_pytest_tmp_20260506110154/`
  - `parcellation_pytest_tmp/`
  - `tmp8d6pz2mi/`
  - `tmpg6totgbh/`
  - `tmptvui6are/`

Do not delete locked temp directories without explicit user approval. Report them separately from product failures.

## Recommended next run

The next run should be a validation-and-hardening pass, not a new feature spree.

Priority order:

1. Re-check repo status and read the current handoff docs.
2. Run documented verification commands:
   - `uv run ruff check .`
   - `uv run pytest`
   - `uv run mypy src`
3. If `uv run` is blocked by cache permissions and approval is unavailable, use direct `.venv` fallback commands and document that fallback.
4. If mypy gives real diagnostics, fix only typed issues in the new Stage 02/04/05 code and rerun focused tests.
5. Rerun Stage 2b and Stage 5 quick smoke.
6. Optionally run non-quick Stage 5 if the quick path and tests are green.
7. Update `docs/codex_runs/NEXT_RUN_RESULT.md` with exact commands, exit codes, and remaining blockers.

## Scientific next steps after validation

1. Run non-quick Stage 5 with 3 seeds:

```powershell
uv run python scripts/run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass
```

2. If that is stable, add a slightly larger candidate budget and seed panel for Stage 5.
3. Implement real Schaefer/Yeo ds003059 extraction. Do not fabricate Schaefer/Yeo empirical targets.
4. Compare `harvard_oxford_8` vs Schaefer/Yeo target reliability.
5. Add dashboard/static report views only after the machine-readable artifacts are stable.

## Claim boundaries to preserve

Use this wording:

- macro-dynamic proxy
- surrogate model
- receptor/gradient-gated neural-mass path
- altered-state-inspired perturbation
- model comparison and mismatch analysis

Avoid:

- direct receptor-level realism
- simulated subjective experience
- consciousness claims
- clinical claims
- calling the best Stage 5 candidate a true biological LSD mechanism
