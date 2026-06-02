# fMRIPrep Motion-Proof Preflight

This is a preprocessing/acquisition preflight, not a motion-safety result. The strict motion gate only passes after real subject/session/run confounds are parsed and joined to dynamic deltas.

- Status: `blocked_derivative_snapshot_not_valid_raw_fmriprep_input`
- Strict proof ready: `False`
- Preflight ready: `False`
- Dataset type: `derivative`
- Local BOLD runs: `90`
- Local non-AppleDouble T1w subjects: `0`
- Missing T1w subjects: `sub-001, sub-002, sub-003, sub-004, sub-006, sub-009, sub-010, sub-011, sub-012, sub-013, sub-015, sub-017, sub-018, sub-019, sub-020`
- Parsed local confound summaries: `0`
- Paired LSD/placebo subject-run confound rows: `0`
- OpenNeuro snapshot T1w files: `15`
- OpenNeuro snapshot confound-like files: `0`
- Runtime availability: `{"apptainer": false, "docker": false, "fmriprep": false, "singularity": false}`

## Blocker

The local ds003059 dataset_description declares DatasetType=derivative and no subject/run FD, DVARS, or censoring tables are present. Do not run fMRIPrep on this derivative snapshot as if it were original raw BIDS.

## Next Action

Obtain author-provided subject/run motion confounds or the original raw BIDS inputs that preceded this derivative release; then run fMRIPrep/MRIQC in a container or HPC environment and ingest desc-confounds_timeseries.tsv files.
