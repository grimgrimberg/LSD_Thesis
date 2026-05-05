# Limitations

## Claim Boundaries

- The simulator is a surrogate model, not a mechanistic receptor or pharmacokinetic model.
- The 8-module abstraction collapses rich regional and laminar structure.
- The switching-barrier and metastability terms are model-level proxies.
- The perturbation operators should be described as hypothesis toggles over a graph-modulated dynamical system, not as neurobiological mechanisms.
- Any match between model outputs and psychedelic neuroimaging signatures should be interpreted as qualitative-to-semiquantitative alignment, not proof of mechanism.

## Empirical And Atlas Limits

- The current ds003059 extraction uses a coarse Harvard-Oxford-based anatomical proxy to define the 8 modules; this is transparent but not a canonical functional network parcellation.
- The sober fit now uses actual ds003059 placebo summaries, but the altered-state deltas extracted under this coarse mapping do not perfectly reproduce the canonical literature-level signature.
- Some Harvard-Oxford source labels are assigned to more than one macro-module. The current label image builder resolves overlaps by module order, so later modules overwrite earlier assignments. This is acceptable only if it is explicitly reported as a proxy-mapping limitation.
- The ds003059 path uses Rest1/Rest3 resting-state runs and excludes Rest2 music runs. This should be stated whenever empirical results are shown.

## Metric And Fitting Limits

- The perturbation operator still underexpresses the empirical delta magnitudes, especially for cross-network communication and thalamic shifts.
- Entropy/diversity, switching rate, metastability, and effective barrier are computed observables of the extracted or simulated time series. They are not direct measurements of neural entropy, state transitions, or energy barriers.
- The current metric implementation uses KMeans-derived labels for several dynamic proxies, so sensitivity to seed, windowing, and clustering parameters must be reported before making strong claims.
- The current fitting search evaluates candidate parameters on stochastic simulations. Candidate ranking should be treated as provisional until top candidates are re-scored on a fixed multi-seed panel.

## Dashboard And Artifact Limits

- The dashboard is an MVP for inspection and communication, not a clinical or scientific decision tool.
- Three of eight empirical LSD-minus-placebo delta metrics extracted from ds003059 under the current 8-module Harvard-Oxford mapping are sign-reversed relative to literature-derived expectations (within_network_stability, entropy_diversity, metastability_proxy). Mechanism rankings in Stages 3-4 should be interpreted with this caveat.
- The current repository has an unborn git branch in local runs captured by the stage summaries. Until a baseline commit exists, regenerated figures and reports have weak provenance.
- Generated data, caches, and figures are local artifacts. Submission packages should either version the required outputs explicitly or document the exact commands and lockfile used to regenerate them.
