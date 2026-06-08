# Stage 05 Literature-Weighted Objective And Fitting

## Status

Completed as a quick deterministic development path.

## Implemented

- `src/lsd_thesis/objectives.py` with `literature_weighted_lsd_objective`.
- `src/lsd_thesis/fitting_literature.py` with multi-seed candidate evaluation, objective summaries, sign/overshoot tables, and ablation ranking.
- CLI aliases:
  - `run-stage-5`
  - `run-rgg-fit`
  - `run-literature-fit`
- Quick command:
  - `.venv\Scripts\python.exe scripts\run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass --quick`

## Outputs

- `results/stage_5/literature_weighted_fit_summary.json`
- `results/stage_5/placebo_fit_summary.json`
- `results/stage_5/lsd_perturbation_fit_summary.json`
- `results/stage_5/per_seed_metrics.csv`
- `results/stage_5/sign_match_table.csv`
- `results/stage_5/overshoot_table.csv`
- `results/stage_5/ablation_leaderboard.csv`
- `docs/stage_reports/stage_5.md`

## Validation

- RED: `tests/test_literature_fitting.py` initially failed because `lsd_thesis.fitting_literature` did not exist.
- GREEN: `.venv\Scripts\python.exe -m pytest tests\test_cli.py tests\test_literature_fitting.py -q -o addopts= -o cache_dir=codex_logs\pytest-cache`: 15 passed.
- Ruff passed on touched Stage 05 files.
- Quick Stage 5 run completed with 12 candidates; the best quick-budget candidate was `striatal_routing_only`.

## Limits

- The quick run used one seed for runtime control.
- The placebo baseline is evaluated with the default receptor/gradient neural-mass config; broader placebo parameter search is left as future work.
- The leaderboard ranks macro-dynamic perturbation hypotheses only. It does not identify a true biological LSD mechanism.
