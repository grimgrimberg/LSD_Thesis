# Psychedelic-Dynamics Target Specification

## Framing

This document defines macro-dynamic targets for surrogate model comparison. It does not define a mechanistic receptor model, a subjective-experience model, a consciousness model, a clinical model, or a pharmacological simulation.

Use these terms:

- surrogate model
- macro-dynamic target
- literature-aligned proxy
- candidate perturbation family
- empirical target validation
- model comparison
- failure mode

## Primary Empirical Targets

Measure these directly from `ds003059` wherever the parcellation supports them:

- LSD-minus-placebo change in global or cross-network functional connectivity.
- LSD-minus-placebo change in visual/global connectivity.
- LSD-minus-placebo change in sensory/somatomotor global connectivity.
- LSD-minus-placebo thalamus-to-sensory and thalamus-to-transmodal connectivity.
- LSD-minus-placebo unimodal-to-transmodal coupling.
- Hierarchy/gradient flattening proxy between unimodal and transmodal cortex.
- Dynamic FC variance or time-resolved integration/segregation proxy.
- Entropy-like state occupancy and transition-rate proxies.
- FC-to-SC coupling proxy if structural connectivity is available or a documented synthetic fallback is used.

## Secondary And Exploratory Targets

Use as exploratory unless data and validation are strong:

- Striatum-to-sensory and striatum-to-transmodal connectivity.
- Network-specific within-network FC changes by Yeo network.
- Between-network FC matrix changes.
- State-transition entropy and dwell-time distributions.
- Control-energy or landscape-flattening proxy derived from receptor-gradient metadata.
- BOLD/HRF observation differences between latent and observed signals.

## Old Metrics Retained For Backward Compatibility

Keep these names and behaviors available for Stage 1-4 compatibility:

- `within_network_stability`
- `cross_network_communication`
- `thalamic_coupling`
- `hierarchical_compression`
- `entropy_diversity`
- `switching_rate`
- `metastability_proxy`
- `effective_barrier_proxy`

These are model-level proxies. They must not be renamed into direct biological measurements.

## Literature-Derived Expectations

These expectations are suitable as priors or sign/weighting guidance, not as proof:

- Increased global or cross-network functional connectivity is a recurring LSD fMRI target.
- Visual-network connectivity and sensory-global coupling are high-priority LSD targets.
- Thalamic connectivity changes are high-priority, especially when interpreted with receptor-informed caution.
- Reduced hierarchical differentiation between unimodal and transmodal cortex is a high-priority gradient target.
- Entropy-like and dynamic integration/segregation changes are plausible model-comparison targets but need careful metric definitions.
- Receptor-informed control-energy or landscape-flattening work supports a spatially heterogeneous perturbation family, not a receptor-level simulation in this repository.

## Directly Measured From ds003059

Required measurement path:

1. Use only `ses-LSD` and `ses-PLCB`.
2. Use resting-state `run-01` and `run-03`.
3. Exclude `run-02` music.
4. Report subject count, run count, timepoints, and missingness.
5. Report whether targets come from `harvard_oxford_8` or `schaefer_100_yeo_7`.
6. Save raw target tables and confidence intervals under a stage-specific output directory.

Current measured baseline:

- `results/stage_2/empirical_data_quality.json` reports 15 paired subjects, 60 records, and 217 timepoints per run.
- Current `harvard_oxford_8` deltas conflict with literature-style signs for `within_network_stability`, `entropy_diversity`, and `metastability_proxy`.

## What Must Not Be Overclaimed

Do not claim:

- LSD pharmacology has been simulated.
- 5-HT2A receptor binding has been mechanistically modeled.
- Subjective experience has been simulated.
- Consciousness, ego dissolution, or clinical effects have been explained or predicted.
- A best-fitting perturbation is the true biological mechanism.
- A Schaefer/Yeo parcellation result is validated before the extraction and reliability artifacts exist.

## Literature Sources Checked

- Carhart-Harris et al. 2016, PNAS, DOI `10.1073/pnas.1518377113`.
- Tagliazucchi et al. 2016, Current Biology, DOI `10.1016/j.cub.2016.02.010`.
- Preller et al. 2018, eLife, DOI `10.7554/eLife.35082`.
- Lebedev et al. 2016, Human Brain Mapping, DOI `10.1002/hbm.23234`.
- Luppi et al. 2021, NeuroImage, DOI `10.1016/j.neuroimage.2020.117653`.
- Girn et al. 2022, NeuroImage, DOI `10.1016/j.neuroimage.2022.119220`.
- Singleton et al. 2022, Nature Communications, DOI `10.1038/s41467-022-33578-1`.
- Herzog et al. 2023, Scientific Reports, DOI `10.1038/s41598-023-32649-7`.

## Minimum Target Table Schema

Every new target table should include:

- `metric`
- `parcellation_id`
- `condition_a`
- `condition_b`
- `delta`
- `bootstrap_ci_low`
- `bootstrap_ci_high`
- `paired_subject_count`
- `run_count`
- `expected_sign`
- `observed_sign`
- `sign_match`
- `source`
- `notes`

