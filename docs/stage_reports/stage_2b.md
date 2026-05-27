# Stage 2b Literature-Metric Target Validation

This report summarizes literature-aligned proxy metrics on cached empirical resting-state records.
It does not add receptor-level or subjective-experience claims.

## Summary

- Status: complete
- Source: cached_stage_2_harvard_oxford_8
- Records: 60
- Paired subjects: 15
- Metrics with paired deltas: 13

## Metric Deltas

| Metric | LSD - placebo mean | 95% bootstrap CI | Paired subjects |
| --- | ---: | ---: | ---: |
| dynamic_fc_variance | -0.000938062825 | -0.00481311277 to 0.003843495319 | 15 |
| global_mean_fc | 0.071510263179 | 0.031419896238 to 0.116486556014 | 15 |
| gradient_flattening_delta | 0 | 0 to 0 | 15 |
| hierarchy_differentiation | -0.000136522609 | -0.036294339901 to 0.037666153769 | 15 |
| sensory_somatomotor_global_connectivity | 0.057473876561 | 0.013126488366 to 0.098746003991 | 15 |
| state_occupancy_entropy | 0 | 0 to 0 | 15 |
| striatum_to_sensory_fc | 0 | 0 to 0 | 15 |
| thalamus_to_sensory_fc | 0.098029263352 | -0.008868953366 to 0.199468384404 | 15 |
| thalamus_to_transmodal_fc | 0.136334910042 | 0.063638803305 to 0.202313833763 | 15 |
| transition_entropy | 0.009576783163 | -0.001816498816 to 0.019912819245 | 15 |
| transition_rate | 0.018672839506 | 0.000462962963 to 0.036581790123 | 15 |
| unimodal_transmodal_fc | 0.047335029864 | 0.006848467036 to 0.085069939525 | 15 |
| visual_global_connectivity | 0.077778302242 | 0.040570387942 to 0.120880050224 | 15 |

## Guardrails

- These are macro-dynamic target checks in the available parcellation space.
- Sign conflicts or weak stability should be treated as model failure evidence, not polished away.
- Schaefer/Yeo outputs remain metadata-prepared until real extraction is run.
