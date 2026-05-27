# Short Proposal

## Title

Literature-aligned surrogate modeling of psychedelic-like macro-dynamics in resting-state fMRI.

## Aim

Build and evaluate a transparent surrogate modeling pipeline that compares placebo and LSD resting-state fMRI dynamics from OpenNeuro ds003059 against graph-modulated and receptor/gradient-gated neural-mass models.

## Background

The repository already implements a small eight-module surrogate model and a real-data bridge to ds003059. The first model is useful as a baseline but does not robustly match LSD-minus-placebo deltas. This motivates a stronger model path grounded in macro-scale literature targets: sensory/transmodal coupling, hierarchy differentiation, visual/global connectivity, thalamic routing, and dynamic-state diversity.

## Methods

- Preserve the legacy Stages 1-4 model as a baseline.
- Prepare Schaefer/Yeo functional parcellation support.
- Compute literature-aligned target reliability summaries from cached empirical time series.
- Fit a receptor/gradient neural-mass model using uncertainty-aware, sign-aware, multi-seed objectives.
- Report sign conflicts, overshoots, seed variance, and ablation leaderboards directly.

## Expected contribution

The contribution is a reproducible mismatch-analysis pipeline, not a claim that the model simulates LSD phenomenology. The value is in showing which macro-dynamic perturbation families are compatible with empirical target deltas and which fail.

## Near-term milestones

1. Run full multi-seed Stage 5 beyond the quick smoke budget.
2. Implement real Schaefer/Yeo extraction for ds003059.
3. Compare eight-module and Schaefer/Yeo target spaces.
4. Add paper-style figures and supervisor-reviewed failure-mode tables.
