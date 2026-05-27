# Dynamic Mechanism Ranking Design

Date: 2026-05-17

## Purpose

Define the approved thesis direction before implementation: use AI/ML to rank transparent control-theoretic surrogate mechanisms against empirical LSD-minus-placebo macro-dynamics targets from `ds003059`.

This design replaces the vague idea that "AI finds the LSD dynamic" with a constrained, testable research method. The method must allow a negative result: none of the current candidate mechanisms may fit the empirical targets well.

## Audience

- Thesis author: needs a concrete modeling plan and defensible scope.
- Supervisor or examiner: needs clear claims, evidence boundaries, and failure criteria.
- Future implementer: needs enough structure to build the next experiments without inventing the thesis framing again.

## Core Research Question

Can simple control-theoretic surrogate dynamics, ranked with leakage-controlled AI/ML methods, explain which candidate mechanisms best align with empirical LSD-minus-placebo macro-dynamics targets?

## Approved Modeling Direction

The primary implementation target is A plus B:

1. Control-energy / transition-barrier dynamic.
2. Controlled linear dynamics / DMDc baseline.

The design should leave room for C and D:

3. Hierarchy / precision-relaxation dynamic.
4. Dynamic repertoire / integration-segregation metrics.

The first implementation should not start with high-capacity neural dynamics. Neural ODEs, transformers, or unconstrained latent models are out of scope until simple dynamics are implemented, validated, and shown insufficient.

## A. Control-Energy / Transition-Barrier Dynamic

Model the module-level time series as movement between recurring macro-states.

Inputs:

- module-level empirical time series from `ds003059`,
- condition labels such as placebo versus LSD,
- run labels such as rest versus music when run-02 is available and valid,
- subject identifiers for subject-disjoint validation.

Candidate outputs:

- state occupancy,
- dwell time,
- transition probability,
- switching-rate proxy,
- entropy-like repertoire proxy,
- metastability proxy,
- barrier or transition-effort proxy.

Safe claim:

> The analysis estimates whether candidate surrogate mechanisms alter macro-state occupancy and transition structure in a way that aligns with empirical proxy targets.

Forbidden claim:

> The analysis proves that LSD lowers true biological energy barriers.

## B. Controlled Linear Dynamics / DMDc Baseline

Fit a simple controlled dynamical model:

```text
x[t+1] = A x[t] + B u[t] + noise
```

Where:

- `x[t]` is the module-level brain-state vector at time `t`,
- `A` estimates baseline transition dynamics,
- `u[t]` encodes condition or surrogate control input,
- `B` estimates how the control input changes the next state.

Primary comparison:

- model without condition input,
- model with LSD/placebo input,
- model with rest/music input only when run-02 is approved and available,
- model with candidate mechanism inputs.

Safe claim:

> DMDc tests whether a simple controlled linear system provides a useful approximation for ranking candidate surrogate mechanisms.

Forbidden claim:

> The fitted `A` and `B` matrices are the real governing equations of the brain under LSD.

## C. Hierarchy / Precision-Relaxation Layer

This layer is initially interpretive and feature-based, not the first fitted model.

Candidate features:

- transmodal-unimodal coupling,
- sensory-associative coupling,
- thalamic-gateway coupling,
- hierarchy-compression proxy,
- top-down constraint proxy.

Use:

- explain rankings from A and B,
- test whether ranked mechanisms are consistent with REBUS-style precision-relaxation framing,
- provide thesis narrative only when proxy metrics support it.

## D. Dynamic Repertoire / Integration-Segregation Layer

This layer supplies target metrics and robustness checks.

Candidate metrics:

- dynamic FC change,
- integration versus segregation,
- entropy-like repertoire,
- state diversity,
- switching rate,
- dwell-time distribution.

Use:

- score candidate dynamics,
- compare to literature-motivated target signs,
- expose sign conflicts as first-class results.

## MPC-Like Inverse Scoring

Model predictive control can be used later as a scoring analogy if A and B are stable.

Defensible framing:

> Use an MPC-like inverse analysis to ask which surrogate control inputs would most efficiently move a placebo-like macro-state model toward empirical LSD-like proxy targets.

Illustrative objective:

```text
min over u[0:H-1]  sum_t ||x[t] - x_target||_Q^2 + lambda ||u[t]||_R^2

subject to:
x[t+1] = A x[t] + B u[t]
u[t] within allowed surrogate mechanism bounds
```

Allowed output:

- relative control effort,
- trajectory fit to proxy targets,
- instability or failure to reach targets,
- mechanism ranking under the fitted surrogate.

Forbidden output:

- claims of real-time brain control,
- clinical intervention claims,
- proof of biological mechanism.

## Validation Requirements

Required before making a mechanism-selection claim:

- subject-disjoint split,
- fold-local preprocessing for any fitted transform,
- random-ranking baseline,
- seed-noise null,
- simple heuristic baseline,
- uncertainty across seeds or folds,
- explicit failure criteria.

Condition prediction is allowed only as a secondary benchmark. It cannot become the main thesis claim unless it is subject-disjoint and shown not to rely on leakage artifacts.

## Failure Criteria

The current dynamic story is weakened if:

- mechanism rankings are unstable across folds or seeds,
- rankings do not beat random or simple heuristic baselines,
- DMDc performs no better than no-input dynamics,
- state-transition metrics are dominated by clustering choices,
- empirical target signs conflict across metrics,
- run-02 or motion-sensitive analyses remain blocked.

These are useful thesis results, not project failures, if they are reported clearly.

## Deliverables

Minimum viable thesis deliverables:

- A+B fitted on approved empirical outputs.
- Mechanism-ranking table with uncertainty.
- Null and heuristic baseline comparison.
- Explanation report for top-ranked and failed mechanisms.
- Dashboard view showing state-transition and DMDc ranking results.
- HTML presentation/report with claims separated into implemented facts, proxy observations, and hypotheses.

Ambitious deliverables:

- C/D explanation layer integrated into rankings.
- MPC-like inverse scoring after A+B are stable.
- Music/rest control-input analysis after run-02 and motion review are ready.
- Slide-ready visuals for defense.

## Design Approval

Approved by the user on 2026-05-17:

- start with A+B,
- leave room for C+D,
- explore MPC-like scoring only after discussing and validating the math,
- use hierarchy/precision relaxation and broader literature as secondary exploratory paths.
