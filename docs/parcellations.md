# Parcellations

## Supported IDs

- `harvard_oxford_8`: legacy eight-module Harvard-Oxford anatomical proxy.
- `schaefer_100_yeo_7`: primary Schaefer 2018 100-parcel cortical target space labeled by Yeo 7 networks.
- `schaefer_200_yeo_7`: Schaefer 200/Yeo 7 sensitivity target.
- `schaefer_100_yeo_17`: Schaefer 100/Yeo 17 sensitivity target.
- `schaefer_200_yeo_17`: Schaefer 200/Yeo 17 sensitivity target.

## Output Layout

Parcellation-specific outputs live under:

```text
results/stage_2/parcellations/<parcellation_id>/
```

Current parcellation artifacts:

- `node_metadata.json`
- `atlas_metadata.json`
- `dry_run_plan.json`
- `parcellation_extraction_summary.json`
- `empirical_viewer/group_overview.json`

Mechanism-ranking sensitivity summaries live under:

```text
results/parcellation_sensitivity/<parcellation_id>/summary.json
```

The root Stage 2 files remain the legacy `harvard_oxford_8` empirical baseline and are not overwritten by parcellation-specific outputs.

## Schaefer/Yeo Status

The current primary Schaefer/Yeo layer is implemented for local `ds003059` LSD/placebo evidence. The strict thesis-upgrade gate treats `schaefer_100_yeo_7` as complete when these artifacts exist:

- `results/stage_2/parcellations/schaefer_100_yeo_7/parcellation_extraction_summary.json`
- `results/stage_2/parcellations/schaefer_100_yeo_7/empirical_viewer/group_overview.json`
- `results/parcellation_sensitivity/schaefer_100_yeo_7/summary.json`

Current checked evidence records `15` subjects, `60` records, `100` parcels, top layer `C`, and a Schaefer 2018 atlas loaded from the local nilearn cache. `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, and `schaefer_200_yeo_17` are implemented sensitivity rows in `results/parcellation_sensitivity/parcellation_sensitivity_status.json`.

The current Schaefer metadata uses neutral placeholder receptor weights. They are included only to satisfy downstream schema needs and should not be interpreted as receptor maps.

## Remaining Work

1. Keep `schaefer_100_yeo_7` as the primary high-resolution inference layer unless a newer status artifact says otherwise.
2. Use the Schaefer 200 and Yeo 17 rows as sensitivity checks rather than silently promoting a new primary layer.
3. Add Harvard-Oxford subcortical thalamus, caudate, and putamen nodes only if atlas availability and masking are stable.
4. Do not treat neutral receptor-weight placeholders as PET receptor evidence; use the receptor-prior artifacts and spatial-null outputs for that claim family.
5. Keep parcellation-specific outputs under `results/stage_2/parcellations/<parcellation_id>/` and ranking summaries under `results/parcellation_sensitivity/`.

## Guardrails

- Keep `harvard_oxford_8` as the legacy baseline.
- Do not overwrite `results/stage_2/empirical_*` root targets during Schaefer work.
- Label neutral metadata clearly.
- Do not claim Schaefer/Yeo results are current unless the extraction summary, empirical viewer, and parcellation-sensitivity summary all exist.
