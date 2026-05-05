# Cloud Training

## Purpose

The simulator itself is intentionally small and explainable.

The cloud-training scaffold is for later experiments such as:
- sequence autoencoders on extracted module windows
- latent-state predictors
- condition classifiers
- hybrid learned surrogates that sit next to, not inside, the transparent simulator

## Current Infrastructure

### Real exported dataset

Run:

```bash
uv run python scripts/export_training_dataset.py
```

This writes:
- `results/training/ds003059_windows.npz`

Contents:
- `windows`: shape `[sample, window, 8]`
- `condition`: `0 = placebo`, `1 = LSD`
- `subject`
- `session`
- `run`
- `window_length`
- `stride`

By default this is built from:
- `results/stage_2/empirical_run_summaries.json`
- the saved module time-series `.npy` files produced in Stage 2

### Cloud job scaffold

The first cloud-ready training script is:

- `cloud/hf_jobs/train_sequence_autoencoder.py`

It is a minimal PyTorch GRU autoencoder with a small condition-classification head.

Why this choice:
- simple
- cheap
- easy to inspect
- useful as a baseline representation learner for 8-module trajectories

## Why Hugging Face Jobs

This repo already has a lightweight managed-job target in mind:
- easy GPU access later
- reproducible script-based jobs
- no need to contaminate the main simulator package with heavy training dependencies

The job script is written as a PEP 723 UV script so it can be run in managed environments cleanly.

## Suggested Workflow

1. Run Stage 2 so the real ds003059 extraction exists.
2. Export the training windows:

```bash
uv run python scripts/export_training_dataset.py
```

3. Upload or copy `results/training/ds003059_windows.npz` to the cloud job environment.
4. Run `cloud/hf_jobs/train_sequence_autoencoder.py`.
5. Save:
   - model weights
   - training history
   - latent embeddings
   - downstream evaluation metrics

## What To Try Later

### Baseline
- GRU autoencoder on 8-module trajectories

### Better next experiments
- temporal convolutional autoencoder
- contrastive next-window predictor
- latent ODE on the 8-module dynamics
- mixture-of-experts model where experts correspond to perturbation mechanisms

## Guardrails

Use cloud training for:
- representation learning
- compression
- classification
- emulation experiments

Do not use it to overclaim:
- that the learned model captures subjective states
- that the learned latent space is a mechanistic account of psychedelic action
- that high accuracy implies biological realism

## Current Limitation

This infrastructure is a scaffold, not a finished training pipeline.

What is already real:
- actual ds003059-derived windows
- tested local export
- a cloud-ready training script

What is still missing:
- managed job submission wrapper
- automatic artifact upload
- multi-run experiment tracking
- uncertainty-aware evaluation
