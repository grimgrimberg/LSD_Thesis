# Whole-Brain Surrogate Design

## Problem Frame

Build a transparent 8-module dynamical system that captures macro-scale altered-state signatures without making receptor-level or phenomenology-level claims.

## Approaches Considered

### Approach A: Stochastic graph-coupled bistable modules

Pros:
- transparent
- metastability emerges naturally
- easy to perturb and ablate
- cheap to simulate

Cons:
- limited biological realism
- coarse mapping from parameter to neuroimaging effect

### Approach B: Small RNN per module

Pros:
- more expressive
- richer temporal dynamics

Cons:
- less interpretable
- easier to overfit
- harder to explain parameter meaning

### Approach C: Neural ODE / continuous latent model

Pros:
- flexible continuous dynamics
- smooth trajectories

Cons:
- unnecessary complexity for MVP
- weaker transparency

## Recommendation

Use Approach A first. It is the simplest model that can support metastability, switching, and graph-level perturbation in a way that can be tested, ablated, and explained.

## Assumptions

- Macro-module statistics are sufficient for the MVP.
- The first empirical pass can use precomputed/public summary statistics if raw fMRI processing is too heavy.
- Top-down constraint is treated as a model prior toward a sober manifold, not a direct biological process.

