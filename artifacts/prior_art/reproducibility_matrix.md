# Reproducibility Matrix - ds003059 Prior-Art Landscape

Ranked from most immediately reproducible to least immediately reproducible in
this workspace. Scores reflect code/data availability and local blockers, not
scientific importance.

## Matrix

| Rank | Analysis family | Score | Public code | Missing derivatives | MATLAB dependency | Receptor/PET maps | Structural connectome | Ambiguous preprocessing | Author-only | Notes |
|---:|---|---:|---|---|---|---|---|---|---|---|
| 1 | CopBET entropy | 5/5 | Yes | Full ROI/volume derivatives needed beyond bundled examples | Primary MATLAB; Python port partial | No | No | Atlas/cerebellum handling | No | Direct ds003059 examples and ROI extraction script; best first reproduction target |
| 2 | Cortical gradients / BrainSpace | 5/5 | Yes | FC matrices needed | Optional | No | No | Low once FC/parcellation fixed | No | Excellent toolbox docs and BSD license; paper-specific ds003059 pipeline still separate |
| 3 | Neuroreceptor priors / eigenmodes | 4/5 | Yes | Local parcellation alignment needed | Optional, depending on method | Yes | Optional | Receptor-map alignment | No | Strong resource availability; license/citation and noncommercial terms matter |
| 4 | Ising + LZW complexity | 4/5 | Yes | Required `.npy`/`.mat` derivatives missing | No | No | No | Binarization and parcellation order | No | Direct notebook and code; main repo has no root license file |
| 5 | LSD music brain states | 4/5 | Yes | Run-02/music derivatives and exclusions needed | No obvious MATLAB dependency | No | No | Notebook parameters and K selection | No | Notebook code available but no README; local music claims remain gated |
| 6 | Energy landscape / network control | 3/5 | Yes | Parcellated series and state partitions needed | Yes | Yes | Yes | State-space and connectome provenance | No | Direct ds003059 reference; structural and receptor inputs are the hard gates |
| 7 | REACT connectivity | 3/5 | Yes | Preprocessed fMRI needed | No | PET templates required | No | Image space/resolution/FSL-style masks | No | General toolbox, not ds003059-specific code |
| 8 | Dynamic integration / segregation | 3/5 | Yes | Time-varying FC needed | Yes | No | No | Windowing and community choices | No | Method code public, but not ds003059-specific in README |
| 9 | GNW/IIT consciousness | 2/5 | Yes, Zenodo code | Processed cross-state data not downloaded | Yes | No | No | Hard-coded paths and cross-dataset alignment | No | `Code.zip` verified and extracted; `Data.zip` is large and remains manual |
| 10 | Traveling waves | 2/5 | Supporting dependency only | Preprocessed time series/surfaces needed | No | Optional maps/nulls | No | CPC implementation details | No | `neuromaps` is not a full analysis repo |
| 11 | Mesoscale ReHo | 1/5 | No verified public code | Preprocessed volumes needed | Yes | No | No | AFNI/JASP/MATLAB pipeline specifics | No | Independent reconstruction required unless code appears |
| 12 | DLPFC Granger causality | 1/5 | No public code verified | fMRI/MEG derivatives needed | Unknown | No | No | MEG-fMRI fusion and model order | Yes | Author-only code; manual contact template prepared |

## Blocker Types

| Blocker | Meaning |
|---|---|
| Missing derivatives | The public raw dataset alone is insufficient; analysis needs preprocessed volumes, ROI time series, FC matrices, or paper-specific arrays. |
| MATLAB dependency | Reproduction likely requires a MATLAB license or careful independent reimplementation. |
| Receptor/PET maps | Receptor density maps or PET templates must be aligned to local fMRI data. |
| Structural connectome | A structural connectivity matrix is required and must match the parcellation. |
| Ambiguous preprocessing | The precise preprocessing, parcellation, run inclusion, or statistical design needs clarification. |
| Author-only | Code is not public and should be requested manually if needed. |

## Current Local Input Check

`uv run python prior_art/scripts/dry_run_analysis_inputs.py all` currently checks
required input roots and reports `results/prior_art` as a creatable output
target. It currently finds:

- Present: `results/stage_2`, `data/ds003059`,
  `results/stage_2/parcellations`,
  `results/cortical_maps/neuromaps_annotations`, and
  `results/structural_connectome`.
- Output target: `results/prior_art`.

The output directory is harmless for dry-run use and can be created by future
wrapper work. Missing input roots remain real blockers for strict checks.
