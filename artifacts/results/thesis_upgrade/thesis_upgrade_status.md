# Thesis Upgrade Status

This status file upgrades evidence visibility and fails closed on missing science. It does not convert proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof.

## Gate Summary

| Gate | Status | Ready | Score | Blocker / next action |
| --- | --- | ---: | ---: | --- |
| Motion and confounds | implemented_image_derived_motion_qc_control | true | 0.82 | Raw-BOLD image-derived motion/QC sensitivity is implemented; fMRIPrep FD/DVARS/censoring remains the preferred future gold-standard control. |
| Canonical parcellation | implemented_mechanism_ranking | false | 0.45 | Canonical Schaefer/Yeo extraction is not yet a completed empirical result with dashboard-visible outputs. |
| Neuromaps spatial nulls | blocked_missing_neuromaps_surface_input_manifest | false | 0.55 | Full surface/parcellation spatial-autocorrelation null testing has not been run. |
| ROCKET benchmark | supporting_internal_signal | true | 1.00 | Add permutation-null, calibration, and MiniRocket/MultiRocket gates before treating this as strong ML evidence. |
| External validation | implemented_ds006072_unchanged_scoring_validation | true | 1.00 | Need ds006072 drug-order mapping and processed-rest CIFTI manifest before comparable extraction planning. |
| Receptor + structural control | proxy_or_blocked | false | 0.30 | Need both a documented structural-connectome graph and PET-derived receptor prior with null controls. |
| Receptor/myelin/gradient claim | not_supported_yet | false | 0.45 | Current receptor/myelin/gradient alignments are exploratory priors; q-values do not pass FDR and CIs overlap zero. |
| Reproducible archive | manifest_ready | true | 0.75 | Generate the archive manifest, then publish a GitHub release and Zenodo DOI. |

## Strict Completion Audit

| Requirement | Status | Complete | Missing | Next action |
| --- | --- | ---: | --- | --- |
| Schaefer/Yeo high-resolution parcellation layer | implemented_mechanism_ranking | false | The high-resolution layer is not fully dashboard-visible until extraction, viewer, and ranking outputs all exist. | Run the ds003059 extraction/ranking contract for Schaefer 100/Yeo 7, then repeat sensitivity for Schaefer 200 and Yeo 17. |
| Full neuromaps spatial-autocorrelation nulls | blocked_missing_neuromaps_surface_input_manifest | false | neuromaps is installed and its null API imports, but the surface/high-resolution map input manifest and executed null results are missing. | Create results/cortical_maps/neuromaps_surface_inputs.json, project receptor/myelin/gradient maps to Schaefer/Yeo or surface space, run neuromaps nulls, and FDR-correct the family. |
| ds006072 psilocybin external validation | implemented_ds006072_unchanged_scoring_validation | true | None: ds006072 paired psilocybin/MTP CIFTI records were extracted and scored unchanged; current scope is a structure-family external stress test. | Upgrade this from structure-family stress test to stronger replication by adding a surface/parcellation-matched ds006072 extractor. |
| Motion/confound control result | implemented_image_derived_motion_qc_control | true | None for the current dedicated result layer: raw-BOLD image-derived motion/QC sensitivity is implemented. fMRIPrep FD/DVARS/censoring remains the stronger future gold-standard control. | Use the image-derived QC result as the current motion/signal-quality control layer, and upgrade to authorized fMRIPrep FD/DVARS/censoring when available. |
| Receptor/myelin/gradient claim resolution | not_supported_yet | false | The strongest current map alignment remains exploratory: no FDR pass and CI overlap with zero. | Promote the claim only after high-resolution parcellation, neuromaps spatial nulls, FDR pass, and uncertainty intervals that do not cross zero. |
| Project phase | pi_pitch_ready_research_proposal_not_completed_thesis | false | One or more required scientific gates is still missing or fail-closed. | Keep pitching this as an AI/engineering research proposal until every strict evidence gate passes. |

## Canonical Next State

- Primary canonical parcellation target: `schaefer_100_yeo_7`.
- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.
- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.
- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.
- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.
