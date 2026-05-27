# Network-Control And Graph-Theory Upgrade

Date: 2026-05-19

## Purpose

Record the concrete fixes made after the scholarly-control review. The goal is to make the thesis more supportive by adding stronger tests and clearer nulls, not by forcing all results to be positive.

## Implemented Fixes

| Gap | Fix | Current status | Claim boundary |
| --- | --- | --- | --- |
| 1. Missing network-control energy layer | Added E: receptor-informed finite-horizon control-energy proxy. | Implemented in `src/lsd_thesis/dynamic_mechanism.py`. | Proxy-control only; not full structural-connectome NCT. |
| 2. B overstated as control theory | Kept B as DMDc predictive baseline and labels negative B as a negative-control baseline. | Implemented. | DMDc is not control-energy evidence. |
| 3. C hierarchy metrics too coarse | Added hierarchy-gradient flattening and receptor-weighted global coupling metrics. | Implemented on 8-module proxy. | Still not canonical Schaefer/Yeo gradient extraction. |
| 4. D missing graph-theory measures | Added modularity, modularity-reduction, participation coefficient, and global efficiency. | Implemented on positive weighted FC graph. | Graph metrics are FC proxies, not structural topology. |
| 5. Receptor priors were neutral | Replaced neutral placeholder metadata with coarse proxy receptor weights and explicit source labels. | Implemented for Harvard-Oxford 8 and Schaefer/Yeo metadata generators. | Priors are not PET-derived receptor maps. |
| 6. Missing null/stress tests | Added random receptor-prior permutation null and degree-control profile inside E. | Implemented. | Still missing degree-preserving graph rewires and spatial receptor-map nulls. |

## E Result Interpretation

The current E layer gives a split result:

- Supportive: LSD within-condition transitions require lower control energy than placebo under both receptor-profile and uniform control.
- Not supportive yet: receptor-prior control is not lower-energy than uniform control or random receptor-prior permutations.
- Interpretation: there is first-pass support for a flattened control-energy landscape proxy, but not for a strong receptor-specific control-placement claim.

## Literature Anchors

| Area | Source | Use |
| --- | --- | --- |
| Psychedelic network control | Singleton et al. 2022, Nature Communications, receptor-informed control-energy landscape under LSD/psilocybin. | Main motivation for E. |
| Brain controllability | Gu et al. 2015, Nature Communications, controllability of structural brain networks. | Mathematical basis for graph-control framing. |
| Control energy and topology | Betzel et al. 2016, Scientific Reports, optimally controlling the human connectome. | Supports topology/control-energy language. |
| Dynamic repertoire | Luppi et al. 2021 NeuroImage; Atasoy et al. 2017 Scientific Reports. | Supports D graph-dynamic/repertoire targets. |
| Graph theory | Bullmore and Sporns 2009; Rubinov and Sporns 2010. | Supports modularity, participation, efficiency, integration/segregation metrics. |
| Method caveats | Tu et al. 2018; practical NCT methodology papers. | Supports explicit caution around controllability assumptions. |

## Next Stronger Version

1. Replace the macro-module proxy graph with a normative structural connectome in the same parcellation.
2. Replace coarse receptor priors with PET-derived 5-HT2A maps projected to parcels.
3. Run Schaefer/Yeo extraction for C/D instead of relying on the 8-module proxy.
4. Add degree-preserving graph rewires and spatial-autocorrelation-preserving receptor-map nulls.
5. Re-run E under subject/bootstrap splits and report uncertainty, not only point estimates.

