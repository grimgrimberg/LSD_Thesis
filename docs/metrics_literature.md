# Literature-Aligned Metrics

This module adds macro-dynamic proxy metrics that can be evaluated on cached empirical BOLD-like time series or simulated BOLD/activity.

Primary targets:
- `unimodal_transmodal_fc`
- `hierarchy_differentiation`
- `visual_global_connectivity`
- `sensory_somatomotor_global_connectivity`
- `transition_entropy`
- `state_occupancy_entropy`
- `thalamus_to_sensory_fc`
- `striatum_to_sensory_fc` when metadata supports it

Secondary diagnostics:
- `global_mean_fc`
- `dynamic_fc_variance`
- `transition_rate`
- `thalamus_to_transmodal_fc`
- optional `fc_to_sc_coupling` when structural connectivity is provided

Guardrails:
- These metrics are proxies for macro-scale dynamics, not direct receptor, consciousness, clinical, or subjective-experience measurements.
- The legacy eight-module Harvard-Oxford extraction remains a transparent proxy space.
- Schaefer/Yeo metadata is prepared, but full Schaefer/Yeo empirical extraction has not been run in this prompt-pack pass.

Commands:

```bash
uv run python scripts/run_pipeline.py stage-2b-target-validation --parcellation harvard_oxford_8
uv run python scripts/run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass --quick
```
