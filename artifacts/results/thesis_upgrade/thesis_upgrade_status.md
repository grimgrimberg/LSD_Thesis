# Thesis Upgrade Status

This status file upgrades evidence visibility. It does not convert proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof.

## Gate Summary

| Gate | Status | Ready | Score | Blocker / next action |
| --- | --- | ---: | ---: | --- |
| Motion and confounds | unavailable_not_found | false | 0.00 | No structured subject/session/run confounds with FD/DVARS/censoring coverage are available locally. |
| Canonical parcellation | implemented_mechanism_ranking | true | 1.00 | Canonical Schaefer/Yeo extraction and ranking are available. |
| ROCKET benchmark | supporting_internal_signal | true | 1.00 | Add permutation-null, calibration, and MiniRocket/MultiRocket gates before treating this as strong ML evidence. |
| External validation | extraction_contract_ready_missing_local_cifti_payloads | false | 0.60 | Drug-order mapping and unchanged scoring are locked, but local ds006072 CIFTI/module time-series payloads are absent. Download or provide authorized processed rest CIFTIs before claiming validation. |
| Receptor + structural control | fully_integrated | true | 1.00 | Need both a documented structural-connectome graph and PET-derived receptor prior with null controls. |
| Reproducible archive | manifest_ready | true | 0.75 | Generate the archive manifest, then publish a GitHub release and Zenodo DOI. |

## Canonical Next State

- Primary canonical parcellation target: `schaefer_100_yeo_7`.
- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.
- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.
- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.
- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.
