# Commands

## Environment Notes

The project is on a Windows path opened through a Linux/WSL-style Codex shell. In this shell, `uv` is not on Linux `PATH`, but Windows `uv` is available through `cmd.exe`.

Use one of these command styles:

- Windows terminal from `D:\LSD_Thesis`: `uv run ...`
- Current Codex/WSL shell: `cmd.exe /C "uv run ..."`

## Setup

Windows:

```bash
uv sync --extra dev
```

Codex/WSL shell:

```bash
cmd.exe /C "uv sync --extra dev"
```

Status: not rerun during this phase because the existing Windows virtualenv resolves Python 3.13.13.

## Run Tests

Full default test suite with coverage:

```bash
uv run pytest
```

Codex/WSL:

```bash
cmd.exe /C "uv run pytest"
```

Fast smoke without coverage gate:

```bash
uv run pytest tests/test_imports.py tests/test_simulator.py tests/test_metrics.py tests/test_perturbation.py -q -o addopts=
```

## Lint

```bash
uv run ruff check .
```

Codex/WSL:

```bash
cmd.exe /C "uv run ruff check ."
```

## Type Check

```bash
uv run mypy src
```

Codex/WSL:

```bash
cmd.exe /C "uv run mypy src"
```

## Format

No formatter is configured beyond Ruff linting. Proposed command if formatting is adopted later:

```bash
uv run ruff format .
```

Do not run a formatter that rewrites files unless that is part of an approved change.

## Run Stages

```bash
uv run python scripts/run_pipeline.py stage1
uv run python scripts/run_pipeline.py stage2
uv run python scripts/run_pipeline.py stage3
uv run python scripts/run_pipeline.py stage4
uv run python scripts/run_pipeline.py run-all
```

Stage 2 may process/download raw ds003059 data and can be slow.

## Demo UI

```bash
uv run python scripts/run_dashboard.py
```

Open `http://127.0.0.1:8000/`.

In this environment, launching the browser itself requires user action; the server command is enough for local inspection.

## Generate Plots

```bash
uv run python scripts/run_pipeline.py run-all
```

Generated Plotly HTML figures are written under `results/stage_*/figures/`.

Render the current publication figure bundle from cached stage outputs:

```bash
uv run python scripts/render_publication_figures.py --all
```

By default this writes PNGs under `results/publication_figures/`, which is treated as generated output.

## Reproduce Main Experiment

```bash
uv run python scripts/run_pipeline.py run-all
uv run python scripts/export_training_dataset.py
uv run scripts/benchmark_condition_models.py
uv run scripts/benchmark_multitask_models.py
uv run python scripts/build_publication_package.py
```

One-command local workflow:

```bash
uv run python scripts/run_pipeline.py run-everything
```

## Clean

Manual cleanup targets, all ignored by Git:

```bash
rm -rf .pytest_cache .ruff_cache .mypy_cache
rm -rf output tmp tmp_*
```

Ask before deleting raw `/data/` or generated `/results/` artifacts.

## Discovered Command Results

- `cmd.exe /C "uv --version"`: succeeded, `uv 0.9.21`.
- `cmd.exe /C "uv run python --version"`: succeeded, Python 3.13.13.
- `cmd.exe /C "uv run pytest --collect-only -q -o addopts="`: succeeded during planning, 98 tests collected before the repo hygiene test was added.
- `cmd.exe /C "uv run pytest tests/test_imports.py tests/test_simulator.py tests/test_metrics.py tests/test_perturbation.py tests/test_repo_hygiene.py -q -o addopts="`: succeeded, 9 passed.
- `cmd.exe /C "uv run ruff check ."`: succeeded after lint fixes revealed by tracking `src/lsd_thesis/data/`.
- `cmd.exe /C "uv run mypy src"`: succeeded, 26 source files.
- `cmd.exe /C "uv run pytest"`: succeeded, 99 passed with 84.84% coverage.
- `cmd.exe /C "uv run python scripts/run_pipeline.py run-everything"`: succeeded on 2026-05-05; stages 1-4, training export, condition benchmark, and multitask benchmark completed.
- `cmd.exe /C "uv run python scripts/render_publication_figures.py --all"`: succeeded and wrote `stage1_metric_shift.png` and `stage2_fit_robustness.png` under `results/publication_figures/`.
- `cmd.exe /C "uv run python scripts/build_publication_package.py"`: succeeded and rebuilt markdown, DOCX, HTML, PPTX, and publication figures under `output/doc/`.
- Linux-shell `uv ...`: failed because `uv` was not on Linux `PATH`; use the Windows command wrapper above.
