# Whole-Brain Surrogate Model MVP

This repository builds a small, transparent surrogate model for altered-state-inspired whole-brain dynamics.

Plain English:
- it is a toy whole-brain simulator with 8 big brain modules
- it is tuned against macro-scale fMRI summary statistics
- it is meant for experiments, ablations, and hypothesis ranking
- it is not a receptor model
- it is not a model of subjective experience
- it is not a claim that the code is simulating "what LSD feels like"

## If You Know Nothing, Start Here

Think of the project as three connected parts:

1. `src/lsd_thesis/simulator.py`
This is the toy brain. It updates 8 module states over time.

2. `src/lsd_thesis/data/ds003059.py`
This is the real-data bridge. It downloads actual resting-state runs from OpenNeuro `ds003059`, extracts 8 coarse module time series, and turns them into summary targets.

3. `scripts/run_pipeline.py`
This is the main entry point. It runs the staged workflow and writes figures, JSON summaries, and markdown reports.

## What This Project Is Trying To Do

The scientific goal is modest:
- create a modular graph-based surrogate model
- reproduce macro-scale signatures linked to altered states
- test which perturbation mechanisms matter most

The defensible thesis claim is narrower:

> A transparent 8-module stochastic surrogate can be calibrated against coarse ds003059 resting-state summaries and used to show which simple graph-level perturbations do, and do not, match the observed macro-dynamic deltas.

This is a mismatch-analysis project as much as a modeling project. A good demo should show the empirical bridge, the model response, and the remaining failures together.

The current 8 modules are:
- visual
- auditory
- salience
- default_mode
- executive_frontoparietal
- limbic_affective
- thalamic_gateway
- sensorimotor

Each module has its own latent state and tunable dynamics. The modules are connected by a weighted graph. A perturbation operator changes things like coupling, rigidity, noise, and barriers, then we measure how the resulting simulated signals change.

## What It Is Not

Do not describe this repo as:
- simulating LSD itself
- simulating consciousness
- simulating a subjective trip
- a clinical or diagnostic system

Safer language:
- surrogate model
- macro-scale analogue
- altered-state-inspired perturbation
- graph-modulated dynamics

## Real Data Status

This repo now uses actual data from [OpenNeuro ds003059](https://openneuro.org/datasets/ds003059/versions/1.0.0).

Important details:
- only resting-state runs are used: `run-01` and `run-03`
- music runs are excluded: `run-02`
- the current full Stage 2 real-data path downloads 15 subjects and 60 resting-state runs
- first real-data extraction is slow and can take a long time because it downloads and processes several GB of NIfTI files
- repeated runs are much faster because the extracted targets are cached in `results/stage_2/`

Current audit warning:
- the current ds003059 extraction supports increased cross-network communication and thalamic coupling
- the same extraction gives literature-sign conflicts for `within_network_stability`, `entropy_diversity`, and `metastability_proxy`
- Stage 3's best perturbation score is still high, so the result should be framed as a transparent surrogate with visible failure modes, not as a reproduced psychedelic mechanism

## Quick Start

### 1. Install dependencies

```bash
uv sync --extra dev
```

### 2. Run tests

```bash
uv run pytest -v
```

For quick local validation while iterating on the dashboard/docs layer, use a focused smoke set and bypass the slow coverage default:

```bash
uv run pytest tests/test_simulator.py tests/test_ds003059.py tests/test_perturbation.py tests/test_web.py -q -o addopts=
```

On machines where numerical libraries oversubscribe CPU threads, pin BLAS/OpenMP threads before running metric-heavy tests. Full collection is currently slow enough that it should not be treated as the fast feedback command until the KMeans-backed metric tests are separated or optimized.

### 3. Run the staged pipeline

```bash
uv run python scripts/run_pipeline.py stage1
uv run python scripts/run_pipeline.py stage2
uv run python scripts/run_pipeline.py stage3
uv run python scripts/run_pipeline.py stage4
```

### 4. Or run everything

```bash
uv run python scripts/run_pipeline.py run-all
```

This runs only Stages 1-4.

### 5. Or run the full local workflow

```bash
uv run python scripts/run_pipeline.py run-everything
```

This runs:
- Stages 1-4
- training window export
- condition benchmark
- multitask spectral benchmark

### 6. Launch the dashboard

```bash
uv run python scripts/run_dashboard.py
```

Then open `http://127.0.0.1:8000/`.

### 7. One-command build plus dashboard

```bash
uv run python scripts/run_pipeline.py run-all-serve
```

This now does two things:
- runs Stages 1-4
- starts the local dashboard server at `http://127.0.0.1:8000/`

### 8. Full local workflow plus dashboard

```bash
uv run python scripts/run_pipeline.py run-everything-serve
```

This runs:
- Stages 1-4
- training window export
- condition benchmark
- multitask spectral benchmark
- then starts the local dashboard server at `http://127.0.0.1:8000/`

## Publication Outputs

Build the publication package from the existing staged outputs:

```bash
uv run python scripts/build_publication_package.py
```

This writes publication-facing artifacts under `output/doc/`, including:
- `thesis_report_revised.md`
- `thesis_report_revised.docx`
- `defense_outline.md`
- `defense_outline.docx`
- `thesis_microsite.html`
- `defense_presentation.html`
- `figures/*.png`

If a PDF export is generated separately in your local environment, keep it alongside the other files in `output/doc/`.

## What The Dashboard Now Shows

There are two different viewers in the same page:

1. **Model explorer**
- the synthetic surrogate simulation
- parameter sliders
- synthetic FC and ablation plots

2. **Empirical explorer**
- group-average placebo vs LSD summaries from real `ds003059` resting-state runs
- a subject picker for paired `ses-PLCB` vs `ses-LSD`
- a run picker for `run-01` and `run-03`
- a focus-module selector for group trace uncertainty
- a window slider that aligns:
  - downsampled raw fMRI slice previews
  - module traces
  - FC matrices
  - window-level metric deltas
- uncertainty bands and error bars across paired subjects on the group summaries
- a play/pause control that animates the selected empirical windows
- report/gallery links to saved empirical figures

Important:
- the raw fMRI visuals in the dashboard are precomputed downsampled previews
- they are meant for interpretation and teaching
- they are not a clinical imaging viewer

## What Each Stage Does

### Stage 1
Builds the simulator and synthetic plots.

Outputs:
- simulated time series
- FC matrices
- graph figures
- entropy and switching figures

Main files:
- `src/lsd_thesis/simulator.py`
- `src/lsd_thesis/reporting.py`
- `docs/stage_reports/stage_1.md`

### Stage 2
Uses actual `ds003059` resting-state data to build sober/placebo targets, then fits the sober regime.

Outputs:
- extracted module time series per run
- empirical sober target YAML
- empirical perturbation target YAML
- sober fit report and figures

Main files:
- `src/lsd_thesis/data/ds003059.py`
- `src/lsd_thesis/fit.py`
- `results/stage_2/`
- `docs/stage_reports/stage_2.md`

### Stage 3
Ranks one-at-a-time perturbation mechanisms against ds003059-derived LSD-minus-placebo deltas.

Outputs:
- mechanism ranking figure
- empirical-vs-model delta comparison figure
- stage report

Main files:
- `src/lsd_thesis/perturbation.py`
- `docs/stage_reports/stage_3.md`

### Stage 4
Runs single and pairwise ablations.

Outputs:
- ablation ranking
- pairwise heatmap
- stage report

Main files:
- `src/lsd_thesis/ablation.py`
- `docs/stage_reports/stage_4.md`

## Repo Map

- `configs/`
  Static YAML configs for graph structure, regimes, and fallback targets.
- `src/lsd_thesis/`
  Main Python package.
- `tests/`
  Unit tests for simulator, metrics, fitting, perturbations, web payloads, and training export helpers.
- `docs/`
  Architecture, stage reports, limitations, next steps, experiment log.
- `results/`
  Generated artifacts. This is where the useful outputs end up.
- `scripts/`
  Small command-line entry points.
- `cloud/`
  Cloud-training scaffolding for later DNN experiments.

## The Most Important Output Files

- `results/stage_2/empirical_sober_targets.yaml`
- `results/stage_2/empirical_perturbation_targets.yaml`
- `results/stage_2/stage_2_summary.json`
- `results/stage_3/stage_3_summary.json`
- `results/stage_4/stage_4_summary.json`
- `results/training/condition_benchmark/comparison_summary.json`
- `results/training/condition_benchmark/benchmark_report.md`
- `results/training/multitask_benchmark/comparison_summary.json`
- `results/training/multitask_benchmark/benchmark_report.md`
- `docs/stage_reports/stage_1.md`
- `docs/stage_reports/stage_2.md`
- `docs/stage_reports/stage_3.md`
- `docs/stage_reports/stage_4.md`
- `docs/multitask_benchmark_conclusions.md`

## How The Real ds003059 Path Works

The real-data path is intentionally simple and inspectable:

1. Query OpenNeuro GraphQL for the ds003059 file tree.
2. Keep only:
   - `ses-LSD`
   - `ses-PLCB`
   - `task-rest`
   - `run-01`
   - `run-03`
3. Download only the exact BOLD files needed.
4. Extract 8 coarse module time series using a transparent Harvard-Oxford-based anatomical proxy mapping.
5. Compute shared observables:
   - within-network stability
   - cross-network communication
   - thalamic coupling
   - hierarchical compression
   - entropy/diversity
   - switching rate
   - metastability proxy
   - effective barrier proxy
6. Fit the sober regime to placebo summaries.
7. Compare perturbations to LSD-minus-placebo deltas.

## Known Scientific Weaknesses

The current weak point is not hidden:
- the real ds003059 extraction works
- the sober fit improved a lot after widening the search
- but the simulator still underexpresses the empirical delta magnitudes
- the coarse 8-module anatomical mapping does not yield a perfectly canonical psychedelic signature on every metric
- the Harvard-Oxford proxy mapping has overlapping source labels that are assigned by module order; this is transparent but underdefended without an atlas audit table
- the entropy, switching, metastability, and barrier metrics are clustering/statistical proxies, not direct biological quantities
- the current repository has no committed baseline yet, so generated outputs should be treated as local artifacts until a provenance commit exists

That means:
- the pipeline is real
- the outputs are useful
- but the model still needs better perturbation sensitivity and possibly better macro-module definitions

## Training Benchmarks And Cloud Scaffold

There is now infrastructure for local benchmark comparisons and later DNN-style training:

1. Export a windowed dataset from Stage 2:

```bash
uv run python scripts/export_training_dataset.py
```

This writes:
- `results/training/ds003059_windows.npz`

2. Run the local condition benchmark:

```bash
uv run scripts/benchmark_condition_models.py
```

This writes:
- `results/training/condition_benchmark/comparison_summary.json`
- `results/training/condition_benchmark/benchmark_report.md`
- `results/training/condition_benchmark/fold_predictions.csv`

3. Run the local multitask spectral benchmark:

```bash
uv run scripts/benchmark_multitask_models.py
```

This writes:
- `results/training/multitask_benchmark/window_fc_eigenvalue_targets.npz`
- `results/training/multitask_benchmark/comparison_summary.json`
- `results/training/multitask_benchmark/benchmark_report.md`
- `results/training/multitask_benchmark/classification_predictions.csv`
- `results/training/multitask_benchmark/eigen_predictions.csv`

What this benchmark does:
- predicts `LSD vs placebo` from the exported Stage 2 windows under subject-held-out CV
- regresses each window's 8-module FC eigenspectrum as a compact graph-level target
- compares linear/boosting feature baselines against a small multitask temporal CNN

Current takeaway:
- the small temporal CNN is the best condition classifier in the current local benchmark
- the HistGradientBoosting multitask baseline is the best per-window eigenvalue regressor
- the detailed interpretation lives in `docs/multitask_benchmark_conclusions.md`

4. Use the cloud job scaffold:

- `cloud/hf_jobs/train_sequence_autoencoder.py`

That script is a minimal sequence autoencoder + condition head scaffold intended for managed jobs, not for rewriting the simulator.

Read:
- `docs/cloud_training.md`

If you want the local end-to-end workflow in one command, use:

```bash
uv run python scripts/run_pipeline.py run-everything
```

If you want the same workflow plus the dashboard, use:

```bash
uv run python scripts/run_pipeline.py run-everything-serve
```

## Recommended Reading Order

If you are new:

1. `README.md`
2. `SPEC.md`
3. `docs/architecture.md`
4. `docs/methods.md`
5. `docs/audit_repo_map.md`
6. `docs/stage_reports/stage_2.md`
7. `docs/stage_reports/stage_3.md`
8. `docs/limitations.md`

If you want code:

1. `src/lsd_thesis/core.py`
2. `src/lsd_thesis/simulator.py`
3. `src/lsd_thesis/metrics.py`
4. `src/lsd_thesis/data/ds003059.py`
5. `src/lsd_thesis/fit.py`
6. `src/lsd_thesis/perturbation.py`

## Common Questions

### Why are the modules so coarse?
Because the goal is transparency and ablation, not fine-grained realism.

### Why use actual ds003059 but still call this a surrogate?
Because matching fMRI summary statistics does not make the simulator a mechanistic model of the drug.

### Why are some empirical signatures weaker or different than expected?
Because the current 8-module extraction is a coarse anatomical proxy. That is useful, but it is not the last word.

### What is the best current figure?
Look first at:
- `results/stage_2/figures/sober_metric_fit.html`
- `results/stage_3/figures/mechanism_ranking.html`
- `results/stage_4/figures/pairwise_ablation_heatmap.html`

## One-Line Summary

This repo is a transparent whole-brain surrogate sandbox: it downloads actual ds003059 resting-state data, extracts coarse macro-module targets, fits a simple 8-module dynamical model, ranks perturbation mechanisms, and exports a training-ready dataset for later cloud experiments.
