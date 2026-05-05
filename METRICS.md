# Metrics

All metrics are model-level or empirical-summary proxies. None is a direct biological, subjective, receptor-level, clinical, or diagnostic measurement.

## Core Proxy Metrics

- `fc_matrix`: Pearson correlation matrix across module time series.
- `within_network_stability`: mean FC among modules in the same coarse group.
- `cross_network_communication`: mean FC across coarse groups.
- `thalamic_coupling`: mean FC between `thalamic_gateway` and all other modules.
- `hierarchical_compression`: correlation between sensory mean signal and associative mean signal.
- `entropy_diversity`: normalized entropy of KMeans-derived state labels.
- `switching_rate`: fraction of adjacent timepoints where KMeans-derived state label changes.
- `metastability_proxy`: sliding-window FC change magnitude.
- `effective_barrier_proxy`: mean dwell time in KMeans-derived state labels.

## Perturbation/Comparison Metrics

- `sober_vs_perturbed_delta`: perturbed metric minus sober metric under matched model setup.
- `empirical_delta`: ds003059 LSD minus placebo paired summary.
- `ablation_effect_size`: mismatch-score change when one or two perturbation mechanisms are active.
- `sign_agreement_fraction`: fraction of nonzero target deltas where model and target signs agree.
- `seed_noise_null`: sober-vs-sober offset-seed comparison used to contextualize perturbation scores.

## Robustness Metrics

- Fixed-seed reproducibility.
- Mean and standard deviation across seed panels.
- Sensitivity across perturbation strengths.
- Proposed: atlas sensitivity across alternative module definitions.
- Proposed: clustering sensitivity for KMeans-derived metrics.

## Implementation Status

- Implemented: FC, dynamic FC, entropy/diversity, switching, dwell/barrier proxy, thalamic coupling, hierarchy compression, multi-seed mean/std, perturbation score, sign agreement, seed-noise null.
- Present but broken: some intended altered-state directions are not consistently expressed by the current Stage 1 perturbed config.
- Proposed: make slow/sensitive metrics clearly marked and documented in reports.

## Safe Wording

Use: "entropy-like activity proxy", "switching-rate proxy", "metastability proxy", "model-level barrier proxy", "cross-module coupling proxy".

Avoid: "neural entropy was measured", "the brain entered a psychedelic state", "the model simulates LSD", "receptor mechanism".
