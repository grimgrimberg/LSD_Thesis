# Stage 00 Audit - Receptor/Gradient-Gated Neural-Mass Direction

## Scope

This audit preserves the current eight-module bistable surrogate as a transparent baseline and plans a stronger model path. It does not treat the repository as a receptor-level, pharmacological, subjective-experience, consciousness, clinical, or diagnostic simulator.

## Current Architecture Map

The current pipeline is stage-oriented and compact:

```text
YAML configs
  -> graph loader (`src/lsd_thesis/graph.py`)
  -> regime loader (`src/lsd_thesis/simulator.py`)
  -> eight-module bistable simulator (`src/lsd_thesis/simulator.py`)
  -> observable proxies (`src/lsd_thesis/metrics.py`)
  -> sober fitting (`src/lsd_thesis/fit.py`)
  -> perturbation ranking (`src/lsd_thesis/perturbation.py`)
  -> ablation (`src/lsd_thesis/ablation.py`)
  -> reports, figures, dashboard (`src/lsd_thesis/reporting.py`, `src/lsd_thesis/web/app.py`)
```

Empirical and training side paths:

```text
OpenNeuro ds003059
  -> exact rest-run manifest/download (`src/lsd_thesis/data/ds003059.py`)
  -> Harvard-Oxford-derived 8-module proxy extraction
  -> empirical target YAML/JSON under `results/stage_2/`
  -> empirical dashboard cache
  -> training windows (`src/lsd_thesis/training.py`)
```

## Current Data Flow

- Dataset anchor: OpenNeuro `ds003059`, version `1.0.0`.
- Conditions used: `ses-PLCB` and `ses-LSD`.
- Resting-state runs used: `run-01` and `run-03`.
- Music run excluded: `run-02`.
- Cached empirical payload reports 15 paired subjects, 60 resting-state runs, and 217 timepoints per run.
- Current parcellation: an 8-module Harvard-Oxford anatomical proxy with documented overlapping source labels.
- Generated target files:
  - `results/stage_2/empirical_sober_targets.yaml`
  - `results/stage_2/empirical_perturbation_targets.yaml`
  - `results/stage_2/empirical_run_summaries.json`
  - `results/stage_2/empirical_data_quality.json`

## Current Model Failure Diagnosis

The old model is useful as a falsification scaffold but not strong enough for the new scientific direction.

- Stage 2 sober fit improved the one-shot objective from `5.2439` to `0.9774`, but the multi-seed summary of the selected regime drifts substantially from the one-shot best metrics.
- Stage 3 one-shot winner is `less_hierarchical_constraint @ 0.25`, but it overshoots within-network, cross-network, thalamic, hierarchy, and barrier-like metrics.
- Stage 3 seed-panel winner in the current cached summary changes to `more_cross_talk @ 0.10`, with mean score `13.0935`, score std `6.3777`, and sign agreement `0.75`.
- The seed-noise null score mean is `36.9287`, so the best robust perturbation is better than a seed offset null, but effect magnitudes remain small.
- Stage 4 pairwise combinations do not rescue the old mechanism family. The best pairwise score is still large relative to the desired target-matching role.
- The empirical target itself has sign conflicts against the literature-style target file for:
  - `within_network_stability`
  - `entropy_diversity`
  - `metastability_proxy`

Interpretation: preserve the old model as a transparent baseline, then add a model-zoo path that can compare a receptor/gradient-gated neural-mass surrogate without deleting or mutating the baseline.

## Literature Anchors Checked

Primary/official paper pages were checked on 2026-05-06:

- Carhart-Harris et al. 2016, PNAS, DOI `10.1073/pnas.1518377113`: multimodal LSD neuroimaging, including visual-network changes and BOLD/MEG framing.
- Tagliazucchi et al. 2016, Current Biology, DOI `10.1016/j.cub.2016.02.010`: increased global functional connectivity under LSD.
- Preller et al. 2018, eLife, DOI `10.7554/eLife.35082`: global and thalamic connectivity changes associated with 5-HT2A receptor-informed analyses.
- Lebedev et al. 2016, Human Brain Mapping, DOI `10.1002/hbm.23234`: entropic brain-activity framing.
- Luppi et al. 2021, NeuroImage, DOI `10.1016/j.neuroimage.2020.117653`: dynamic integration/segregation and FC-to-SC coupling themes.
- Girn et al. 2022, NeuroImage, DOI `10.1016/j.neuroimage.2022.119220`: reduced hierarchical differentiation of unimodal and transmodal cortex.
- Singleton et al. 2022, Nature Communications, DOI `10.1038/s41467-022-33578-1`: receptor-informed control-energy landscape flattening.
- Herzog et al. 2023, Scientific Reports, DOI `10.1038/s41598-023-32649-7`: whole-brain model of neural entropy increase.

These sources support target families and cautious modeling hypotheses. They do not authorize claims that this repository simulates LSD pharmacology, receptor binding, subjective experience, consciousness, clinical outcomes, or a true biological mechanism.

## Files That Must Change

Stage 01:

- `src/lsd_thesis/models/__init__.py`
- `src/lsd_thesis/models/base.py`
- `src/lsd_thesis/models/bistable.py`
- `src/lsd_thesis/models/registry.py`
- Focused model-zoo tests.

Stage 02:

- `src/lsd_thesis/models/receptor_gradient_neural_mass.py`
- `configs/models/receptor_gradient_neural_mass.yaml`
- registry entry and tests for deterministic finite simulations and perturbation effects.

Stage 03:

- New parcellation module, likely `src/lsd_thesis/parcellation.py`.
- Schaefer/Yeo extraction/preparation helpers if local dependencies and data allow.
- Tests using synthetic node metadata.

Stage 04:

- `src/lsd_thesis/metrics_literature.py`
- Optional `src/lsd_thesis/target_validation.py`
- Synthetic metric tests.

Stage 05:

- New objective/fitting module, likely `src/lsd_thesis/literature_objective.py` or `src/lsd_thesis/literature_fitting.py`.
- Quick-mode script or callable function for stage-5 artifacts.
- Tests for sign, overshoot, seed variance, and sparsity penalties.

Stage 06:

- Supervisor-facing docs under `docs/`.
- Stage 2b/Stage 5 reporting docs.
- Dashboard payload updates only if safe and inexpensive.

## Files Not To Change Yet

- Do not delete or rewrite `src/lsd_thesis/simulator.py`; wrap it as the `bistable` baseline instead.
- Do not overwrite existing `results/stage_1` through `results/stage_4` outputs.
- Do not rewrite dataset formats under `data/` or cached NPY/NPZ outputs.
- Do not remove old perturbation, ablation, reporting, or dashboard paths.
- Do not add heavy dependencies unless the stage can degrade without them.

## Risks

- Schaefer/Yeo extraction may need nilearn network access or cached atlases that are unavailable in this session.
- Full pytest is currently blocked by Windows temp/cache permissions; narrow tests need local temp/cache settings.
- `uv run` is currently blocked by Windows uv cache/venv access permissions; `.venv\Scripts` is the reliable fallback.
- Mypy exits with status 1 and no diagnostic output in this session.
- Stage 5 fitting can become expensive; quick mode must remain cheap.
- A receptor/gradient-gated model name can invite overclaiming; docs must keep "surrogate" and "proxy" language.

## Test Strategy

- Use test-first changes for new behavior where practical.
- Keep focused test slices with `-o addopts=` to bypass the coverage gate during iteration.
- Use local temp/cache settings for pytest:
  - `TEMP=D:\LSD_Thesis\codex_logs\temp`
  - `TMP=D:\LSD_Thesis\codex_logs\temp`
  - `--basetemp=codex_logs\pytest-basetemp-*`
  - `-o cache_dir=codex_logs\pytest-cache`
- Inject Git safe-directory in subprocess tests when needed:
  - `GIT_CONFIG_COUNT=1`
  - `GIT_CONFIG_KEY_0=safe.directory`
  - `GIT_CONFIG_VALUE_0=D:/LSD_Thesis`
- Run final feasible gates:
  - `.venv\Scripts\python.exe -m pytest ...`
  - `.venv\Scripts\ruff.exe check .`
  - `.venv\Scripts\python.exe -m mypy src ...` if diagnostics become available.

## Milestone Sequence

1. Add a model-zoo interface and wrap the old simulator as `bistable`.
2. Add receptor/gradient-gated neural-mass surrogate with deterministic synthetic tests.
3. Add parcellation abstraction with `harvard_oxford_8` preserved and `schaefer_100_yeo_7` prepared.
4. Add literature-aligned metrics that work on synthetic FC/time-series/node metadata.
5. Add literature-weighted objective and cheap multi-seed evaluation/fitting path.
6. Update reports, dashboard payloads, and supervisor-facing artifacts without fabricating missing results.

## Recommended Naming

- Canonical model id: `receptor_gradient_neural_mass`
- Short alias: `rgg_nmm`
- Baseline model id: `bistable`
- Legacy parcellation id: `harvard_oxford_8`
- Prepared functional parcellation id: `schaefer_100_yeo_7`

## Acceptance Criteria For Stages 01-06

- Stage 01: old model is accessible through model registry; default behavior remains old baseline.
- Stage 02: new neural-mass surrogate returns finite deterministic shapes and exposes perturbation knobs.
- Stage 03: parcellation metadata abstraction exists and legacy outputs are not overwritten.
- Stage 04: literature metrics produce finite, interpretable values on synthetic data.
- Stage 05: objective penalties are explicit, tested, and quick-mode artifacts are written without expensive full fitting.
- Stage 06: supervisor docs clearly distinguish implemented results from partial/scaffolded work.

## Validation Status

- Ruff baseline passed via `.venv\Scripts\ruff.exe check .`.
- Focused smoke baseline passed: `10 passed`.
- Full pytest was blocked by Windows temp/cache permissions.
- Mypy currently exits with status 1 and no diagnostic output.
- No source implementation changes were made in Stage 00.

