# LSD Thesis Context

This file records project-specific domain language for the LSD Thesis evidence workbench. It keeps public wording aligned with the repository's scientific guardrails.

## Language

**Mechanism-Proxy Ranking**:
Ranking transparent surrogate mechanism families by agreement with macro-dynamic proxy targets.
_Avoid_: unqualified mechanism ranking, strongest mechanism, final mechanism

**Macro-Dynamic Proxy**:
A model-level or fMRI-summary quantity used as an analogue for large-scale dynamics.
_Avoid_: biological mechanism, subjective experience, receptor-level effect

**C Hierarchy/Routing Proxy**:
The current leading A-E proxy family under cached ds003059 evidence, pending motion/confound proof and atlas-level replication.
_Avoid_: C proves the LSD mechanism, C is thesis-complete

**E1 Lower Transition/Control-Energy Proxy**:
The supported part of E: LSD-placebo differences that are consistent with lower transition/control-energy proxy behavior.
_Avoid_: receptor proof

**E2 Receptor-Specific Placement**:
The unsupported or future part of E that would require structural graph, PET 5-HT2A priors, and spatial-null discipline before promotion.
_Avoid_: receptor-informed network control as a single positive claim

**B DMDc Negative-Control Baseline**:
A retained predictive/control baseline that is currently unsupported as the main control-theory result.
_Avoid_: B as central mechanism

**Motion-Proof Gate**:
The blocked thesis gate requiring subject/session/run FD, DVARS, censoring/outlier, and confound-regression evidence.
_Avoid_: image-derived motion QC as thesis-grade motion proof

**Static Public Review Surface**:
The GitHub Pages or PI-review package built from derived artifacts, not raw data or a live FastAPI server.
_Avoid_: citable archive, completed publication

**PI-Review-Ready Research Demo**:
A supervisor-facing, claim-gated package that can be reviewed as a research workbench while strict thesis gates remain open.
_Avoid_: completed thesis, citable archive, full scientific validation

**Production Academic Submission**:
A fully gated, citable submission state after required motion/confound proof, archive DOI, and quality gates are complete. The current package should not use this label without those gates.
_Avoid_: using this phrase for the current PI-review package without blockers

## Relationships

- **Mechanism-Proxy Ranking** ranks **C Hierarchy/Routing Proxy**, **E1 Lower Transition/Control-Energy Proxy**, **E2 Receptor-Specific Placement**, **B DMDc Negative-Control Baseline**, and related A/D proxy families.
- **C Hierarchy/Routing Proxy** cannot become a stronger thesis claim until the **Motion-Proof Gate** is closed.
- **E1 Lower Transition/Control-Energy Proxy** and **E2 Receptor-Specific Placement** are distinct claims with different evidence requirements.
- **Static Public Review Surface** can present artifacts, but it does not close the DOI/archive or motion-proof gates.
- **PI-Review-Ready Research Demo** can use the **Static Public Review Surface**, but it is not a **Production Academic Submission**.

## Example Dialogue

> **Dev:** "Can the landing page say C is the strongest mechanism?"
> **Domain expert:** "No. Say C is the leading mechanism-proxy family under cached analysis, pending the motion-proof gate."

## Flagged Ambiguities

- "External validation" has been used for ds006072. Resolved: call it an external cross-dataset stress test unless a completed, comparable validation gate exists.
- "Ready" has meant both presentation-ready and thesis-complete. Resolved: public pages must say research-demo or PI-review-ready unless strict gates prove thesis completion.
- "Receptor-informed network control" has mixed E1 and E2. Resolved: split lower-energy proxy support from receptor-specific placement.
- "Production-ready academic submission" has been used as an aspirational goal. Resolved: call the current state PI-review-ready research demo until motion/confound proof, archive DOI, and quality gates pass.
