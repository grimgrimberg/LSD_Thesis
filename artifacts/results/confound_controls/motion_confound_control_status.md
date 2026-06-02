# Motion/Confound Control Status

Motion/confound handling remains a limitation until this artifact contains implemented FD/DVARS/censoring sensitivity results. If source availability is false, the correct academic action is to downgrade motion-sensitive claims rather than infer safety from proxies.

- Status: `blocked_absent_authorized_subject_level_motion_confounds`
- Claim status: `not_proven_motion_confound_control_missing`
- Merged subject/run rows: `0`
- High-risk FDR motion associations: `0`

## Blocker

Local repo search, OpenNeuro ds003059 snapshot metadata, and public OpenNeuroDerivatives repo checks did not verify subject-level FD/DVARS/censoring confounds.

## Required local input contract

- Motion summary: `results/setting_seed/motion/motion_summary.json`
- Dynamic subject views: `results/stage_2/empirical_viewer/subject_views/*.json`
- Minimum overlap: `4` subject/run rows
- Next action: Place authorized fMRIPrep confounds TSV/CSV files under one configured search root, then rerun scripts/run_setting_seed_motion_summary.py.
