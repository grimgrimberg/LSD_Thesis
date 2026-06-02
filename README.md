# LSD Thesis Macro-Dynamics Pitch

This repository is a data-science and engineering pitch for a master's thesis idea:

> Test whether LSD-like empirical macro-dynamics are better explained by altered transition/control dynamics than by generic noise, motion, or static connectivity changes.

The project has two audiences:
- **Developer mode:** run the local FastAPI dashboard and inspect the full backend-driven analysis.
- **PI pitch mode:** open the public GitHub Pages site and walk through the claim ladder, methods, limitations, and derived artifacts without needing raw data or a live server.

Plain English:
- it is a toy whole-brain simulator with 8 big brain modules
- it is tuned against macro-scale fMRI summary statistics
- it is meant for experiments, ablations, and hypothesis ranking
- it is not a receptor model
- it is not a model of subjective experience
- it is not a claim that the code is simulating "what LSD feels like"

## Start Here For A PI Pitch

Public site:

- `https://grimgrimberg.github.io/LSD_Thesis/`

Use this order in a meeting:

1. **Pitch homepage:** the one-sentence claim and why this is a data-science/engineering project.
2. **Thesis story:** what is supported now, proxy-supported, exploratory, or blocked/future work.
3. **Evidence dashboard:** claim status, uncertainty fields, FDR/CI visibility, and artifact search.
4. **Methods:** motion/confounds, parcellation limits, external validation status, and local-dashboard boundary.
5. **Appendix:** derived artifacts only; no raw private data is published.

The shortest honest framing:

> This is a conservative macro-dynamics surrogate project. It is strong as a PI pitch and thesis proposal because it has a real empirical anchor, leak-proof validation scaffolding, explicit claim gates, and visible negative results. It is not yet a completed neuroscience thesis or receptor-level mechanism proof.

## What Works Where

| Surface | URL / command | What works there | What does not work there |
| --- | --- | --- | --- |
| Public pitch site | `https://grimgrimberg.github.io/LSD_Thesis/` | PI story, claim ladder, methods, static dashboard, derived artifacts | Live simulation, subject-level API calls, raw-data viewing |
| Public evidence dashboard | `https://grimgrimberg.github.io/LSD_Thesis/dashboard/` | Claim Status, q/FDR/CI fields where available, artifact search | FastAPI-only simulation and empirical subject picker |
| Local clean dashboard | `uv run python scripts/run_dashboard.py`, then `http://127.0.0.1:8000/dashboard` | Same clean dashboard, backed by local FastAPI JSON | Public sharing unless the server is running on your machine |
| Local full dashboard | `http://127.0.0.1:8000/local-dashboard` | Legacy full interactive model explorer, simulation controls, empirical viewer, local artifact serving | Suitable for a live demo, not GitHub Pages |

If something interactive does not work on GitHub Pages, that is expected: GitHub Pages is a static host. The backend-only features are intentionally available only through the local FastAPI dashboard.

## What Is Actually Proven Right Now

- The public site is a static derived-artifact snapshot.
- The local dashboard has a separate backend route for interactive features.
- The project keeps receptor/myelin/gradient/structural-connectome layers as exploratory priors unless stronger gates pass.
- Motion/confound handling, external psilocybin validation, high-resolution parcellation, and full spatial-null testing remain explicit thesis gates.
- Negative or not-supported-yet results are part of the evidence story, not hidden failures.

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

## Set / Setting / Seed Extension

PASS 2A adds a safe rest-only foundation for the working title "Set, Setting, and Seed: Guided Latent Brain Dynamics Under LSD."

Run:

```bash
uv run python scripts/run_setting_seed_pass2a.py
```

Outputs:

- `results/setting_seed/data_audit/data_audit.json`
- `results/setting_seed/reliability/reliability_table.csv`
- `results/setting_seed/latent/trajectory_metrics.csv`
- `results/setting_seed/control/control_scaffold.json`
- `results/setting_seed/dashboard/dashboard_payload.json`
- `output/doc/set_setting_seed_microsite.html`

Current boundary:

- run-02 music module time series are excluded from the legacy `results/stage_2` cache; a non-legacy run-02 extraction output exists separately for music-specific work
- subject/run-level fMRIPrep FD, DVARS, confound, and censoring tables are not currently cached
- music-control analysis is scaffolded only
- PCA outputs are visualization-only
- all claims remain macro-dynamics proxy claims, not clinical, subjective-experience, receptor, or Stable-Diffusion-literal claims

PASS 2B-0 adds readiness support only. It does not download data or extract run-02:

```bash
uv run python scripts/run_setting_seed_pass2b0.py
```

For a one-command live dashboard run:

```bash
uv run python scripts/run_everything_live.py
```

This rebuilds the current setting-seed readiness artifacts, runs the dashboard preflight, then serves:

- `http://127.0.0.1:8020/` by default, or the first available local port after that
- `http://127.0.0.1:8020/artifacts/output/doc/set_setting_seed_microsite.html` by default, or the matching selected port

To run the existing full legacy pipeline first, use:

```bash
uv run python scripts/run_everything_live.py --with-legacy-pipeline
```

This still does not run run-02 extraction, downloads, or actual music-control analysis. Those remain approval-gated.

After explicit user approval, the guarded run-02 extraction command is:

```bash
uv run python scripts/run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 --stage2-output-dir results/setting_seed/run02_extraction/stage_2_music
```

This command is intentionally non-default and writes outside legacy `results/stage_2`.

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

### 5. Run the experimental literature-aligned path

```bash
uv run python scripts/run_pipeline.py stage-2b-target-validation --parcellation harvard_oxford_8
uv run python scripts/run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass --quick
```

This path preserves the old Stages 1-4 baseline and adds a receptor/gradient neural-mass comparison against literature-aligned macro-dynamic proxy metrics. The quick Stage 5 command is a development smoke run, not a final model fit.

### 6. Or run the full local workflow

```bash
uv run python scripts/run_pipeline.py run-everything
```

This runs:
- Stages 1-4
- training window export
- condition benchmark
- multitask spectral benchmark

### 7. Launch the dashboard

```bash
uv run python scripts/run_dashboard.py
```

Then open:

- `http://127.0.0.1:8000/` for the local pitch homepage
- `http://127.0.0.1:8000/dashboard` for the clean local evidence dashboard
- `http://127.0.0.1:8000/local-dashboard` for the full backend-only interactive dashboard
- `http://127.0.0.1:8000/dashboard/full` as an alias for the full dashboard

### 8. One-command build plus dashboard

```bash
uv run python scripts/run_pipeline.py run-all-serve
```

This now does two things:
- runs Stages 1-4
- starts the local dashboard server at `http://127.0.0.1:8000/`

### 9. Full local workflow plus dashboard

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

There are two dashboard modes:

1. **Clean evidence dashboard**
- local route: `/dashboard`
- public route: `/dashboard/`
- purpose: PI pitch, claim status, uncertainty gates, artifact search
- limitation: static GitHub Pages cannot call local APIs

2. **Full local dashboard**
- local route: `/local-dashboard`
- alias: `/dashboard/full`
- purpose: backend-driven simulation controls, empirical subject/run explorer, full Plotly-heavy diagnostics
- limitation: requires `uv run python scripts/run_dashboard.py`

Inside the full local dashboard there are two different viewers:

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

### Stage 2b
Computes literature-aligned empirical target reliability checks on cached Stage 2 time series.

Outputs:
- literature metric deltas
- bootstrap confidence intervals
- leave-one-subject-out influence
- run-split stability

Main files:
- `src/lsd_thesis/metrics_literature.py`
- `src/lsd_thesis/target_validation.py`
- `docs/stage_reports/stage_2b.md`

### Stage 5
Runs the experimental receptor/gradient neural-mass objective against Stage 2b deltas.

Outputs:
- literature-weighted fit summary
- placebo baseline evaluation summary
- perturbation leaderboard
- per-seed metric deltas
- sign-match and overshoot tables

Main files:
- `src/lsd_thesis/objectives.py`
- `src/lsd_thesis/fitting_literature.py`
- `docs/stage_reports/stage_5.md`

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

## Artifact Policy

- **Tier A tracked evidence:** curated source docs, configs, command docs, stage reports, selected JSON/YAML summaries, checksums, and archive manifests.
- **Tier B generated outputs:** `output/`, temporary review folders, Plotly HTML, generated figures, CSV exports, NPY/NPZ caches, and empirical viewer payloads. These are ignored by default and should be regenerated from commands.
- **Tier C forbidden/private artifacts:** raw OpenNeuro data, local environments, machine logs, `.env` files, tokens, SSH keys, and credentials. These must not be committed or archived.

See `docs/ARCHIVE_POLICY.md` for the archive rules used when preparing a citable snapshot.

## The Most Important Output Files

- `results/stage_2/empirical_sober_targets.yaml`
- `results/stage_2/empirical_perturbation_targets.yaml`
- `results/stage_2/stage_2_summary.json`
- `results/stage_3/stage_3_summary.json`
- `results/stage_4/stage_4_summary.json`
- `results/training/condition_benchmark/comparison_summary.json`
- `results/training/condition_benchmark/benchmark_report.md`
- `results/training/rocket_condition_benchmark/comparison_summary.json`
- `results/training/rocket_condition_benchmark/benchmark_report.md`
- `results/thesis_upgrade/thesis_upgrade_status.json`
- `results/reproducible_archive/ARCHIVE_MANIFEST.json`
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
- generated outputs should be tied to their recorded provenance commit and dirty-status metadata, not treated as timeless ground truth

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

3. Run the leak-proof ROCKET-style condition benchmark:

```bash
uv run python scripts/benchmark_rocket_condition_models.py --cv5-manifest output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json --n-kernels 128
```

This writes:
- `results/training/rocket_condition_benchmark/comparison_summary.json`
- `results/training/rocket_condition_benchmark/benchmark_report.md`
- `results/training/rocket_condition_benchmark/subject_session_run_predictions.csv`
- `results/training/rocket_condition_benchmark/window_predictions_secondary.csv`

What this benchmark does:
- predicts `LSD vs placebo` using ROCKET-style random convolutional features with logistic regression
- uses the approved subject-disjoint CV5 manifest when provided
- fits normalization inside each training fold only
- reports primary metrics after aggregating window probabilities to `subject/session/run`
- keeps window-level predictions as secondary diagnostics, not primary evidence

Current takeaway:
- the ROCKET benchmark is supporting internal proxy evidence for condition signal in the exported windows
- it is not receptor-level, clinical, subjective-experience, or external-validity evidence

4. Run the local multitask spectral benchmark:

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

5. Use the cloud job scaffold:

- `cloud/hf_jobs/train_sequence_autoencoder.py`

That script is a minimal sequence autoencoder + condition head scaffold intended for managed jobs, not for rewriting the simulator.

Read:
- `docs/cloud_training.md`

If you want the local end-to-end workflow in one command, use:

```bash
uv run python scripts/run_pipeline.py run-everything
```

## Thesis Readiness And Archive Gates

The thesis-readiness layer is explicit about what is ready, proxy-only, or blocked:

```bash
uv run python scripts/build_thesis_upgrade_status.py
uv run python scripts/build_external_ingestion_status.py
uv run python scripts/build_reproducible_archive.py
```

After a GitHub release and Zenodo DOI exist for a citable snapshot, rebuild the archive with `--release-url`, `--doi`, and `--verify-publication` so the package gate records that both external identifiers resolve. Current evidence snapshot release: `https://github.com/grimgrimberg/LSD_Thesis/releases/tag/thesis-evidence-2026-06-02`; the remaining archive-publication step is a Zenodo DOI for that release.

Read:
- `docs/THESIS_READINESS_GATES.md`
- `docs/ARCHIVE_POLICY.md`

Current canonical parcellation target:
- `schaefer_100_yeo_7` as the first canonical network definition.
- `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, and `schaefer_200_yeo_17` as sensitivity targets.

The current 8-module Harvard-Oxford extraction remains a transparent proxy baseline. It should not be presented as the canonical whole-brain network definition.

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

## Audit Upgrade Entry Points

For the current thesis/research-prototype audit, read these root documents first:

1. `EXECUTIVE_SUMMARY.md`
2. `THESIS_CONCEPT_AUDIT.md`
3. `AUDIT.md`
4. `ARCHITECTURE.md`
5. `COMMANDS.md`
6. `METRICS.md`
7. `NEXT_STEPS.md`

## Research Honesty Statement

This repository supports macro-scale surrogate experiments and mismatch analysis. It does not support claims about receptor-level mechanisms, subjective psychedelic experience, clinical interpretation, or diagnostic use. Metrics such as entropy/diversity, metastability, switching, and effective barrier are proxies unless separately validated.

## Expected Outputs

After a full local run, expect stage summaries under `results/stage_*/`, generated figures under `results/stage_*/figures/`, empirical target YAML files under `results/stage_2/`, dashboard payloads under `results/stage_2/empirical_viewer/`, training summaries under `results/training/`, and publication outputs under `output/doc/`. Tier B generated outputs and Tier C raw/private artifacts are intentionally not part of the lean Git baseline.
