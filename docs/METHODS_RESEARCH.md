# Methods Research

Date: 2026-05-12

Scope: PASS 1 literature and tooling scan for the Set / Setting / Seed extension. This file records sources and how they can or cannot be used in the thesis. It is not a claim that every method should be implemented.

## 1. Predictive Processing / REBUS / Entropic Brain

### Carhart-Harris and Friston 2019

- Title: REBUS and the Anarchic Brain: Toward a Unified Model of the Brain Action of Psychedelics
- Source type: review / theory paper
- Link: https://doi.org/10.1124/pr.118.017160
- Use in thesis: motivates cautious language about relaxed high-level priors and altered precision as a conceptual frame for `hierarchy_precision_only`.
- Cannot be used as: proof that the current module surrogate measures priors directly.

### Carhart-Harris et al. 2014

- Title: The Entropic Brain: A Theory of Conscious States Informed by Neuroimaging Research with Psychedelic Drugs
- Source type: theory / review paper
- Link: https://doi.org/10.3389/fnhum.2014.00020
- Use in thesis: background for entropy-like and metastability proxies.
- Cannot be used as: support for unqualified claims that entropy increased in this repo, especially because the current `entropy_diversity` target is near zero and negative.

### Carhart-Harris 2018

- Title: The entropic brain - revisited
- Source type: review / theory paper
- Link: https://doi.org/10.1016/j.neuropharm.2018.03.010
- Use in thesis: updated entropic-brain context and caution around altered-state complexity.
- Cannot be used as: validation that a specific model mechanism is biologically correct.

### Friston 2010

- Title: The free-energy principle: a unified brain theory?
- Source type: review / theory paper
- Link: https://doi.org/10.1038/nrn2787
- Use in thesis: broad predictive-processing context for priors, prediction error, and control-like interpretations.
- Cannot be used as: direct empirical evidence for LSD-specific dynamics.

## 2. Psychedelic fMRI Methodological Heterogeneity

### Carhart-Harris et al. 2016

- Title: Neural correlates of the LSD experience revealed by multimodal neuroimaging
- Source type: primary paper
- Link: https://doi.org/10.1073/pnas.1518377113
- Use in thesis: primary context for the dataset and LSD neuroimaging findings.
- Cannot be used as: permission to infer subjective content from the current surrogate.

### Luppi et al. 2021

- Title: LSD alters dynamic integration and segregation in the human brain
- Source type: primary paper
- Link: https://doi.org/10.1016/j.neuroimage.2020.117653
- Use in thesis: supports dynamic integration/segregation framing and motivates dynamic FC/HMM-style analyses.
- Cannot be used as: proof that the current eight-module metrics exactly reproduce the paper's methods.

### Lord et al. 2019

- Title: Dynamical exploration of the repertoire of brain networks at rest is modulated by psilocybin
- Source type: primary paper
- Link: https://doi.org/10.1016/j.neuroimage.2019.05.060
- Use in thesis: cross-psychedelic dynamic repertoire context.
- Cannot be used as: direct evidence for LSD-specific conclusions in `ds003059`.

### Daws et al. 2022

- Title: Increased global integration in the brain after psilocybin therapy for depression
- Source type: primary clinical neuroimaging paper
- Link: https://doi.org/10.1038/s41591-022-01744-z
- Use in thesis: background that psychedelic-related integration can be studied at network level.
- Cannot be used as: clinical support for this LSD surrogate or any treatment claim.

### Siegel et al. 2025

- Title: A precision functional atlas of personalized psychedelic responses
- Source type: primary / dataset paper
- Link: https://doi.org/10.1038/s41597-025-05189-0
- Use in thesis: recent methodological context for personalized psychedelic neuroimaging and subject-specific response structure.
- Cannot be used as: evidence unless its dataset and methods are separately reviewed in detail.

## 3. LSD, Music, And Setting Effects

### Kaelen et al. 2015

- Title: LSD enhances the emotional response to music
- Source type: primary paper
- Link: https://doi.org/10.1007/s00213-015-4014-y
- Use in thesis: supports treating music as a relevant external context or setting variable.
- Cannot be used as: proof that this repo's current cached data contain music-run module time series.

### Kaelen et al. 2018

- Title: The hidden therapist: evidence for a central role of music in psychedelic therapy
- Source type: primary / theory-linked paper
- Link: https://doi.org/10.1007/s00213-017-4820-5
- Use in thesis: supports careful discussion of music as setting and context.
- Cannot be used as: clinical outcome evidence for this project.

### Hartogsohn 2016

- Title: Set and setting, psychedelics and the placebo response
- Source type: review / theory paper
- Link: https://doi.org/10.1177/0269881116677852
- Use in thesis: conceptual grounding for set and setting.
- Cannot be used as: direct neuroimaging evidence.

### Hartogsohn 2017

- Title: Constructing drug effects: A history of set and setting
- Source type: historical / theory paper
- Link: https://doi.org/10.1177/2050324516683325
- Use in thesis: philosophical and historical framing.
- Cannot be used as: quantitative support for any model score.

### Carhart-Harris et al. 2015

- Title: LSD enhances suggestibility in healthy volunteers
- Source type: primary paper
- Link: https://doi.org/10.1007/s00213-014-3714-z
- Use in thesis: context for altered sensitivity to external guidance.
- Cannot be used as: direct support for music-input gain without empirical run-02 analyses.

## 4. Thalamocortical Routing And Sensory Gating Under Psychedelics

### Preller et al. 2018

- Title: Changes in global and thalamic brain connectivity in LSD-induced altered states of consciousness are attributable to the 5-HT2A receptor
- Source type: primary paper
- Link: https://doi.org/10.7554/eLife.35082
- Use in thesis: supports thalamic connectivity and sensory-gating context.
- Cannot be used as: receptor-level validation of this model unless receptor maps are explicitly added as priors.

### Preller et al. 2019

- Title: Effective connectivity changes in LSD-induced altered states of consciousness in humans
- Source type: primary paper
- Link: https://doi.org/10.1073/pnas.1815129116
- Use in thesis: supports routing/effective-connectivity framing.
- Cannot be used as: proof that this repo's cross-network metric measures effective connectivity.

### Bedford et al. 2023

- Title: Altered thalamocortical and intra-thalamic functional connectivity during salvinorin-A induced dissociation
- Source type: primary paper
- Link: https://doi.org/10.1038/s41386-023-01574-8
- Use in thesis: broader altered-state thalamocortical context.
- Cannot be used as: LSD-specific evidence.

### Doss et al. 2022

- Title: Models of psychedelic drug action: modulation of cortical-subcortical circuits
- Source type: review / primary synthesis
- Link: https://doi.org/10.1016/j.neuroimage.2022.119434
- Use in thesis: cautious discussion of cortical-subcortical routing.
- Cannot be used as: direct validation of the eight-module thalamic gateway proxy.

## 5. Network Control Theory / Control Energy Under LSD Or Psilocybin

### Gu et al. 2015

- Title: Controllability of structural brain networks
- Source type: primary methods paper
- Link: https://doi.org/10.1038/ncomms9414
- Use in thesis: background for network controllability and control-energy concepts.
- Cannot be used as: direct support for a functional module-level LSD control-energy estimate.

### Betzel et al. 2016

- Title: Optimally controlling the human connectome: the role of network topology
- Source type: primary methods paper
- Link: https://doi.org/10.1038/srep30770
- Use in thesis: control-energy motivation and topology/control framing.
- Cannot be used as: validation of the current empirical target deltas.

### Bassett and Sporns 2017

- Title: Network neuroscience
- Source type: review
- Link: https://doi.org/10.1038/nn.4502
- Use in thesis: broad network-neuroscience vocabulary.
- Cannot be used as: method-specific validation.

### Singleton et al. 2022

- Title: LSD flattens the brain's control energy landscape: evidence from receptor-informed network control theory
- Source type: primary paper
- Link: https://doi.org/10.1038/s41467-022-33578-1
- Use in thesis: directly relevant prior for control-energy language and receptor-informed analyses.
- Cannot be used as: support for receptor-level claims in this repo unless receptor maps are actually added and separated as priors.

## 6. Latent Diffusion As Analogy For Guided Stochastic Latent Processes

### Ho et al. 2020

- Title: Denoising Diffusion Probabilistic Models
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.2006.11239
- Use in thesis: analogy for iterative stochastic latent sampling.
- Cannot be used as: biological evidence.

### Rombach et al. 2022

- Title: High-Resolution Image Synthesis with Latent Diffusion Models
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.2112.10752
- Use in thesis: analogy for latent-space guided generation.
- Cannot be used as: claim that brain dynamics are image diffusion.

### Ho and Salimans 2022

- Title: Classifier-Free Diffusion Guidance
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.2207.12598
- Use in thesis: analogy for guidance strength and conditioning.
- Cannot be used as: literal analogy for music, priors, or thalamic routing.

### Song et al. 2021

- Title: Score-Based Generative Modeling through Stochastic Differential Equations
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.2011.13456
- Use in thesis: mathematical background for stochastic differential generative systems.
- Cannot be used as: direct model of BOLD dynamics.

## 7. Dynamic FC, HMMs, Latent State-Space Methods

### Hutchison et al. 2013

- Title: Dynamic functional connectivity: promise, issues, and interpretations
- Source type: review
- Link: https://doi.org/10.1016/j.neuroimage.2013.05.079
- Use in thesis: cautionary framing for dynamic FC interpretation.
- Cannot be used as: proof that short-window dynamics are reliable in this dataset.

### Calhoun et al. 2014

- Title: The chronnectome: time-varying connectivity networks as the next frontier in fMRI data discovery
- Source type: review
- Link: https://doi.org/10.1016/j.neuron.2014.10.015
- Use in thesis: background for time-varying connectivity and dynamic network methods.
- Cannot be used as: direct validation of any one windowing choice.

### Baker et al. 2014

- Title: Fast transient networks in spontaneous human brain activity
- Source type: primary paper
- Link: https://doi.org/10.7554/eLife.01867
- Use in thesis: background for transient state/event-like dynamics.
- Cannot be used as: guarantee that eight-module LSD runs support the same timescale.

### Vidaurre et al. 2017

- Title: Brain network dynamics are hierarchically organized in time
- Source type: primary paper
- Link: https://doi.org/10.1073/pnas.1705120114
- Use in thesis: motivates HMM/state-dwell summaries.
- Cannot be used as: direct evidence for this dataset without implementation and validation.

## 8. DMD, DMDc, Koopman With Control

### Schmid 2010

- Title: Dynamic mode decomposition of numerical and experimental data
- Source type: primary methods paper
- Link: https://doi.org/10.1017/S0022112010001217
- Use in thesis: foundation for DMD summaries.
- Cannot be used as: evidence that DMD modes are neural mechanisms.

### Proctor, Brunton, and Kutz 2016

- Title: Dynamic Mode Decomposition with Control
- Source type: primary methods paper
- Link: https://doi.org/10.1137/15M1013857
- Use in thesis: foundation for modeling substance/run/music as control inputs.
- Cannot be used as: reason to skip subject-disjoint validation.

### Brunton et al. 2022

- Title: Modern Koopman Theory for Dynamical Systems
- Source type: review / methods paper
- Link: https://doi.org/10.1137/21M1401243
- Use in thesis: Koopman framing for linear representations of nonlinear dynamics.
- Cannot be used as: justification for overinterpreting learned observables.

### Ichinaga et al. 2024

- Title: PyDMD: A Python package for robust dynamic mode decomposition
- Source type: package paper
- Link: https://jmlr.org/papers/v25/24-0739.html
- Use in thesis: package citation if PyDMD is added in PASS 2.
- Cannot be used as: scientific validation by itself.

### PyDMD Documentation

- Title: PyDMD documentation
- Source type: package docs
- Link: https://pydmd.github.io/PyDMD/
- Use in thesis: implementation reference for `DMDc(svd_rank=-1).fit(snapshots, u)` and reconstruction with control inputs.
- Cannot be used as: thesis evidence.

## 9. SINDy / SINDy With Control

### Brunton, Proctor, and Kutz 2016

- Title: Discovering governing equations from data by sparse identification of nonlinear dynamical systems
- Source type: primary methods paper
- Link: https://doi.org/10.1073/pnas.1517384113
- Use in thesis: foundation for sparse dynamical-system discovery.
- Cannot be used as: evidence that small-N fMRI can recover true governing equations.

### de Silva et al. 2020

- Title: PySINDy: A Python package for the sparse identification of nonlinear dynamical systems from data
- Source type: package paper
- Link: https://doi.org/10.21105/joss.02104
- Use in thesis: package citation if PySINDy is added.
- Cannot be used as: validation of biological mechanism.

### Kaptanoglu et al. 2022

- Title: PySINDy: A comprehensive Python package for robust sparse system identification
- Source type: package paper
- Link: https://doi.org/10.21105/joss.03994
- Use in thesis: current package-method reference.
- Cannot be used as: substitute for tests on synthetic and held-out data.

### Kaiser, Kutz, and Brunton 2018

- Title: Sparse identification of nonlinear dynamics for model predictive control in the low-data limit
- Source type: primary methods paper
- Link: https://doi.org/10.1098/rspa.2018.0335
- Use in thesis: low-data SINDy-with-control caution and motivation.
- Cannot be used as: guarantee that current fMRI data are enough for nonlinear discovery.

### PySINDy Documentation

- Title: PySINDy documentation
- Source type: package docs
- Link: https://pysindy.readthedocs.io/
- Use in thesis: implementation reference for `model.fit(x_train, u=u_train, t=dt)` and control libraries.
- Cannot be used as: empirical evidence.

## 10. Neural ODE / Neural CDE / Neural SDE

### Chen et al. 2018

- Title: Neural Ordinary Differential Equations
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.1806.07366
- Use in thesis: optional exploratory sequence-model background.
- Cannot be used as: first-line method for small-N validation.

### Rubanova et al. 2019

- Title: Latent Ordinary Differential Equations for Irregularly-Sampled Time Series
- Source type: primary ML paper
- Link: https://proceedings.neurips.cc/paper/2019/hash/42a6845a557bef704ad8ac9cb4461d43-Abstract.html
- Use in thesis: optional latent state-space modeling context.
- Cannot be used as: justification for high-capacity models without nested validation.

### Kidger et al. 2020

- Title: Neural Controlled Differential Equations for Irregular Time Series
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.2005.08926
- Use in thesis: optional CDE framing for controlled time series.
- Cannot be used as: core PASS 2 method unless simple baselines fail.

### Li et al. 2020

- Title: Scalable Gradients for Stochastic Differential Equations
- Source type: primary ML paper
- Link: https://doi.org/10.48550/arXiv.2001.01328
- Use in thesis: optional neural SDE background.
- Cannot be used as: support for overfitting small fMRI datasets.

### torchdiffeq, torchcde, torchsde, Diffrax

- Source type: package docs
- Links:
  - https://github.com/rtqichen/torchdiffeq
  - https://github.com/patrick-kidger/torchcde
  - https://github.com/google-research/torchsde
  - https://docs.kidger.site/diffrax/
- Use in thesis: implementation options only if PASS 2 explicitly adds neural differential models.
- Cannot be used as: evidence for scientific claims.

## 11. Small-N ML Validation And Leakage Control

### Varma and Simon 2006

- Title: Bias in error estimation when using cross-validation for model selection
- Source type: primary methods paper
- Link: https://doi.org/10.1186/1471-2105-7-91
- Use in thesis: supports nested validation or fixed hyperparameter requirements.
- Cannot be used as: a recipe by itself; implementation tests still needed.

### Kriegeskorte et al. 2009

- Title: Circular analysis in systems neuroscience: the dangers of double dipping
- Source type: methods warning paper
- Link: https://doi.org/10.1038/nn.2303
- Use in thesis: explicit anti-leakage justification.
- Cannot be used as: evidence that all leakage is solved.

### Varoquaux 2018

- Title: Cross-validation failure: Small sample sizes lead to large error bars
- Source type: methods paper
- Link: https://doi.org/10.1016/j.neuroimage.2017.06.061
- Use in thesis: small-N caution for neuroimaging ML.
- Cannot be used as: reason to avoid validation; it motivates more cautious validation.

### Kapoor and Narayanan 2023

- Title: Leakage and the reproducibility crisis in machine-learning-based science
- Source type: review / methods paper
- Link: https://doi.org/10.1016/j.patter.2023.100804
- Use in thesis: modern leakage-control framing.
- Cannot be used as: proof that the repo is leakage-free.

## 12. Dashboard/UI Inspiration

### FastAPI Documentation

- Title: FastAPI templates and response documentation
- Source type: official docs
- Link: https://fastapi.tiangolo.com/
- Use in thesis/repo: current dashboard stack already uses FastAPI and Jinja2; PASS 2 should extend it instead of migrating frameworks.
- Cannot be used as: scientific evidence.

### Plotly Documentation

- Title: Plotly JavaScript and Python documentation
- Source type: official docs
- Link: https://plotly.com/
- Use in thesis/repo: interactive dashboard figures and local browser-friendly visuals.
- Cannot be used as: validation evidence.

### Streamlit, Dash, Panel, And Bokeh Documentation

- Source type: official docs
- Links:
  - https://docs.streamlit.io/
  - https://dash.plotly.com/
  - https://panel.holoviz.org/
  - https://docs.bokeh.org/
- Use in thesis/repo: design inspiration for status cards, selectors, and linked plots.
- Cannot be used as: reason to rewrite the existing FastAPI dashboard during PASS 2 unless a clear repo need emerges.

## 13. 2026-05-14 Life Science Research Additions

These additions came from a targeted Life Science Research routed literature pass for the current Set / Setting / Seed roadmap. They should tighten the thesis framing without loosening the guardrails.

| Source | Type | Link / DOI | Use in thesis | Cannot be used as |
|---|---|---|---|---|
| Carhart-Harris and Friston 2019, REBUS and the Anarchic Brain | review / theory | https://doi.org/10.1124/pr.118.017160 | Predictive-processing and prior-precision framing for "guidance" and "set" language. | Direct evidence for this dataset or proof that the model captures subjective experience. |
| Carhart-Harris et al. 2016, Neural correlates of the LSD experience revealed by multimodal neuroimaging | primary LSD neuroimaging paper | https://doi.org/10.1073/pnas.1518377113 | Background for modern LSD neuroimaging and multimodal measurement heterogeneity. | A license to claim consciousness simulation or clinical prediction. |
| Tagliazucchi et al. 2016, Increased Global Functional Connectivity Correlates with LSD-Induced Ego Dissolution | primary LSD fMRI paper | https://pubmed.ncbi.nlm.nih.gov/27085214/ | Context for cross-network communication as a plausible rest target. | Proof that the repo's 8-module proxy captures ego dissolution or subjective content. |
| Preller et al. 2018, Changes in global and thalamic brain connectivity in LSD-induced altered states are attributable to the 5-HT2A receptor | primary LSD fMRI paper | https://doi.org/10.7554/eLife.35082 | Context for thalamocortical routing and thalamic coupling hypotheses. | Receptor-mechanism proof for this repo unless receptor maps are explicitly added as priors. |
| Kaelen et al. 2016, LSD modulates music-induced imagery via changes in parahippocampal connectivity | primary LSD + music fMRI paper | https://doi.org/10.1016/j.euroneuro.2016.03.018 | Supports music/setting as a real empirical design axis and motivates run-02 extraction. | Evidence for current repo music-control effects while run-02 module time series are absent. |
| Atasoy et al. 2017, Connectome-harmonic decomposition of human brain activity reveals dynamical repertoire re-organization under LSD | primary LSD dynamics paper | https://doi.org/10.1038/s41598-017-17546-0 | Supports dynamical-repertoire language and the importance of stimulus/music conditions. | Justification to replace current transparent module metrics with unvalidated high-complexity representations. |
| Singleton et al. 2022, Receptor-informed network control theory links LSD and psilocybin to a flattening of the brain's control energy landscape | primary control-theory paper | https://doi.org/10.1038/s41467-022-33578-1 | Strong methodological precedent for control-energy landscape questions. | Direct validation of the repo's lower-barrier mechanism or any receptor-level claim. |
| Mediano et al. 2024, Effects of External Stimulation on Psychedelic State Neurodynamics | primary external-stimulation paper | https://doi.org/10.1021/acschemneuro.3c00289 | Supports the scientific value of context/stimulus manipulations and dashboard setting controls. | Current empirical evidence in this repo until run-02 and motion summaries are available. |
| Dynamic functional connectivity review papers | review / methods | https://pmc.ncbi.nlm.nih.gov/articles/PMC3807588/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC6130444/ | Cautionary methods background for dynamic FC, HMM, metastability, and sliding-window interpretations. | Proof that any one dynamic metric is biologically privileged. |
| Varoquaux 2018 and neuroimaging leakage literature | methods / validation | https://doi.org/10.1016/j.neuroimage.2017.06.061 | Supports subject-disjoint validation and wide uncertainty language for small-N ML. | A reason to skip validation; it motivates stricter validation. |

## Research Synthesis For PASS 2

1. Use REBUS, entropic brain, and predictive processing as philosophical context, not direct measurement claims.
2. Treat music as an external setting/control input only after run-02 data are extracted and music exclusions are enforced.
3. Prioritize routing and thalamic coupling because those are the strongest current empirical targets.
4. Use DMDc and simple control summaries before high-capacity neural differential models.
5. Keep all fitted transforms fold-local in validation.
6. Maintain dashboard caveats so users see data availability, proxy status, and validation status.

## 14. 2026-05-17 Life Science Research Framing Check

This check used the Life Science Research routing workflow plus targeted PubMed/Entrez and primary-source lookups. The goal was to test whether the current markdown framing supports a thesis centered on LSD, control theory, and AI.

### Working Conclusion

The current markdown is mostly scientifically cautious, but the goal should be reframed away from "AI discovers LSD dynamics" and toward "AI-assisted ranking of transparent control-theoretic surrogate mechanisms against empirical proxy targets."

### Evidence Updates

| Source | Type | Link / DOI | Use in thesis | Cannot be used as |
|---|---|---|---|---|
| Girn et al. 2026, An international mega-analysis of psychedelic drug effects on brain circuit function | primary mega-analysis | https://doi.org/10.1038/s41591-026-04287-9 | Current benchmark for broad psychedelic rsfMRI circuit findings, including transmodal-unimodal coupling and subcortical sensorimotor involvement. | Proof that this repo's 8-module proxy is sufficient or that mechanisms are settled. |
| Singleton et al. 2022, Receptor-informed network control theory links LSD and psilocybin to a flattening of the brain's control energy landscape | primary control-theory paper | https://doi.org/10.1038/s41467-022-33578-1 | Strong precedent for using recurrent states, transition energy, and receptor-informed control language in psychedelic neuroimaging. | Direct validation of this repo's barrier proxy unless structural-connectome and receptor-map assumptions are implemented and validated. |
| Gu et al. 2015, Controllability of structural brain networks | primary methods paper | https://doi.org/10.1038/ncomms9414 | Foundational network-control framing for state transitions over structural brain networks. | Direct evidence for LSD, functional-only module control, or small-N mechanism discovery. |
| Adamska and Finc 2023, Effect of LSD and music on the time-varying brain dynamics | primary LSD + music fMRI paper | https://doi.org/10.1007/s00213-023-06394-8 | Supports treating music as a setting/control input in `ds003059` and motivates run-02 extraction. | Current repo evidence for music-control effects before run-02 module time series and exclusions exist. |
| Dai et al. 2023, Classical and non-classical psychedelic drugs induce common network changes in human cortex | primary fMRI paper | https://doi.org/10.1016/j.neuroimage.2023.120097 | Supports between-network and within-network connectivity targets with `ds003059` as one input dataset. | A guarantee that current local target signs will match all literature findings. |

### Implications For The Current Markdown

1. `GOAL.md` should explicitly center mechanism ranking, with condition prediction as a supporting experiment.
2. `THESIS_CONCEPT_AUDIT.md` should treat wrong or unstable rankings as scientifically useful failure evidence.
3. `SCIENTIFIC_GUARDRAILS.md` should ban claims that AI discovers the true LSD mechanism.
4. Music/setting remains literature-supported but locally blocked until run-02 extraction and subject exclusions are complete.
5. Control-theory language is justified, but only if the report names the simplified state representation, control inputs, null baselines, and validation split.

## 15. 2026-05-25 Data-Methods Addendum (small-N + dynamic + control focus)

Recent method-layer updates from 2025–2026 that are useful for thesis framing:

- Low-dimensional controllability methods remain a valid low-parameter control-comparison baseline for network-level dynamics, with explicit attention to dimensionality reduction trade-offs and interpretability.
  - DOI: https://doi.org/10.1371/journal.pcbi.1012691
- Time-resolved network control analysis is a stronger fit for transient psychedelic trajectories than static summaries alone and should be treated as a distinct follow-up experiment, not a replacement for existing rest-target metrics.
  - DOI: https://doi.org/10.1038/s42003-025-08078-9
- Travelling-wave and propagation framing under serotonergic psychedelics has renewed traction as a mechanistic interpretation of global connectivity shifts; this is most defensible as a parallel analysis path, because run-level BOLD confounds remain unmodelled in current ds003059 preprocessing.
  - DOI: https://doi.org/10.1038/s42003-026-09912-4
- Recent psilocybin precision imaging and mega-analysis work strengthens two practical constraints for this repo:
  - high-quality parcellation and atlas consistency are sensitive to cross-subject variance,
  - and full claims should be qualified by validated split designs and small-N uncertainty.
  - Representative sources:
    - https://pubmed.ncbi.nlm.nih.gov/41942645/
    - https://pubmed.ncbi.nlm.nih.gov/40666257/

## 16. 2026-05-25 Inference-Upgrade Checklist (small-N rigorous framing)

To keep the mechanism layer academically explicit, the current ranking pipeline now reports uncertainty and multiplicity-aware inferential diagnostics:

- paired metric deltas are summarized with bootstrap percentile CIs (resample-within observed pair-level deltas),
- sign-direction tests are adjusted across mechanism-metric families with Benjamini–Hochberg FDR,
- all inferential outputs are treated as exploratory constraints, not population-level claims.

### Core references for this inference upgrade

| Topic | Reference | Use in this repo |
|---|---|---|
| False-discovery control in multiple testing | Benjamini & Hochberg (1995) | FDR principle for sign-flip p-values across mechanism metric families. |
| Bootstrap uncertainty in small samples | Efron and Tibshirani resampling line (bootstrap CI family) | percentile-based bootstrap CI construction for metric means/differences. |
| Neuroimaging multiple-testing caution | Follow-on neuroimaging multiple-testing literature | reinforces why FDR is preferred over one-off uncorrected p-values in mechanism tables. |

Representative links used in this pass:

- https://doi.org/10.1111/j.2517-6161.1995.tb02031.x (BH method)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC1456787/ (FDR in QTL/statistical context)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7958418/ (bootstrap CI context)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC3699340/ (neuroimaging FDR discussion)

Required implementation implication:

1. Every mechanism metric table should include CI and q-values with clear interpretation.
2. Layer ranking claims should cite uncertainty descriptors as "descriptive and exploratory."
3. Any future inference extensions should keep p-value families aligned to a declared family and a declared correction method.

## Recommended implementation implication for this codebase

1. Keep current rest-only ds003059 targets as the primary thesis evidence arm until run-02 and motion summaries are available.
2. Add time-resolved control-energy experiments only where input signals are explicit and validation folds remain subject-disjoint.
3. Use propagation/travel-wave claims only in discussion sections tied to uncertainty and proxy limitations.
