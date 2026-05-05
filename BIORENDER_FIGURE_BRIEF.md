# BioRender Figure Brief

BioRender access was not available in the local environment, so this is a BioRender-ready planning brief rather than a claim that final BioRender assets were created.

## Figure 1 - Conceptual Model

- Title: Transparent Macro-Dynamics Surrogate For Altered-State-Inspired Perturbations
- Caption: "A coarse eight-module graph surrogate is used to test macro-level perturbation hypotheses. It is not a receptor, clinical, or subjective-experience model."
- Layout: left `sober baseline graph`, center `perturbation knobs`, right `changed proxy dynamics`.
- Labels: within-module stability, cross-module coupling, hierarchy constraint, stochastic drive, switching barrier proxy.
- Style: neutral scientific palette; avoid psychedelic imagery.
- Code output feeds: `results/stage_1/figures/graph_overview.html`, Stage 1 summaries.
- Safe wording: "altered-state-inspired macro perturbation", "proxy metrics".

## Figure 2 - Computational Pipeline

- Title: Data-To-Surrogate Pipeline
- Caption: "Public ds003059 resting-state runs are reduced to coarse module summaries and compared with surrogate-model outputs."
- Layout: OpenNeuro ds003059 -> rest-run filter -> 8-module extraction -> target summaries -> model fit -> perturbation ranking.
- Labels: run-01/run-03, ses-PLCB, ses-LSD, empirical targets, model deltas.
- Code output feeds: `results/stage_2/*.yaml`, `results/stage_2/*summary*.json`.
- Safe wording: "coarse empirical summary", "paired LSD-minus-placebo delta".

## Figure 3 - Results And Metrics

- Title: Proxy Metric Alignment And Mismatch
- Caption: "The model is evaluated by mismatch to empirical summary deltas, with sign conflicts reported directly."
- Layout: empirical delta bar plot, model delta bar plot, mismatch score ranking, seed-panel uncertainty.
- Labels: entropy-like proxy, cross-module communication, thalamic coupling, metastability proxy.
- Code output feeds: Stage 2 metric deltas, Stage 3 rankings, Stage 4 ablations.
- Safe wording: "ranked hypothesis toggles", "mismatch analysis".

## Figure 4 - Thesis/Paper Framing

- Title: What The Prototype Supports And Does Not Support
- Caption: "The prototype supports transparent macro-scale hypothesis ranking, not mechanistic claims about receptors or subjective psychedelic experience."
- Layout: supported claims column, limitations column, next validation column.
- Labels: implemented, proxy, speculative, out of scope.
- Code output feeds: `THESIS_CONCEPT_AUDIT.md`, `AUDIT.md`, `METRICS.md`.
- Safe wording: "transparent surrogate", "macro-scale analogue", "requires empirical validation".
