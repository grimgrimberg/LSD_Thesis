# Published ds003059 Motion QC Context

Use this as motion-context evidence only. Do not claim motion confounds are controlled until the dedicated subject-level FD/DVARS/censoring gate passes.

- Status: `implemented_published_ds003059_motion_qc_context`
- Claim status: `published_fd_context_available_not_subject_level_confound_control`
- Source: `data/ds003059/README`

## Published QC facts

| Measure | Value | Unit | Interpretation |
| --- | ---: | --- | --- |
| subjects_excluded_for_excessive_head_motion | 4 | subjects | The original dataset excluded high-motion subjects before group BOLD analyses. |
| retained_bold_subject_count | 15 | subjects | The local empirical anchor uses the retained BOLD-analysis sample. |
| initial_scrubbing_exclusion_threshold | 15.0 | percent_scrubbed_volumes_at_fd_0_5_mm | Subjects above this threshold were excluded in the original analysis. |
| post_exclusion_scrubbing_fd_threshold | 0.4 | mm_fd | The retained analysis used a stricter scrubbing threshold after high-motion exclusions. |
| retained_placebo_mean_fd | 0.074 +/- 0.032 | mm_fd | Published retained-sample placebo mean FD. |
| retained_lsd_mean_fd | 0.12 +/- 0.05 | mm_fd | Published retained-sample LSD mean FD. |
| retained_between_condition_mean_fd_difference | 0.046 +/- 0.032; p=0.0002 | mm_fd | Published retained-sample LSD/placebo motion difference; this remains a serious confound risk. |
| placebo_scrubbed_volume_percent | 0.4 +/- 0.8 | percent_volumes | Published retained-sample placebo scrubbing burden. |
| lsd_scrubbed_volume_percent | 1.7 +/- 2.3 | percent_volumes | Published retained-sample LSD scrubbing burden. |
| maximum_scrubbed_volume_percent_per_scan | 7.1 | percent_volumes | Published maximum retained-scan scrubbing burden. |
| distance_fd_rsfc_correlation_lsd | -0.0009; p=0.089 | correlation | Published distance-dependent motion QC was approximately null for LSD. |
| distance_fd_rsfc_correlation_placebo | -0.025; p<0.001 | correlation | Published placebo distance-dependent motion QC was small but statistically nonzero. |

## Limitations

- This is published aggregate QC context, not subject/run confound data.
- It cannot join framewise displacement, DVARS, or censoring burden to each empirical dynamic delta.
- It strengthens the motion defense slide but does not complete the strict motion/confound gate.

## Next action

Add subject/session/run confound TSV/CSV files with FD, DVARS, and censoring columns, then rerun scripts/build_motion_confound_controls.py.
