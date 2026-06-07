# Dynamic Mechanism Ranking: A+B+C+D+E Proxy-Control Pass

Generated: `2026-06-02T09:44:22.883624+00:00`

## Scope

These are AI/ML surrogate results for ranking macro-dynamic mechanisms; they do not establish receptor-level, clinical, external-validity, or subjective-experience claims.

- Dataset scope: cached ds003059 paired placebo/LSD empirical viewer records
- Paired subject/run records: 30
- Subjects: 15
- Runs: run-01, run-03

## Mechanism Ranking

| Rank | Layer | Mechanism | Status | Score | Evidence |
| --- | --- | --- | --- | ---: | --- |
| 1 | C | `hierarchy_routing_layer` | implemented_first_pass | 0.332606 | sensory-transmodal, associative, thalamic-gateway, and hierarchy-flattening FC proxies |
| 2 | E | `receptor_informed_network_control_energy` | implemented_proxy_control_energy | 0.182875 | finite-horizon control energy with receptor, hierarchy, transmodal, random, and degree-control profiles |
| 3 | D | `dynamic_repertoire_layer` | implemented_first_pass | 0.150619 | integration, segregation, graph modularity, participation, dynamic-FC variance, and trajectory-step proxies |
| 4 | A | `transition_state_proxy` | implemented_first_pass | 0.148906 | state occupancy, transition entropy, transition rate, dwell/barrier, and step-distance proxies |
| 5 | B | `dmdc_condition_interaction` | implemented_negative_control_baseline | -0.0740637 | leave-one-subject-out one-step RMSE change; retained as a predictive baseline, not control-energy evidence |

## Literature Grounding

| Layer | What it supports | Source |
| --- | --- | --- |
| A | Transition/barrier language is a proxy framing, not a demonstrated biological energy landscape. | [Carhart-Harris and Friston 2019 REBUS; energy/free-energy framing is theoretical.](https://pubmed.ncbi.nlm.nih.gov/31221820/) |
| B | DMDc is a defensible data-driven controlled-dynamics baseline, but it is not network-control energy. | [Proctor, Brunton, and Kutz 2016 Dynamic Mode Decomposition with Control.](https://epubs.siam.org/doi/10.1137/15M1013857) |
| C | Hierarchy/routing proxies are motivated by sensory-associative and thalamic connectivity findings. | [Preller et al. 2018 eLife; Preller et al. 2019 PNAS.](https://elifesciences.org/articles/35082) |
| D | Dynamic repertoire and integration/segregation are directly studied LSD fMRI targets. | [Luppi et al. 2021 NeuroImage; Atasoy et al. 2017 Scientific Reports.](https://www.nature.com/articles/s41598-017-17546-0) |
| E | Receptor-informed control-energy landscape tests are directly motivated by psychedelic network-control papers. | [Singleton et al. 2022 Nature Communications; Gu et al. 2015 controllability of structural brain networks.](https://www.nature.com/articles/s41467-022-33578-1) |

## A. Transition-State Proxy

Transition-state metrics are macro-state proxy summaries; they are not true biological energy barriers.

| Metric | Mean Delta | SD | Signed Effect | Direction |
| --- | ---: | ---: | ---: | --- |
| `state_occupancy_entropy` | -0.00035259 | 0.000685259 | -0.514535 | positive means broader state occupancy under LSD (sign consistency 0.276, sign-test p=0.996) |
| `transition_entropy` | 0.00389023 | 0.0227059 | 0.171332 | positive means more diverse transitions under LSD (sign consistency 0.667, sign-test p=0.0494) |
| `transition_rate` | 0.00848765 | 0.0542918 | 0.156334 | positive means more frequent state switching under LSD (sign consistency 0.621, sign-test p=0.132) |
| `mean_dwell_time` | -0.0582229 | 0.309656 | 0.188024 | negative means shorter dwell times under LSD (sign consistency 0.621, sign-test p=0.132) |
| `barrier_reduction_proxy` | 0.0582229 | 0.309656 | 0.188024 | positive means shorter dwell times under LSD (sign consistency 0.621, sign-test p=0.132) |
| `transition_step_distance_proxy` | 0.00701819 | 0.0877994 | 0.0799344 | positive means larger one-step macro-state movement under LSD (sign consistency 0.5, sign-test p=0.572) |

## B. DMDc / Controlled Dynamics

DMDc coefficients are descriptive surrogate parameters, not real governing equations of LSD brain dynamics.

- Validation: leave-one-subject-out one-step prediction with paired placebo/LSD normalization inside each subject/run record
- Selected variant for B score: `condition_interaction`
- Ridge alpha: 1.0
- Fold count: 15
- No-input RMSE: 0.527364 +/- 0.0175141
- Condition-bias RMSE: 0.527365 +/- 0.0175144
- Condition-interaction RMSE: 0.527759 +/- 0.0176873
- Condition-bias relative RMSE improvement: -5.66143e-05% +/- 0.000181988%
- Condition-interaction relative RMSE improvement: -0.0740637% +/- 0.19075%

Interpretation: B is only evidence for controlled dynamics if the held-out condition-interaction variant improves one-step prediction. A near-zero or negative improvement is a meaningful negative result.

## C. Hierarchy / Routing Evidence Layer

Hierarchy/routing metrics are coarse FC proxies; they do not prove REBUS, precision relaxation, or thalamic gating.

| Metric | Mean Delta | SD | Signed Effect | Direction |
| --- | ---: | ---: | ---: | --- |
| `sensory_transmodal_coupling` | 0.047335 | 0.100449 | 0.471233 | positive means stronger sensory-to-transmodal coupling under LSD (sign consistency 0.733, sign-test p=0.00806) |
| `sensory_global_coupling` | 0.0574739 | 0.105419 | 0.545197 | positive means stronger sensory/somatomotor global coupling under LSD (sign consistency 0.733, sign-test p=0.00806) |
| `associative_global_coupling` | 0.069585 | 0.09861 | -0.705658 | negative means weaker associative-network global coupling under LSD (sign consistency 0.3, sign-test p=0.992) |
| `thalamic_global_coupling` | 0.119918 | 0.176044 | 0.681182 | positive means stronger thalamic-gateway coupling with cortex under LSD (sign consistency 0.767, sign-test p=0.00261) |
| `thalamic_sensory_coupling` | 0.0980293 | 0.230389 | 0.425494 | positive means stronger thalamic-gateway coupling with sensory modules under LSD (sign consistency 0.6, sign-test p=0.181) |
| `thalamic_transmodal_coupling` | 0.136335 | 0.178598 | 0.763361 | positive means stronger thalamic-gateway coupling with transmodal modules under LSD (sign consistency 0.8, sign-test p=0.000715) |
| `hierarchy_differentiation` | -0.000136523 | 0.100689 | 0.00135589 | negative means reduced within-vs-cross hierarchy separation under LSD (sign consistency 0.533, sign-test p=0.428) |
| `hierarchy_flattening_proxy` | 0.000136523 | 0.100689 | 0.00135589 | positive means hierarchy differentiation is reduced under LSD (sign consistency 0.533, sign-test p=0.428) |
| `hierarchy_coupling_gradient_magnitude` | -0.0640194 | 0.276698 | 0.231369 | negative means node global-coupling is less tied to the hierarchy proxy under LSD (sign consistency 0.533, sign-test p=0.428) |
| `hierarchy_gradient_flattening_proxy` | 0.0640194 | 0.276698 | 0.231369 | positive means reduced hierarchy/global-coupling gradient strength under LSD (sign consistency 0.533, sign-test p=0.428) |
| `receptor_weighted_global_coupling` | 0.0790878 | 0.0943967 | 0.837824 | positive means stronger global coupling in high receptor-prior modules under LSD (sign consistency 0.767, sign-test p=0.00261) |
| `receptor_global_coupling_alignment` | 0.270381 | 0.451883 | 0.598344 | positive means high receptor-prior modules align more with global coupling under LSD (sign consistency 0.667, sign-test p=0.0494) |

## D. Dynamic Repertoire Evidence Layer

Dynamic repertoire metrics are descriptive FC/time-series proxies; they are not direct measures of subjective richness.

| Metric | Mean Delta | SD | Signed Effect | Direction |
| --- | ---: | ---: | ---: | --- |
| `global_mean_fc` | 0.0715103 | 0.0977902 | 0.731262 | positive means globally stronger FC under LSD (sign consistency 0.733, sign-test p=0.00806) |
| `within_network_segregation` | 0.0471985 | 0.126613 | -0.372778 | negative means weaker within-network segregation under LSD (sign consistency 0.467, sign-test p=0.708) |
| `between_network_integration` | 0.0938997 | 0.135835 | 0.691275 | positive means stronger between-network integration under LSD (sign consistency 0.733, sign-test p=0.00806) |
| `integration_segregation_balance` | 0.0467012 | 0.134548 | 0.347096 | positive means integration increases relative to segregation under LSD (sign consistency 0.533, sign-test p=0.428) |
| `dynamic_fc_variance` | -0.000938063 | 0.0112601 | -0.0833084 | positive means a broader time-varying FC repertoire under LSD (sign consistency 0.433, sign-test p=0.819) |
| `dynamic_fc_path_length` | -0.0957026 | 0.153042 | -0.625334 | positive means larger movement through FC-state space under LSD (sign consistency 0.333, sign-test p=0.979) |
| `trajectory_step_distance` | 0.00701819 | 0.0877994 | 0.0799344 | positive means larger macro-trajectory steps under LSD (sign consistency 0.5, sign-test p=0.572) |
| `graph_modularity_q` | -0.00943284 | 0.061164 | 0.154222 | negative means lower graph modularity under LSD (sign consistency 0.5, sign-test p=0.572) |
| `graph_modularity_reduction_proxy` | 0.00943284 | 0.061164 | 0.154222 | positive means reduced graph modularity under LSD (sign consistency 0.5, sign-test p=0.572) |
| `mean_participation_coefficient` | 0.0278678 | 0.0711206 | 0.391839 | positive means nodes distribute connectivity across more communities under LSD (sign consistency 0.567, sign-test p=0.292) |
| `global_efficiency` | 0.0525297 | 0.0748353 | 0.701938 | positive means stronger graph-theoretic integration under LSD (sign consistency 0.733, sign-test p=0.00806) |

## E. Receptor-Informed Network-Control Energy

E is a receptor/hierarchy-informed proxy-control test. It is not full receptor-informed network control theory until a structural connectome and PET-derived receptor map are added.

- Method: finite-horizon discrete network-control energy over matched PCA-state centroids; control profiles share the same mean control budget
- Equation: `x[t+1] = A_graph x[t] + B_profile u[t]; energy = min sum_t ||u[t]||^2 over a finite horizon`
- Horizon: 8
- Graph source: configs/graphs/macro_modules.yaml macro-module proxy graph; not a subject structural connectome
- Structural connectome: False
- Receptor prior source: coarse module-level proxy prior from receptor-gradient model config; not a PET-derived receptor map
- Random receptor-prior permutation nulls per pair: 128

| Metric | Mean Value | SD | Signed Effect | Direction |
| --- | ---: | ---: | ---: | --- |
| `lsd_vs_placebo_receptor_transition_energy_reduction_pct` | 4.7022 | 12.5136 | 0.375766 | positive means LSD within-condition transitions need less receptor-profile control energy than placebo (sign consistency 0.633, sign-test p=0.1) |
| `lsd_vs_placebo_uniform_transition_energy_reduction_pct` | 6.93589 | 9.57709 | 0.724217 | positive means LSD within-condition transitions need less uniform-control energy than placebo (sign consistency 0.767, sign-test p=0.00261) |
| `receptor_vs_uniform_energy_reduction_pct` | -34.387 | 23.5869 | -1.45789 | positive means receptor-prior control needs less energy than uniform control (sign consistency 0, sign-test p=1) |
| `receptor_vs_random_energy_reduction_pct` | -15.4343 | 18.548 | -0.832125 | positive means receptor-prior control needs less energy than random receptor-prior permutations (sign consistency 0.267, sign-test p=0.997) |
| `hierarchy_vs_uniform_energy_reduction_pct` | -300.47 | 130.811 | -2.29698 | positive means hierarchy-prior control needs less energy than uniform control (sign consistency 0, sign-test p=1) |
| `transmodal_vs_uniform_energy_reduction_pct` | -674.316 | 331.413 | -2.03467 | positive means transmodal-prior control needs less energy than uniform control (sign consistency 0, sign-test p=1) |
| `state_target_alignment_receptor` | 0.133003 | 0.286867 | 0.463641 | positive means modules with higher receptor prior align with larger LSD-minus-placebo state displacement (sign consistency 0.7, sign-test p=0.0214) |

## Robustness And Literature Benchmark

These robustness checks are in-sample stress tests on the cached LSD data. They do not replace the ds006072 cross-drug stress test, structural-connectome controls, PET receptor maps, or Schaefer/Yeo sensitivity.

### Subject Bootstrap

| Layer | Score Mean | 95% Bootstrap Interval | Rank-1 Fraction | Median Rank |
| --- | ---: | ---: | ---: | ---: |
| A | 0.163748 | -0.131526 to 0.493676 | 0.117 | 3 |
| B | -0.0744303 | -0.165982 to 0.0121405 | 0 | 5 |
| C | 0.349477 | 0.222188 to 0.520315 | 0.844 | 1 |
| D | 0.148384 | -0.0193018 to 0.329665 | 0.0195 | 3 |
| E | 0.195633 | -0.0162498 to 0.392784 | 0.0195 | 3 |

### E Horizon Sensitivity

| Horizon | E Support Score | LSD Receptor Energy Reduction % | Receptor vs Random Energy Reduction % |
| ---: | ---: | ---: | ---: |
| 4 | 0.20594 | 4.76742 | -12.7529 |
| 8 | 0.189545 | 4.7022 | -12.6957 |
| 12 | 0.160931 | 4.47763 | -14.1435 |
| 16 | 0.179289 | 4.31555 | -13.6198 |

### Claim Verdicts

| Claim | Verdict | Evidence | Next Action |
| --- | --- | --- | --- |
| C hierarchy/routing is currently the strongest implemented LSD mechanism layer. | supported_first_pass | Bootstrap rank-1 fraction=0.844. | Re-run C under Schaefer/Yeo and motion-sensitive exclusions before final thesis claims. |
| E supports a landscape-flattening proxy. | supported_proxy | Default-horizon receptor transition-energy reduction=4.702%. | Replace macro graph with structural connectome and add graph-rewire nulls. |
| E supports receptor-specific control placement. | not_supported_yet | Receptor-vs-random energy reduction=-15.434%. | Replace coarse priors with PET 5-HT2A maps and spatial nulls before making receptor claims. |
| Current LSD patterns align with the 2026 transmodal-unimodal benchmark. | directionally_aligned | C sensory-transmodal mean delta=0.0473. | Test the same benchmark in ds006072 and Schaefer/Yeo parcellations. |
| Current LSD patterns address striatal/unimodal effects. | not_testable_current_proxy | not_available_current_8_module_proxy | Add striatal parcels before comparing this part of the Nature Medicine result. |
| B DMDc is the main control-theory result. | reject_as_main_claim | B bootstrap rank-1 fraction=0.000. | Keep B as a negative/sanity baseline unless held-out prediction improves clearly. |

### Literature Benchmark

| Benchmark | Layer | Metric | Status | Observed Delta | Caveat |
| --- | --- | --- | --- | ---: | --- |
| 2026 Nature Medicine transmodal-unimodal coupling | C | `sensory_transmodal_coupling` | aligned | 0.047335 | Current project uses 8 modules, not the consortium atlas/Bayesian mega-analysis pipeline. |
| 2026 Nature Medicine increased between-network integration | D | `between_network_integration` | aligned | 0.0938997 | Integration metric is descriptive FC, not the exact mega-analysis posterior. |
| 2026 Nature Medicine within-network coupling reduction | D | `within_network_segregation` | opposes_or_weak | 0.0471985 | The paper notes not all visually apparent patterns yielded high-confidence posteriors. |
| 2026 Nature Medicine thalamic-unimodal coupling | C | `thalamic_sensory_coupling` | aligned | 0.0980293 | The current thalamic module is coarse and does not resolve thalamic nuclei. |
| Singleton 2022 lower psychedelic control energy | E | `lsd_vs_placebo_receptor_transition_energy_reduction_pct` | aligned | 4.7022 | This is not full receptor-informed NCT until structural connectome and PET receptor maps are added. |
| Singleton 2022 receptor-informed control placement | E | `receptor_vs_random_energy_reduction_pct` | opposes_or_weak | -15.4343 | A negative or weak result should block receptor-specific claims. |
| 2026 Nature Medicine striatal-unimodal coupling | C/D | `not_available_current_8_module_proxy` | missing_required_region | n/a | Do not claim striatal support from the current Harvard-Oxford 8-module proxy. |

## Generated Artifacts

- `results/dynamic_mechanism_ranking/summary.json`
- `results/dynamic_mechanism_ranking/transition_metric_deltas.csv`
- `results/dynamic_mechanism_ranking/hierarchy_routing_metric_deltas.csv`
- `results/dynamic_mechanism_ranking/dynamic_repertoire_metric_deltas.csv`
- `results/dynamic_mechanism_ranking/network_control_energy_metric_deltas.csv`
- `results/dynamic_mechanism_ranking/network_control_energy_profiles.csv`
- `results/dynamic_mechanism_ranking/dmdc_loso_folds.csv`
- `results/dynamic_mechanism_ranking/figures/transition_proxy_deltas.html`
- `results/dynamic_mechanism_ranking/figures/dmdc_fold_rmse.html`
- `results/dynamic_mechanism_ranking/figures/dmdc_condition_vector.html`
- `results/dynamic_mechanism_ranking/figures/dmdc_condition_interaction_vector.html`
- `results/dynamic_mechanism_ranking/figures/hierarchy_routing_deltas.html`
- `results/dynamic_mechanism_ranking/figures/dynamic_repertoire_deltas.html`
- `results/dynamic_mechanism_ranking/figures/network_control_energy.html`

## Limitations

- Macro-state labels use a deterministic PCA-quantile proxy; clustering choices remain a sensitivity risk even with step-distance diagnostics.
- DMDc uses one-step ridge-linear prediction on paired-normalized cached module trajectories; it is a baseline, not the network-control result.
- C and D use coarse 8-module FC and graph proxies, not canonical network or thalamic-nucleus definitions.
- E currently uses a macro-module proxy graph and coarse receptor priors; it is not full structural-connectome/PET receptor-informed network control theory.
- Nulls include receptor-weight permutations and degree controls, but not yet degree-preserving structural graph rewires or spatial-autocorrelation-preserving receptor-map nulls.
- Metric summaries now include bootstrap confidence intervals and BH-FDR correction for sign-consistency p-values; with small n these are uncertainty descriptors, not population claims.
- Run-02 music data are available in the fMRI explorer but are not part of this primary A+B+C+D+E ranking summary.
