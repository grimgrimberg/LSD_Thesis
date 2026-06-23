# SPEC.md

## Goal

Build an MSc-grade computational neuroscience / Neuro-AI MVP that tests whether transparent graph-modulated surrogate mechanisms can partially match, rank, or fail against psychedelic-like macro-dynamic proxy signatures.

## Chosen Approach

The simulator uses 8 graph-coupled latent modules with stochastic bistable dynamics, adaptation, and an optional low-dimensional top-down constraint. This is the simplest defensible path that can express metastability, controllable switching, coupling reconfiguration, and increased signal diversity without introducing opaque deep-learning machinery.

## Mathematical Formulation

For module `i`, the latent state evolves as:

`dx_i = ( barrier_i * (x_i - x_i^3) - rigidity_i * (x_i - baseline_i) - adaptation_gain_i * a_i + cross_scale * sum_j W_ij * tanh(x_j) + constraint_scale * ((H x)_i - x_i) ) / tau_i * dt + temperature_i * dW_i`

`da_i = (x_i - a_i) / adaptation_tau_i * dt`

Interpretation:
- `barrier_i`: controls local metastability depth in the surrogate model
- `rigidity_i`: local within-module stabilizing pull
- `W`: inter-module graph
- `cross_scale`: global cross-network communication scale
- `constraint_scale`: pull toward a sober low-dimensional manifold `H`
- `temperature_i`: stochasticity level
- `tau_i`: timescale

Important caveat: these are model-level control terms, not direct neurobiological parameters.

## Two Main Regimes

### Sober Baseline

Target behavior:
- stronger within-network stability
- lower cross-network communication
- lower diversity / entropy
- fewer state transitions
- longer dwell times in metastable states

### Altered-State-Inspired Perturbation

Target behavior:
- weaker within-network stability
- stronger cross-network communication
- higher diversity / entropy
- more state transitions
- lower effective switching-barrier proxy

## Stages

### Stage 1

Synthetic graph, simulator, metrics, plots, deterministic tests, first dashboard slice.

### Stage 2

Summary-statistics ingestion path, sober feature extraction, sober fitting routine, fit report.

### Stage 3

Perturbation operator, mechanism-proxy ranking, empirical comparison path, perturbed-vs-sober report.

### Stage 4

Ablation study, ranked mechanism importance, pairwise combinations if feasible, polished dashboard.

## Empirical Strategy

Primary initial anchor:
- OpenNeuro `ds003059` version `1.0.0`

Fallback strategy:
- use precomputed/public summary statistics first
- keep raw-ingestion interfaces stable so real data can replace summaries later

## Outputs

Required files:
- `README.md`
- `AGENTS.md`
- `SPEC.md`
- `docs/architecture.md`
- `docs/stage_reports/stage_1.md`
- `docs/stage_reports/stage_2.md`
- `docs/stage_reports/stage_3.md`
- `docs/stage_reports/stage_4.md`
- `docs/limitations.md`
- `docs/next_steps.md`
