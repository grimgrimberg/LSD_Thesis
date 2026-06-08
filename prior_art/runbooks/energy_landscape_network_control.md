# Energy Landscape / Network Control

## Scope

Document the Singleton et al. receptor-informed network-control energy
landscape workflow and map it to this thesis only as a proxy-level comparison.

## Verified Code Source

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `singlesp/energy_landscape` | `prior_art/repositories/singleton_energy_landscape/` | `47cd3d2347e7` | Public, cloned |

Verified repository facts:

- The README identifies the analysis as code for "Psychedelics flatten the
  brain's energy landscape".
- It requires MATLAB R2017a or later and R packages including `ggplot2`,
  `R.matlab`, `RColorBrewer`, `lm.beta`, `reshape2`, `viridis`, and `plotrix`.
- The README says raw BOLD data are available at OpenNeuro ds003059 v1.0.0.
- `split` options include `main`, `gsr`, `music`, `psilo`, and `sch`.
- Key scripts include `repeatkmeans_sps.m`, `elbow_sps.m`, `ami_calc.m`,
  `transProbs.m`, `subcentroids.m`, `T_sweep_sps.m`, `subj_energy.m`,
  `spin_receptor_map.m`, `complexity_measures.m`, and `E_corrs.m`.

## Data Requirements

- Parcellated fMRI time series, likely Lausanne-463 or matching repository
  assumptions.
- Brain-state clustering outputs.
- Structural connectome matrix, with receptor-weighted control-energy inputs.
- Receptor map and spatial-null inputs for spin testing.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py energy_landscape_network_control
```

## Reproduction Path

1. Treat this as a reference implementation, not code to copy into production.
2. Verify the structural connectome source and parcellation alignment before
   running any energy calculation.
3. Run k-means stability and transition-probability steps before energy sweeps.
4. Keep receptor-specific control claims gated unless receptor and structural
   inputs are locally verified.

## Expected Outputs

- Brain-state centroids and transition probabilities.
- Subject-specific centroids.
- Energy-vs-transition correlations and chosen `T`.
- Receptor spin-test null summaries.
- LZ complexity of meta-state sequences where state hierarchy is defined.

## Connection to the Surrogate Model

Maps most directly to Layer E (control-energy proxy), with secondary links to
Layer A (state transitions) and Layer D (state repertoire). Receptor-informed
energy results should remain proxy-level design inspiration unless local
structural and receptor inputs pass their gates.

## Blockers and Open Questions

- The checked repo has no root license file.
- Structural connectome provenance must be verified.
- Some runtime estimates in the README are nontrivial; permutation tests can
  take many hours.
