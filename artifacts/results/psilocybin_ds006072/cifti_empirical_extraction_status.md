# ds006072 CIFTI Empirical Extraction Status

This is real ds006072 CIFTI extraction into an empirical viewer, but it uses broad CIFTI structure families. It is stronger than manifest readiness and weaker than a surface/parcellation-matched stress test unless schaefer100_empirical_viewer_ready is true; it is not replication evidence by itself.

- Status: `implemented_ds006072_schaefer100_parcellation_empirical_viewer`
- Claim status: `schaefer100_empirical_viewer_ready_for_unchanged_scoring`
- Minimum subjects required: `3`
- Subject-view count: `3`
- Module contract: `CIFTI brain-structure-family 8-module external stress test`

## Modules

`cortex_left`, `cortex_right`, `thalamus`, `striatal_basal_ganglia`, `limbic_medial_temporal`, `cerebellum`, `brain_stem`, `ventral_diencephalon`

## Stronger Schaefer100 Layer

- Schaefer100 ready: `true`
- Schaefer100 subject-view count: `3`
- Schaefer100 viewer: `results/psilocybin_ds006072/parcellations/schaefer_100_yeo_7/empirical_viewer`

## Next commands

- `.\.venv\Scripts\python.exe scripts\build_ds006072_payload_plan.py --execute`
- `.\.venv\Scripts\python.exe scripts\build_ds006072_cifti_empirical_viewer.py --execute`
- `.\.venv\Scripts\python.exe scripts\build_ds006072_comparable_validation.py`
