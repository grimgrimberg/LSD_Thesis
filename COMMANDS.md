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

## External Data Roots

All new thesis data and package atlas caches should stay under `D:\LSD_Thesis` by default.

```bash
uv run python scripts/prepare_external_data.py
```

This creates and records:

- Nilearn/Schaefer atlas cache: `results/nilearn_data/`
- OpenNeuro `ds006072` target: `data/ds006072/`
- HCP structural-connectome target: `data/hcp_structural_connectome/`
- PET/receptor-prior target: `data/receptor_priors/`
- Manifest: `results/external_data/external_data_manifest.json`

Do not allow package defaults to write atlas or dataset caches under `C:\Users\...` for this thesis repo.

Download the small `ds006072` metadata/provenance slice into the repo-local data root:

```bash
uv run python scripts/download_ds006072_metadata.py
```

This uses the repo's OpenNeuro GraphQL path because the installed `openneuro-py` downloader currently fails against the live schema by querying the removed `DatasetFile.key` field.

Do not use a package-default OpenNeuro download location. Full `ds006072` imaging downloads must target `data/ds006072/` and should use repo-owned or patched download code that records a manifest.

Build the ds006072 functional and processed-CIFTI manifest before any full imaging download:

```bash
uv run python scripts/build_ds006072_func_manifest.py
```

Outputs:

- `data/ds006072/ds006072_func_manifest.json`
- `data/ds006072/ds006072_func_manifest.csv`
- `data/ds006072/ds006072_cifti_manifest.csv`

Export the current thesis evidence loop to CSV and Excel:

```bash
uv run python scripts/export_thesis_loop_tables.py
```

Output workbook:

- `results/thesis_evidence_loop/exports/thesis_evidence_loop_tables.xlsx`

## Parcellation Sensitivity

Run Schaefer/Yeo extraction and mechanism ranking without overwriting the legacy 8-module Stage 2 cache:

```bash
uv run python scripts/run_parcellation_sensitivity.py --parcellation schaefer_100_yeo_7
```

Outputs:

- `results/stage_2/parcellations/<parcellation>/empirical_viewer/`
- `results/parcellation_sensitivity/<parcellation>/summary.json`

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
uv run python scripts/benchmark_rocket_condition_models.py --cv5-manifest output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json --n-kernels 128
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
