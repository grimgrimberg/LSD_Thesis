# Defense Outline

## Slide 1: Framing
- Talking points:
  - This is a surrogate model of altered-state-inspired macro-dynamics.
  - The goal is to explain proxy shifts, not receptor mechanisms or subjective reports.
  - The repository is strongest when it makes narrow, testable macro-dynamics claims.

## Slide 2: Stage 1 shift
- Talking points:
  - Baseline and perturbed conditions differ in the proxy values.
  - The stage 1 figure highlights changes in entropy and switching rate.

## Slide 3: Stage 2 robustness
- Talking points:
  - Stage 2 objective changed from 1628.945 to 2.054 (decreased); lower scores are better. The selected score comes from the optimization step.
  - Benchmark anchor: OpenNeuro ds003059 placebo resting-state summary (15 session averages).
  - The comparison uses 15 subjects and 60 runs.
  - Multi-seed summaries offer limited evidence about run-to-run consistency.

## Slide 4: Mechanism ranking
- Talking points:
  - Best single mechanism: `less_hierarchical_constraint` at strength 0.25.
  - Best pair: `less_hierarchical_constraint+lower_switching_barrier`.
  - Sign mismatches: within_network_stability, entropy_diversity, metastability_proxy.

## Slide 5: Limits
- Talking points:
  - The work is explicit about proxy metrics, cached evidence, and limited generalization claims.
  - Any biological interpretation should stay at the macro-dynamics level.

## Likely challenge
- Likely challenge: Why should anyone trust these proxies if they do not model receptors or subjective experience?
- Answer: The value is in transparent, testable macro-level structure, not in pretending to be a direct mechanistic model.
