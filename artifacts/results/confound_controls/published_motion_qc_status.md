# Published ds003059 Motion QC Context

Use this as motion-context evidence only. Do not claim motion confounds are controlled until the dedicated subject-level FD/DVARS/censoring gate passes.

- Status: `blocked_missing_published_motion_qc_source`
- Claim status: `not_proven_motion_qc_context_missing`
- Source: `data/ds003059/README`

## Blocker

The local ds003059 README did not contain all expected motion QC snippets.

- Missing snippets: `excluded_high_motion_subjects, fd_exclusion_threshold, retained_mean_fd_difference, condition_fd_difference, scrubbed_volume_percentages, distance_related_motion_qc`

## Limitations

- This is published aggregate QC context, not subject/run confound data.
- It cannot join framewise displacement, DVARS, or censoring burden to each empirical dynamic delta.
- It strengthens the motion defense slide but does not complete the strict motion/confound gate.

## Next action

Add subject/session/run confound TSV/CSV files with FD, DVARS, and censoring columns, then rerun scripts/build_motion_confound_controls.py.
