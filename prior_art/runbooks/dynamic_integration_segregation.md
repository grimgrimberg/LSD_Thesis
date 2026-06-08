# Dynamic Integration and Segregation

## Scope

Document dynamic integration/segregation code and its relation to this repo's
macro-dynamic proxy vocabulary.

## Verified Code Source

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `macshine/integration` | `prior_art/repositories/shine_integration/` | `d00534027ab8` | Public, cloned |

Verified repository facts:

- The README says the repository contains MATLAB code supporting "The Dynamics
  of Functional Brain Networks: Integrated Network States during Cognitive Task
  Performance".
- Top-level files include `integration_expt.m`, `guimera_model.m`,
  `apcluster.m`, `hungarian1.m`, `munkres.m`, and coefficient NIfTI files.
- No root license file is present in the checked commit.

## Data Requirements

- Time-varying functional connectivity or dynamic community assignments.
- MATLAB environment and compatible graph/network functions.
- Brain Connectivity Toolbox functions if reproducing cartographic profiles.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py dynamic_integration_segregation
```

## Reproduction Path

1. Treat the Shine repo as methodological reference code.
2. Define the local dynamic-FC windowing, edge threshold, and community choices.
3. Compute within-module and between-module integration measures on local
   ds003059-derived matrices.
4. Compare results against this thesis only as dynamic-repertoire proxies.

## Expected Outputs

- Participation/integration measures over time.
- State labels or integrated/segregated state summaries.
- Group-level LSD/placebo contrasts if local data are available.

## Connection to the Surrogate Model

Maps to Layer D (dynamic repertoire) and the integration/segregation proxy
metrics. It is useful for checking whether the surrogate's repertoire claims
align with established network-state summaries.

## Blockers and Open Questions

- The code is MATLAB-only and not ds003059-specific.
- Preprocessing and windowing choices strongly determine the interpretation.
