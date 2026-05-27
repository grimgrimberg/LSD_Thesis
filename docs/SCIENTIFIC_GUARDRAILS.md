# Scientific Guardrails

Date: 2026-05-12

Scope: Set / Setting / Seed extension for the LSD whole-brain surrogate project.

## Core Boundary

This project is a transparent surrogate and empirical module-level analysis of macro-scale dynamics. It is not a model of subjective experience, hallucination content, clinical outcomes, receptor pharmacology, or consciousness.

## Explicit Non-Claims

- Not a clinical model.
- Not a subjective-experience simulator.
- Not hallucination decoding.
- Not a receptor model unless receptor maps are explicitly added, documented, and treated only as priors.
- Not evidence that "the brain is Stable Diffusion".
- Not proof that a fitted surrogate captures biological mechanism.
- Not proof that a proxy objective score is a causal explanation.
- Not proof that AI has discovered the true dynamics of LSD.

## Allowed Framing

Use:

- surrogate model
- macro-scale analogue
- altered-state-inspired perturbation
- graph-modulated dynamics
- module-level proxy
- AI-assisted mechanism ranking
- control-theoretic surrogate mechanism
- reliability-gated exploratory analysis
- guided stochastic latent dynamics as analogy
- control input or setting variable
- subject-disjoint validation

Avoid:

- "the model is tripping"
- "the brain runs Stable Diffusion"
- "hallucination decoder"
- "consciousness simulator"
- "receptor-realistic LSD model" unless receptor maps are added and framed as priors
- "clinical prediction" or "treatment outcome" claims
- "proof" where the evidence is a proxy ranking
- "AI discovered the mechanism of LSD"
- "the learned model explains psychedelic experience"

## AI And Control-Theory Guardrail

The current thesis direction may combine LSD neuroimaging, control theory, and AI/ML, but each layer has a different evidential role.

| Layer | Allowed role | Not allowed as |
|---|---|---|
| LSD neuroimaging | Empirical constraint, target sign, held-out benchmark | Direct access to subjective experience or receptor mechanism |
| Control theory | Interpretable state-transition, barrier, input, and energy-proxy language | Proof that the brain literally follows the simplified surrogate equations |
| AI/ML | Ranking, prediction benchmark, attribution, and failure analysis | Unconstrained discovery of true biological dynamics |

Required wording:

> AI/ML ranks candidate surrogate mechanisms against empirical proxy targets; it does not prove the biological mechanism of LSD.

Any mechanism-ranking claim must name:

- candidate mechanisms,
- empirical target metrics,
- null baselines,
- leakage-safe split,
- uncertainty or robustness check,
- failure criteria.

## Small-N Caution

Current paired rest analysis uses 15 subjects. This is useful for transparent exploratory modeling, but it is small for high-dimensional modeling, ML classification, and mechanism selection.

Required language:

- "exploratory"
- "proxy-ranking"
- "subject-disjoint validation"
- "consistent with"
- "does not prove biological mechanism"

Avoid:

- population-general claims,
- clinical claims,
- precise effect-generalization claims,
- large-model claims unsupported by subject-disjoint validation.

## Motion Caution

Current cached outputs do not include subject-level FD, DVARS, confound, or censoring summaries.

PASS 2 must:

- audit whether motion/confound files are present before using them,
- label analyses without motion control clearly,
- avoid claiming that motion artifacts are ruled out,
- add motion covariates only when real subject/run-level summaries are available.

## Atlas And Module Caution

The current 8-module extraction is a transparent proxy, not a canonical network definition.

Current modules:

- `visual`
- `auditory`
- `salience`
- `default_mode`
- `executive_frontoparietal`
- `limbic_affective`
- `thalamic_gateway`
- `sensorimotor`

PASS 2 must:

- keep the module proxy status visible,
- avoid overclaiming anatomical specificity,
- keep Schaefer/Yeo or other parcellation extensions marked as unrun until actually extracted,
- report atlas/module limitations in every major report.

## Run-02 Music Exclusion Caution

Dataset design:

- `run-01`: Rest1.
- `run-02`: Music.
- `run-03`: Rest3.

Music-specific analyses must exclude:

- `S03`
- `S12`
- `S15`

These exclusions apply to music-specific analyses only. They should not automatically exclude valid rest-only data.

Current cached Stage 2 module time series do not include `run-02`, so music-specific modeling must fail closed until music extraction exists.

## Exploratory Vs Confirmatory Labels

Use the following labels in reports and dashboard output:

| Label | Meaning |
|---|---|
| Implemented fact | Directly produced by current code/artifacts |
| Empirical observation | Derived from cached empirical outputs |
| Proxy target | Metric intended as a macro-dynamic analogue |
| Calibration result | Fit or ranking on full data, not held-out validation |
| Subject-disjoint validation | Evaluation where subjects are disjoint across train/test |
| Hypothesis | Mechanistic idea not established by current artifacts |
| Analogy | Conceptual bridge, not literal biological claim |

## Validation Rules

Subject-disjoint validation is mandatory for:

- ML models,
- mechanism selection claims,
- latent/control models with fitted transforms,
- any train/test performance metric.

Forbidden:

- naive window-level random train/test splits,
- tuning on held-out subjects,
- fitting normalizers, PCA, feature selectors, or model hyperparameters on all subjects before validation,
- citing root Stage 3 scaffold outputs as approved CV5 evidence.

Allowed:

- fold-local preprocessing,
- fixed preprocessing documented as frozen extraction,
- approved CV5 manifests,
- leave-one-subject or leave-group-out validation.

## Proxy Objective Score Caution

Current objective scores rank transparent surrogate mechanisms against proxy targets. They do not prove:

- receptor-level mechanism,
- subjective effect,
- causal biological routing,
- clinical relevance,
- generalizability beyond the analyzed data.

Every model-ranking report should state:

> Mechanism scores are proxy-alignment scores for transparent model comparison. They are not biological proof.

## Stable Diffusion Analogy Guardrail

Allowed:

- "latent diffusion is an analogy for guided stochastic latent processes."
- "guidance resembles the idea of control inputs, priors, or routing constraints."
- "seed maps loosely to stochastic initialization and subject-specific latent state."

Forbidden:

- "the brain implements Stable Diffusion."
- "LSD changes classifier-free guidance in the brain."
- "music is a text prompt for the brain."
- any literal claim that diffusion-model internals map directly onto neurobiology.

## Dashboard Text Guardrails

Dashboard text should be concise and status-like:

- "Run-02 music data not extracted in current cache."
- "Motion summaries unavailable."
- "Subject-disjoint CV required for validation claims."
- "Proxy target, not biological proof."

Avoid long explanatory blocks in the UI. Put detailed caveats in linked reports.

## PASS 2A Status Guardrail

PASS 2A implements rest-only cache auditing, reliability tiers, descriptive PCA geometry, and a music-control scaffold. It does not implement run-02 extraction, empirical music-control claims, motion sensitivity, heavy ML, or a new biological mechanism claim.

## PASS 2B-0 Readiness Guardrail

PASS 2B-0 implements guarded run-02 extraction support and motion-summary parsing support only. It does not run extraction, download data, or compute empirical music effects.

Required wording:

- "run-02 extraction support exists behind an explicit flag."
- "run-02 data are not present in the current cache."
- "motion-summary support exists, but local motion/confounds were not found."
- "music-control analysis remains blocked."

Forbidden wording:

- "music-control effects were found."
- "motion sensitivity was controlled."
- "run-02 was analyzed."
- "the music setting explains the LSD effect."
