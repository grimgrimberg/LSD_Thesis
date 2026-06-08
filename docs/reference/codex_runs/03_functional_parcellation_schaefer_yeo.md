# Stage 03 - Functional Parcellation And Schaefer/Yeo Preparation

## Status

Implemented a parcellation abstraction and dry-run output path. Full Schaefer/Yeo fMRI extraction was not run.

## Source Changes

- Added `src/lsd_thesis/data/parcellations.py`.
- Added `tests/test_parcellations.py`.
- Added `generate-empirical-targets --parcellation ... --dry-run` support to `scripts/run_pipeline.py`.
- Added `docs/parcellations.md`.

## Supported Parcellations

- `harvard_oxford_8`: legacy eight-module Harvard-Oxford proxy.
- `schaefer_100_yeo_7`: metadata-ready Schaefer 100 / Yeo 7 cortical target space.

## Output Artifacts Written

- `results/stage_2/parcellations/harvard_oxford_8/node_metadata.json`
- `results/stage_2/parcellations/harvard_oxford_8/atlas_metadata.json`
- `results/stage_2/parcellations/harvard_oxford_8/dry_run_plan.json`
- `results/stage_2/parcellations/schaefer_100_yeo_7/node_metadata.json`
- `results/stage_2/parcellations/schaefer_100_yeo_7/atlas_metadata.json`
- `results/stage_2/parcellations/schaefer_100_yeo_7/dry_run_plan.json`

No root Stage 2 target files were overwritten.

## Node Metadata Schema

Each node includes:

- `node_label`
- `parcel_index`
- `yeo_network_label`
- `coarse_class`
- `hierarchy_value`
- `receptor_weight`
- `receptor_weight_source`
- `visual_weight`
- `sensory_weight`
- `somatomotor_weight`
- `transmodal_weight`
- `thalamus_weight`
- `striatum_weight`
- `metadata_source`

For `schaefer_100_yeo_7`, receptor weights are neutral placeholders and explicitly labeled as such.

## Validation

- RED: `tests/test_parcellations.py` initially failed with `ModuleNotFoundError: No module named 'lsd_thesis.data.parcellations'`.
- GREEN: `.venv\Scripts\python.exe -m pytest tests\test_parcellations.py tests\test_cli.py::test_main_runs_parcellation_dry_run -q -o addopts= -o cache_dir=codex_logs\pytest-cache` passed with `7 passed`.
- Dry-run CLI:
  - `.venv\Scripts\python.exe scripts\run_pipeline.py generate-empirical-targets --parcellation schaefer_100_yeo_7 --dry-run`
  - `.venv\Scripts\python.exe scripts\run_pipeline.py generate-empirical-targets --parcellation harvard_oxford_8 --dry-run`
- Ruff: `.venv\Scripts\ruff.exe check src\lsd_thesis\data\parcellations.py scripts\run_pipeline.py tests\test_parcellations.py tests\test_cli.py` passed. Ruff cache writes remain blocked by environment permissions.

## Limitations

- The Schaefer/Yeo path is metadata-ready but has not extracted ds003059 time series.
- Subcortical thalamus, caudate, and putamen are documented as TODO additions.
- Existing dynamic metrics still operate on the old Stage 2 root targets unless a future run writes parcellation-specific target files.

