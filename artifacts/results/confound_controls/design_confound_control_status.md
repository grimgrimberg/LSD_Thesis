# Design Confound Control Status

This artifact strengthens run/session/signal-quality confound handling from existing empirical records. It does not complete the separate motion gate, which still requires structured FD, DVARS, and censoring confounds.

- Status: `implemented_design_confound_control_result`
- Claim status: `no_fdr_design_confound_signal_detected`
- Subject/run rows: `30`
- High-risk design-confound flags: `0`

## Paired run tests

| Metric | n | difference | q | Flag |
| --- | ---: | ---: | ---: | --- |
| entropy_diversity | 15 | -0.011 | 0.697 | no |
| effective_barrier_proxy | 15 | 0.160 | 0.697 | no |
| switching_rate | 15 | -0.012 | 0.697 | no |
| thalamic_coupling | 15 | -0.049 | 0.697 | no |
| cross_network_communication | 15 | -0.024 | 0.697 | no |
| metastability_proxy | 15 | -0.023 | 0.701 | no |
| within_network_stability | 15 | -0.017 | 0.697 | no |
| hierarchical_compression | 15 | 0.024 | 0.701 | no |
