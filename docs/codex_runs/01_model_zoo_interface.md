# Stage 01 - Model Zoo Interface

## Status

Implemented the model-zoo interface while preserving the old bistable simulator as the default baseline.

## Source Changes

- Added `src/lsd_thesis/models/base.py`.
- Added `src/lsd_thesis/models/bistable.py`.
- Added `src/lsd_thesis/models/registry.py`.
- Added `src/lsd_thesis/models/__init__.py`.
- Added `tests/test_model_zoo.py`.
- Added `docs/model_zoo.md`.
- Added `--model` validation to `scripts/run_pipeline.py`; Stage 1-4 still run the old baseline path.

## Behavior

- `get_model("bistable")` returns a `BistableModel`.
- `get_model("legacy_bistable")` returns the same baseline wrapper.
- Unknown model ids raise a `ValueError` with available model names.
- `BistableModel().simulate()` adapts the old simulator output into the model-zoo `SimulationResult`.
- Existing Stage 1-4 code paths remain direct calls to the old simulator and are not scientifically changed.

## Validation

Stage-specific RED:

- `tests/test_model_zoo.py` initially failed because `lsd_thesis.models` did not exist.

Stage-specific GREEN:

- Pending in this log; see `01_model_zoo_interface_result.md` after validation.

## Remaining Risks

- Non-bistable model families are registered in later stages but are not yet wired into full Stage 1-4 output generation.
- The model-zoo result interface is intentionally minimal; future models may need richer typed metadata once Schaefer/Yeo support lands.

