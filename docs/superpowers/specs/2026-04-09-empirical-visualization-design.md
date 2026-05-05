# Empirical Visualization Design

## Problem Frame

The repository already extracts real `ds003059` resting-state runs into 8-module time series, but the current outputs do not make the empirical pipeline easy to read for non-specialists. The missing capability is a visual bridge from raw fMRI signal to module-level summaries and then to placebo-versus-LSD comparisons.

## Goal

Add an empirical visualization layer that lets a user inspect:

- group-average placebo versus LSD summaries
- paired subject runs with a subject picker
- windowed views that line up raw signal previews, module traces, FC matrices, and metric changes
- a precomputed gallery of saved figures for quick review

## Constraints

- Keep claims at the macro-dynamics level.
- Do not pretend the 8-module anatomical proxy is a canonical network definition.
- Avoid live full-resolution NIfTI rendering in the browser.
- Prefer precomputed, dashboard-friendly assets that remain explainable and fast.

## Recommended Approach

Use a two-layer empirical viewer:

1. Precompute dashboard-friendly empirical assets during Stage 2.
   - Per-run raw fMRI previews as downsampled axial/coronal/sagittal slice panels.
   - Per-run normalized-window summaries with FC matrices, module traces, and metric snapshots.
   - Group-average summaries pooled across subjects and sessions.

2. Expose those assets in the existing FastAPI dashboard.
   - Default to a group overview.
   - Add a subject picker for paired `ses-PLCB` versus `ses-LSD` viewing.
   - Add a window slider so the same time segment can be inspected across raw previews, module traces, and FC.
   - Add a report/gallery section with saved Stage 2 empirical figures.

## Why This Path

- It shows the chain from raw scan to model-facing summaries.
- It is interactive without requiring a heavy neuroimaging viewer.
- It keeps the dashboard understandable for non-experts.
- It reuses the existing Stage 2 cache instead of building a second empirical pipeline.

## Output Shape

### Dashboard

- Model explorer: existing simulator controls and surrogate plots.
- Empirical explorer:
  - group overview
  - subject picker
  - run picker
  - normalized window slider
  - raw preview panel
  - module trace panel
  - FC comparison panel
  - plain-English metric interpretation panel
- Gallery/report section with saved empirical HTML figures.

### Stage 2 artifacts

- `results/stage_2/empirical_viewer/group_overview.json`
- `results/stage_2/empirical_viewer/subject_index.json`
- `results/stage_2/empirical_viewer/subject_views/*.json`
- `results/stage_2/figures/empirical_*`

## Risks

- Raw preview generation can become slow if recomputed too often.
- JSON payload size can balloon if slice panels are too large or too numerous.
- Window alignment across runs is approximate because runs are normalized into a shared window count rather than synchronized in biological time.

## Guardrails

- Label raw previews as downsampled window summaries, not direct diagnostic images.
- Label window metrics as descriptive empirical summaries, not inferential statistics.
- Keep interpretation text explicit about proxy status and coarse anatomical mapping.
