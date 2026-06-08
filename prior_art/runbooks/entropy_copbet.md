# Entropy Standardization / CopBET

## Scope

Use CopBET as the primary entropy/complexity toolbox for ds003059-compatible
time-series and volume inputs.

## Verified Code Source

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `anders-s-olsen/CopBET` | `prior_art/repositories/olsen_copbet/` | `8787820bbb95` | Public, cloned |

Verified repository facts:

- `CopBET_main_CH2016data.m` demonstrates entropy metrics on the openly
  available acute IV LSD dataset.
- `LSDdata/LSDdata_ROI.m` loops over `ses-LSD` and `ses-PLCB`, and explicitly
  uses runs `[1,3]` with the comment that run 2 is music.
- The repo includes example shortened NIfTI and ROI `.mat` files for one
  subject across several atlases.
- The README states MATLAB R2018b testing and GPL terms, although no root
  license file is present.
- `copbet_py/` contains a Python translation, with DCC entropy not yet fully
  implemented in Python according to the README.

## Data Requirements

- Raw or preprocessed ds003059 BOLD volumes for voxel metrics.
- ROI time series for time-series metrics.
- Atlas files in matching space: AAL90, Yeo, Schaefer, Shen, Craddock,
  Lausanne, Smith, or Schaefer-Tian variants are referenced in the repo.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py entropy_copbet
```

## Reproduction Path

1. Start with the repo's example data to validate MATLAB/Python setup.
2. If using full ds003059, regenerate ROI files rather than copying external
   derived outputs into this repository.
3. Prefer a small metric subset first: sample entropy, geodesic entropy,
   temporal entropy, and time-series complexity.
4. Record the atlas, run inclusion, cerebellum treatment, and metric-specific
   preprocessing decisions.

## Expected Outputs

- Per-subject/per-condition entropy tables.
- Optional voxel-wise metric outputs for atlas-dependent functions.
- Permutation or mixed-model statistical summaries if using the R helper.

## Connection to the Surrogate Model

Maps to Layer D (dynamic repertoire) and partly Layer A (transition-state
summary). CopBET metrics can benchmark entropy/diversity proxies produced by
the surrogate model against standardized prior-art entropy measures.

## Blockers and Open Questions

- Full ds003059 data are not downloaded by this runbook.
- DCC entropy remains MATLAB-only in the checked source.
- Atlas-space matching must be verified before any voxel-wise metric is trusted.
