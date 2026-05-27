# Supervisor Pitch

## One-sentence summary

I built a transparent macro-dynamics surrogate for ds003059 placebo/LSD resting-state fMRI, found where the original eight-module model fails, and added a stronger experimental path based on receptor/gradient-gated neural-mass dynamics, literature-aligned targets, and multi-seed fitting.

## What exists now

- A legacy eight-module graph-modulated bistable surrogate that still runs as Stages 1-4.
- A real-data bridge to OpenNeuro ds003059 resting-state runs.
- Cached empirical target artifacts for 15 paired subjects and 60 resting-state runs.
- Literature-aligned proxy metrics for sensory/transmodal FC, hierarchy differentiation, visual/global connectivity, thalamic/sensory coupling, and dynamic-state summaries.
- A receptor/gradient neural-mass model path with a quick literature-weighted fitting leaderboard.

## Why the first model failed informatively

The original model could improve some placebo summaries, but the LSD-minus-placebo perturbation path stayed weak. The key failure is not hidden: several old proxy metrics have sign conflicts or overshoots, and the coarse eight-module anatomical mapping is underpowered for canonical network claims.

## Better research direction

The next project should treat the old model as a baseline and develop the new path:

- Schaefer/Yeo functional parcellations instead of only eight anatomical modules.
- Receptor/gradient-gated neural-mass dynamics as a richer surrogate model.
- Literature-aligned macro-dynamic targets instead of only legacy equal-weight summary metrics.
- Multi-seed, uncertainty-aware, sign-aware fitting with ablation leaderboards.

## Claim boundary

This is not a receptor-level LSD model, not a model of subjective experience, and not a consciousness simulator. It is a macro-scale analogue for testing whether graph and hierarchy perturbations can reproduce selected fMRI summary deltas.

## Ask

Develop this into a master's project or paper prototype focused on honest model comparison: old transparent surrogate baseline, new receptor/gradient model, stronger empirical target space, and clear failure-mode reporting.
