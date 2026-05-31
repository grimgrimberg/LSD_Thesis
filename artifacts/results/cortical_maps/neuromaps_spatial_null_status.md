# Neuromaps Spatial Null Status

The current exact 8-module permutation test is not a substitute for neuromaps spatial-autocorrelation null testing.

- Status: `blocked_missing_neuromaps_surface_input_manifest`
- neuromaps dependency available: `true`
- neuromaps null API importable: `true`
- neuromaps version: `0.0.5`
- Spatial nulls complete: `false`
- Current module statistic: `exact_module_label_permutation_null_not_surface_spatial_null`
- Blocker: High-resolution outputs exist, but there is no neuromaps surface/input manifest describing map space and null family.

## Map-family Moran nulls

- Receptor spatial nulls complete: `false`
- Myelin spatial nulls complete: `false`
- Functional-gradient spatial nulls complete: `false`
- Gene-expression spatial nulls complete: `false`
- Partial spatial nulls complete: `false`
- Execution error: `None`

## Candidate inputs

- Surface manifest: `results/cortical_maps/neuromaps_surface_inputs.json` exists=`false`
- Schaefer 100/Yeo 7 summary: `results/stage_2/parcellations/schaefer_100_yeo_7/parcellation_extraction_summary.json` exists=`true`
- Module-level alignment: `results/cortical_maps/cortical_map_alignment_status.json` exists=`true`

## Required execution contract

- Use surface or high-resolution Schaefer/Yeo map space.
- Use a neuromaps spatial-autocorrelation preserving null family appropriate to that space.
- Report r, p, q, FDR pass, CI overlap with zero, and claim status.
