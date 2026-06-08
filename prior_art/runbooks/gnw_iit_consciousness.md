# GNW / IIT Consciousness Analysis

## Scope

Document the Zenodo code archive for cross-state consciousness analysis and
identify what would be needed before using it as a local reproducibility target.

## Verified Archive Source

| Source | Local path | DOI | Status |
|---|---|---|---|
| Zenodo 14029241 | `prior_art/repositories/zenodo_14029241_code/Code/` | `10.5281/zenodo.14029241` | Code archive downloaded; large data archive not downloaded |

Verified archive facts:

- Zenodo record title: "Neural Correlates of Psychedelic, Sleep, and Sedated
  States Support Global Theories of Consciousness".
- License: CC BY 4.0.
- `Code.zip` is 6,473 bytes and was extracted locally.
- `Data.zip` is 435,268,809 bytes and was not downloaded.
- Extracted code files are `FC_analysis.m` and `integration_analysis_v2.m`.
- `FC_analysis.m` has hard-coded Windows paths and generates FC matrices plus
  anterior/posterior within/between summaries from 450-ROI time series.
- `integration_analysis_v2.m` loads reordered FC matrices for LSD, ketamine,
  nitrous oxide, propofol, and sleep/sedation datasets.

## Data Requirements

- Reordered functional-connectivity matrices or source time series matching the
  archive scripts.
- Cross-dataset condition labels and ROI ordering.
- MATLAB functions used in the scripts, including effect-size and FDR helpers.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py gnw_iit_consciousness
```

## Reproduction Path

1. Keep the Zenodo `Data.zip` download manual because it is a large processed
   data dependency.
2. Parameterize hard-coded paths before running any MATLAB code.
3. Start by reproducing only the LSD within/between integration branch.
4. Treat cross-state comparisons as external-validation context, not as core
   LSD_Thesis evidence unless all datasets are locally verified.

## Expected Outputs

- FC matrices and anterior/posterior network summaries.
- Within/between integration effect sizes.
- Cross-state comparison plots and statistics if all datasets are present.

## Connection to the Surrogate Model

Maps to Layer C and Layer D as an external cross-state comparison. GNW/IIT
language should not be imported into thesis claims unless local outputs are
explicitly framed as macro-dynamic connectivity proxies.

## Blockers and Open Questions

- Code is not packaged or parameterized.
- The large processed-data archive was not downloaded.
- GNW/IIT interpretation requires careful separation from this thesis's
  macro-dynamic mechanism-ranking claims.
