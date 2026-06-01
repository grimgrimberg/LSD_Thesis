# Thesis Readiness Gates

This document defines what must be true before the project can be described as thesis-ready without overclaiming.

## Current Framing

The defensible thesis claim is:

> This repository implements a transparent macro-dynamics surrogate and evidence-gated mechanism-ranking workflow for public psychedelic neuroimaging data.

It is not a receptor model, subjective-experience model, clinical model, pharmacokinetic model, or proof of the biological mechanism of LSD.

## Gates

| Gate | Thesis-ready meaning | Current first-pass treatment |
| --- | --- | --- |
| Motion/confounds | Subject/session/run FD, DVARS, and censoring summaries exist and are used as sensitivity gates. | Explicit blocker if structured confounds are missing; `results/confound_controls/fmriprep_motion_proof_plan.json` records whether the current checkout can produce those inputs or needs original raw BIDS/author confounds. |
| Canonical parcellation | Schaefer/Yeo extraction reproduces or falsifies the current 8-module conclusions. | `schaefer_100_yeo_7` is the named primary canonical target; 8-module remains proxy baseline. |
| ROCKET strength | Subject-disjoint ROCKET/MiniRocket/MultiRocket beats permutation nulls with calibrated subject/run aggregation. | Current ROCKET remains supporting internal signal until null and calibration gates exist. |
| External validation | The same scoring rules run on an independent psychedelic dataset. | `ds006072` is the target; metadata/manifest alone is not validation. |
| Receptor/structural control | PET-derived receptor priors and structural-connectome graphs are projected to the active parcellation and tested against null controls. | E remains proxy-only until both layers exist. |
| Reproducible archive | A GitHub release and Zenodo DOI cite a checksum-backed derived-artifact snapshot. | Archive manifest and metadata are scaffolded; DOI requires release workflow. |
| Public dashboard | Static Pages exposes results and blockers without requiring local raw data. | Presentation layer only; not the citable archive. |

## External Ingestion Contracts

The second-pass ingestion contract writes validated local inputs into the file paths already consumed by the evidence loop:

- Structural-connectome graph: `data/hcp_structural_connectome/macro_modules.csv`
- PET receptor prior: `data/receptor_priors/fs5ht_5ht2a_macro_modules.csv`
- Ingestion readiness: `results/external_ingestion/external_ingestion_status.json`

Commands:

```powershell
uv run python scripts/build_external_ingestion_status.py
uv run python scripts/ingest_external_priors.py --structural-csv <path-to-structural-csv>
uv run python scripts/ingest_external_priors.py --receptor-csv <path-to-receptor-csv>
uv run python scripts/run_thesis_evidence_loop.py
```

The ingestion scripts validate schemas and provenance paths. They do not invent PET receptor maps or normative structural matrices.

## Motion-Proof Contract

The strict motion gate passes only after structured subject/session/run confounds are available and joined to dynamic deltas. The required local input shape is:

- `data/ds003059/derivatives/fmriprep/sub-*/ses-*/func/*desc-confounds_timeseries.tsv`
- `framewise_displacement`
- `std_dvars` or `dvars`
- motion outlier, censor, scrub, or non-steady-state columns where available
- subject, session/condition, and run metadata in the path or an equivalent joinable subject/session/run record
- at least four paired LSD and placebo/PLCB subject/run rows before the fMRIPrep preflight can treat parsed confounds as strict-gate-ready inputs

Run:

```powershell
uv run python scripts/build_fmriprep_motion_proof_plan.py --fetch-remote
uv run python scripts/run_setting_seed_motion_summary.py
uv run python scripts/build_motion_confound_controls.py
uv run python scripts/build_thesis_upgrade_status.py --fetch-motion-remote
```

If authorized fMRIPrep or author-provided confounds are supplied outside the repository, thread the same root through the gate refresh so the preflight, motion summary, confound-control result, and thesis status agree:

```powershell
uv run python scripts/build_thesis_upgrade_status.py --fetch-motion-remote --motion-root <path-to-authorized-fmriprep-or-confounds-root>
```

The preflight artifact is not motion proof. It may report that the current ds003059 snapshot is a derivative release with no subject-level confound tables; in that case, the strict gate requires author-provided confounds or original raw BIDS inputs processed through fMRIPrep/MRIQC.

Files with FD/DVARS columns but no subject/session/run metadata remain unusable for the strict gate because they cannot be joined to the empirical dynamic deltas.

## Canonical Parcellation Decision

Primary canonical target: `schaefer_100_yeo_7`.

Rationale:
- Schaefer parcels are functional-connectivity-derived and multiresolution.
- Yeo labels preserve interpretable network-level summaries.
- The state dimension is large enough to improve over the 8-module proxy while remaining tractable for control-theory and ML diagnostics.

Sensitivity targets:
- `schaefer_200_yeo_7`
- `schaefer_100_yeo_17`
- `schaefer_200_yeo_17`

## ROCKET Strength Criteria

ROCKET becomes strong supporting ML evidence only if all conditions hold:

- Approved subject-disjoint folds.
- Primary metrics aggregate windows to `subject/session/run`.
- No window-random reporting.
- Label-permutation null distribution is generated inside the same split contract.
- Calibration metrics are reported.
- MiniRocket or MultiRocket-style transforms are compared.
- The same scoring rule is tested on external psilocybin data when available.

## Archive Criteria

The thesis archive should include code, configs, reports, derived aggregate artifacts, and checksums. It should cite OpenNeuro source datasets instead of republishing raw imaging data.
