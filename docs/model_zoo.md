# Model Zoo

The model zoo is a thin selection layer for model families. It preserves the original eight-module bistable simulator as the default baseline and creates a stable place for stronger surrogate models.

## Available Models

- `bistable`: the existing eight-module stochastic bistable surrogate.
- `legacy_bistable`: alias for `bistable`.
- `receptor_gradient_neural_mass`: lightweight excitatory-inhibitory neural-mass surrogate with receptor/gradient proxy metadata.
- `rgg_nmm`: alias for `receptor_gradient_neural_mass`.

## Result Interface

Model-zoo simulations return `lsd_thesis.models.SimulationResult` with:

- `activity`: latent activity shaped `time x nodes`.
- `bold`: optional BOLD-like activity shaped `time x nodes`.
- `node_labels`: node/module labels.
- `node_metadata`: metadata keyed by node.
- `dt`: simulation time step.
- `seed`: effective seed.
- `model_name`: registry model id.
- `config`: serializable configuration payload.
- `provenance`: source and compatibility metadata.

## Current Pipeline Wiring

The existing Stage 1-4 pipeline still calls the old simulator functions directly. `scripts/run_pipeline.py` accepts `--model`, validates the model id through the registry, and defaults to `bistable`, but non-baseline model families are not yet wired into Stage 1-4 generation.

This is intentional for Stage 01: scientific outputs are not regenerated or changed.

## Scientific Guardrail

The receptor/gradient model family uses proxy metadata and candidate perturbation knobs. It does not simulate receptor-level pharmacology or subjective experience.

