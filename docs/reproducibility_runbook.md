# Reproducibility Runbook

## Install

```bash
uv sync --extra dev
```

## Core checks

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

In this Windows session, `.venv\Scripts\python.exe` and `.venv\Scripts\ruff.exe` were used for focused checks because `uv` and tool caches can hit access-denied warnings.

## Legacy pipeline

```bash
uv run python scripts/run_pipeline.py run-all
```

Outputs are written under:

- `results/stage_1/`
- `results/stage_2/`
- `results/stage_3/`
- `results/stage_4/`
- `docs/stage_reports/`

## Literature target validation

```bash
uv run python scripts/run_pipeline.py stage-2b-target-validation --parcellation harvard_oxford_8
```

Outputs:

- `results/stage_2b/target_reliability_summary.json`
- `results/stage_2b/literature_metric_deltas.csv`
- `results/stage_2b/bootstrap_metric_cis.csv`
- `results/stage_2b/leave_one_subject_out.csv`
- `results/stage_2b/run_split_stability.csv`
- `docs/stage_reports/stage_2b.md`

## Stage 5 quick fit

```bash
uv run python scripts/run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass --quick
```

Outputs:

- `results/stage_5/literature_weighted_fit_summary.json`
- `results/stage_5/placebo_fit_summary.json`
- `results/stage_5/lsd_perturbation_fit_summary.json`
- `results/stage_5/per_seed_metrics.csv`
- `results/stage_5/sign_match_table.csv`
- `results/stage_5/overshoot_table.csv`
- `results/stage_5/ablation_leaderboard.csv`
- `docs/stage_reports/stage_5.md`

## Dashboard

```bash
uv run python scripts/run_dashboard.py
```

Then open `http://127.0.0.1:8000/`.

## If ds003059 data is missing

Run Stage 2 first. The first extraction can be slow because it downloads and processes NIfTI files. Repeated runs should use cached outputs under `results/stage_2/`.

```bash
uv run python scripts/run_pipeline.py stage2
```

## Compute notes

- `--quick` Stage 5 is a development smoke budget.
- Non-quick Stage 5 uses more seeds but is still not a final scientific search.
- A final run should expand candidate count, seed count, and simulation length, then compare sign matches and overshoot tables.
