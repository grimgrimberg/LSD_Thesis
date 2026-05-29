# Thesis Upgrade Status

This status file upgrades evidence visibility and fails closed on missing science. It does not convert proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof.

## Gate Summary

| Gate | Status | Ready | Score | Blocker / next action |
| --- | --- | ---: | ---: | --- |
| Motion and confounds | implemented_design_confound_controls_missing_fd_dvars_motion | false | 0.35 | Run/session/global-signal design controls are implemented, but no FD/DVARS/censoring motion summaries are available. |
| Canonical parcellation | implemented_mechanism_ranking | true | 1.00 | Canonical Schaefer/Yeo extraction, empirical viewer, and mechanism ranking are available. |
| Neuromaps spatial nulls | implemented_schaefer100_full_map_family_moran_spatial_nulls | true | 1.00 | Schaefer100 map-family Moran spatial nulls are complete across receptor, myelin, functional-gradient, and gene-expression priors. |
| ROCKET benchmark | supporting_internal_signal | true | 1.00 | Add permutation-null, calibration, and MiniRocket/MultiRocket gates before treating this as strong ML evidence. |
| External validation | blocked_missing_local_ds006072_empirical_viewer | false | 0.45 | No paired ds006072 empirical-viewer subject views exist. Provide harmonized records under results/psilocybin_ds006072/empirical_viewer/subject_views with ses-PLCB control and ses-LSD psilocybin aliases. |
| Receptor + structural control | fully_integrated | true | 1.00 | Need both a documented structural-connectome graph and PET-derived receptor prior with null controls. |
| Receptor/myelin/gradient claim | not_supported_yet | false | 0.45 | Current receptor/myelin/gradient alignments are exploratory priors; q-values do not pass FDR and CIs overlap zero. |
| Reproducible archive | manifest_ready | true | 0.75 | Generate the archive manifest, then publish a GitHub release and Zenodo DOI. |

## Strict Completion Audit

| Requirement | Status | Complete | Missing | Next action |
| --- | --- | ---: | --- | --- |
| Schaefer/Yeo high-resolution parcellation layer | implemented_mechanism_ranking | true | None: Schaefer 100/Yeo 7 extraction, empirical viewer, and ranking summary are present. | Use this as the primary high-resolution inference layer and keep Schaefer 200/Yeo 7 plus Yeo 17 variants as sensitivity checks. |
| Full neuromaps spatial-autocorrelation nulls | implemented_schaefer100_full_map_family_moran_spatial_nulls | true | None: full neuromaps spatial-autocorrelation null family coverage is complete. | Use the completed spatial-null family as the primary map-prior evidence layer. |
| ds006072 psilocybin external validation | blocked_missing_local_ds006072_empirical_viewer | false | The repo has readiness/provenance, but not comparable psilocybin/control dynamic extraction scored unchanged. | Supply or derive authorized ds006072 processed rest payloads, build paired empirical viewer records, then apply the locked LSD scoring spec without retuning and with matching scoring hashes. |
| Motion/confound control result | implemented_design_confound_controls_missing_fd_dvars_motion | false | Run/session design controls exist, but a dedicated FD/DVARS/censoring motion-control result is still missing. | Parse confounds for every subject/session/run, then report whether dynamic effects survive FD, DVARS, censoring, and run/order controls. |
| Receptor/myelin/gradient claim support | not_supported_yet | false | The strongest current map alignment remains exploratory: no FDR pass and CI overlap with zero. | Promote the claim only after high-resolution parcellation, neuromaps spatial nulls, FDR pass, and uncertainty intervals that do not cross zero. |
| Project phase | pi_pitch_ready_research_proposal_not_completed_thesis | false | One or more required scientific gates is still missing or fail-closed. | Keep pitching this as an AI/engineering research proposal until every strict evidence gate passes. |

## Canonical Next State

- Primary canonical parcellation target: `schaefer_100_yeo_7`.
- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.
- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.
- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.
- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.
