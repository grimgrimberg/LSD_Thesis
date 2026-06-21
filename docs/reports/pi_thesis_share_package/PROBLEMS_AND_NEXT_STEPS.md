# Problems And Next Steps

## Summary

The project is ready for PI review as a claim-gated research workbench. It is not ready to be presented as a completed thesis. The next useful decision is which blocker must be closed first.

## Problem 1: Motion/Confound Proof Remains Incomplete

Why it matters: Motion, session effects, and preprocessing artifacts can mimic or distort macro-dynamic changes.

Current status: Blocked. `results/thesis_upgrade/thesis_upgrade_status.json` reports `motion_confound_control_result` as `blocked_missing_fmriprep_fd_dvars_censoring_motion_proof`.

Evidence/source file: `results/thesis_upgrade/thesis_upgrade_status.json`; `docs/VALIDATION.md`.

Needed to address it: Authorized subject/run motion confounds or original raw BIDS inputs, fMRIPrep/MRIQC execution in a suitable environment, and ingestion of FD, DVARS, censoring/outlier tables.

Suggested next action: Create a motion-proof planning pack that lists exact required inputs, expected output tables, predicates, and approval gates before running anything.

Risk if ignored: The thesis can overstate mechanism ranking from data that may still be confounded.

## Problem 2: FD/DVARS/Censoring Is Thesis-Critical

Why it matters: The strict predicate requires FD, DVARS, and censoring/outlier family coverage, not only image-level or proxy QC.

Current status: Incomplete. Current artifacts record image-derived QC and related context, but not the strict fMRIPrep FD/DVARS/censoring proof.

Evidence/source file: `results/thesis_upgrade/thesis_upgrade_status.json`; `results/confound_controls/fmriprep_motion_proof_plan.json` as referenced by the status artifact.

Needed to address it: Paired motion-control rows, merged subject/run rows, non-empty association rows, and feature-family coverage for FD, DVARS, and censoring.

Suggested next action: Build the motion-proof planning pack first, then use that pack to determine whether author-provided confounds or original raw inputs are worth pursuing.

Risk if ignored: C and other ranking claims remain vulnerable at the thesis-defense level.

## Problem 3: Zenodo DOI / Archive Publication Is Incomplete

Why it matters: A GitHub release is not the same as a citable reproducibility archive.

Current status: Blocked. The archive manifest records a verified GitHub release URL but no DOI.

Evidence/source file: `results/reproducible_archive/ARCHIVE_MANIFEST.json`.

Needed to address it: Mint and verify a Zenodo DOI, then update the reproducible archive manifest in an approved archive-specific pass.

Suggested next action: Treat DOI work as a packaging milestone after PI approval of the scientific framing.

Risk if ignored: The project can be review-ready but not citation/archive-ready.

## Problem 4: External/PET/Receptor/Neuromaps/SC Evidence Must Stay Gated

Why it matters: These surfaces can make the project sound biologically stronger than the current artifact contract allows.

Current status: Mixed. Some status artifacts report implemented sensitivity or stress-test layers, but receptor/myelin/gradient claims are explicitly not promoted.

Evidence/source file: `results/thesis_upgrade/thesis_upgrade_status.json`; `docs/research/ds003059_prior_art_to_thesis_map.md`.

Needed to address it: A separate audit plan that distinguishes implemented sensitivity checks from biological mechanism claims.

Suggested next action: Create an external/PET/SC/neuromaps evidence audit plan only after the PI agrees on scope and claim thresholds.

Risk if ignored: The thesis may overclaim receptor-specific or external-validation support.

## Problem 5: Run-02/Music Remains Audit-Only

Why it matters: Run-02 has a music-listening context and cannot be treated as equivalent to primary resting-state evidence.

Current status: Gated. Current primary ranking uses run-01 and run-03. Run-02/music remains audit-only unless explicitly approved.

Evidence/source file: `docs/research/ds003059_prior_art_to_thesis_map.md`; `docs/VALIDATION.md`; project instructions in `AGENTS.md`.

Needed to address it: Music-qualified subject rules, technical-problem exclusions, motion/context checks, and explicit PI approval.

Suggested next action: Keep run-02/music out of the thesis core until the motion-proof decision is made.

Risk if ignored: The project can mix incompatible task contexts and weaken the empirical claim.

## Problem 6: Generated Artifacts And Ignored Outputs Are Risky To Clean Or Regenerate

Why it matters: Ignored generated outputs may still be consumed by the dashboard, figure deck, archive manifest, or public snapshot.

Current status: High-risk. The artifact inventory says `results/`, `_site/`, and `output/` include tracked evidence plus ignored generated files.

Evidence/source file: `docs/reports/results_artifact_inventory.md`; `docs/reports/project_state_handoff/PROJECT_STATE_HANDOFF.md`.

Needed to address it: Producer/consumer mapping before any cleanup, deletion, regeneration, or tracking-policy change.

Suggested next action: Create an artifact producer/consumer map as a docs-only planning pass.

Risk if ignored: Review artifacts, public payloads, or test contracts can silently drift.

## Problem 7: Public/Static Payload Drift Needs Caution

Why it matters: Static public output can diverge from local dashboard payloads if Pages builds are run casually.

Current status: Presentation-ready snapshot exists, but no Pages/publication build was run for this package.

Evidence/source file: `docs/reports/project_state_handoff/PROJECT_STATE_HANDOFF.md`; `docs/reports/dashboard_visual_review.md`.

Needed to address it: A no-regeneration drift audit comparing static snapshot and local payload expectations.

Suggested next action: Audit drift as a report-only pass before any new Pages/publication build.

Risk if ignored: PI or public reviewers may see stale status labels or artifact links.

## Problem 8: Dashboard Visual Polish Is Useful But Not The Main Blocker

Why it matters: Visual polish improves presentation, but it does not close scientific gates.

Current status: Future. `docs/reports/dashboard_visual_review.md` recommends CSS-only status-token and first-viewport polish, but this PI package intentionally did not implement it.

Evidence/source file: `docs/reports/dashboard_visual_review.md`.

Needed to address it: A separate CSS-only pass after claim boundaries are fixed and scientific blockers are prioritized.

Suggested next action: Defer visual polish until after PI review of the scientific next step.

Risk if ignored: Low scientific risk, moderate presentation risk.

## Ranked Next Thesis Milestones

1. Motion-proof planning pack.
2. External/PET/SC/neuromaps evidence audit plan.
3. Public-site/static drift audit.
4. Artifact producer/consumer map.
5. Dashboard visual polish only after claim boundaries remain fixed.
6. Package/developer-experience proposal.
