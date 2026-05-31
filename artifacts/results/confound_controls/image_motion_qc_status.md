# Image-Derived Motion/QC Control Status

This is a conservative image-derived motion/QC control, not a full fMRIPrep FD/DVARS/censoring proof. If high-risk associations or unstable high-burden exclusions appear, motion-sensitive mechanism claims must be downgraded.

- Status: `implemented_image_derived_motion_qc_control`
- Claim status: `image_motion_qc_sensitive_downgrade_required`
- Subject/run rows: `30`
- Raw BOLD files summarized: `60`
- High-risk image-QC associations: `0`
- Unstable high-burden exclusions: `4`

## Strongest image-derived motion/QC associations

| Feature | Metric | n | r | q | Flag |
| --- | --- | ---: | ---: | ---: | --- |
| com_displacement_mean_mm_mean_abs | entropy_diversity | 30 | -0.548 | 0.116 | no |
| com_displacement_max_mm_mean_abs | within_network_stability | 30 | 0.525 | 0.116 | no |
| global_signal_derivative_rms_mean_abs | within_network_stability | 30 | 0.524 | 0.116 | no |
| com_displacement_max_mm_mean_abs | entropy_diversity | 30 | -0.514 | 0.116 | no |
| image_dvars_p95_mean_abs | within_network_stability | 30 | 0.500 | 0.116 | no |
| image_dvars_mean_mean_abs | within_network_stability | 30 | 0.498 | 0.116 | no |
| global_signal_derivative_rms_delta_lsd_minus_placebo | within_network_stability | 30 | 0.483 | 0.116 | no |
| image_dvars_mean_mean_abs | entropy_diversity | 30 | -0.482 | 0.116 | no |
| com_displacement_p95_mm_mean_abs | entropy_diversity | 30 | -0.480 | 0.116 | no |
| com_displacement_p95_mm_mean_abs | within_network_stability | 30 | 0.471 | 0.124 | no |
| com_displacement_mean_mm_mean_abs | within_network_stability | 30 | 0.462 | 0.133 | no |
| image_dvars_max_mean_abs | within_network_stability | 30 | 0.454 | 0.135 | no |
