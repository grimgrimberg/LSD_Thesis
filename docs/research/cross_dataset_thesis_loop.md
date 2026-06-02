# Cross-Dataset Thesis Evidence Loop

Date: 2026-05-19

## Purpose

This document defines the stronger thesis loop: LSD first, robustness second, psilocybin/HCP/receptor/parcellation upgrades third, and scholarly comparison last. It is meant to keep the dashboard and final thesis honest while still making the project compelling.

## Thesis Goal

Build a reproducible explainable AI framework that ranks transparent control-theoretic and graph-dynamic surrogate mechanisms across LSD and psilocybin fMRI, then tests whether the strongest claims survive robustness, structural-connectome, receptor-map, atlas, and literature-benchmark checks.

## Evidence Ladder

| Order | Analysis | Dataset / Prior | Model Layer | Why It Matters | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | LSD robustness | OpenNeuro `ds003059` cached LSD/placebo records | A/B/C/D/E | Tests whether current C/E claims survive skepticism. | Implemented first pass |
| 2 | Psilocybin external stress test | OpenNeuro `ds006072` | A/C/D/E first, B optional | Tests cross-drug generalization under a richer psilocybin dataset. | Implemented Schaefer100/Yeo7 unchanged-scoring external stress test; top layer differs from LSD |
| 3 | Structural graph | HCP Young Adult diffusion/connectome data | E | Replaces macro-module proxy graph with a defensible structural prior. | Implemented HCP structural graph sensitivity; still a sensitivity/control layer, not biological proof |
| 4 | PET receptor priors | `neuromaps` / FS5ht receptor maps | C/E | Replaces hand-built receptor weights with documented receptor-map priors. | Implemented PET receptor-prior sensitivity and spatial-null map-prior checks; receptor/myelin/gradient claim remains negative/not promoted |
| 5 | Atlas sensitivity | Schaefer 100/200 and Yeo 7/17 | C/D/E | Tests whether findings are artifacts of the current 8-module proxy. | Full Schaefer 100/200 by Yeo 7/17 matrix implemented |
| 6 | Scholarly benchmark | 2026 psychedelic mega-analysis | C/D/E interpretation | Compares final patterns against transmodal-unimodal and striatal-unimodal literature targets. | Implemented directional proxy benchmark |

## Current Loop Result

Generated artifacts:

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
- `results/parcellation_sensitivity/schaefer_100_yeo_7/summary.json`
- `results/parcellation_sensitivity/schaefer_100_yeo_17/summary.json`
- `results/parcellation_sensitivity/schaefer_200_yeo_7/summary.json`
- `results/parcellation_sensitivity/schaefer_200_yeo_17/summary.json`
- `results/stage_2/parcellations/schaefer_100_yeo_7/empirical_viewer/`
- `data/ds006072/ds006072_func_manifest.json`
- `data/ds006072/ds006072_cifti_manifest.csv`
- `results/structural_connectome/proxy_graph_control_nulls.csv`
- `results/receptor_priors/proxy_receptor_null_board.csv`
- `results/external_data/external_data_manifest.json`
- `results/literature_benchmark/literature_benchmark_status.json`

Current verdicts:

| Claim | Current verdict | Evidence |
| --- | --- | --- |
| C hierarchy/routing is the strongest implemented LSD layer. | Supported first pass. | Subject-bootstrap rank-1 fraction = `0.848`. |
| E supports a landscape-flattening proxy. | Supported as proxy only. | Horizon sensitivity keeps LSD receptor-profile transition-energy reduction around `4.3%` to `4.8%`. |
| E supports receptor-specific control placement. | Not supported yet. | Receptor-vs-random energy reduction is negative, around `-14%` to `-15%`. |
| B DMDc is the main control-theory result. | Reject as main claim. | Bootstrap rank-1 fraction = `0.000`; keep B as a negative-control baseline. |
| 2026 Nature Medicine transmodal-unimodal benchmark is directionally addressed. | Directionally aligned in the current proxy. | C sensory-transmodal mean delta = `0.0473`. |
| 2026 Nature Medicine striatal/unimodal benchmark is addressed. | Not testable in current proxy. | No striatal parcel exists in the current 8-module representation. |
| Schaefer/Yeo sensitivity exists for C/D/E. | Implemented first pass. | All four cells have 15 subjects and 30 paired records. Top layer = C in Schaefer 100/200 with Yeo 7/17. |
| ds006072 is implemented as an external stress test. | Yes, with limits. | Three paired psilocybin/MTP subjects were extracted through Schaefer100/Yeo7 and scored with the locked ds003059 rule; ds006072 top layer = E while LSD reference top layer = C. |

## What We Know

- The current LSD A+B+C+D+E ranking has been implemented and exported.
- Schaefer 100/200 by Yeo 7/17 parcellation sensitivity has been implemented for local `ds003059` run-01/run-03 records.
- ds006072 metadata, raw functional manifest, processed-CIFTI manifest, Schaefer100/Yeo7 empirical viewer, and unchanged scoring summary have been implemented for a small-subject external stress test.
- HCP structural graph sensitivity and PET receptor-prior sensitivity are implemented as control/sensitivity layers, while receptor/myelin/gradient mechanism promotion remains unsupported.
- All new atlas/data roots are targeted under `D:\LSD_Thesis`; see `results/external_data/external_data_manifest.json`.
- Current ranking is C first, E second, D third, A fourth, B fifth.
- B is a negative predictive baseline and should remain visible.
- E currently supports a lower transition-energy proxy but does not support receptor-specific control placement against available nulls.

## What We Assume

- The current 8-module proxy is useful for an MVP but too coarse for final network-neuroscience claims.
- A cross-dataset psilocybin pass is more scientifically valuable than making the current LSD dashboard prettier.
- Receptor-specific claims require PET-derived or explicitly documented receptor maps.
- Structural-control claims require a structural graph, not only a macro-module proxy.

## What We Need To Test

1. Subject/bootstrap uncertainty for A/B/C/D/E.
2. Run-01 versus run-03 sensitivity.
3. E horizon sensitivity.
4. A/E state-labeling sensitivity.
5. D window-size sensitivity.
6. Whether the small-subject `ds006072` top-layer mismatch survives broader extraction or should remain a negative/partial external stress test.
7. Whether HCP structural graph sensitivity changes the E interpretation enough to downgrade the landscape-flattening proxy.
8. Whether neuromaps/FS5ht receptor projection and spatial nulls continue to reject receptor/myelin/gradient mechanism promotion.
9. Schaefer/Yeo sensitivity for C/D/E.
10. Agreement or disagreement with the 2026 psychedelic mega-analysis.

## What Can Go Wrong

- Robustness weakens C/E enough that the thesis becomes a falsification framework rather than a positive mechanism story.
- `ds006072` may stay negative/partial even after broader extraction, especially because the current small-subject stress test ranks E above C while the LSD reference ranks C first.
- HCP structural connectivity makes E weaker, not stronger.
- PET receptor maps fail against spatial nulls.
- Schaefer/Yeo changes the direction of C/D/E effects.
- The literature benchmark may support transmodal-unimodal coupling but not the local E control interpretation.

## Scholarly Anchors

| Source | Use In Project | Caveat |
| --- | --- | --- |
| Girn et al., Nature Medicine 2026, "An international mega-analysis of psychedelic drug effects on brain circuit function" | External benchmark for transmodal-unimodal and striatal/unimodal effects. | Data access is by request; use the paper as a benchmark unless raw data become available. |
| "Psilocybin's acute and persistent brain effects: a precision imaging drug trial", Scientific Data 2025 | `ds006072` psilocybin expansion. | Rich dataset; preprocessing and harmonization are nontrivial. |
| Singleton et al., Nature Communications 2022, receptor-informed network control theory | Main benchmark for E. | Their result does not validate this repo's proxy graph or receptor weights automatically. |
| Markello et al., Nature Methods 2022, `neuromaps` | Receptor and brain-map projection framework. | Requires careful parcellation and spatial nulls. |
| Human Connectome Project Young Adult | Structural-connectome graph source. | Access, data-use terms, and preprocessing choices must be documented. |
| Schaefer et al., Cerebral Cortex 2018 | Standard multiresolution parcellation sensitivity. | Cortical atlas does not solve subcortical/thalamic mapping by itself. |

## Dashboard Contract

The dashboard should expose:

- current A/B/C/D/E ranking;
- robustness status;
- psilocybin expansion status;
- structural graph status;
- receptor-map status;
- Schaefer/Yeo status;
- scholarly comparison status;
- exports and report links;
- claim guardrails and failure cases.

## Thesis-Ready Claim Template

> We built a reproducible explainable mechanism-ranking framework for psychedelic fMRI macro-dynamics. In the current LSD anchor dataset, hierarchy/routing and network-control-energy proxies are most promising, while DMDc is a negative baseline. The final claim depends on robustness, unchanged-scoring psilocybin stress tests, structural-connectome sensitivity, receptor-map nulls, atlas sensitivity, and comparison to recent mega-analytic findings.
