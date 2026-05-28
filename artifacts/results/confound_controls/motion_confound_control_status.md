# Motion/Confound Control Status

Motion/confound handling remains a limitation until this artifact contains implemented sensitivity results.

- Status: `unavailable_not_found`
- Claim status: `not_proven_motion_confound_control_missing`
- Merged subject/run rows: `0`
- High-risk FDR motion associations: `0`

## Blocker

No parsed subject/session/run motion summaries are available.

## Required local input contract

- Motion summary: `results/setting_seed/motion/motion_summary.json`
- Dynamic subject views: `results/stage_2/empirical_viewer/subject_views/*.json`
- Minimum overlap: `4` subject/run rows
- Next action: Place authorized fMRIPrep confounds TSV/CSV files under one configured search root, then rerun scripts/run_setting_seed_motion_summary.py.
