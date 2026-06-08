# Stage 02 - Receptor/Gradient Neural-Mass Model

## Status

Implemented.

## Source Changes

- Added `src/lsd_thesis/models/receptor_gradient_neural_mass.py`.
- Registered `receptor_gradient_neural_mass`.
- Registered alias `rgg_nmm`.
- Added `configs/models/receptor_gradient_neural_mass.yaml`.
- Added `tests/test_receptor_gradient_neural_mass.py`.
- Added `docs/receptor_gradient_neural_mass.md`.
- Updated `docs/model_zoo.md`.

## Model Summary

The model uses one excitatory and one inhibitory state per node. Excitatory input includes local excitation, inhibition, global coupling, node-wise gain, and homeostatic feedback. Inhibitory input tracks excitatory activity and local homeostatic feedback.

The model supports:

- receptor-weighted gain modulation,
- visual and sensory gain,
- hierarchy-distance coupling changes,
- transmodal/transmodal decoherence,
- thalamus-to-sensory routing,
- striatum-to-sensory routing,
- noise changes,
- homeostatic stabilization,
- lightweight HRF/BOLD-like output.

## Assumptions

- Default node metadata arrays are transparent proxy weights for testing model behavior.
- No mechanistic receptor binding is implemented.
- The HRF is a lightweight observation layer, not a full validated BOLD forward model.
- The config is deliberately small enough for unit tests and quick smoke runs.

## Validation

- RED: `tests/test_receptor_gradient_neural_mass.py` failed before implementation with `ModuleNotFoundError: No module named 'lsd_thesis.models.receptor_gradient_neural_mass'`.
- GREEN: `.venv\Scripts\python.exe -m pytest tests\test_receptor_gradient_neural_mass.py tests\test_model_zoo.py -q -o addopts= -o cache_dir=codex_logs\pytest-cache --basetemp=codex_logs\pytest-basetemp-rgg-green-3` passed with `13 passed`.
- Smoke: `.venv\Scripts\python.exe -c "from lsd_thesis.models.registry import get_model; m=get_model('rgg_nmm'); r=m.simulate(seed=5); print(r.model_name, r.activity.shape, None if r.bold is None else r.bold.shape, r.seed)"` produced `receptor_gradient_neural_mass (200, 8) (200, 8) 5`.
- Ruff: `.venv\Scripts\ruff.exe check src\lsd_thesis\models tests\test_receptor_gradient_neural_mass.py` passed. Ruff cache writes still fail because `.ruff_cache` is access-denied in this session.

## Limitations

- The model is not yet connected to empirical fitting or Stage 1-4 artifact generation.
- Default receptor and hierarchy arrays are explicit proxy metadata, not validated receptor maps.
- Schaefer/Yeo node metadata is prepared in Stage 03, not implemented here.

