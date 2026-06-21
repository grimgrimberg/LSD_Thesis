# Subagent / Workstream Findings

## Project State Auditor

Files inspected:

- `AGENTS.md`
- `README.md`
- `ARCHITECTURE.md`
- `SPEC.md`
- `docs/VALIDATION.md`
- `docs/reports/project_state_handoff/PROJECT_STATE_HANDOFF.md`
- `docs/reports/project_state_handoff/CHATGPT_PASTEBACK.md`
- `docs/reports/project_state_handoff/manifest.json`
- `docs/reports/dashboard_visual_review.md`

Findings:

- Current branch: `audit/full-cleanup-and-prior-art`.
- Current HEAD: `1a51eb54d909cbda6bf3584cd2ecf99f187c355d`.
- Validation-baseline commit: `69b0397 docs: refresh validation baseline`.
- Current status before package creation had one allowed untracked file: `docs/reports/dashboard_visual_review.md`.
- Current documented validation baseline: ruff passed, mypy passed on 109 source files, collect-only found 82 tests, latest full pytest baseline was 82 passed with 82.69% coverage, `uv pip check` passed, dashboard strict preflight passed, and dashboard JS syntax passed.
- Thesis readiness: 6/9; strict completion: 4/6; package readiness: 1/2.
- Motion/confound proof and Zenodo DOI remain blocked.

Uncertainty:

- The prior handoff manifest snapshots commit `69b0397`, while current HEAD is `1a51eb5` because the handoff package was later committed.

Deliverables created:

- Current-state facts used in `PI_REVIEW_BRIEF.md`, `README_SEND_TO_PI.md`, `PROBLEMS_AND_NEXT_STEPS.md`, and `manifest.json`.

No-touch confirmations:

- No source, tests, scripts, templates, CSS, JS, result artifacts, docs/reference, dependencies, staging, commits, servers, workflows, downloads, or publication actions.

## Evidence And Calculation Analyst

Files inspected:

- `results/dynamic_mechanism_ranking/summary.json`
- `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`
- `results/dynamic_mechanism_ranking/robustness/*.csv`
- `results/dynamic_mechanism_ranking/exports/*.csv`
- `results/stage_2/empirical_viewer/group_overview.json`
- `results/stage_1/stage_1_summary.json`
- `results/stage_2/stage_2_summary.json`
- `results/thesis_upgrade/thesis_upgrade_status.json`
- `results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json`
- `results/reproducible_archive/ARCHIVE_MANIFEST.json`
- `src/lsd_thesis/web/dashboard_payload.py`
- `src/lsd_thesis/web/figure_payload.py`
- `src/lsd_thesis/publication_figures.py`

Findings:

- Mechanism ranking values are safely extractable: C, E, D, A, B.
- C has bootstrap rank-1 fraction 0.843750.
- B has bootstrap rank-1 fraction 0.000000 and remains a negative baseline.
- Empirical viewer group deltas are safely extractable for 8 metrics.
- Figure Deck status cards are backed by thesis status, CV5, and archive artifacts.
- The two publication figures have recoverable calculations from `publication_figures.py`.

Uncertainty:

- Historical setting/seed screenshot values were not safely recovered in this packaging pass and are treated as historical/context-only.

Deliverables created:

- `EVIDENCE_AND_CALCULATIONS.md`
- nine derived CSV tables under `assets/data/`.

No-touch confirmations:

- No workflows were rerun and no scientific output was regenerated.

## Visual Publishing Curator

Files inspected:

- `docs/reports/project_state_handoff/assets/screenshots/`
- `docs/reports/project_state_handoff/assets/representative_figures/`
- `docs/reports/project_state_handoff/manifest.json`

Findings:

- All six preferred dashboard screenshots exist.
- All four preferred representative figures exist.
- Visual review recommends future CSS-only polish, but this package did not implement it.

Uncertainty:

- Full-page screenshots were not created here; existing viewport screenshots were reused.

Deliverables created:

- Copied screenshots under `assets/screenshots/`.
- Copied figures under `assets/figures/`.
- Offline static landing page under `site/`.
- Package-only CSS under `assets/css/pi_package.css`.

No-touch confirmations:

- Original images were not modified.
- Existing dashboard CSS/JS/templates were not touched.

## Scholarly Context Analyst

Files inspected:

- `prior_art/README.md`
- `prior_art/code_inventory.md`
- `prior_art/reproducibility_matrix.md`
- `prior_art/repository_manifest.md`
- `prior_art/repository_metadata.md`
- `prior_art/archive_manifest.md`
- all 12 files under `prior_art/runbooks/`
- `docs/research/ds003059_prior_art_to_thesis_map.md`
- `docs/research/dynamic_mechanism_literature_support.md`
- `docs/research/network_control_graph_theory_upgrade.md`
- `docs/research/psychedelic_dynamics_targets.md`

Findings:

- Prior art supports context and method design, not automatic local proof.
- Singleton-style control-energy work maps to E, but receptor-specific placement remains unsupported.
- Music brain-state work maps to A/C/D but run-02/music remains blocked for primary claims.
- Entropy, Ising, gradients, dynamic integration, REACT, receptor maps, and consciousness analyses are useful scholarly context with clear limitations.

Uncertainty:

- Bibliographic metadata is incomplete for some entries; missing details were not invented.

Deliverables created:

- `SCHOLARLY_CONTEXT.md`.

No-touch confirmations:

- No external repositories, runbooks, or prior-art files were modified.

## Methods And Data-Skills Analyst

Files inspected:

- `pyproject.toml`
- `src/lsd_thesis/core.py`
- `src/lsd_thesis/simulator.py`
- `src/lsd_thesis/metrics.py`
- `src/lsd_thesis/metrics_literature.py`
- `src/lsd_thesis/dynamic_mechanism/`
- `src/lsd_thesis/dynamic_robustness.py`
- `src/lsd_thesis/data/ds003059/`
- `src/lsd_thesis/web/`
- selected tests under `tests/`

Findings:

- The repo shows applied Python, fMRI summary handling, surrogate modeling, dashboarding, artifact-contract, validation, and reproducibility skills.
- Codex/autoresearch should be framed as engineering assistance, not scientific approval.

Uncertainty:

- No fresh tests or workflows were run by this workstream.

Deliverables created:

- `METHODS_AND_DATA_SKILLS.md`.

No-touch confirmations:

- No source or tests were edited.

## PI Communication Writer

Files inspected:

- Project handoff docs.
- Validation docs.
- Evidence extraction outputs.
- Scholarly/methods findings.

Findings:

- The PI message should be direct: the package is ready for review, not final defense.
- The decision request should focus on the next scientific blocker.

Uncertainty:

- Final wording may need adjustment for the PI's personal style.

Deliverables created:

- `EMAIL_TO_PI.md`
- `PI_MEETING_SCRIPT.md`
- PI-facing sections in `PI_REVIEW_BRIEF.md`.

No-touch confirmations:

- No email was sent.

## Publication / Sharing Packager

Files inspected:

- Package requirements from the user request.
- Existing handoff package structure.

Findings:

- The safest share paths are email attachment, ZIP, GitHub folder link after commit/push, cloud-drive link, and future static hosting after PI approval.

Uncertainty:

- No external link exists because no upload/publish action was taken.

Deliverables created:

- `PUBLICATION_OPTIONS.md`
- `README_SEND_TO_PI.md`
- `site/README.md`
- `site/index.html`

No-touch confirmations:

- No upload, Pages build, release, PR, issue, email, staging, commit, or push.

## QA And Guardrail Reviewer

Files inspected:

- Initial and final `git status --short --untracked-files=all`.
- Package file list.
- Manifest JSON.
- Derived table list.
- Validation command outputs.

Findings:

- Package writes stayed under `docs/reports/pi_thesis_share_package/`.
- Pre-existing allowed untracked input remains `docs/reports/dashboard_visual_review.md`.
- Claims are framed as model-level macro-dynamic proxy evidence with blocked gates visible.

Uncertainty:

- Full pytest was not rerun; current full-suite baseline remains the documented 82 passed with 82.69% coverage.

Deliverables created:

- `manifest.json` QA fields and final no-touch confirmations.

No-touch confirmations:

- No source, tests, scripts, templates, existing CSS/JS, routes, schemas, result artifacts, ignored outputs, raw data, caches, private data, docs/reference, pyproject, uv.lock, or dependencies were modified.
