# Thesis Upgrade Status

This status file upgrades evidence visibility and fails closed on missing science. It does not convert proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof.

## Gate Summary

- Strict completion: 4/6 gates complete.
- Package readiness: 1/2 gates complete.
- Missing strict requirement IDs: motion_confound_control_result, project_phase.
- Missing package requirement IDs: reproducible_archive_publication.
- Remaining hard requirements: fMRIPrep FD/DVARS/censoring motion proof.
- Remaining packaging requirements: Reproducible archive publication.

| Gate | Status | Ready | Score | Blocker / next action |
| --- | --- | ---: | ---: | --- |
| Motion and confounds | implemented_image_derived_motion_qc_control | false | 0.82 | Raw-BOLD image-derived motion/QC sensitivity is implemented; fMRIPrep FD/DVARS/censoring remains the preferred future gold-standard control. |
| Canonical parcellation | implemented_mechanism_ranking | true | 1.00 | Canonical Schaefer/Yeo extraction, empirical viewer, and mechanism ranking are available. |
| Neuromaps spatial nulls | implemented_schaefer100_full_map_family_moran_spatial_nulls | true | 1.00 | Schaefer100 map-family Moran spatial nulls are complete across receptor, myelin, functional-gradient, and gene-expression priors. |
| ROCKET benchmark | supporting_internal_signal | false | 0.85 | Add permutation-null, calibration, and MiniRocket/MultiRocket gates before treating this as strong ML evidence. |
| Public dashboard | static_snapshot_ready | true | 1.00 | Static GitHub Pages dashboard snapshot and key gate/archive artifacts are present and synchronized with the current readiness artifact. This is presentation evidence, not a citable archive. |
| External validation | implemented_ds006072_unchanged_scoring_validation | true | 1.00 | Schaefer100/Yeo7 ds006072 extraction and unchanged scoring are complete; ranking_differs_from_lsd_top_layer; ds006072 top=E, LSD reference top=C. |
| Receptor + structural control | fully_integrated | true | 1.00 | Documented structural-connectome graph sensitivity and PET-derived receptor-prior sensitivity are implemented with null/control context; keep biological mechanism promotion governed by the separate receptor/myelin/gradient claim gate. |
| Receptor/myelin/gradient claim | resolved_negative_not_promoted | true | 1.00 | The map-prior claim is resolved as a negative control: do not promote receptor/myelin/gradient mechanism claims from this dataset. |
| Reproducible archive | manifest_ready_release_doi_missing | false | 0.55 | Checksum manifest exists, but thesis-readiness still requires a citable GitHub release and Zenodo DOI. |

## Package Readiness Audit

| Requirement | Status | Complete | Missing | Next action |
| --- | --- | ---: | --- | --- |
| Public dashboard static snapshot | static_snapshot_ready | true | None: static Pages snapshot contains the required dashboard and evidence artifacts. | Keep rebuilding the static site after gate/status artifact changes. |
| Reproducible archive publication | manifest_ready_release_doi_missing | false | Citable archive publication is missing a validated GitHub release URL and Zenodo DOI. | Create a GitHub release, mint a Zenodo DOI for that release, then rebuild scripts/build_reproducible_archive.py with --release-url and --doi. |

## Strict Completion Audit

| Requirement | Status | Complete | Missing | Next action |
| --- | --- | ---: | --- | --- |
| Schaefer/Yeo high-resolution parcellation layer | implemented_mechanism_ranking | true | None: Schaefer 100/Yeo 7 extraction, empirical viewer, and ranking summary are present. | Use this as the primary high-resolution inference layer and keep Schaefer 200/Yeo 7 plus Yeo 17 variants as sensitivity checks. |
| Full neuromaps spatial-autocorrelation nulls | implemented_schaefer100_full_map_family_moran_spatial_nulls | true | None: full neuromaps spatial-autocorrelation null family coverage is complete. | Use the completed spatial-null family as the primary map-prior evidence layer. |
| ds006072 psilocybin external validation | implemented_ds006072_unchanged_scoring_validation | true | None: ds006072 paired psilocybin/MTP CIFTI records were extracted through Schaefer100/Yeo7 cortex parcels and scored unchanged. | Use this as the stronger parcellation-matched ds006072 evidence layer; keep the small-subject scope visible. |
| Motion/confound control result | blocked_missing_fmriprep_fd_dvars_censoring_motion_proof | false | Raw-BOLD image-derived motion/QC sensitivity is implemented, but strict completion still requires fMRIPrep FD/DVARS/censoring motion proof. fMRIPrep preflight status: blocked_derivative_snapshot_not_valid_raw_fmriprep_input. | Obtain author-provided subject/run motion confounds or the original raw BIDS inputs that preceded this derivative release; then run fMRIPrep/MRIQC in a container or HPC environment and ingest desc-confounds_timeseries.tsv files. |
| Receptor/myelin/gradient claim resolution | resolved_negative_not_promoted | true | None: the claim is resolved as a negative/control result and is not promoted as a mechanism claim. | Use the negative map-prior result as a guardrail: keep receptor/myelin/gradient as future hypotheses, not current claims. |
| Project phase | research_demo_ready_not_completed_thesis | false | Proxy/stress-test evidence gates are visible, but completion still requires fMRIPrep FD/DVARS/censoring motion proof. | Keep this as a controlled research demo while upgrading fMRIPrep FD/DVARS/censoring motion proof. |

## Canonical Next State

- Primary canonical parcellation target: `schaefer_100_yeo_7`.
- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.
- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.
- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.
- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.
