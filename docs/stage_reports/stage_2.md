# Stage 2 Report

## Plan

- Load actual ds003059 resting-state targets when a dataset directory is provided; otherwise fall back to the placeholder config.
- Fit the sober baseline regime with a transparent random search around the baseline config.
- Save the canonical full empirical cohort provenance and keep the MVP subset helper as a separate convenience bootstrap artifact.

## What Is Fitted Exactly

- Within-network stability
- Cross-network communication
- Thalamic coupling
- Hierarchical compression
- Entropy / diversity
- Switching rate
- Dynamic FC change / metastability proxy
- Effective barrier proxy
- The sober FC target matrix

## What Is Only Qualitatively Anchored

- The atlas-to-module mapping, which is a transparent coarse anatomical proxy rather than a canonical network parcellation.
- The interpretation of these summary metrics as macro-level signatures rather than direct mechanistic readouts.
- The sign agreement between the current 8-module ds003059 extraction and the literature-style target file.

## Empirical Sign Check

- The current paired ds003059 extraction supports increased cross-network communication and thalamic coupling under this proxy.
- It conflicts with the literature-style target signs for `within_network_stability`, `entropy_diversity`, and `metastability_proxy`.
- Stage 3 and Stage 4 should therefore be presented as mismatch analysis under one coarse anatomical proxy.

## Atlas Mapping Audit

- Atlas audit artifact: `atlas_mapping_audit.json`
- Assigned atlas voxels: `108814`
- Overlapping source labels: `2`

## Empirical Data Quality

- Data quality artifact: `empirical_data_quality.json`
- Paired subjects: `15`
- Complete subjects: `15`
- Sign conflicts: `3`

## Empirical Viewer Outputs

- Group-average empirical overview cache
- Subject/run paired empirical detail cache
- Precomputed empirical gallery figures for traces, FC, and delta summaries

## Results

- Initial score: 5.2439
- Best score: 0.9774
- Best within-network stability: 0.2913
- Best cross-network communication: 0.1014
- Best entropy / diversity: 0.8194
- Best switching rate: 0.2412

## Critical Review

- The fitting loop is intentionally small and transparent, so it should be treated as calibration rather than optimization proof.
- If actual ds003059 targets were used, the remaining mismatch is now a model limitation rather than a placeholder-data limitation.
- The full empirical cohort provenance is the canonical reproducibility record for this run.
- The saved MVP subset helper is a convenience bootstrap artifact and is not the canonical fit provenance.
- The empirical viewer uses downsampled window previews for interpretability and speed; it is not a diagnostic-grade imaging viewer.
- The current Harvard-Oxford macro-module mapping contains overlapping source labels; the label-image builder resolves those overlaps by assignment order.

## Provenance

- The canonical Stage 2 provenance comes from the full empirical cohort used to derive the fitted targets.
- The MVP subset helper is stored separately as a convenience bootstrap artifact for lightweight ds003059 setup.
