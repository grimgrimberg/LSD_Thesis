# Neuroreceptor Eigenmodes

## Scope

Document receptor-map and core-matrix resources that could support
neuroreceptor/eigenmode analyses as future or proxy-level extensions.

## Verified Code Sources

| Source | Local path | Commit | Status |
|---|---|---:|---|
| `netneurolab/hansen_receptors` | `prior_art/repositories/hansen_receptors/` | `f8b41da92a73` | Public, cloned |
| `macshine/corematrix` | `prior_art/repositories/shine_corematrix/` | `6f0997526430` | Public, cloned |

Verified repository facts:

- `hansen_receptors` provides PET NIfTI images, parcellated receptor CSV files,
  and Python analysis scripts such as `parcellate.py`,
  `make_receptor_matrix.py`, `rsimilarity.py`, `connectivity.py`, and
  `dynamics.py`.
- The Hansen README states CC BY-NC-SA 4.0 licensing and asks users to cite the
  source PET papers.
- `corematrix` contains thalamic CALB/PVALB difference maps and a short README.

## Data Requirements

- Receptor maps aligned to the selected cortical surface or parcellation.
- Functional connectivity or BOLD summaries from ds003059 if reconstructing
  activity with receptor/eigenmode bases.
- Optional structural/geometric eigenmode basis, depending on the exact method.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py neuroreceptor_eigenmodes
```

## Reproduction Path

1. Use receptor resources as external priors only after checking license and
   citation terms.
2. Choose a parcellation shared by local ds003059 outputs and receptor maps.
3. Build a receptor matrix, then evaluate whether it predicts or reconstructs
   local macro-dynamic metrics.
4. Keep claims at receptor-prior/proxy level unless empirical receptor evidence
   is directly tested.

## Expected Outputs

- Region-by-receptor matrices.
- Receptor similarity or principal-component summaries.
- Optional eigenmode reconstruction or correlation statistics.

## Connection to the Surrogate Model

Maps to Layer C (hierarchy/routing) and receptor-prior sensitivity. These
resources can define alternative anatomical or receptor priors for model
comparison, while remaining external priors rather than empirical proof.

## Blockers and Open Questions

- Noncommercial ShareAlike licensing may constrain redistribution.
- Corematrix has no root license file in the checked commit.
- Eigenmode methods require an explicit geometric basis that is not defined by
  these repositories alone.
