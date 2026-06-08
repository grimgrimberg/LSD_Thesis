# Cortical Gradients / BrainSpace

## Scope

Use BrainSpace as the preferred documented toolbox for cortical gradient
analysis, while keeping psychedelic hierarchy claims separate from local proof.

## Verified Code Source

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `MICA-MNI/BrainSpace` | `prior_art/repositories/mica_brainspace/` | `8730de88ae32` | Public, cloned |

Verified repository facts:

- BrainSpace is a Python and MATLAB toolbox for macroscale gradient mapping.
- The README points to `https://brainspace.readthedocs.io` for installation and
  documentation.
- The checked repository includes `requirements.txt`, `setup.py`, Python docs,
  MATLAB analysis code, and a BSD 3-Clause license file.

## Data Requirements

- Functional connectivity matrices or surface data.
- A chosen gradient approach such as diffusion map embedding.
- Optional alignment target if comparing gradients across conditions.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py cortical_gradients_brainspace
```

## Reproduction Path

1. Build or load local condition-specific FC matrices.
2. Fit gradients with a fixed kernel and embedding choice.
3. Align LSD/placebo gradients before computing condition contrasts.
4. Report hierarchy compression or gradient shift as a macro-scale proxy, not
   as subjective-experience evidence.

## Expected Outputs

- Gradient component scores.
- Aligned condition-level gradient maps.
- Gradient contrast statistics and optional spatial-null tests.

## Connection to the Surrogate Model

Maps to Layer C (hierarchy/routing). Gradient compression or alignment can
benchmark whether surrogate hierarchy effects resemble known cortical
hierarchy metrics, but it remains a macro-scale proxy comparison.

## Blockers and Open Questions

- BrainSpace is a general toolbox, not a ds003059 analysis repository.
- Surface/parcellation alignment must be fixed before comparison.
