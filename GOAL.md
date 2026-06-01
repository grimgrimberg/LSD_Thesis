# Goal

Date: 2026-05-19

## 0. 2026-05-19 Cross-Dataset Thesis-Ready Revamp

This section supersedes the LSD-only framing where the two disagree. The LSD A+B+C+D+E analysis remains the anchor, but the thesis should now be judged as a cross-dataset, multi-scale, explainable mechanism-ranking project.

### 2026-05-19 Implemented Loop Status

The current loop is now more than a static concept board. `scripts/run_dynamic_mechanism_ranking.py` regenerates the A+B+C+D+E ranking, robustness checks, literature-benchmark mapping, figures, and CSV/XLSX exports.

Current LSD anchor result:

| Rank | Layer | Score | Interpretation |
| --- | --- | ---: | --- |
| 1 | C hierarchy/routing | 0.332606 | Strongest implemented first-pass layer. |
| 2 | E network-control energy | 0.175078 | Supports lower LSD transition-energy proxy, not receptor-specific placement. |
| 3 | D dynamic repertoire | 0.150619 | Supportive but window-sensitive and mixed. |
| 4 | A transition-state proxy | 0.148906 | Supportive but state-label dependent. |
| 5 | B DMDc | -0.074064 | Negative-control predictive baseline, not the main control-theory claim. |

Current robustness result:

- C is the current thesis anchor: subject-bootstrap rank-1 fraction = `0.848`.
- E horizon sensitivity supports a landscape-flattening proxy: LSD receptor-profile transition-energy reduction is about `4.3%` to `4.8%` across tested horizons.
- E receptor-specific placement is not supported: receptor-vs-random energy reduction is negative, around `-14%` to `-15%`.
- B should not be sold as the main result: bootstrap rank-1 fraction = `0.000`.
- Literature benchmark alignment is `4/6` measurable checks. The current proxy aligns with transmodal-unimodal, between-network integration, thalamic-sensory, and lower-control-energy directions; it opposes/weakens within-network reduction and receptor-placement checks.
- Striatal/unimodal effects from the 2026 Nature Medicine mega-analysis are not testable in the current 8-module proxy because there is no striatal parcel.

Current export artifacts:

- `results/dynamic_mechanism_ranking/summary.json`
- `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`
- `results/dynamic_mechanism_ranking/exports/dynamic_mechanism_results.xlsx`
- `results/dynamic_mechanism_ranking/exports/*.csv`
- `results/dynamic_mechanism_ranking/figures/*.html`
- `results/thesis_evidence_loop/thesis_evidence_loop_status.json`
- `results/psilocybin_ds006072/psilocybin_ds006072_status.json`
- `results/structural_connectome/structural_connectome_status.json`
- `results/receptor_priors/receptor_prior_status.json`
- `results/parcellation_sensitivity/parcellation_sensitivity_status.json`
- `results/literature_benchmark/literature_benchmark_status.json`
- `results/thesis_evidence_loop/external_source_plan.csv`
- `results/thesis_evidence_loop/external_source_plan.md`

Current evidence-loop implementation status:

| Step | Status | Scientific meaning |
| --- | --- | --- |
| LSD robustness | `implemented_lsd_robustness` | Current LSD C/E robustness is populated. |
| Psilocybin `ds006072` | `implemented_ds006072_unchanged_scoring_validation` | A local Schaefer100/Yeo7 psilocybin/MTP stress test now exists under unchanged scoring; it is stronger than the earlier structure-family pass, but the small-sample ranking differs from the LSD top layer and must be reported as a negative/partial external result. |
| HCP structural graph | `implemented_hcp_structural_graph_sensitivity` | E can be rerun with a local structural-connectome CSV graph and graph controls. |
| PET receptor priors | `implemented_pet_receptor_prior_sensitivity` | PET-derived prior sensitivity is generated, but receptor-specific placement remains unsupported unless it beats uniform/random/degree/spatial controls. |
| Schaefer/Yeo sensitivity | `implemented_status_matrix` | Schaefer 100/200 by Yeo 7/17 sensitivity rows exist; treat them as C/D/E sensitivity evidence, not a replacement for full subcortical/striatal testing. |
| Mega-analysis comparison | `implemented_directional_proxy_benchmark` | Directional proxy benchmark is populated from current LSD results. |

External source plan:

| Source | Planned role | Use in project |
| --- | --- | --- |
| Girn et al., Nature Medicine 2026 | planned comparison | Final external benchmark for C/D/E directionality: transmodal-unimodal coupling, subnetwork specificity, and striatal-unimodal effects. |
| Dosenbach/Siegel group, Scientific Data 2025 | planned dataset | OpenNeuro `ds006072` is the first cross-drug psilocybin expansion after LSD robustness, using raw/minimally processed/fully processed imaging provenance. |
| Markello et al., Nature Methods 2022 | planned biological prior | `neuromaps` replaces hand-built receptor proxies with documented receptor-map projection and spatial-null tooling. |
| Human Connectome Project Young Adult | planned graph prior | HCP Young Adult is the normative diffusion/resting-fMRI source for structural-connectome graph and null sensitivity. |
| Schaefer et al., Cerebral Cortex 2018 | planned parcellation | Schaefer/Yeo is the sensitivity layer for C/D/E beyond the 8-module proxy. |

The thesis claim should therefore be:

> A transparent, explainable mechanism-ranking framework finds that hierarchy/routing proxies are the most stable current LSD evidence layer, while network-control energy supports only a landscape-flattening proxy and does not yet support receptor-specific control placement. The framework is thesis-ready as a falsifiable evidence ladder, not as proof of a biological LSD mechanism.

### One-Sentence Thesis Goal

Build a reproducible explainable AI framework that ranks transparent control-theoretic and graph-dynamic surrogate mechanisms across LSD and psilocybin fMRI, then tests whether the strongest claims survive robustness, structural-connectome, receptor-map, atlas, and literature-benchmark checks.

### Research Question

Which interpretable macro-dynamic mechanisms best explain psychedelic drug-vs-control fMRI changes, and which claims fail under robustness, cross-dataset, and biological-prior tests?

### Hypotheses

1. C hierarchy/routing remains the strongest or among the strongest LSD mechanisms after subject/bootstrap, run, and atlas sensitivity.
2. E network-control energy supports a landscape-flattening proxy only if lower drug-state transition energy survives horizon, state-label, graph, and null sensitivity.
3. E receptor-specific control placement is supported only if PET-derived 5-HT2A priors beat uniform, degree, random, graph-rewire, and spatial nulls.
4. D dynamic repertoire contributes supportive evidence only if integration/segregation effects survive window-size and parcellation sensitivity.
5. LSD and psilocybin should show convergent transmodal-unimodal coupling if the framework is aligned with the 2026 psychedelic mega-analysis; striatal/unimodal effects are a secondary benchmark, not a current implemented result.

### Prediction Target

Primary target: rank A/B/C/D/E mechanism layers by signed alignment with paired drug-minus-control fMRI proxy evidence, with uncertainty and null comparisons.

Secondary target: compare the final ranked patterns against scholarly targets:

- LSD internal robustness.
- Psilocybin `ds006072` replication.
- HCP structural-connectome control-energy sensitivity.
- neuromaps/FS5ht receptor-prior sensitivity.
- Schaefer 100/200 and Yeo 7/17 parcellation sensitivity.
- 2026 Nature Medicine transmodal-unimodal and striatal-unimodal benchmark.

### Scientific Contribution

The stronger thesis contribution is not a single LSD result. It is a falsifiable evidence ladder that turns broad psychedelic mechanism stories into ranked, reproducible, explainable, and stress-tested computational hypotheses.

### Practical Contribution

The final project should be a hireable research-engineering artifact: runnable commands, documented data provenance, exported CSV/XLSX tables, saved figures, dashboard truth board, model cards, dataset cards, failure cases, and defense slides.

### Success Criteria

Minimum thesis-ready success:

- Current LSD A+B+C+D+E results regenerate.
- Robustness pass reports whether C/E survive subject/bootstrap, run, horizon, state-label, and window-size sensitivity.
- Dashboard exposes implemented, planned, failed, and blocked states without hiding negative results.
- Claims stay at macro-dynamics/proxy level.
- At least one external expansion is implemented or clearly scoped with a reproducible data-ingestion blocker.

Strong thesis-ready success:

- `ds006072` psilocybin replication runs under the same scoring rules.
- E is rerun with a structural graph and PET receptor priors.
- C/D/E are rerun under Schaefer/Yeo sensitivity.
- Final results are compared to the 2026 Nature Medicine mega-analysis without overclaiming causality.

### Risks And Unknowns

- `ds006072` is richer and heavier than the current LSD cache; preprocessing may dominate the project.
- HCP access and structural-connectome preprocessing may introduce data-use and compute constraints.
- PET receptor-map projection can create spatial-autocorrelation artifacts if nulls are weak.
- Schaefer/Yeo may change the current 8-module result.
- The final scientifically honest result may be that C survives but E receptor-specific placement fails.

### Minimum Viable Thesis Version

Use current LSD results plus robustness plus dashboard/documentation. This is enough if the evidence is honest and visually clear.

### Ambitious Version

Add psilocybin, structural connectome, PET receptors, Schaefer/Yeo, and scholarly comparison. This is the version that best signals MSc readiness because it demonstrates AI, data science, neuroscience, reproducibility, and skeptical reasoning.

## 1. One-Sentence Thesis Goal

Build and evaluate an explainable AI/ML mechanism-ranking framework that tests which transparent control-theoretic and graph-dynamic surrogate mechanisms best align with empirical LSD-minus-placebo macro-dynamics in fMRI, while explicitly reporting where the current mechanisms fail.

## 2. Research Question

Can a transparent AI-assisted ranking pipeline distinguish which candidate macro-dynamic mechanisms are most compatible with paired LSD-placebo fMRI proxy evidence, and can it separate plausible control-theoretic explanations from unsupported or overfit ones?

## 3. Hypotheses

### H1: Hierarchy/Routing

LSD-placebo differences will be most consistently expressed in hierarchy/routing proxies: sensory-transmodal coupling, thalamic coupling, hierarchy-gradient flattening, and receptor-prior-weighted global coupling.

### H2: Control-Energy Landscape

LSD will show lower within-condition transition-control energy than placebo in a graph-control surrogate, consistent with a flattened macro-scale control-energy landscape.

### H3: Receptor-Specific Control Placement

Receptor-prior control profiles should require less energy than uniform, random, or degree-control profiles if the receptor-informed control claim is locally supported.

Current status: this is not yet supported. E shows lower LSD transition energy, but receptor-prior control does not beat uniform/random controls.

### H4: Dynamic Repertoire

LSD will show increased graph-theoretic integration and reduced modular segregation, but dynamic-FC variance and path-length metrics may be unstable or window-sensitive.

### H5: Predictive Baseline

DMDc condition inputs should improve held-out one-step prediction only if simple linear controlled dynamics capture useful condition structure.

Current status: this is negative. B is retained as a baseline/negative control, not as the main control-theory result.

## 4. Prediction Target

Primary target: rank candidate mechanism layers by signed alignment with paired empirical LSD-minus-placebo proxy targets.

Current candidate layers:

| Layer | Mechanism | Current role |
| --- | --- | --- |
| A | Transition-state proxy | State occupancy, dwell, switching, barrier-like summaries. |
| B | DMDc condition-interaction | Predictive controlled-dynamics baseline and negative control. |
| C | Hierarchy/routing | Main currently supported layer. |
| D | Dynamic repertoire / graph metrics | Supporting graph-dynamic evidence layer. |
| E | Network-control energy | Best control-theory layer, currently promising but incomplete. |

Secondary target: condition prediction or one-step trajectory prediction, only as a supporting benchmark and only with subject-disjoint validation.

## 5. Input Data / Features

Current empirical data:

- Cached ds003059 paired placebo/LSD empirical viewer records.
- 30 paired subject/run records.
- 15 subjects.
- Runs used in the current A+B+C+D+E ranking: run-01 and run-03.
- Run-02 music appears in the explorer but is not part of the primary ranking until motion/context checks are completed.

Current feature families:

- Coarse 8-module time series.
- Static and dynamic functional connectivity summaries.
- PCA-quantile macro-state labels.
- Transition entropy, transition rate, dwell time, and step-distance proxies.
- Hierarchy/routing metrics.
- Graph metrics: modularity, participation coefficient, global efficiency, integration/segregation.
- Finite-horizon network-control energy over a macro-module proxy graph.
- Coarse receptor-prior weights, explicitly labeled as non-PET proxy priors.

## 6. Scientific Contribution

The thesis contribution is not "AI discovers the true LSD mechanism."

The defensible contribution is:

> A transparent, reproducible, explainable framework for ranking control-theoretic and graph-dynamic surrogate mechanisms against paired psychedelic fMRI macro-dynamic proxy evidence, including nulls, negative baselines, and explicit claim boundaries.

This is scientifically useful because it turns vague mechanistic stories into testable mechanism-ranking hypotheses.

## 7. Practical Contribution

- A runnable local pipeline that produces ranking results, figures, CSV/XLSX exports, and a dashboard.
- A reviewer-facing evidence board showing which mechanisms are supported, weak, or contradicted.
- A thesis-safe interpretation framework that separates proxy evidence, assumptions, and unsupported claims.
- A reproducible demo suitable for presentation without claiming subjective-state realism or clinical validity.

## 8. Evaluation Metrics

### Main Ranking Metrics

- Signed effect size by metric.
- Sign consistency across paired subject/run records.
- Sign-test p-values as descriptive directional checks.
- Layer support score from predeclared signed components.

### Control-Energy Metrics

- LSD-vs-placebo transition-energy reduction under receptor and uniform control.
- Receptor-prior-vs-uniform energy reduction.
- Receptor-prior-vs-random-permutation energy reduction.
- Hierarchy/transmodal-vs-uniform energy reduction.
- Receptor-prior alignment with LSD-placebo target displacement.

### Baselines And Nulls

- Random ranking.
- Uniform control profile.
- Degree-control profile.
- Random receptor-prior permutations.
- DMDc no-input baseline.
- Subject-disjoint held-out validation where fitting is involved.

Still needed:

- Degree-preserving graph rewires.
- Spatial-autocorrelation-preserving receptor-map nulls.
- Window-size sensitivity for dynamic FC.
- Alternative state-labeling sensitivity for A/E.

## 9. Success Criteria

Minimum thesis-ready success:

- The project can be run end-to-end with documented commands.
- A+B+C+D+E results regenerate from cached data.
- CSV/XLSX exports and dashboard visualizations are produced.
- Claims are written at macro-dynamics/proxy level.
- C remains the strongest or one of the strongest layers under robustness checks.
- E cleanly separates two claims:
  - landscape flattening proxy: supported if LSD transition energy is lower;
  - receptor-specific control placement: supported only if receptor priors beat uniform/random/degree controls.
- B remains as a negative or supporting baseline, not as the main thesis claim.
- Limitations are explicit enough that a skeptical reviewer cannot accuse the project of hiding weak results.

Strong result:

- C and E remain high-ranked under subject/bootstrap splits and run sensitivity.
- Schaefer/Yeo extraction confirms C/D patterns beyond the 8-module proxy.
- A structural-connectome version of E preserves lower LSD transition energy and improves receptor-prior null comparisons.

Failure-but-still-valid result:

- If E fails under structural-connectome or receptor-map nulls, the thesis can still argue that the current macro-module proxy does not support receptor-specific control placement, while hierarchy/routing and graph-integration proxies remain better supported.

## 10. Risks And Unknowns

Critical risks:

- The current 8-module extraction is too coarse for strong network neuroscience claims.
- Current receptor priors are coarse proxy weights, not PET-derived receptor maps.
- E currently uses a macro-module proxy graph, not a structural connectome.
- Motion/confound sensitivity is not fully resolved.
- Run-02/music should not be used for primary claims until motion/context checks are complete.
- Dynamic-FC results may depend strongly on window size.
- PCA-quantile state labels may not be stable enough for final transition-energy claims.

Interpretation risks:

- A supportive ranking is not proof of a biological mechanism.
- A receptor-weighted metric is not receptor-level pharmacology.
- Lower control energy in a proxy graph is not automatically the same as true brain controllability.
- Subjective experience must not be inferred from these metrics.

## 11. Minimum Viable Thesis Version

MVP title:

> Explainable AI Ranking of Control-Theoretic Surrogate Mechanisms for LSD-Related Macro-Dynamics in fMRI

MVP scope:

1. Use cached ds003059 paired placebo/LSD run-01 and run-03 data.
2. Rank A+B+C+D+E layers.
3. Present C as strongest current support.
4. Present E as a split result: lower LSD transition energy, but no receptor-specific control-placement support yet.
5. Present B as negative-control baseline.
6. Export all results to CSV/XLSX.
7. Use the dashboard as the demo.
8. Include a model card, dataset card, limitations section, and defense slides.

MVP claim:

> In this dataset and proxy representation, hierarchy/routing and graph-control-energy summaries align better with LSD-placebo macro-dynamic differences than generic DMDc condition prediction, but receptor-specific network-control claims remain unproven.

## 12. Stronger / Ambitious Version

Ambitious version:

1. Replace the 8-module proxy with Schaefer/Yeo cortical parcels plus subcortical thalamic regions.
2. Add a normative structural connectome in the same parcellation.
3. Project PET-derived 5-HT2A receptor maps to the parcellation.
4. Re-run E as true receptor-informed network control theory.
5. Add graph-rewire and spatial receptor-map nulls.
6. Add HMM or clustering sensitivity for A/E states.
7. Add window-size sensitivity and dynamic-community robustness for D.
8. Add run-02/music only after motion and setting/context checks are completed.
9. Build a final dashboard page with:
   - mechanism ranking;
   - evidence matrix;
   - null comparisons;
   - failure cases;
   - thesis-safe interpretations.

Ambitious claim, only if supported:

> Receptor/hierarchy-informed network-control and graph-dynamic summaries provide a more defensible account of LSD-related macro-dynamic changes than generic linear prediction baselines, but remain surrogate evidence rather than biological proof.

## What We Know

- Current A+B+C+D+E ranking is implemented and exported.
- Current ranking: C first, E second, D third, A fourth, B fifth.
- B is negative and should stay as a baseline.
- E supports lower LSD transition energy but does not yet support receptor-specific control placement.
- The dashboard and exports can show the evidence rather than only describe it.

## What We Assume

- Coarse module time series are useful enough for a first-pass surrogate analysis.
- Signed proxy metrics can serve as a defensible ranking target if limitations are explicit.
- Literature-motivated priors are acceptable for exploratory proxy analyses when clearly labeled.

## What We Need To Test

1. Does C remain strong under subject/bootstrap/run sensitivity?
2. Does E remain supportive when state labels and horizon vary?
3. Does E improve when using a structural connectome instead of the macro graph?
4. Do receptor-map nulls weaken or strengthen the receptor-specific claim?
5. Does D survive window-size and dynamic-community sensitivity?
6. Can the full pipeline regenerate without permission/cache issues?

## What Can Go Wrong

- The stronger structural-connectome E version may weaken the current E result.
- Schaefer/Yeo extraction may change C/D conclusions.
- Motion or preprocessing confounds may explain part of the observed effects.
- The dataset may be too small for stable high-dimensional ML.
- The strongest thesis result may be negative: current receptor-specific claims are underconstrained.

That negative result is acceptable if the thesis is framed as mechanism-ranking and failure analysis rather than mechanism proof.
