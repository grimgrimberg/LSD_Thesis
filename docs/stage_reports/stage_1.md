# Stage 1 Report

## Plan

- Run the config-driven simulator in sober and altered-state-inspired regimes.
- Save activity, FC, graph, diversity, and switching figures.
- Review whether the perturbed regime moves the model in the intended macro direction.

## Results

| Metric | Baseline | Perturbed |
| --- | ---: | ---: |
| State entropy | 0.989 | 0.998 |
| Switching rate | 0.147 | 0.203 |
| Dynamic FC change | 1.265 | 1.257 |
| Within-group FC | 0.109 | 0.073 |
| Cross-group FC | 0.086 | -0.015 |

## Critical Review

- Observed gain: state entropy increased, which is consistent with a richer surrogate state repertoire.
- Observed gain: switching rate increased while within-group FC decreased, matching the intended reduction in local stability.
- Failure: the current static cross-group FC proxy decreased despite the configured increase in cross-group coupling. This suggests the first perturbation is partly producing decorrelation/noise rather than cleaner integrative dynamics.
- Failure: dynamic FC change did not increase. Stage 2 and Stage 3 should treat this perturbation as provisional rather than validated.
- Guardrail: these are model-level macro analogues and proxy metrics, not direct neurobiological estimates.
