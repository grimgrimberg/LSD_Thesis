# Thesis Readiness Gates

This document defines what must be true before the project can be described as thesis-ready without overclaiming.

## Current Framing

The defensible thesis claim is:

> This repository implements a transparent macro-dynamics surrogate and evidence-gated mechanism-ranking workflow for public psychedelic neuroimaging data.

It is not a receptor model, subjective-experience model, clinical model, pharmacokinetic model, or proof of the biological mechanism of LSD.

## Current Strict Completion Snapshot

Current generated status as of 2026-06-01:

- Thesis readiness gates: `6/9`.
- Strict completion gates: `4/6`.
- Missing strict requirements: `motion_confound_control_result`, `project_phase`.
- Real remaining hard requirement: fMRIPrep FD/DVARS/censoring motion proof.
- Project phase: `research_demo_ready_not_completed_thesis`.

The missing `project_phase` item is derived from the motion-proof blocker. Do not treat raw-BOLD image QC, published aggregate FD context, design controls, module-DVARS proxies, archive manifests, or static dashboard publication as full thesis-readiness proof.

## Gates

| Gate | Thesis-ready meaning | Current generated status |
| --- | --- | --- |
| Motion/confounds | Subject/session/run FD, DVARS, and censoring summaries exist and are used as sensitivity gates. | Raw-BOLD image-derived motion/QC controls exist, but the strict gate remains incomplete until subject/run fMRIPrep FD, DVARS, and censoring proof is available. `results/confound_controls/fmriprep_motion_proof_plan.json` records whether the current checkout can produce those inputs or needs original raw BIDS/author confounds. |
| Canonical parcellation | Schaefer/Yeo extraction reproduces or falsifies the current 8-module conclusions. | `schaefer_100_yeo_7` is the primary canonical layer, with extraction, empirical viewer, and mechanism-ranking summary present; 8-module remains proxy baseline. |
| ROCKET strength | Subject-disjoint ROCKET/MiniRocket/MultiRocket beats permutation nulls with calibrated subject/run aggregation. | Current ROCKET is an internal subject-disjoint signal, but the generated gate is not ready until permutation-null, calibration, and MiniRocket/MultiRocket evidence exists. |
| External validation | The same scoring rules run on an independent psychedelic dataset. | Implemented as a small-subject ds006072 Schaefer100/Yeo7 unchanged-scoring external stress test. The ds006072 top layer differs from the LSD reference top layer, so this is a negative/partial cross-drug stress test rather than population replication. |
| Receptor/structural control | PET-derived receptor priors and structural-connectome graphs are projected to the active parcellation and tested against null controls. | Implemented HCP structural graph and PET receptor-prior sensitivity layers exist. The receptor/myelin/gradient mechanism claim remains resolved negative/not promoted because the map-prior tests do not support promotion. |
| Reproducible archive | A GitHub release and Zenodo DOI cite a checksum-backed derived-artifact snapshot. | Archive manifest and metadata are scaffolded, but this gate is not ready until a citable release URL and Zenodo DOI are recorded. |
| Public dashboard | Static Pages exposes results and blockers without requiring local raw data. | Static snapshot gate is ready when `_site` contains the index, dashboard payload, thesis status artifact, archive manifest artifact, and matching pages manifest entries; this remains presentation-only, not the citable archive. |

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

Author-provided long-form tables may use compact metadata values such as `001`, `LSD`, or `1`; the parser normalizes those to the dashboard join keys `sub-001`, `ses-LSD`, and `run-01`. Values that cannot be normalized or held constant per file remain unusable for strict joining.

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
uv run python scripts/check_ds003059_motion_sources.py --root <path-to-authorized-fmriprep-or-confounds-root>
uv run python scripts/build_github_pages.py --motion-root <path-to-authorized-fmriprep-or-confounds-root>
```

The preflight artifact is not motion proof. It may report that the current ds003059 snapshot is a derivative release with no subject-level confound tables; in that case, the strict gate requires author-provided confounds or original raw BIDS inputs processed through fMRIPrep/MRIQC.

Files with FD/DVARS columns but no subject/session/run metadata remain unusable for the strict gate because they cannot be joined to the empirical dynamic deltas.
The source-availability artifact reports both discovered motion-like files and parser readiness. A local TSV only counts as available confounds after it parses with joinable subject/session/run metadata; a found but unusable TSV remains below the source-availability threshold.
Reachable public derivative repository URLs are only candidate leads. They do not count as available subject/run confounds unless file-level FD/DVARS/censoring evidence is verified or authorized local files parse successfully.
OpenNeuro snapshot filename hits are also candidate leads. They do not count as available subject/run confounds until the actual files are verified for FD, DVARS, and censoring columns and parsed into joinable subject/session/run records.

The dedicated motion-control artifact must also fail closed unless its association table spans all three strict motion families: FD, DVARS, and censoring/outlier burden. Parsed fMRIPrep confounds expose FD spike burden and scrub/censor/outlier proportions as joinable motion features, but the gate is still incomplete if any required family is absent from the joined association rows.
The fMRIPrep preflight uses the same strict family contract: paired FD/DVARS files without any motion-outlier, censor, scrub, or non-steady-state columns are structured confounds, but they are not proof-ready inputs for this thesis gate.

## Archive Publication Contract

The archive manifest is a checksum ledger, not the citable archive by itself. The reproducible-archive gate passes only after `results/reproducible_archive/ARCHIVE_MANIFEST.json` records both:

- `release_url`: `https://github.com/<owner>/<repo>/releases/tag/<tag>`
- `doi`: `10.<prefix>/<suffix>` or `https://doi.org/10.<prefix>/<suffix>`

Run:

```powershell
uv run python scripts/build_reproducible_archive.py --release-url https://github.com/<owner>/<repo>/releases/tag/<tag> --doi 10.<prefix>/<suffix>
uv run python -c "from pathlib import Path; from lsd_thesis.thesis_upgrade import write_thesis_upgrade_status; write_thesis_upgrade_status(Path.cwd())"
```

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
