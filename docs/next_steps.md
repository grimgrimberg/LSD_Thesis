# Next Steps

1. Replace the current coarse anatomical 8-module extraction with a stronger macro-network mapping that preserves actual ds003059 deltas while staying interpretable.
2. Improve perturbation sensitivity so the best mechanism can move empirical delta magnitudes instead of only matching their sign or direction weakly.
3. Add multi-seed uncertainty intervals and subject-level bootstrap intervals to all reported metrics and plots.
4. Compare alternative local dynamics:
   - bistable potential
   - low-rank RNN module
   - switching state-space variant
5. Use the exported training dataset and cloud scaffold to benchmark a learned sequence autoencoder or latent ODE against the hand-built surrogate.
6. Add stronger out-of-sample validation across LSD and psilocybin datasets.
