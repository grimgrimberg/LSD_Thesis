# Stage 01 Result

## Status

Completed.

## Prompt

- `codex_prompt_pack/01_model_zoo_interface.md`

## Implemented

- Added `lsd_thesis.models` package with:
  - `SimulationResult`
  - `BaseBrainModel`
  - `BistableModel`
  - model registry helpers
- Wrapped the old eight-module simulator as `bistable`.
- Added `legacy_bistable` as a registry alias.
- Added clear unknown-model errors.
- Added `--model` validation to `scripts/run_pipeline.py` with default `bistable`.
- Added `docs/model_zoo.md`.

## Preserved Behavior

- Stage 1-4 still call the legacy simulator path directly.
- The default model remains the old bistable baseline.
- No result files were regenerated or overwritten.

## Validation

- RED: `tests/test_model_zoo.py` failed before implementation with `ModuleNotFoundError: No module named 'lsd_thesis.models'`.
- GREEN: `.venv\Scripts\python.exe -m pytest tests\test_model_zoo.py tests\test_simulator.py tests\test_cli.py -q -o addopts= -o cache_dir=codex_logs\pytest-cache --basetemp=codex_logs\pytest-basetemp-model-zoo-green` passed with `15 passed`.
- Ruff: `.venv\Scripts\ruff.exe check src\lsd_thesis\models scripts\run_pipeline.py tests\test_model_zoo.py` passed. Ruff could not write its cache because `.ruff_cache` is access-denied in this environment.

## Remaining Risks

- Future non-bistable models are not yet wired into the Stage 1-4 artifact generators.
- Mypy remains blocked by the pre-existing silent exit behavior documented in the master log.

