# Dynamic Mechanism Literature Support

Date: 2026-05-19

## Purpose

Map the A/B/C/D mechanism-ranking layers to defensible literature support without overstating the thesis claim.

## Working Claim

The current thesis can claim that coarse empirical fMRI proxy metrics are compatible with some macro-dynamic mechanism stories more than others. It cannot claim that the fitted model discovers the true biological dynamics of LSD.

## Source-To-Layer Mapping

| Layer | Thesis use | Supportive literature | Defensible use | Do not claim |
| --- | --- | --- | --- | --- |
| A. Transition/barrier proxy | Macro-state switching, dwell time, transition diversity, and step-distance proxies. | Carhart-Harris and Friston, 2019, REBUS and the Anarchic Brain. https://pubmed.ncbi.nlm.nih.gov/31221820/ | Theoretical motivation for entropy/free-energy/relaxed-prior language at the macro level. | Do not claim true biological energy barriers or receptor-level transition energies. |
| B. DMDc / controlled dynamics | Linear one-step model with condition bias and condition-by-state interaction. | Proctor, Brunton, and Kutz, 2016, Dynamic Mode Decomposition with Control. https://epubs.siam.org/doi/10.1137/15M1013857 | A simple, interpretable predictive controlled-dynamics baseline for input-output system identification. | Do not claim DMDc is network-control energy or that fitted coefficients are brain governing equations. |
| C. Hierarchy/routing | Sensory-transmodal, associative, thalamic-gateway, hierarchy-gradient, and receptor-weighted FC proxies. | Preller et al., 2018, eLife. https://elifesciences.org/articles/35082; Preller et al., 2019, PNAS. https://doi.org/10.1073/pnas.1815129116; hierarchy-gradient psychedelic work. | Motivation for testing sensory-associative, thalamic, hierarchy-flattening, and receptor-prior alignment signatures as proxy evidence layers. | Do not claim proof of REBUS, precision relaxation, or thalamic gating from the 8-module proxy alone. |
| D. Dynamic repertoire | Integration/segregation balance, dynamic-FC variance, FC-state path length, modularity, participation, and global-efficiency metrics. | Luppi et al., 2021, NeuroImage. https://doi.org/10.1016/j.neuroimage.2020.117653; Atasoy et al., 2017, Scientific Reports. https://www.nature.com/articles/s41598-017-17546-0; Rubinov and Sporns 2010. | Direct motivation for dynamic integration/segregation, graph-theory, and repertoire-like target metrics in LSD fMRI. | Do not claim subjective richness or conscious-state content from FC summaries. |
| E. Network-control energy | Finite-horizon control energy over a macro-module graph with receptor, hierarchy, sensory, transmodal, thalamic, random, and degree-control profiles. | Singleton et al., 2022, Nature Communications. https://www.nature.com/articles/s41467-022-33578-1; Gu et al., 2015. https://doi.org/10.1038/ncomms9414; Betzel et al., 2016. https://doi.org/10.1038/srep30770 | Direct motivation for a control-energy landscape proxy and stress tests against null control profiles. | Do not claim full receptor-informed NCT until structural-connectome and PET receptor-map inputs are implemented. |

## Current Empirical Interpretation

The 2026-05-19 A+B+C+D+E ranking is:

1. C hierarchy/routing proxy.
2. E receptor-informed network-control energy proxy.
3. D dynamic repertoire proxy.
4. A transition-state proxy.
5. B DMDc condition-interaction baseline.

This is not a final mechanism conclusion. C has supportive sensory/thalamic/receptor-prior signs but an associative-global sign conflict. E supports a control-energy landscape-flattening proxy, but receptor-prior control does not beat uniform or random receptor-prior control profiles. D becomes more supportive after adding graph-theory integration metrics, but dynamic-FC variance and FC path length still move against the expected repertoire direction. B remains a negative-control baseline because the condition-interaction DMDc variant does not improve held-out one-step RMSE.

## Defense Wording

Use:

> We ranked transparent surrogate mechanisms against paired LSD-minus-placebo fMRI proxy summaries. The strongest current support is for hierarchy/routing-style FC changes, followed by a proxy network-control energy result showing lower within-condition transition energy under LSD. Receptor-specific control placement is not yet supported against null control profiles.

Avoid:

> The AI discovered the true LSD brain dynamic.

## Next Evidence Needed

- Confirm whether C remains rank 1 under subject-disjoint resampling, alternative module definitions, and motion-sensitive exclusions.
- Test A under alternative state-labeling choices, not only PCA quantiles.
- Treat B as weak unless controlled dynamics improve held-out prediction beyond no-input dynamics.
- Treat D as mixed until dynamic-FC metrics are stable across window sizes and run splits.
- Treat E as promising but incomplete until a structural connectome, PET-derived receptor maps, graph-rewire nulls, and spatial receptor-map nulls are added.
