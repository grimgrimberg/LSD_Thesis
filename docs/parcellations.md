# Parcellations

## Supported IDs

- `harvard_oxford_8`: legacy eight-module Harvard-Oxford anatomical proxy.
- `schaefer_100_yeo_7`: prepared Schaefer 2018 100-parcel cortical target space labeled by Yeo 7 networks.

## Output Layout

Parcellation-specific outputs live under:

```text
results/stage_2/parcellations/<parcellation_id>/
```

Current metadata artifacts:

- `node_metadata.json`
- `atlas_metadata.json`
- `dry_run_plan.json`

The root Stage 2 files remain the legacy `harvard_oxford_8` empirical baseline and are not overwritten by parcellation dry runs.

## Schaefer/Yeo Status

The `schaefer_100_yeo_7` path currently provides tested metadata and a dry-run plan. Full fMRI extraction is not run automatically because it can be slow and may require local atlas/data availability.

The current Schaefer metadata uses neutral placeholder receptor weights. They are included only to satisfy downstream schema needs and should not be interpreted as receptor maps.

## Full Extraction TODO

1. Confirm ds003059 data are available under `data/ds003059`.
2. Ensure Schaefer 2018 atlas availability:

```powershell
uv run python -c "from nilearn import datasets; datasets.fetch_atlas_schaefer_2018(n_rois=100, yeo_networks=7, resolution_mm=2)"
```

3. Extend `src/lsd_thesis/data/parcellations.py` with a real `NiftiLabelsMasker` extraction path.
4. Add Harvard-Oxford subcortical thalamus, caudate, and putamen nodes if atlas availability and masking are stable.
5. Write parcellation-specific `empirical_run_summaries.json`, target YAML files, and validation summaries under the parcellation directory.

## Guardrails

- Keep `harvard_oxford_8` as the legacy baseline.
- Do not overwrite `results/stage_2/empirical_*` root targets during Schaefer work.
- Label neutral metadata clearly.
- Do not claim Schaefer/Yeo results exist until extraction and target validation artifacts exist.

