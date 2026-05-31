# Module-DVARS / Censoring Sensitivity Status

This is a module-derived DVARS/censoring sensitivity layer. It strengthens confound handling but does not replace real fMRIPrep FD, DVARS, and censoring confounds.

- Status: `implemented_module_dvars_censoring_sensitivity`
- Claim status: `module_dvars_sensitive_downgrade_required`
- Subject/run rows: `30`
- High-risk module-DVARS associations: `10`
- Unstable high-burden exclusions: `1`

## Strongest module-DVARS associations

| Feature | Metric | n | r | q | Flag |
| --- | --- | ---: | ---: | ---: | --- |
| module_dvars_p95_delta_lsd_minus_placebo | effective_barrier_proxy | 30 | -0.742 | 0.000 | yes |
| module_dvars_max_delta_lsd_minus_placebo | effective_barrier_proxy | 30 | -0.735 | 0.000 | yes |
| module_dvars_p95_delta_lsd_minus_placebo | switching_rate | 30 | 0.735 | 0.000 | yes |
| module_dvars_max_delta_lsd_minus_placebo | switching_rate | 30 | 0.723 | 0.000 | yes |
| module_dvars_mean_delta_lsd_minus_placebo | switching_rate | 30 | 0.698 | 0.000 | yes |
| module_dvars_p95_delta_lsd_minus_placebo | thalamic_coupling | 30 | 0.688 | 0.000 | yes |
| module_dvars_mean_delta_lsd_minus_placebo | effective_barrier_proxy | 30 | -0.671 | 0.001 | yes |
| module_dvars_p95_delta_lsd_minus_placebo | cross_network_communication | 30 | 0.670 | 0.001 | yes |
| module_dvars_spike_fraction_delta_lsd_minus_placebo | cross_network_communication | 30 | 0.634 | 0.002 | yes |
| module_dvars_spike_fraction_delta_lsd_minus_placebo | thalamic_coupling | 30 | 0.562 | 0.010 | yes |
| module_dvars_max_delta_lsd_minus_placebo | thalamic_coupling | 30 | 0.484 | 0.049 | no |
| module_dvars_spike_fraction_delta_lsd_minus_placebo | within_network_stability | 30 | 0.450 | 0.085 | no |
