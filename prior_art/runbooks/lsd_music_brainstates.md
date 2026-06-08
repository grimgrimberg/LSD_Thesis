# LSD and Music Brain-State Dynamics

## Scope

Document the Adamska/Finc music and brain-state workflow while preserving the
repo's gated treatment of music-control claims.

## Verified Code Source

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `igaadamska/LSD-music-brainstates` | `prior_art/repositories/adamska_lsd_music_brainstates/` | `16428ebd0eb9` | Public, cloned |

Verified repository facts:

- No top-level README is present in the checked commit.
- The repository is notebook-based and includes:
  `01_Timeseries_extraction.ipynb`, `02_Timeseries_concatenation.ipynb`,
  `03_KMeans_clustering.ipynb`,
  `04_Correlating_cluster_labels_with _brain_networks.ipynb`,
  `05_Neurosynth_correlations.ipynb`,
  `06_States'_mesures_analysis_part_1.ipynb`,
  `06.1_States'_mesures_analysis_part_2.ipynb`, and `R_MLM_statistics.ipynb`.
- Subfolders provide alternate 5-, 6-, and 8-state notebook variants.
- The repository includes a license file.

## Data Requirements

- ds003059 run-02/music time series if reproducing music-control claims.
- Rest/music/rest run labeling and subject exclusion rules.
- Parcellated time series compatible with the notebooks.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py lsd_music_brainstates
```

## Reproduction Path

1. Do not promote music-control claims until local run-02 artifacts and
   exclusions are ready.
2. Inspect notebooks for hard-coded paths before execution.
3. Recreate time-series extraction and concatenation on a small subject subset.
4. Run k-means and state-measure notebooks only after the extraction outputs are
   verified.

## Expected Outputs

- Brain-state labels.
- State transition matrices.
- Fractional occupancy and dwell-time measures.
- Mixed-model statistics for condition/music effects.

## Connection to the Surrogate Model

Maps to Layer A (state transitions) and Layer D (dynamic repertoire). Music-run
findings are useful design inspiration, but this repository's music-control
claim remains gated until run-02 extraction and subject exclusions are complete.

## Blockers and Open Questions

- Notebook-only workflow makes provenance and parameters harder to audit.
- Local thesis guidance currently treats run-02/music as gated.
