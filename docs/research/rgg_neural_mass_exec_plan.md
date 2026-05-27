# RGG Neural-Mass Execution Plan

## Goal

Add a receptor/gradient-gated neural-mass surrogate path while preserving the existing eight-module bistable model as the default baseline.

This plan is implementation-oriented and does not require user clarification for the prompt-pack stages.

## Stage 01 - Model Zoo Interface

Implement:

- `src/lsd_thesis/models/base.py`
- `src/lsd_thesis/models/bistable.py`
- `src/lsd_thesis/models/registry.py`
- `src/lsd_thesis/models/__init__.py`

Required API:

- `SimulationResult` abstraction with `model_name`, `module_names`, `time`, `time_series`, and optional `metadata`.
- `BaseBrainModel` protocol or abstract base with `simulate()`.
- `BistableModel` wrapper around the existing graph/regime `run_simulation`.
- `get_model("bistable")` returns baseline.
- Unknown model ids fail with a clear `ValueError`.

Keep old pipeline behavior unchanged. Stage 1-4 code can continue importing `run_simulation` directly.

## Stage 02 - Receptor/Gradient Neural-Mass Model

Implement:

- `src/lsd_thesis/models/receptor_gradient_neural_mass.py`
- `configs/models/receptor_gradient_neural_mass.yaml`
- registry ids `receptor_gradient_neural_mass` and `rgg_nmm`.

Minimal state:

- Excitatory state `E_i`.
- Inhibitory state `I_i`.
- Optional BOLD/HRF-observed signal.
- Node metadata arrays:
  - receptor density proxy
  - hierarchy score
  - visual mask/weight
  - sensory mask/weight
  - thalamic mask/weight
  - striatal mask/weight
  - subcortical mask/weight

Perturbation vector:

- `receptor_gain_alpha`
- `hierarchy_cross_coupling_eta`
- `visual_gain_beta`
- `sensory_gain_gamma`
- `associative_decoherence_lambda`
- `thalamic_routing_kappa`
- `striatal_routing_kappa`
- `noise_delta`
- `homeostasis_delta`

Numerical constraints:

- Use stochastic Euler integration with fixed-seed determinism.
- Keep values finite through bounded nonlinearities and clipping only where documented.
- Use homeostatic inhibitory stabilization so strong gain does not trivially diverge.
- Default quick settings should complete in unit tests.

## Stage 03 - Parcellation

Implement a parcellation abstraction before full Schaefer extraction:

- `ParcellationSpec`
- `NodeMetadata`
- `load_parcellation_spec("harvard_oxford_8")`
- `load_parcellation_spec("schaefer_100_yeo_7")`

Legacy support:

- Keep Harvard-Oxford 8-module path intact.
- Save any new parcellation-specific outputs under:
  - `results/stage_2/parcellations/harvard_oxford_8/`
  - `results/stage_2/parcellations/schaefer_100_yeo_7/`

If real extraction is unavailable:

- Add tested synthetic Schaefer/Yeo metadata.
- Write exact commands needed for real extraction in the stage result log.

## Stage 04 - Literature Metrics

Implement:

- `src/lsd_thesis/metrics_literature.py`
- Optional `src/lsd_thesis/target_validation.py`.

Metric functions should accept:

- time series shaped `[time, node]`
- FC matrix shaped `[node, node]`
- node metadata with network labels, hierarchy scores, and optional anatomical role masks.

Required metrics:

- unimodal/transmodal FC
- visual global connectivity
- sensory/somatomotor global connectivity
- within-network FC by Yeo network
- between-network FC matrix
- thalamus-to-sensory FC
- thalamus-to-transmodal FC
- striatum-to-sensory FC
- hierarchy differentiation
- gradient flattening delta/proxy
- state occupancy entropy
- transition entropy
- transition rate
- dynamic FC variance
- optional FC-to-SC coupling

Use synthetic tests for signs, shapes, and finite behavior.

## Stage 05 - Literature-Weighted Objective

Implement:

- `literature_weighted_lsd_objective`
- multi-seed evaluation helper
- quick-mode fitting function that writes Stage 5 artifacts.

Objective terms:

- weighted normalized delta error
- sign mismatch penalty
- overshoot penalty
- seed variance penalty
- sparsity penalty

Fit paths:

- placebo baseline fit path
- LSD perturbation fit path
- ablation leaderboard

Keep defaults cheap. Full fitting can be documented as a later command if it is not cheap.

## Stage 06 - Reporting And Supervisor Artifacts

Implement supervisor-facing docs:

- `docs/supervisor_pitch.md`
- `docs/proposal_short.md`
- `docs/open_source_demo.md`
- `docs/next_month_research_plan.md`
- `docs/supervisor_pitch_10_slides.md`
- `docs/reproducibility_runbook.md`
- `docs/codex_runs/06_final_summary.md`

Rules:

- Do not fabricate Stage 2b or Stage 5 results.
- If a stage produced scaffolds rather than empirical outputs, label it explicitly.
- Keep claims at macro-dynamic surrogate level.
- Report validation failures as environment failures only when supported by exact error text.

## Validation Plan

Use focused tests after each production stage. Prefer:

```powershell
$env:TEMP='D:\LSD_Thesis\codex_logs\temp'
$env:TMP='D:\LSD_Thesis\codex_logs\temp'
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0='D:/LSD_Thesis'
.\.venv\Scripts\python.exe -m pytest <focused tests> -q -o addopts= -o cache_dir=codex_logs\pytest-cache --basetemp=codex_logs\pytest-basetemp-focused
```

Run Ruff after source changes:

```powershell
.\.venv\Scripts\ruff.exe check .
```

Try mypy at the end, but current preflight exits with status 1 and no diagnostic output.

