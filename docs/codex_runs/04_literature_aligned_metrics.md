# Stage 04 Literature-Aligned Metrics

## Status

Completed for the cached Harvard-Oxford 8-module target space.

## Implemented

- `src/lsd_thesis/metrics_literature.py` with static FC, hierarchy, dynamic-state, and optional FC/SC coupling helpers.
- `src/lsd_thesis/target_validation.py` with paired deltas, bootstrap CIs, leave-one-subject-out influence, and run-split stability exports.
- CLI command: `stage-2b-target-validation`.
- Documentation: `docs/metrics_literature.md`.

## Outputs

- `results/stage_2b/target_reliability_summary.json`
- `results/stage_2b/literature_metric_deltas.csv`
- `results/stage_2b/bootstrap_metric_cis.csv`
- `results/stage_2b/leave_one_subject_out.csv`
- `results/stage_2b/run_split_stability.csv`
- `docs/stage_reports/stage_2b.md`

## Validation

- `.venv\Scripts\python.exe -m pytest tests\test_metrics_literature.py -q -o addopts= -o cache_dir=codex_logs\pytest-cache --basetemp=codex_logs\pytest-basetemp-stage04`: 6 passed.
- `.venv\Scripts\python.exe -m pytest tests\test_cli.py -q -o addopts= -o cache_dir=codex_logs\pytest-cache --basetemp=codex_logs\pytest-basetemp-cli`: 8 passed before later CLI additions.
- `.venv\Scripts\ruff.exe check src\lsd_thesis\metrics_literature.py src\lsd_thesis\target_validation.py scripts\run_pipeline.py tests\test_metrics_literature.py tests\test_cli.py`: passed.
- `.venv\Scripts\python.exe scripts\run_pipeline.py stage-2b-target-validation --parcellation harvard_oxford_8`: completed with 13 metrics and 15 paired subjects.

## Limits

- Stage 2b uses the cached legacy eight-module extraction.
- Schaefer/Yeo is metadata-prepared only; no Schaefer/Yeo empirical target values were fabricated.
- Dynamic entropy metrics are state-sequence proxies, not neural entropy measurements.
