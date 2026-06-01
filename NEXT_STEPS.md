# Next Steps

Date: 2026-05-20

## 2026-05-19 Updated Execution Order

The next loop is now:

1. Finish robustness on current LSD results.
2. Add `ds006072` psilocybin as the first real cross-drug expansion.
3. Upgrade E using HCP-derived structural connectivity.
4. Replace receptor proxies with `neuromaps` / FS5ht receptor maps.
5. Re-run C/D/E on Schaefer 100/200 and Yeo 7/17.
6. Compare final patterns to the 2026 Nature Medicine psychedelic mega-analysis, especially transmodal-unimodal coupling and striatal-unimodal effects.

The source plan for those steps is now exported through `results/thesis_evidence_loop/external_source_plan.csv` and `results/thesis_evidence_loop/external_source_plan.md`.

Dashboard rule:

> The dashboard must show implemented results, planned analyses, blocked analyses, scholarly anchors, export paths, and claim limitations in one evidence loop. It must not present planned psilocybin/HCP/receptor/Schaefer results as completed.

Hiring-readiness rule:

> Prioritize work that demonstrates research engineering maturity: reproducible data ingestion, clean models, uncertainty, nulls, XAI, visual evidence, and honest failure reporting.

## Current Project State

The thesis is now best framed as an explainable AI/ML mechanism-ranking project for LSD-related macro-dynamics.

Current implemented ranking:

1. C: hierarchy/routing proxy.
2. E: receptor-informed network-control energy proxy.
3. D: dynamic repertoire / graph metrics.
4. A: transition-state proxy.
5. B: DMDc predictive baseline / negative control.

Current strongest claim:

> Hierarchy/routing and graph-control-energy proxies currently align better with paired LSD-placebo macro-dynamic evidence than generic DMDc condition prediction.

Current key caveat:

> E supports lower LSD transition energy, but receptor-specific control placement is not supported against uniform/random controls yet.

Current atlas/data update:

> Schaefer 100/200 by Yeo 7/17 is now implemented as real `ds003059` parcellation sensitivity with 15 subjects and 30 paired LSD/placebo records in every cell. C remains the top layer in all four cells.

Current psilocybin update:

> `ds006072` metadata and file manifests are implemented under `data/ds006072/`. The raw rest BOLD candidate set is about 2.64 TB; the processed CIFTI candidate set is about 113.6 GB. A local Schaefer100/Yeo7 psilocybin/MTP stress test now exists under unchanged scoring, using the local processed CIFTIs and fsLR Schaefer labels. This upgrades the earlier structure-family pass, but the small-sample psilocybin ranking is not a clean replication of the LSD top layer and must stay framed as a negative/partial external result.

External-data rule:

> All new atlas and dataset files should be placed under `D:\LSD_Thesis` by default. Use `scripts/prepare_external_data.py`; do not let Nilearn/OpenNeuro defaults write into `C:\Users\...`.

## Biggest Bottleneck

The main blocker is not adding a more complex model. The blocker is making E and C/D robust enough that a skeptical reviewer cannot dismiss them as artifacts of the 8-module proxy, receptor placeholders, or metric choice.

## Highest-Leverage Next Actions

### 1. Robustness Check For Current A+B+C+D+E

Run sensitivity analyses before adding new modeling complexity.

Deliverables:

- Subject/bootstrap uncertainty for layer scores.
- Run split: run-01 vs run-03.
- E horizon sensitivity.
- A/E state-labeling sensitivity.
- D window-size sensitivity.
- Updated `summary.json`, CSV/XLSX exports, dashboard plots, and report.

Acceptance criterion:

- C and/or E remain defensible under at least two robustness axes, or the thesis clearly reports where they fail.

### 2. Structural-Connectome Upgrade For E

Replace the macro-module proxy graph with a normative structural-connectome graph in the same parcellation.

Deliverables:

- Graph input documentation.
- Graph provenance table.
- E rerun using structural graph.
- Uniform, degree-control, random, and graph-rewire nulls.

Acceptance criterion:

- We can say whether the E result survives a more defensible graph.

### 3. Receptor-Map Upgrade For E/C

Replace coarse receptor-prior weights with PET-derived or literature-documented 5-HT2A parcel weights.

Deliverables:

- Receptor-map provenance.
- Projection/parcellation method.
- Spatial null or permutation null.
- Updated E receptor-specific tests.

Acceptance criterion:

- Receptor-specific control placement is either supported against nulls or explicitly rejected.

### 4. Schaefer/Yeo Upgrade For C/D

Run a higher-resolution parcellation sensitivity pass.

Deliverables:

- Schaefer/Yeo extraction or documented blocked state.
- Hierarchy-gradient metrics.
- Modularity, participation, global efficiency, integration/segregation.
- Comparison against current 8-module results.

Acceptance criterion:

- C/D findings are not only artifacts of the 8-module anatomical proxy, or the limitation is reported plainly.

Current status:

- `schaefer_100_yeo_7`: implemented first pass.
- `schaefer_100_yeo_17`: implemented first pass.
- `schaefer_200_yeo_7`: implemented first pass.
- `schaefer_200_yeo_17`: implemented first pass.

### 5. Thesis-Ready Documentation Package

Turn the project into something defendable.

Deliverables:

- Dataset card.
- Model card.
- Evaluation report.
- Explainability report.
- Limitations table.
- Defense slide outline.
- Dashboard demo script.

Acceptance criterion:

- Every headline claim has an artifact, metric, source, and limitation attached to it.

## Concrete Task To Complete Today

Implement the robustness pass for current A+B+C+D+E before adding new data sources.

Suggested output:

- `scripts/run_dynamic_mechanism_robustness.py`
- `results/dynamic_mechanism_ranking/robustness/`
- `docs/stage_reports/dynamic_mechanism_robustness.md`
- Dashboard section for robustness checks.

## What To Avoid Right Now

- Do not build a neural network or LLM model for this thesis yet.
- Do not claim receptor-level mechanism from coarse receptor priors.
- Do not use run-02/music as primary evidence until motion/context checks are resolved.
- Do not hide B as a negative result.
- Do not optimize support scores by changing metric weights after seeing results.
- Do not write slides until the robustness story is stable.

## Thesis-Ready Decision Tree

If C and E survive robustness:

- Thesis story: hierarchy/routing plus control-energy flattening are the strongest surrogate explanations.

If C survives but E weakens:

- Thesis story: hierarchy/routing is supported; current graph-control evidence is underconstrained.

If E transition energy survives but receptor-specific control fails:

- Thesis story: landscape flattening proxy is plausible, but receptor-specific control placement is not locally supported.

If all layers weaken:

- Thesis story: the method is still valuable as a falsification framework, but the current dataset/representation cannot support the mechanistic claims.

## What To Send Next

Send one of these:

- "Do the robustness pass."
- "Upgrade E with structural connectome."
- "Upgrade receptor maps."
- "Prepare defense slides from current results."

My recommendation: do the robustness pass first.
