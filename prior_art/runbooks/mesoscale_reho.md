# Mesoscale ReHo

## Scope

Document the mesoscale regional-homogeneity analysis as partially reproducible
unless public scripts are found.

## Verified Code Status

No dedicated public repository has been verified in this workspace.

Review-derived method notes:

- Associated tools: AFNI, JASP, and MATLAB.
- Associated method: voxel-wise Regional Homogeneity / local synchrony.
- Expected finding domain: subcortical or mesoscale synchrony changes under LSD.

## Data Requirements

- Preprocessed 4D fMRI volumes.
- AFNI-compatible ReHo/Kendall's coefficient workflow.
- Statistical design for LSD/placebo paired contrasts.
- Optional JASP statistical tables.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py mesoscale_reho
```

## Reproduction Path

1. Search for newly released code before contacting authors or reimplementing.
2. If no code exists, write an independent AFNI runbook from the paper's methods.
3. Keep exact AFNI command choices, neighborhood definition, blur/smoothing, and
   multiple-comparison correction explicit.
4. Treat outputs as independent reproduction attempts, not verified original
   scripts.

## Expected Outputs

- Voxel-wise ReHo maps.
- Paired LSD/placebo contrast maps.
- Region-level or subcortical summary tables.

## Connection to the Surrogate Model

Maps weakly to local synchrony and module-stability proxies. Because no public
code is verified, ReHo should remain a future independent-reproduction target.

## Blockers and Open Questions

- Missing public scripts.
- Exact preprocessing and statistical choices need paper-level confirmation.
- MATLAB/JASP post-processing is not currently specified.
