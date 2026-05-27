# Thesis Upgrade Evidence Dashboard Design

## Purpose

Upgrade the thesis from a static surrogate-model demo into a reviewer-facing evidence system that makes uncertainty, blockers, and next validation gates explicit.

## Approved Scope

- Motion/confound handling becomes an explicit evidence gate, not a prose caveat.
- Schaefer/Yeo becomes the named canonical parcellation target while the current Harvard-Oxford 8-module extraction remains the transparent proxy baseline.
- ROCKET becomes a stricter benchmark family with subject-disjoint aggregation, permutation-null requirements, calibration checks, and MiniRocket/MultiRocket extension points.
- External validation centers on OpenNeuro `ds006072` psilocybin precision functional mapping while preserving the rule that scoring must not be retuned after looking at external results.
- Receptor and structural-connectome layers are split into clear states: proxy-only, local structural graph available, PET prior available, and fully integrated with null controls.
- GitHub Pages remains a static presentation layer; a reproducible archive manifest plus Zenodo/GitHub release metadata becomes the citable thesis snapshot path.
- Dashboard visuals expose the above gates with stronger 2D/3D reviewer-facing panels.

## Design Principles

- Do not claim receptor-level, clinical, subjective-experience, or external-validity evidence unless the corresponding data layer exists.
- Prefer readiness gates over soft caveats.
- Keep all derived artifacts separate from raw OpenNeuro imaging data.
- Treat missing data as a useful thesis finding when it blocks a claim.
- Use `subject/session/run` aggregation as the primary ML reporting unit.

## Implementation Boundary For First Pass

The first pass builds the evidence scaffold and dashboard surface. It does not download large external datasets, invent receptor priors, or fabricate structural-connectome matrices.

## Evidence Sources

- fMRIPrep/Power-style motion evidence: `framewise_displacement`, `dvars` / `std_dvars`, and motion outlier columns.
- Canonical parcellation target: Schaefer parcels aligned to Yeo 7/17 networks.
- ROCKET strengthening: MiniRocket/MultiRocket-style extensions plus permutation and calibration gates.
- Receptor prior target: neuromaps/FS5ht 5-HT2A PET-derived map projections.
- Structural target: documented HCP/normative structural-connectome graph in the active parcellation.
- Archive target: GitHub release plus Zenodo DOI and a local manifest/checksum record.

## Acceptance Criteria

- The dashboard shows a thesis-readiness gate board with motion, parcellation, ROCKET, external validation, receptor/SC, archive, and visual-publication gates.
- Generated status artifacts state whether each gate is ready, blocked, proxy-only, or planned.
- The public/static Pages build can copy the new status artifacts.
- Documentation names the canonical next parcellation and archive strategy.
- No generated text upgrades a proxy into biological proof.
