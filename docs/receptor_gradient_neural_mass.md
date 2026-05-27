# Receptor/Gradient-Gated Neural-Mass Surrogate

## Purpose

`receptor_gradient_neural_mass` is a lightweight model-zoo family for testing spatially heterogeneous gain and routing perturbations. It is a surrogate neural-mass model, not a receptor-level pharmacology model.

## State Equations

Each node has excitatory activity `E_i` and inhibitory activity `I_i`.

```text
tau_E dE_i/dt =
  -E_i + sigmoid(g_i * (w_EE E_i - w_EI I_i + G sum_j C_ij E_j + b_E - homeostasis))
  + noise

tau_I dI_i/dt =
  -I_i + sigmoid(w_IE E_i - w_II I_i + b_I + local_homeostasis)
```

The first implementation uses deterministic Euler-Maruyama integration under a fixed seed and clips state values to avoid numerical runaway.

## Perturbation Parameters

- `receptor_gain_alpha`
- `hierarchy_cross_coupling_eta`
- `visual_gain_beta`
- `sensory_gain_gamma`
- `associative_decoherence_lambda`
- `thalamic_routing_kappa`
- `striatal_routing_kappa`
- `noise_delta`
- `homeostasis_delta`

These are model-comparison knobs. They should be described as candidate perturbation families, not biological mechanisms.

## Metadata

The default config provides transparent proxy arrays for the existing eight nodes:

- network labels
- hierarchy values
- receptor-weight proxy
- visual/sensory/transmodal weights
- thalamus/striatum weights

The default arrays are placeholders for model comparison until a validated Schaefer/Yeo and receptor-map extraction exists.

## Observation Layer

The model emits latent excitatory activity as `SimulationResult.activity`. When `emit_bold` is true, it also emits a lightweight HRF-convolved `SimulationResult.bold` array with the same shape.

## Config

Example config:

- `configs/models/receptor_gradient_neural_mass.yaml`

## Guardrails

Do not claim this model simulates LSD pharmacology, receptor binding, subjective experience, consciousness, clinical outcomes, or a true biological mechanism.

