# Neuromaps Spatial Null Status

The current exact 8-module permutation test is not a substitute for neuromaps spatial-autocorrelation null testing.

- Status: `implemented_partial_receptor_schaefer100_moran_spatial_nulls`
- neuromaps dependency available: `true`
- neuromaps null API importable: `true`
- neuromaps version: `0.0.5`
- Spatial nulls complete: `false`
- Current module statistic: `exact_module_label_permutation_null_not_surface_spatial_null`
- Blocker: Receptor-only Schaefer100 Moran spatial nulls are executed. Full completion still needs myelin, functional-gradient, gene-expression, and preferably surface-level null coverage.

## Partial receptor Moran nulls

- Receptor spatial nulls complete: `true`
- Partial spatial nulls complete: `true`
- Execution error: `None`

## Candidate inputs

- Surface manifest: `results/cortical_maps/neuromaps_surface_inputs.json` exists=`false`
- Schaefer 100/Yeo 7 summary: `results/stage_2/parcellations/schaefer_100_yeo_7/parcellation_extraction_summary.json` exists=`true`
- Module-level alignment: `results/cortical_maps/cortical_map_alignment_status.json` exists=`true`

## Required execution contract

- Use surface or high-resolution Schaefer/Yeo map space.
- Use a neuromaps spatial-autocorrelation preserving null family appropriate to that space.
- Report r, p, q, FDR pass, CI overlap with zero, and claim status.
