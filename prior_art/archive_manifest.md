# External Archive Manifest

This file records non-GitHub code archives inspected for the ds003059 prior-art
landscape. Large data archives are not downloaded by default.

## Zenodo 14029241

| Field | Value |
|---|---|
| Title | Neural Correlates of Psychedelic, Sleep, and Sedated States Support Global Theories of Consciousness |
| DOI | 10.5281/zenodo.14029241 |
| Record URL | https://zenodo.org/records/14029241 |
| Publication date | 2024-11-02 |
| License | CC BY 4.0 |
| Code archive | `Code.zip` |
| Code archive size | 6,473 bytes |
| Code archive MD5 | `6487a260c9a3478eb0e791b2245e43ed` |
| Local extracted path | `prior_art/repositories/zenodo_14029241_code/Code/` |
| Data archive | `Data.zip` |
| Data archive size | 435,268,809 bytes |
| Data archive policy | Not downloaded; treated as a large processed-data dependency. |

Verified code files:

| File | Notes |
|---|---|
| `FC_analysis.m` | MATLAB script with hard-coded Windows paths, 450-ROI time-series input, FC matrix generation, within/between anterior/posterior network summaries, paired REST2 vs REST1 tests, and CSV/figure outputs. |
| `integration_analysis_v2.m` | MATLAB script comparing within/between integration across LSD, ketamine, nitrous oxide, propofol, and sleep/sedation datasets. Uses precomputed reordered FC matrices and writes effect-size summaries. |

Reproducibility caveat: the code is public and small, but the scripts are not
parameterized and require preprocessed/reordered functional-connectivity inputs.
They should be wrapped or reimplemented before running inside this repository.
