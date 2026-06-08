# Project Context

This file records domain terms that affect how agents and maintainers should interpret requests in this repository.

## Glossary

### Implemented Safe Everything

The currently runnable end-to-end workflow that does not download data, does not extract run-02 music data, and does not overwrite legacy Stage 1-5 semantics.

It includes:

- Stage 1-4 legacy surrogate and empirical rest pipeline.
- Training-window export.
- Existing subject-disjoint condition and multitask ML benchmark scripts.
- Stage 2b target reliability validation.
- Stage 5 literature/proxy-weighted mechanism ranking.
- PASS 2B-0 Set/Setting/Seed readiness artifacts.
- Dashboard preflight and local dashboard serving.

### Gated Everything

Future workflow that includes run-02 extraction and actual music-control analysis. This is intentionally not the default meaning of "run everything" because it can download or extract larger data and changes the evidence boundary.

Gated everything requires explicit user approval before:

- downloading data,
- extracting run-02 music module time series,
- running expensive full pipelines,
- adding heavy dependencies.

### Music-Control Claim

An empirical claim about music or setting effects. This claim is not allowed until run-02 module time series are present, `S03`, `S12`, and `S15` are excluded for music-specific analyses, and the analysis is rerun from actual data.

### Proxy-Ranking Artifact

A mechanism ranking from Stage 5 or related surrogate objectives. It is useful for ordering hypotheses, but it is not biological proof, external validation, or a clinical prediction.

### Ranking Prediction Target

The preferred thesis prediction framing: use AI/ML to rank candidate perturbation mechanisms or parameter settings by how well their held-out proxy-metric deltas match empirical macro-dynamics targets.

This is not a claim that the system discovers true biological LSD mechanisms. It is a hypothesis-ranking task over transparent surrogate mechanisms, evaluated by mismatch, robustness, and failure analysis.

### Dynamic Method

The evolving thesis method that connects three layers:

- LSD neuroimaging targets as empirical constraints.
- Control-theoretic surrogate mechanisms as the interpretable hypothesis space.
- AI/ML ranking and explainability as tools for model comparison and failure analysis.

This term should not be used as a vague synonym for any complex model. A dynamic method must define its state representation, control or perturbation inputs, prediction target, validation split, and failure criteria.

### AI-Assisted Mechanism Ranking

The use of machine learning to score, rank, or explain candidate surrogate mechanisms against empirical proxy targets.

Allowed claim: the ranking identifies which candidate mechanism best aligns with the current proxy targets under the current validation design.

Forbidden claim: the ranking discovers the real biological mechanism of LSD.
