# Repository Metadata

Detailed metadata for public repositories and archives inspected for the
ds003059 prior-art layer. Commit hashes are from the local clone manifest.

## GitHub Repositories

| Repository | Local directory | Branch | Commit | License status | Main language/framework | README summary | Installation notes | ds003059 support |
|---|---|---|---:|---|---|---|---|---|
| `giulioruffini/LSD-paper-code-Ruffini-et-al.-2022` | `ruffini_lsd_paper_code` | `main` | `50bb2958aa3a` | No root license file found | Python / Jupyter | Notebook and SMITH/Neurotwin code for Ising models from BOLD data and personalized temperature fitting | Requires Python notebook stack plus private/derived `data/lsd/` and `data/supp_data/` inputs described in README | Direct, via expected LSD derivative arrays |
| `giulioruffini/StarLZW` | `ruffini_starlzw` | `Python3` | `4bf55f801f2b` | Root `LICENSE` found | Python | LZW compression package and demos for binary data complexity | Python library/demo usage from repo; no ds003059 install path required | Supporting dependency for algorithmic complexity |
| `anders-s-olsen/CopBET` | `olsen_copbet` | `master` | `8787820bbb95` | GPL terms stated in README; no root license file found | MATLAB / Python | Copenhagen Brain Entropy Toolbox with MATLAB functions and Python translation | MATLAB path setup via `addpath(genpath(...))`; Python requirements in `copbet_py/requirements.txt` | Direct, includes `CopBET_main_CH2016data.m` and `LSDdata/LSDdata_ROI.m` |
| `singlesp/energy_landscape` | `singleton_energy_landscape` | `main` | `47cd3d2347e7` | No root license file found | MATLAB / R | Code for receptor-informed network-control energy landscape analysis | MATLAB R2017a+, R packages listed in README; scripts require local `basedir` edits | Direct, README cites OpenNeuro ds003059 v1.0.0 |
| `ottaviadipasquale/react-fmri` | `dipasquale_react_fmri` | `main` | `48462c0a94e8` | MIT license found | Python CLI package | REACT two-step receptor-enriched functional connectivity package | `pip install react-fmri`; CLI scripts `react_normalize`, `react_masks`, `react` | Method dependency, not ds003059-specific |
| `netneurolab/hansen_receptors` | `hansen_receptors` | `main` | `f8b41da92a73` | CC BY-NC-SA 4.0 license found | Python plus PET/receptor data | Receptor/transporter maps and scripts for parcellation, receptor matrices, and analyses | Change path variables in scripts; requires netneurotools/neuromaps-style dependencies depending on script | Receptor-prior dependency, not direct ds003059 pipeline |
| `macshine/corematrix` | `shine_corematrix` | `main` | `6f0997526430` | No root license file found | NIfTI map resource | CALB/PVALB thalamic core-matrix maps supporting Muller et al. 2020 | No install path; resource files are NIfTI maps | Supporting dependency only |
| `macshine/integration` | `shine_integration` | `master` | `d00534027ab8` | No root license file found | MATLAB | MATLAB code supporting dynamic functional brain network integration states | MATLAB scripts; likely requires graph/community-analysis dependencies | Method dependency/directly related dynamic integration method |
| `MICA-MNI/BrainSpace` | `mica_brainspace` | `master` | `8730de88ae32` | BSD 3-Clause license found | Python / MATLAB | Cross-platform macroscale gradient mapping toolbox | Docs at `https://brainspace.readthedocs.io`; repo includes Python setup and MATLAB toolbox files | Method dependency, not ds003059-specific |
| `igaadamska/LSD-music-brainstates` | `adamska_lsd_music_brainstates` | `main` | `16428ebd0eb9` | Root `LICENSE` found | Jupyter notebooks | Notebook-only workflow for time-series extraction, K-means brain states, Neurosynth correlations, and MLM statistics | No README; inspect notebooks and hard-coded paths before execution | Direct, but local run-02/music claims remain gated |
| `till-m/TNM_project` | `muehlbauer_tnm_project` | `master` | `1d23c9a7b63c` | No root license file found | Python / MATLAB | Teaching/project code for translational neuromodeling and DCM-style analysis | `pip install -r requirements.txt`; optional MATLAB engine; README asks for ds003059 and ds000030 under `data/` | Secondary/pedagogical direct ds003059 reference |

## Non-GitHub Archive

| Source | Local path | DOI | License | Contents | Data policy | ds003059 support |
|---|---|---|---|---|---|---|
| Zenodo record `14029241` | `prior_art/repositories/zenodo_14029241_code/Code/` | `10.5281/zenodo.14029241` | CC BY 4.0 | `FC_analysis.m`, `integration_analysis_v2.m` extracted from 6,473 byte `Code.zip` | 435,268,809 byte `Data.zip` not downloaded by default | Direct LSD branch plus cross-state comparisons, but requires processed FC inputs |

## Metadata Caveats

- "License status" records root license files or explicit README license text
  found during inspection. It is not legal advice.
- "Direct" means the source explicitly references ds003059 or provides a
  ds003059-specific workflow. It does not mean the workflow is locally runnable.
- Cloned code stays in `prior_art/repositories/` and remains gitignored.
