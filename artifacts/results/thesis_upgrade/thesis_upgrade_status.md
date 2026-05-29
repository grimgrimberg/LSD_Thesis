# Thesis Upgrade Status

This status file upgrades evidence visibility and fails closed on missing science. It does not convert proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof.

## Gate Summary

| Gate | Status | Ready | Score | Blocker / next action |
| --- | --- | ---: | ---: | --- |
| Motion and confounds | implemented_published_fd_context_and_proxy_controls_missing_subject_level_fd | false | 0.65 | Published ds003059 FD/scrubbing QC context plus local run/design and module-DVARS proxy controls are implemented, but subject-level FD/DVARS confounds are unavailable. |
| Canonical parcellation | implemented_mechanism_ranking | true | 1.00 | Canonical Schaefer/Yeo extraction, empirical viewer, and mechanism ranking are available. |
| Neuromaps spatial nulls | implemented_schaefer100_full_map_family_moran_spatial_nulls | true | 1.00 | Schaefer100 map-family Moran spatial nulls are complete across receptor, myelin, functional-gradient, and gene-expression priors. |
| ROCKET benchmark | supporting_internal_signal | true | 1.00 | Add permutation-null, calibration, and MiniRocket/MultiRocket gates before treating this as strong ML evidence. |
| External validation | implemented_ds006072_unchanged_scoring_validation | true | 1.00 | Run the ds006072 module time-series extraction and empirical-viewer writer, then rerun the thesis evidence loop. |
| Receptor + structural control | fully_integrated | true | 1.00 | Need both a documented structural-connectome graph and PET-derived receptor prior with null controls. |
| Receptor/myelin/gradient claim | not_supported_yet | false | 0.45 | Map-prior negative result is formalized; the mechanism claim remains not_supported_yet. |
| Reproducible archive | manifest_ready | true | 0.75 | Generate the archive manifest, then publish a GitHub release and Zenodo DOI. |

## Strict Completion Audit

| Requirement | Status | Complete | Missing | Next action |
| --- | --- | ---: | --- | --- |
| Schaefer/Yeo high-resolution parcellation layer | implemented_mechanism_ranking | true | None: Schaefer 100/Yeo 7 extraction, empirical viewer, and ranking summary are present. | Use this as the primary high-resolution inference layer and keep Schaefer 200/Yeo 7 plus Yeo 17 variants as sensitivity checks. |
| Full neuromaps spatial-autocorrelation nulls | implemented_schaefer100_full_map_family_moran_spatial_nulls | true | None: full neuromaps spatial-autocorrelation null family coverage is complete. | Use the completed spatial-null family as the primary map-prior evidence layer. |
| ds006072 psilocybin external validation | implemented_ds006072_unchanged_scoring_validation | true | None: ds006072 paired psilocybin/MTP CIFTI records were extracted and scored unchanged; current scope is a structure-family external stress test. | Upgrade this from structure-family stress test to stronger replication by adding a surface/parcellation-matched ds006072 extractor. |
| Motion/confound control result | implemented_published_fd_context_and_proxy_controls_missing_subject_level_fd | false | A source-availability check found no local/OpenNeuro raw/public derivative subject-level FD/DVARS/censoring confounds; full motion proof requires authorized fMRIPrep outputs or a local preprocessing run. | Supply authorized fMRIPrep outputs or run preprocessing to create desc-confounds_timeseries.tsv files, then report whether dynamic effects survive FD, DVARS, censoring, and run/order controls. |
| Receptor/myelin/gradient claim support | not_supported_yet | false | The map-prior negative result is formalized: no module-level or spatial-null family FDR support, and the best spatial-null CI crosses zero. | Promote the claim only after high-resolution parcellation, neuromaps spatial nulls, FDR pass, and uncertainty intervals that do not cross zero. |
| Project phase | pi_pitch_ready_research_proposal_not_completed_thesis | false | One or more required scientific gates is still missing or fail-closed. | Keep pitching this as an AI/engineering research proposal until every strict evidence gate passes. |

## Canonical Next State

- Primary canonical parcellation target: `schaefer_100_yeo_7`.
- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.
- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.
- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.
- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.
