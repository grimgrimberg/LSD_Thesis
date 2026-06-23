# Whole-Project Roast And Repair Audit

Date: 2026-06-22

## 1. Executive Verdict

This repository is a strong research-demo evidence workbench, but it is not a completed neuroscience thesis. Its best current claim is a mechanism-proxy ranking over cached LSD-placebo macro-dynamic summaries, with C leading and E split between lower-energy proxy support and unsupported receptor-specific placement. A PI or reviewer can distrust it when stale exports, raw claim statuses, static-public readiness claims, or dense dashboard routes make blockers look secondary.

## 2. The Roast

The project has too many artifacts competing to be the front door. Transparency is being used as a partial substitute for hierarchy: there are useful CSVs, status JSON files, generated pages, screenshots, and dashboards, but the first reader still needs a forced path from question to evidence to blocker. The most dangerous failure mode is not a missing plot; it is a reader seeing a polished dashboard and assuming the thesis is complete while the motion/confound gate is still blocked.

## 3. What Works

- The repo repeatedly labels motion/confound, receptor placement, DOI/archive, and external-dataset work as gated rather than hiding the weak parts.
- `/pi-review/`, decision gates, claim ledger, methods, and figure atlas sources now give the right public-information architecture.
- The dynamic robustness story is useful: C has strong internal rank stability, E is split, and B is kept visible as a negative baseline.
- Static publication uses derived artifacts rather than raw datasets.
- Contract tests already protect several public-page markers.

## 4. P0 Dealbreakers

| Dealbreaker | Current State | Required Fix |
| --- | --- | --- |
| Motion/confound proof | Blocked: no subject/run FD, DVARS, censoring/outlier confound tables in local evidence | Keep public blocker visible; do not promote C beyond proxy-supported until proof exists |
| Public entrypoint | Local rebuild plan exists, but live/static state may be stale | Make `/pi-review/` canonical and root sparse after build/deploy |
| Claim vocabulary | Legacy statuses leaked: `supported_first_pass`, `not_supported_yet`, `reject_as_main_claim` | Normalize public claim labels to `implemented`, `proxy-supported`, `mixed`, `unsupported`, `blocked`, `future` |
| Archive/DOI | GitHub release and Zenodo DOI states are separate; DOI remains missing | Preserve split state everywhere |
| Stale exports | Dynamic exports were older than current JSON/robustness evidence | Regenerate or clearly deprecate export bundle |

## 5. Scientific Claim Audit

| Claim | Location | Evidence Source | Status | Problem | Required Fix |
| --- | --- | --- | --- | --- | --- |
| C is current top layer | README, dashboard, dynamic reports | `results/dynamic_mechanism_ranking/summary.json`; robustness CSV | proxy-supported | Some wording implied strongest LSD mechanism | Say leading macro-dynamic proxy, motion-gated |
| E lower transition/control energy | dynamic summary and robustness | E horizon/control-energy rows | proxy-supported | Often collapsed with receptor placement | Name as E1 lower-energy proxy |
| E receptor-specific placement | claim verdicts, receptor-prior artifacts | receptor-vs-random; PET/spatial-null status | unsupported | Positive E language can over-promote receptor claims | Name as E2 unsupported/future |
| B as main control result | claim verdicts | B score and rank-1 fraction | unsupported | Rejected claim text was quote-unsafe | Phrase as rejected candidate and negative-control baseline |
| ds006072 | thesis loop, PI pages | ds006072 status JSON | mixed | Called external validation too easily | Call external cross-dataset stress test |
| Public dashboard readiness | PI package CSV/pages | thesis upgrade status and `_site` state | blocked/mixed | Presentation readiness drifted from current build state | Regenerate static site and gate wording |

## 6. Mechanism Language Audit

- Replace public "mechanism ranking" with "mechanism-proxy ranking."
- Replace "strongest mechanism" with "leading current proxy family."
- Replace "external validation" with "cross-dataset stress test" unless strict comparability is proved.
- Replace "bootstrap confidence" with "cached sensitivity interval" unless a population target is explicitly defined.
- Keep "completed thesis" only in negated phrases such as "not completed neuroscience thesis."

## 7. C/E/B Audit

- C: acceptable only as a provisional leading macro-dynamic proxy with motion/confound and atlas caveats.
- E: split into E1 lower transition/control-energy proxy and E2 receptor-specific placement.
- B: keep as implemented negative-control baseline; unsupported as the main control-theory result.

## 8. Motion/Confound Gate Audit

The strict gate remains blocked. The required evidence is subject/session/run FD, DVARS, censoring/outlier burden, and confound-regression sensitivity joined to the motion-sensitive FC/dynamic metrics. Image-derived QC, module-DVARS proxies, published aggregate FD context, and OpenNeuro filename checks are useful context only.

## 9. Evidence And Provenance Audit

Top-level numbers generally have source artifacts, but derived PI-package CSVs can drift from current JSON/robustness artifacts. Figure cards should retain claim, status, role, source data, calculation note, and required next check. Static pages must distinguish source data, calculation routes, blocker artifacts, and future work.

## 10. Information Architecture Audit

Recommended public route hierarchy:

- `/`: sparse router, not a dense dashboard
- `/pi-review/`: canonical first read
- `/pi-review/pages/decision-gates.html`: blockers and decisions
- `/pi-review/pages/claim-ledger.html`: claim-to-evidence map
- `/pi-review/pages/figure-atlas.html`: curated visual route
- `/pi-review/pages/evidence-and-calculations.html`: evidence ledger before numeric detail
- `/dashboard/`: technical evidence console, not first read

Demote `full-package.html`, old meeting agenda, dashboard-offline screenshots, and legacy route-map pages to appendix/deep-audit status.

## 11. Code/Build/Repo Health Audit

The stack is Python 3.13 with `uv`, FastAPI/Jinja dashboard templates, Plotly JS, and a static GitHub Pages builder. The build script has side effects: it refreshes evidence-loop, motion, archive, thesis-upgrade, and static output artifacts. Do not hand-edit `_site/`; regenerate it. Contract tests are the right guard for public route semantics.

## 12. Accessibility And Figure Quality Audit

Dashboard accessibility is stronger than the PI package. Remaining risks are generic screenshot alt text, clipped long status tokens, dense nav variants, and chart labels that imply more certainty than the evidence supports. Public figure cards need descriptive links and status text that wraps without hiding caveats.

## 13. Release/Archive Audit

GitHub release exists and Zenodo DOI/public reproducible archive remains missing. Pages publication, GitHub release, and DOI/archive completion must stay separate. A static dashboard can be presentation-ready without being a citable archive.

## 14. Backlog

P0:
- Keep motion/confound proof blocked and first-visible.
- Normalize public claim-status vocabulary.
- Regenerate or deprecate stale dynamic exports.
- Make `/pi-review/` canonical and root sparse after build.

P1:
- Split E everywhere.
- Make B quote-safe everywhere.
- Demote dashboard to technical console.
- Add/root maintain `CONTEXT.md` terminology.

P2:
- Merge or demote redundant PI-package routes.
- Improve alt text and focus/keyboard behavior in static package pages.
- Add stronger link/static-route checks.

P3:
- New motion-proof data acquisition.
- Structural/PET/spatial-null promotion work.
- Atlas-level replication beyond current cached artifacts.
- External validation beyond mixed cross-dataset stress test.

## 15. What Not To Say

- Do not say "completed neuroscience thesis"; say "research-demo evidence package."
- Do not say "C is the LSD mechanism"; say "C is the leading current macro-dynamic proxy."
- Do not say "E proves receptor-specific NCT"; say "E1 lower-energy proxy is supported; E2 receptor-specific placement is unsupported/future."
- Do not say "external validation"; say "external cross-dataset stress test" unless comparability is proved.
- Do not say "Zenodo archive complete" while DOI verification is missing.

## 16. Reviewer Attack Surface

| Question | Current Answer |
| --- | --- |
| Did motion drive the FC/dynamic result? | Fails until FD/DVARS/censoring proof exists |
| Is C a biological mechanism? | No; proxy-supported only |
| Does E prove receptor placement? | No; unsupported/future |
| Why trust ds006072? | Mixed stress test, not clean validation |
| Which URL should I open? | `/pi-review/` should be canonical |
| Are exports current? | Must be regenerated and verified |
| Is the archive citable? | GitHub release yes; Zenodo DOI no |
| Are prior-art comparisons reproductions? | No; alignment/context unless recreated with method equivalence |
| Are bootstrap intervals population CIs? | No; cached sensitivity intervals |
| Is the dashboard the thesis? | No; technical evidence console |

## 17. Final Recommendation

This pass should implement wording, status, route, and export-hygiene fixes. It should not claim to close the motion gate or DOI gate. The next scientific pass must be motion-proof-first: authorized fMRIPrep confounds, subject/run joins, association rows, and downgrade rules for C if motion-sensitive evidence fails.
