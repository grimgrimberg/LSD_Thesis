# Set, Setting, and Seed: Guided Latent Brain Dynamics Under LSD

Date: 2026-05-12

Status: PASS 2A partial implementation. The safe empirical foundation is implemented for cached rest data; run-02 music extraction, motion sensitivity, heavy ML, and full surrogate model comparison remain future work.

## One-Paragraph Thesis

This project extends the existing transparent whole-brain LSD surrogate and empirical fMRI analysis into a reliability-gated, control-theoretic account of guided latent brain dynamics. It asks whether LSD-associated module-level dynamics in OpenNeuro `ds003059` are better explained by unstructured stochasticity, lowered switching barriers, altered thalamocortical and cross-network routing, altered hierarchical guidance or prior precision, increased sensitivity to external context such as music, or a combined routing-plus-setting mechanism. Stable Diffusion and latent diffusion are used only as analogies for guided stochastic latent-state sampling under noise, priors, and control inputs; the project does not claim the brain literally implements diffusion models or that the surrogate simulates subjective experience.

## Exact Research Questions

1. Does LSD-minus-placebo change module-level dynamics in a way that is more consistent with unstructured noise or with structured routing changes?
2. Are the strongest current empirical targets, `cross_network_communication` and `thalamic_coupling`, better matched by routing mechanisms than by noise-only mechanisms?
3. Can lowered barriers or flattened control-energy proxies explain empirical dynamics without overfitting sign-conflicted metrics?
4. Does hierarchical compression behave as a weak but useful marker of altered guidance or prior precision?
5. If `run-02` music data are extracted, does music act as an external control input that amplifies or redirects LSD-associated dynamics?
6. Do subject baseline geometry and placebo/rest reference state explain meaningful variance in LSD response?
7. Are model rankings stable under subject-disjoint validation?
8. Can dashboard-facing outputs communicate set, setting, seed, substance, routing, and guidance without implying subjective-experience simulation or biological proof?

## Dataset Design

Dataset: OpenNeuro `ds003059`.

Conditions:

- `ses-PLCB`: placebo.
- `ses-LSD`: LSD.

Runs:

- `run-01`: Rest1.
- `run-02`: Music.
- `run-03`: Rest3.

Music exclusions:

- Three subjects had technical problems with the music run and should not be used for music-specific analyses: `S03`, `S12`, `S15`.
- These subjects remain eligible for rest-only analyses if their rest data are otherwise valid.

Current cached analysis state:

- Rest module time series exist for `run-01` and `run-03`.
- `run-02` music module time series were not found in current cached `results/stage_2/module_time_series`.
- Current rest-only paired cohort has 15 paired subjects and 60 records.
- Current module time series have 217 timepoints and 8 modules.
- PASS 2A outputs live under `results/setting_seed/`.

Validation requirement:

- Any ML or model selection must use subject-disjoint validation.
- Naive window-level train/test splitting is forbidden because it leaks subject identity and condition-specific preprocessing structure.

## Current Repo Facts

### Eight Modules

- `visual`
- `auditory`
- `salience`
- `default_mode`
- `executive_frontoparietal`
- `limbic_affective`
- `thalamic_gateway`
- `sensorimotor`

### Empirical Targets

| Metric | LSD-minus-placebo delta | Confidence | Interpretation |
|---|---:|---|---|
| `cross_network_communication` | `+0.07407619939923198` | strong | Primary routing target |
| `thalamic_coupling` | `+0.11991820431751381` | strong | Primary thalamocortical/routing target |
| `hierarchical_compression` | `+0.054149688768586765` | weak | Candidate hierarchy/guidance target |
| `within_network_stability` | `+0.06609328671299261` | moderate | Diagnostic, sign-conflicted |
| `entropy_diversity` | `-0.0022526077494528915` | weak | Diagnostic, sign-conflicted |
| `metastability_proxy` | `-0.053960353741377386` | moderate | Diagnostic, sign-conflicted |
| `effective_barrier_proxy` | `-0.1491923940892797` | weak | Exploratory barrier proxy |
| `switching_rate` | `+0.012345679012345678` | weak | Exploratory transition proxy |

### Existing Model-Ranking Facts

- Stage 5 non-quick full-cohort best candidate: `thalamic_routing_only`, loss `0.762443`.
- Approved CV5 subject-disjoint validation selected `more_cross_talk @ 0.1` in all five folds.
- The CV5 result is proxy-ranking evidence, not biological proof.
- Stage 5 full-cohort ranking is not itself subject-disjoint validation.

## Conceptual Mapping

| Concept | Operational meaning | Repo-facing representation |
|---|---|---|
| Set | Subject baseline geometry, placebo reference, priors, and stable subject traits | Subject-level rest/placebo summaries, baseline latent coordinates, module covariance geometry |
| Setting | External context, especially music vs rest | `run-01` Rest1, `run-02` Music, `run-03` Rest3, music exclusion flags |
| Seed | Endogenous stochasticity, initial condition, subject-specific latent state | Simulation seed, first-window state, subject-specific latent initialization |
| Substance | LSD perturbation relative to placebo | `ses-LSD` vs `ses-PLCB`, condition delta targets |
| Routing | Cross-network and thalamocortical information flow proxies | `cross_network_communication`, `thalamic_coupling`, DMDc/control summaries |
| Guidance | Priors, hierarchy, precision, context sensitivity | `hierarchical_compression`, control input gains, routing-plus-music interactions |

## Candidate Mechanisms And Expected Signatures

| Mechanism | Expected empirical signature | Caveat |
|---|---|---|
| `noise_only` | Increased variance and stochastic spread without consistent thalamic or cross-network specificity | Should not be treated as sufficient if routing targets dominate |
| `lower_barrier_only` | Reduced effective barrier proxy, faster switching, easier transitions between module states | Current barrier and switching targets are weak |
| `cross_talk_only` | Increased cross-network communication with broad inter-module coupling | May fit CV5 proxy result but not isolate thalamic routing |
| `thalamic_routing_only` | Increased thalamic coupling and sensory/network routing, especially thalamic gateway interactions | Full-cohort Stage 5 fit only; needs subject-disjoint extension |
| `hierarchy_precision_only` | Increased hierarchical compression or altered top-down/bottom-up balance | Current target is weak and should remain candidate-level |
| `music_input_gain_only` | Stronger condition effects during `run-02` Music than rest, especially auditory and salience coupling | Requires new run-02 extraction; excludes `S03`, `S12`, `S15` |
| `carryover_tau_only` | Rest3 differs from Rest1 in a direction consistent with lingering context/substance dynamics | Needs careful run-order interpretation |
| `routing_plus_music_gain` | Thalamic/cross-network routing changes are amplified or redirected by music context | Most thesis-relevant, but depends on music data availability |
| `noise_plus_routing` | Noise broadens exploration while routing determines structured target alignment | Plausible hybrid; must avoid fitting every metric |
| `full_guided_latent_model` | Best joint account of set, setting, seed, substance, routing, and guidance under subject-disjoint validation | Highest overfitting and overclaiming risk |

## Proposed Outputs And Artifacts

```text
results/setting_seed/
  data_audit/RUN_COVERAGE.md
  data_audit/run_coverage.json
  reliability/RELIABILITY_SUMMARY.md
  reliability/target_eligibility.json
  latent/LATENT_SUMMARY.md
  latent/latent_metrics.csv
  control/CONTROL_SUMMARY.md
  control/control_metrics.csv
  surrogate/MECHANISM_RANKING.md
  surrogate/mechanism_scores.csv
  ml/SUBJECT_DISJOINT_ML_SUMMARY.md
  ml/predictions.csv
  dashboard/dashboard_payload.json
  figures/
  FINAL_REPORT.md
```

## Implementation Milestones

1. Data audit and music availability report.
2. Reliability and target-eligibility layer.
3. Latent trajectory summaries.
4. DMD/DMDc/control summaries.
5. Config-driven mechanism registry.
6. Subject-disjoint scoring and ML.
7. Dashboard payload and UI update.
8. Final report and validation.

## Risks And Mitigations

| Risk | Mitigation |
|---|---|
| `run-02` music data absent | Fail closed for music analyses; implement audit first |
| Motion summaries absent | Label motion limitation; do not claim motion-controlled results |
| Small N | Use subject-disjoint validation and cautious language |
| Window leakage | Forbid random window splits; test subject separation |
| Atlas/module proxy limitations | Label current 8-module extraction as transparent proxy |
| Stage 5 overinterpretation | Treat as model ranking, not proof |
| Neural models overfit | Make neural ODE/CDE/SDE optional exploratory layer |
| Stable Diffusion analogy overreach | State analogy only; no literal brain-diffusion claim |
| Dashboard oversells findings | Use data-availability warnings and claim labels |

## BRATING Rubric

Scores are 1 to 5. Higher is better except overclaiming risk, where lower is better.

| Decision | Scientific validity | Interpretability | Leakage resistance | Reproducibility | Implementation risk | Compute cost | Thesis relevance | UI value | Novelty | Overclaiming risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cached rest-only reliability extension first | 4 | 5 | 5 | 5 | 2 | 1 | 5 | 3 | 3 | 1 |
| Music extraction only after explicit run audit | 4 | 4 | 4 | 4 | 3 | 3 | 5 | 5 | 4 | 2 |
| DMDc and linear state-space before neural SDE | 4 | 4 | 4 | 4 | 3 | 2 | 5 | 4 | 4 | 2 |
| Neural ODE/CDE/SDE as exploratory only | 3 | 2 | 3 | 3 | 5 | 5 | 4 | 3 | 4 | 3 |
| Subject-disjoint ML only | 4 | 3 | 5 | 4 | 3 | 2 | 4 | 3 | 3 | 2 |
| Dashboard set/setting/seed panels | 3 | 5 | 4 | 4 | 3 | 2 | 5 | 5 | 3 | 1 |

## PASS 2 Plan

PASS 2 should begin with a read-only data audit command. It should not start by adding models.

Recommended first implementation slice:

1. Add `src/lsd_thesis/setting_seed/data.py`.
2. Add `configs/setting_seed.yaml`.
3. Add `scripts/run_setting_seed_reliability.py`.
4. Add `tests/test_setting_seed_data.py`.
5. Produce `results/setting_seed/data_audit/RUN_COVERAGE.md`.

Acceptance for the first slice:

- The command reports `run-01` and `run-03` coverage.
- The command reports current `run-02` absence.
- The command records music-specific exclusions.
- The command records missing motion summaries.
- Tests prove that music-specific exclusions do not remove valid rest-only subjects.

## PASS 2A Implemented Artifacts

- `src/lsd_thesis/setting_seed/data.py`
- `src/lsd_thesis/setting_seed/reliability.py`
- `src/lsd_thesis/setting_seed/latent.py`
- `src/lsd_thesis/setting_seed/control_input.py`
- `src/lsd_thesis/setting_seed/dashboard_payload.py`
- `configs/setting_seed.yaml`
- `results/setting_seed/PASS2A_REPORT.md`

PASS 2A interpretation: the current available cache supports rest-only reliability and descriptive latent trajectory analysis. Music-control analysis is scaffolded but blocked until run-02 module time series are extracted.

## PASS 2B-0 Readiness Update

PASS 2B-0 prepares run-02 and motion readiness without extracting or downloading data.

Implemented decisions:

- Legacy Stage 2 default remains rest-only: `run-01`, `run-03`.
- `run-02` requires `--include-music`.
- The first music extraction must write to `results/setting_seed/run02_extraction/stage_2_music`, not legacy `results/stage_2`.
- Empirical target YAML remains rest-run based, so Music does not silently enter rest target semantics.
- Motion readiness requires parsed structured confounds, not filename-only detection.
- The dashboard distinguishes support, file presence, and analysis readiness.

Current readiness:

- run-02 support available: true.
- run-02 data present: false.
- run-02 analysis ready: false.
- motion-summary support available: true.
- motion data present: false.
- motion analysis ready: false.

BRATING update:

| Decision | Scientific validity | Interpretability | Leakage resistance | Reproducibility | Implementation risk | Compute cost | Thesis relevance | UI value | Novelty | Overclaiming risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Disabled-by-default run-02 extraction support | 5 | 5 | 5 | 5 | 2 | 1 | 5 | 4 | 3 | 1 |
| Separate run-02 extraction root before legacy merge | 5 | 5 | 5 | 5 | 2 | 1 | 5 | 4 | 3 | 1 |
| Motion parser with explicit unavailable/found-unusable states | 5 | 5 | 4 | 5 | 3 | 1 | 5 | 4 | 3 | 1 |

## PASS 2B Roadmap

The remaining implementation sequence is:

1. PASS 2B-1: user-approved run-02 extraction.
2. PASS 2B-2: actual music-control analysis.
3. PASS 2B-3: reliability-weighted surrogate + ML baselines.
4. PASS 2B-4: thesis-level dashboard and final report.

PASS 2B-1 is a data-production pass, not an interpretation pass. PASS 2B-2 must remain descriptive until motion readiness and subject/run coverage are confirmed. PASS 2B-3 must use subject-disjoint validation for any ML baseline.
