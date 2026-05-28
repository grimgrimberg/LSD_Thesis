# External cortical-map alignment

External receptor, myelin, functional-gradient, and transcriptomic maps are treated as anatomical or molecular priors. Agreement with LSD-placebo dynamics is exploratory module-level proxy evidence, not receptor pharmacology, clinical validation, or subjective-experience evidence.

| Map | Target | r | p | q | CI overlaps zero | Status |
| --- | --- | ---: | ---: | ---: | --- | --- |
| PET 5-HT2A receptor prior | DMDC LSD-specific state-update coefficient | -0.320 | 0.4416 | 0.9922 | yes | exploratory_no_fdr_support |
| PET 5-HT2A receptor prior | DMDC LSD-specific update magnitude | -0.047 | 0.9190 | 0.9922 | yes | exploratory_no_fdr_support |
| PET 5-HT2A receptor prior | DMDC condition-input coefficient | 0.665 | 0.0719 | 0.8628 | yes | exploratory_no_fdr_support |
| HCP T1w/T2w myelin hierarchy proxy | DMDC LSD-specific state-update coefficient | -0.100 | 0.8107 | 0.9922 | yes | exploratory_no_fdr_support |
| HCP T1w/T2w myelin hierarchy proxy | DMDC LSD-specific update magnitude | 0.225 | 0.5756 | 0.9922 | yes | exploratory_no_fdr_support |
| HCP T1w/T2w myelin hierarchy proxy | DMDC condition-input coefficient | 0.240 | 0.6074 | 0.9922 | yes | exploratory_no_fdr_support |
| Principal functional gradient proxy | DMDC LSD-specific state-update coefficient | -0.026 | 0.9517 | 0.9922 | yes | exploratory_no_fdr_support |
| Principal functional gradient proxy | DMDC LSD-specific update magnitude | -0.260 | 0.5187 | 0.9922 | yes | exploratory_no_fdr_support |
| Principal functional gradient proxy | DMDC condition-input coefficient | 0.005 | 0.9922 | 0.9922 | yes | exploratory_no_fdr_support |
| AHBA HTR2A expression-direction proxy | DMDC LSD-specific state-update coefficient | -0.259 | 0.5390 | 0.9922 | yes | exploratory_no_fdr_support |
| AHBA HTR2A expression-direction proxy | DMDC LSD-specific update magnitude | -0.030 | 0.9445 | 0.9922 | yes | exploratory_no_fdr_support |
| AHBA HTR2A expression-direction proxy | DMDC condition-input coefficient | 0.558 | 0.1510 | 0.9058 | yes | exploratory_no_fdr_support |

## Method boundary

This pass compares maps after aggregation to the 8-module thesis contract with exact label-permutation p-values. It is not a full neuromaps surface-level spatial-autocorrelation null analysis.
