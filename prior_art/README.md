# Prior-Art Landscape - OpenNeuro ds003059

This directory is a reproducible code-retrieval and implementation workspace
for prior analyses that reuse, depend on, or methodologically relate to
[OpenNeuro ds003059](https://openneuro.org/datasets/ds003059/versions/1.0.0).
The work here supports thesis-safe prior-art mapping; it does not convert
external papers into local biological proof.

## Dataset

| Field | Value |
|---|---|
| OpenNeuro accession | `ds003059` |
| Version used in this workspace | `1.0.0` |
| DOI | `10.18112/openneuro.ds003059.v1.0.0` |
| Dataset URL | https://openneuro.org/datasets/ds003059/versions/1.0.0 |
| Local default path | `data/ds003059/` |

The dataset is associated with multimodal neuroimaging of LSD and placebo
sessions and is commonly reused for psychedelic neuroimaging methods work.
Obtaining the dataset may require substantial storage and BIDS-compatible tools.
Do not download or regenerate large derivatives by default.

Suggested manual dataset retrieval options:

```powershell
# Option A: OpenNeuro CLI, if installed
openneuro download --dataset ds003059 --snapshot 1.0.0 data/ds003059

# Option B: datalad, if installed
datalad install https://github.com/OpenNeuroDatasets/ds003059.git data/ds003059
```

## Contents

| Path | Purpose |
|---|---|
| `code_inventory.md` | Master table of studies, code, dependencies, inputs, outputs, and reproducibility status |
| `reproducibility_matrix.md` | Ranked blockers and feasibility notes |
| `comparison_extraction_plan.json` | Dashboard-ready test, comparison, and extraction plan for each family |
| `repository_sources.json` | Source-of-truth clone list for public GitHub repositories |
| `repository_manifest.md` | Checked commits, branches, README/license presence, and non-clone sources |
| `repository_metadata.md` | Per-source language, license, install, README summary, and ds003059 support notes |
| `archive_manifest.md` | Non-GitHub archive metadata, including Zenodo 14029241 |
| `runbooks/` | One runbook per major analysis family |
| `scripts/` | Safe clone, verification, and dry-run input-check utilities |
| `repositories/` | External cloned or extracted code, gitignored and not modified |

## Verified Workspace State

- 11 public GitHub repositories were cloned into `prior_art/repositories/`.
- Commit hashes are recorded in `repository_manifest.md` and
  `repository_manifest.json`.
- Zenodo record `14029241` was inspected; only the 6,473 byte `Code.zip` archive
  was downloaded and extracted.
- Zenodo `Data.zip` is 435,268,809 bytes and was not downloaded.
- `igaadamska/LSD-music-brainstates` has no top-level README in the checked
  commit, so its status relies on notebook inspection.

## Analysis Families

| Family | Code status | ds003059 relation | Primary local doc |
|---|---|---|---|
| Ising thermodynamics and algorithmic complexity | Public GitHub | Direct derivatives required | `runbooks/ising_temperature_and_algorithmic_complexity.md` |
| Entropy / CopBET | Public GitHub | Direct examples and ROI extraction | `runbooks/entropy_copbet.md` |
| Energy landscape / network control | Public GitHub | Direct raw dataset reference | `runbooks/energy_landscape_network_control.md` |
| REACT receptor connectivity | Public GitHub | Method dependency | `runbooks/react_receptor_connectivity.md` |
| Neuroreceptor eigenmodes | Public GitHub | Receptor-map dependency | `runbooks/neuroreceptor_eigenmodes.md` |
| Dynamic integration / segregation | Public GitHub | Method dependency/direct related analysis | `runbooks/dynamic_integration_segregation.md` |
| Cortical gradients / BrainSpace | Public GitHub | Method dependency | `runbooks/cortical_gradients_brainspace.md` |
| LSD and music brain states | Public GitHub notebooks | Direct, but run-02 gated locally | `runbooks/lsd_music_brainstates.md` |
| GNW/IIT consciousness | Public Zenodo code archive | Direct plus cross-state processed inputs | `runbooks/gnw_iit_consciousness.md` |
| Mesoscale ReHo | No verified public code | Direct method from review | `runbooks/mesoscale_reho.md` |
| Traveling waves | Supporting dependency only | Partial, no dedicated repo verified | `runbooks/traveling_waves.md` |
| DLPFC Granger causality | Author-only | Direct method from review | `runbooks/dlpfc_granger_causality.md` |

## Commands

```powershell
# Preview clone targets without network changes
powershell -NoProfile -ExecutionPolicy Bypass -File prior_art/scripts/clone_all_repos.ps1 -DryRun

# Clone or inspect public GitHub repositories and regenerate manifests
powershell -NoProfile -ExecutionPolicy Bypass -File prior_art/scripts/clone_all_repos.ps1

# Verify local clone health
uv run python prior_art/scripts/verify_repos.py

# Dry-run required inputs for all analysis families
uv run python prior_art/scripts/dry_run_analysis_inputs.py all

# Fail only when required input roots are missing; output folders are reported as creatable targets
uv run python prior_art/scripts/dry_run_analysis_inputs.py all --strict
```

## Test, Compare, Extract Layer

`comparison_extraction_plan.json` is the source of truth for the dashboard's
prior-art execution plan. Each family records:

- the safe dry-run command to test local input availability
- the local thesis evidence layer it can be compared against
- the input or output data that should be extracted from the article/code
- the claim boundary that prevents prior-art wrappers from becoming original
  thesis evidence

The local dashboard and static GitHub Pages read this manifest through
`/api/prior-art-data` or `dashboard/prior-art-data.json`.

## Thesis Boundary

Prior-art code is used as design inspiration, reproducibility context, and
method comparison. Do not copy external code into production modules. Do not
claim receptor-level realism, subjective-experience modeling, music-control
effects, or cross-state validation unless local artifacts explicitly support
those claims.
