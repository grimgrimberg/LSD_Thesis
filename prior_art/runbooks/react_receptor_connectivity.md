# REACT Receptor Connectivity

## Scope

Use `react-fmri` as a documented receptor-enriched functional-connectivity
toolbox, not as evidence that receptor-specific ds003059 findings have been
locally reproduced.

## Verified Code Source

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `ottaviadipasquale/react-fmri` | `prior_art/repositories/dipasquale_react_fmri/` | `48462c0a94e8` | Public, cloned |

Verified repository facts:

- The README describes REACT as a two-step multivariate regression using PET
  templates as spatial priors.
- Command-line scripts are present: `react_normalize`, `react_masks`, and
  `react`.
- Example files include `data/pet_atlas.nii.gz`, `data/gm_mask.nii.gz`, and
  `data/subject_list.txt`.
- Requirements include Python 3, NumPy, SciPy, nibabel, and scikit-learn.
- The repository includes an MIT license file.

## Data Requirements

- Preprocessed 4D fMRI in standard space.
- PET receptor templates in the same resolution/space.
- Grey-matter and stage masks.
- Output directory for subject-level receptor-enriched maps.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py react_receptor_connectivity
```

## Reproduction Path

1. Normalize receptor/PET templates with `react_normalize`.
2. Build subject list and masks with `react_masks`.
3. Run `react` per subject only after confirming all images share space and
   resolution.
4. Summarize receptor-enriched FC maps as method outputs, not biological
   receptor validation for this thesis.

## Expected Outputs

- `*_react_stage1.txt` receptor-associated time series.
- `*_react_stage2.nii.gz` subject-specific target-enriched FC maps.
- Optional split maps per PET atlas.

## Connection to the Surrogate Model

Maps to Layer E and receptor-prior sensitivity checks. In this thesis it can
support future receptor-map control experiments, but it cannot by itself promote
receptor-level realism claims for the 8-module surrogate.

## Blockers and Open Questions

- Requires PET templates and FSL-compatible preprocessing decisions.
- The checked source is a general toolbox, not a ds003059-specific pipeline.
