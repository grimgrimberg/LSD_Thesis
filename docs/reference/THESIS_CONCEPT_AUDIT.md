# Thesis Concept Audit

## 0. 2026-05-19 Thesis-Readiness Update

Implemented since the original audit: the project now has an A+B+C+D+E mechanism-ranking pass with exported JSON, CSV/XLSX, dashboard plots, and a markdown report.

Current result:

1. C hierarchy/routing proxy is strongest.
2. E receptor-informed network-control energy proxy is second.
3. D dynamic repertoire / graph metrics is third.
4. A transition-state proxy is fourth.
5. B DMDc condition-interaction is a negative predictive baseline.

Current thesis-safe interpretation:

- Supported: hierarchy/routing-style FC proxies align best with the current paired LSD-placebo macro-dynamic evidence.
- Partly supported: E shows lower LSD within-condition transition energy, consistent with a flattened control-energy landscape proxy.
- Not yet supported: receptor-prior control does not beat uniform/random control profiles, so receptor-specific control placement remains unproven.
- Negative baseline: DMDc does not improve held-out one-step prediction, so it should remain a baseline rather than the core control-theory claim.

Current main missing work:

- Robustness for A+B+C+D+E under subject/bootstrap, run split, E horizon, A/E state labeling, and D window-size sensitivity.
- Structural-connectome upgrade for E.
- PET-derived or otherwise documented receptor-map upgrade for E/C.
- Schaefer/Yeo sensitivity for C/D.
- Degree-preserving graph rewires and spatial receptor-map nulls.

## 1. Current Thesis Idea

Implemented: the repo builds a transparent 8-module stochastic graph-coupled surrogate model and compares macro-level simulated observables with coarse ds003059 resting-state summaries.

Proposed current framing: the thesis should become a dynamic method between LSD neuroimaging, control theory, and AI. The main AI task should be mechanism ranking: estimate which transparent perturbation mechanisms or parameter families best align with empirical LSD-minus-placebo proxy targets, while preserving the possibility that the current macro-dynamic assumptions fail.

## 2. Explicit Hypothesis

Inferred: simple graph-level perturbations such as stronger cross-module coupling, relaxed hierarchy, increased stochasticity, or lowered switching barriers can be ranked by how well they move surrogate macro-dynamics toward empirical LSD-minus-placebo deltas.

Proposed:

- H1: Control-theoretic surrogate perturbations produce distinguishable proxy-metric deltas, but only some will align with empirical LSD-minus-placebo targets.
- H2: A leakage-controlled AI/ML ranking model can prioritize candidate perturbation mechanisms better than random ranking, seed-noise nulls, and simple single-metric heuristics.
- H3: A negative or unstable ranking is scientifically useful because it identifies where the current macro-dynamics story is wrong or underconstrained.
- Supporting benchmark: placebo/rest baseline versus LSD/perturbed condition prediction can be included, but only as secondary evidence.

## 3. Implied Computational Model

Implemented: eight latent modules evolve with bistable local drive, rigidity toward baseline, adaptation, graph coupling, hierarchy projection, and stochastic noise. The documented equation is in `SPEC.md`.

## 4. Scientific Assumptions

- Implemented: ds003059 resting-state runs can be reduced to eight coarse macro-module time series.
- Inferred: group summary metrics are useful empirical anchors for a transparent surrogate.
- Speculative: the chosen perturbation knobs capture meaningful macro analogues of altered-state dynamics.

## 5. Engineering Assumptions

- Implemented: YAML configs define graph and regimes.
- Implemented: fixed seeds support deterministic simulation tests.
- Proposed: keep all generated outputs reproducible from commands and avoid committing raw data.

## 6. What Is Currently Implemented

- Synthetic stage 1 simulator, metrics, figures, and report.
- ds003059 manifest/extraction path, target payloads, atlas audit, data quality summaries, empirical viewer cache, and sober fit.
- Perturbation ranking with one-shot and seed-panel robustness.
- Ablation ranking.
- FastAPI dashboard payloads and templates.
- Publication package and training benchmark scaffolds.

## 7. What Is Missing

- Proposed: stricter repo hygiene guard against accidentally ignored source.
- Proposed: clearer root-level audit documentation and command report.
- Proposed: atlas sensitivity analysis beyond the current Harvard-Oxford proxy.
- Proposed: optimized or marked slow metric-heavy tests.
- Proposed: stronger thesis figure storyboard and reproducibility package.

## 8. What Is Hand-Wavy

- Present but broken: Stage 1 perturbed config increased entropy and switching but decreased static cross-group FC and did not increase dynamic FC change.
- Described only: some literature-style target signs are used as qualitative anchors, not fully validated targets.
- Speculative: mapping model perturbation mechanisms to biological mechanisms.
- Implemented first pass: the A+B+C+D+E ranking target, candidate mechanism space, and first null baselines are now explicit.
- Still underdefined for final thesis: robustness weighting, structural-connectome nulls, PET receptor-map nulls, and Schaefer/Yeo sensitivity.
- Risk: "AI finds the dynamics" is not defensible unless the dynamics are defined as a constrained hypothesis space with explicit failure criteria.

## 9. More Thesis-Worthy

- Implement fixed seed panels for all model comparisons.
- Report sign conflicts and failures as first-class results.
- Add atlas sensitivity or at least a stronger atlas audit table.
- Separate empirical target extraction, model fit, perturbation response, and mismatch analysis in figures.

## 10. More Paper-Worthy

- Add preregistered metric definitions and robustness checks.
- Compare against simple null models and seed-noise nulls.
- Provide exact data provenance and regeneration commands.
- Add a concise narrative that emphasizes mismatch analysis over mechanism proof.

## 11. Risks Of Overclaiming Neuroscience Validity

- The model is not receptor-level, pharmacokinetic, clinical, or phenomenological.
- The 8-module anatomical extraction is transparent but not canonical.
- KMeans-derived switching/metastability proxies are sensitive to clustering and seed choices.
- Some ds003059 deltas conflict with literature-style target signs.

## 12. Honest Framing

Implemented: a macro-scale computational surrogate for graph-modulated dynamics. The safest claim is that it can rank simple perturbation hypotheses by mismatch to coarse empirical summaries.

Updated thesis-safe framing: the project uses AI/ML to rank control-theoretic surrogate mechanisms against empirical macro-dynamics targets. It does not discover true LSD mechanisms directly; it tests whether a constrained set of transparent mechanisms is consistent with observed proxy summaries.

## 13. Claims That Can Be Made Safely

- The simulator is deterministic for fixed seeds.
- The pipeline produces stage summaries, figures, and dashboard payloads.
- Under the current extraction, 15 paired subjects and 60 resting runs are summarized.
- Current ds003059 deltas align with some target directions and conflict with others.

## 14. Claims Requiring Empirical Validation

- Any claim that a perturbation reflects a real biological LSD mechanism.
- Any claim about subjective experience.
- Any claim that the 8-module mapping is a canonical network definition.
- Any generalization beyond the local ds003059 extraction and current preprocessing.

## 15. What Should Be Shown Visually

- 8-module graph.
- Sober versus perturbed time series and FC matrices.
- ds003059 placebo versus LSD metric deltas with sign conflicts.
- Mechanism ranking with seed-panel uncertainty.
- Ablation ranking and pairwise heatmap.
- Pipeline diagram from raw/public data to targets to model to mismatch.

## 16. What Should Be Demonstrated Experimentally

- Fixed-seed reproducibility.
- Sober fit improvement against targets.
- Perturbation deltas versus empirical deltas.
- Seed-noise null comparison.
- Atlas mapping audit and sensitivity plan.
- Robustness across parameter sweeps.
- Mechanism-ranking performance against random ranking, single-metric heuristics, and seed-noise nulls.
- Subject-disjoint condition-prediction benchmark as a supporting experiment, not the main thesis claim.
- Fold-local preprocessing for any fitted ML/XAI pipeline.
