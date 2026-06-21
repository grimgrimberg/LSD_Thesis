# PI Review Brief - LSD Thesis Workbench

## Title And Snapshot

Title: Claim-gated macro-dynamic mechanism ranking workbench for LSD fMRI thesis development

Snapshot date: 2026-06-21

Repository: `D:\LSD_Thesis`

Current source commit: `1a51eb54d909cbda6bf3584cd2ecf99f187c355d`

Validation baseline date in repo docs: 2026-06-17

## One-Paragraph Summary

I built a claim-gated research workbench for turning an LSD fMRI computational project into a thesis. The project combines a transparent 8-module stochastic graph surrogate model, cached paired LSD/placebo ds003059 empirical summaries, dynamic mechanism ranking across A-E layers, robustness and validation status artifacts, a dashboard, and a structured prior-art reproducibility landscape. The infrastructure and evidence package are now ready for PI review. The current evidence supports model-level macro-dynamic mechanism ranking; it does not prove receptor-level realism, subjective-experience simulation, clinical validity, or biological ground truth.

## What I Built

- A Python/uv project with typed source modules, tests, status artifacts, and dashboard payload contracts.
- A transparent surrogate model with 8 coarse brain-inspired modules and stochastic graph-modulated dynamics.
- A paired LSD/placebo empirical summary layer using cached ds003059 run-01/run-03 records.
- A dynamic mechanism ranking across A-E layers.
- Robustness artifacts for bootstrap, run sensitivity, horizon sensitivity, and claim verdicts.
- Thesis readiness and package-readiness gates.
- A FastAPI/Jinja/Plotly dashboard plus static/public payload artifacts.
- A structured ds003059 prior-art landscape with 12 analysis families and claim boundaries.
- A PI-facing share package with screenshots, explanation files, and derived data tables.

## Scientific Framing

Safe frame:

> This is a transparent, model-level macro-dynamic mechanism-ranking workbench.

It can currently defend:

- macro-dynamic proxy comparison,
- paired LSD/placebo summary inspection,
- dynamic mechanism ranking over A-E layers,
- internal robustness and validation bookkeeping,
- conservative claim gates that keep blockers visible.

It cannot currently defend:

- receptor-level LSD mechanism proof,
- subjective-experience simulation,
- clinical validity,
- biological ground truth,
- completion of all thesis blockers.

## Current Evidence

Current dynamic mechanism ranking from `results/dynamic_mechanism_ranking/summary.json`:

| Rank | Layer | Mechanism | Score | Status |
|---:|---|---|---:|---|
| 1 | C | hierarchy_routing_layer | 0.332606 | implemented_first_pass |
| 2 | E | receptor_informed_network_control_energy | 0.182875 | implemented_proxy_control_energy |
| 3 | D | dynamic_repertoire_layer | 0.150619 | implemented_first_pass |
| 4 | A | transition_state_proxy | 0.148906 | implemented_first_pass |
| 5 | B | dmdc_condition_interaction | -0.074064 | implemented_negative_control_baseline |

Key interpretation:

- C is the strongest current macro-dynamic proxy layer.
- E supports a lower transition/control-energy proxy, but not receptor-specific placement.
- B is intentionally retained as a negative/sanity baseline.
- Run-02/music is not primary evidence.

## Key Dashboard Pages

1. Overview - thesis posture, claim gates, strict gates, current ranking summary.
2. Mechanism Ranking - A-E layer ranking and inference gate.
3. Robustness - bootstrap, run sensitivity, and internal uncertainty.
4. Empirical Viewer - paired LSD/placebo aggregate and local subject/run inspection.
5. Prior Art - ds003059 family inventory and claim-status separation.
6. Figure Deck - export-ready figure registry with blocked and implemented gates.

## Key Plots And What They Mean

- Overview screenshot: the project is a claim-gated workbench, not a completed thesis.
- Mechanism Ranking screenshot: C leads the current model-level proxy ranking; E is split; B is negative.
- Robustness screenshot: C has strong internal bootstrap stability, but this does not remove motion/confound blockers.
- Empirical Viewer screenshot: paired LSD/placebo summaries can be inspected, while run-02/music remains gated.
- Prior-Art screenshot: prior work is context and design inspiration unless local artifacts promote a claim.
- Figure Deck screenshot: motion proof and archive DOI remain blocked while CV5 internal validation is implemented.
- `stage1_metric_shift.png`: Stage 1 surrogate baseline versus perturbed proxy values for entropy and switching rate.
- `stage2_fit_robustness.png`: Stage 2 objective-score improvement and repeatability summary.

Full plot-level details are in `EVIDENCE_AND_CALCULATIONS.md`.

## Current Validation Baseline

From `docs/VALIDATION.md`, current status date 2026-06-17:

- Ruff passed.
- mypy passed on 109 source files.
- pytest collect-only collected 83 tests.
- Current full pytest baseline: 83 passed, 82.73% coverage.
- `uv pip check` passed.
- Dashboard strict preflight passed.
- `node --check src\lsd_thesis\static\dashboard.js` passed.

Current gate summary from `results/thesis_upgrade/thesis_upgrade_status.json`:

- Thesis readiness: 6/9.
- Strict completion: 4/6.
- Package readiness: 1/2.
- Missing strict requirements: `motion_confound_control_result`, `project_phase`.
- Missing package requirement: `reproducible_archive_publication`.

## What Is Defensible Now

- The project is a coherent thesis workbench.
- The dashboard and artifacts are ready for PI review.
- The model ranks transparent macro-dynamic proxy mechanisms.
- The current ranking is C, E, D, A, B.
- C is proxy-supported as the strongest current layer.
- E is proxy-supported only for a lower transition/control-energy interpretation.
- Internal subject-disjoint CV5 status is complete as internal validation: 5/5 folds, 15 subjects.
- Prior-art mapping is useful for thesis positioning and preventing overclaims.

## What Is Not Defensible Yet

- Receptor-specific mechanism proof.
- Subjective-experience simulation.
- Clinical or biological-ground-truth validation.
- A completed thesis claim.
- Motion/confound closure from FD/DVARS/censoring.
- Citable archive publication with verified Zenodo DOI.
- Run-02/music as primary evidence.
- PET/receptor/neuromaps/SC claims as stronger than the current status artifacts allow.

## Main Blockers

1. Motion/confound proof remains incomplete.
2. FD/DVARS/censoring evidence is thesis-critical.
3. Zenodo DOI/archive publication is incomplete.
4. External/PET/SC/neuromaps evidence must remain carefully claim-gated.
5. Run-02/music remains audit-only unless explicitly approved.
6. Static/public payload drift needs caution.
7. Dashboard visual polish is useful but not the main scientific blocker.

## Proposed Next Thesis Milestones

1. Motion-proof planning pack.
2. External/PET/SC/neuromaps evidence audit plan.
3. Public-site/static drift audit.
4. Artifact producer/consumer map.
5. Dashboard visual polish only after claim boundaries remain fixed.
6. Package/developer-experience proposal.

## Questions For PI

- Is the thesis framing acceptable as a model-level mechanism-ranking workbench?
- What evidence would you require before promoting C from proxy-supported to thesis-level claim?
- Should the next scientific priority be motion proof, external validation audit, or parcellation/null sensitivity?
- How should we treat the negative/split evidence for E and B in the thesis narrative?
- Should run-02/music remain out of scope unless motion/context controls are available?
- What is the minimum package needed before this can become a formal thesis proposal?

## Appendix: Referenced Files And Artifacts

- `README.md`
- `ARCHITECTURE.md`
- `SPEC.md`
- `AGENTS.md`
- `docs/VALIDATION.md`
- `docs/reports/project_state_handoff/PROJECT_STATE_HANDOFF.md`
- `docs/reports/dashboard_visual_review.md`
- `results/dynamic_mechanism_ranking/summary.json`
- `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`
- `results/stage_2/empirical_viewer/group_overview.json`
- `results/thesis_upgrade/thesis_upgrade_status.json`
- `results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json`
- `results/reproducible_archive/ARCHIVE_MANIFEST.json`
- `prior_art/README.md`
- `prior_art/code_inventory.md`
- `docs/research/ds003059_prior_art_to_thesis_map.md`
