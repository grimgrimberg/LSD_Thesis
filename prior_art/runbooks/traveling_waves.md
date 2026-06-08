# Traveling Brain Waves

## Scope

Document traveling-wave/CPC analysis as a partial reproducibility target because
only supporting dependencies are currently verified.

## Verified Supporting Source

| Source | Role | Status |
|---|---|---|
| `https://netneurolab.github.io/neuromaps/installation.html` | Supporting dependency documentation | Not a verified full analysis repository |

Review-derived method notes:

- Associated method: Complex Principal Components (CPC), CPC1, and traveling
  wave propagation.
- Associated comparison domain: LSD, deep sleep, and anesthesia.
- `neuromaps` should be treated as a map/spatial-null support package unless a
  dedicated analysis repository is found.

## Data Requirements

- Preprocessed fMRI time series or surfaces.
- CPC implementation details.
- Spatial axis definition and task-positive/task-negative mapping.
- Cross-state comparison inputs if reproducing external comparisons.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py traveling_waves
```

## Reproduction Path

1. Search for a dedicated traveling-wave analysis repository before
   reimplementation.
2. If unavailable, document an independent CPC implementation with explicit
   phase, filtering, and surface/parcel assumptions.
3. Use `neuromaps` only for map alignment or spatial-null support.
4. Keep traveling-wave outputs as future/partial until code and preprocessing
   are verified.

## Expected Outputs

- CPC components and phase maps.
- Propagation-axis summaries.
- Condition or state contrast statistics.

## Connection to the Surrogate Model

Maps to Layer D and possible hierarchy-axis dynamics. Without verified CPC code,
traveling-wave results should remain partial/future context rather than current
thesis evidence.

## Blockers and Open Questions

- No dedicated public analysis repo is verified here.
- CPC parameters and preprocessing are under-specified from the prompt alone.
