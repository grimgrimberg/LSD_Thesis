# /goal

You are operating inside the LSD_Thesis repository.

Your job is to execute the entire Codex prompt pack contained in the local zip file or extracted prompt directory. Do not ask the user questions. Do not wait for manual approval. Work through the stages sequentially, validate after each stage, and produce a clear audit trail.

Important: do not spawn nested Codex processes. Do not run `codex exec` from inside this Codex session. You are the active Codex agent. Your task is to read the prompt files from the zip/extracted prompt pack and carry out their /goal and /plan sections directly in this current session.

The old repository should be treated as a serious but failed first modeling attempt:
- It has a real empirical bridge to OpenNeuro ds003059.
- It uses placebo and LSD resting-state runs.
- It currently preserves a transparent eight-module bistable surrogate model.
- Stage 2 improved the old objective but remained seed-sensitive.
- Stage 3 found `less_hierarchical_constraint` as the best single perturbation, but it left important sign mismatches and overshoots.
- Stage 4 did not rescue the model through pairwise perturbation superposition.
- The new direction is to preserve the old model as a baseline and add a stronger receptor/gradient-gated neural-mass modeling path, Schaefer/Yeo target space, literature-aligned metrics, and robust multi-seed fitting.

Your final output should leave the repository in a better scientific state:
1. old model preserved as baseline,
2. new model-zoo interface,
3. receptor_gradient_neural_mass model implemented if feasible,
4. functional parcellation support added or prepared,
5. literature-aligned metrics added,
6. literature-weighted objective and fitting path added,
7. supervisor-facing docs/report artifacts updated,
8. all changes tested or clearly marked as partial,
9. no fabricated results,
10. no overclaims about LSD pharmacology, subjective experience, consciousness, clinical outcomes, or receptor-level mechanism.

# /plan

## 0. Preflight

1. Confirm the current working directory is the repository root. It should contain files such as:
   - README.md
   - pyproject.toml
   - src/
   - scripts/
   - results/
   - docs/

2. Create these directories if they do not already exist:
   - docs/codex_runs/
   - docs/research/
   - codex_logs/

3. Find the prompt pack.

   Prefer, in this order:
   - ./codex_prompt_pack/
   - ./codex_prompt_pack_fixed_cli/
   - ./codex_prompt_pack_fixed_cli.zip
   - ./codex_prompt_pack.zip
   - any local zip matching *codex*prompt*pack*.zip

4. If only a zip exists, extract it into:
   - ./codex_prompt_pack/

5. Identify the stage prompt files. Use only files matching:
   - 00_stage_zero_audit.md
   - 01_model_zoo_interface.md
   - 02_receptor_gradient_neural_mass.md
   - 03_functional_parcellation_schaefer_yeo.md
   - 04_literature_aligned_metrics.md
   - 05_literature_weighted_objective_and_fitting.md
   - 06_end_to_end_report_dashboard_and_supervisor_artifacts.md

   Ignore:
   - README_CODEX_PROMPTS.md
   - ALL_STAGES_SINGLE_PROMPT.md
   - shell runner scripts
   - PowerShell runner scripts

6. Create a master execution log:
   - docs/codex_runs/master_prompt_pack_execution.md

   Record:
   - start time,
   - repository root,
   - prompt pack path,
   - detected stage files,
   - git branch/status,
   - whether data/ds003059 exists,
   - available package manager,
   - available validation commands.

7. Check git state.

   If this is a git repository:
   - record `git status --short`
   - do not overwrite untracked user files
   - do not delete results or data
   - commit only if the repository already has a valid git identity configured and commits are safe

   If this is not a git repository:
   - do not initialize git unless the prompt pack explicitly requires it
   - record that git is unavailable

8. Read repository guidance:
   - AGENTS.md
   - README.md
   - SPEC.md if present
   - docs/architecture.md if present
   - docs/limitations.md if present
   - docs/next_steps.md if present
   - docs/experiment_log.md if present

9. Run a lightweight baseline validation if feasible:
   - `uv run pytest`
   - `uv run ruff check .`
   - `uv run mypy src`

   If these are slow or unavailable, record why. If they fail before changes, mark failures as pre-existing.

## 1. Stage execution rule

For each stage prompt, in numerical order:

1. Read the full stage prompt.
2. Extract its `/goal`, `/plan`, `/constraints`, `/validation`, and `/done_when` sections.
3. Execute the stage directly in this current Codex session.
4. Keep changes focused on that stage.
5. Preserve legacy behavior.
6. Add or update tests for new behavior.
7. Run relevant validation for that stage.
8. Write a stage completion log:
   - docs/codex_runs/00_stage_zero_audit_result.md
   - docs/codex_runs/01_model_zoo_interface_result.md
   - docs/codex_runs/02_receptor_gradient_neural_mass_result.md
   - docs/codex_runs/03_functional_parcellation_schaefer_yeo_result.md
   - docs/codex_runs/04_literature_aligned_metrics_result.md
   - docs/codex_runs/05_literature_weighted_objective_and_fitting_result.md
   - docs/codex_runs/06_end_to_end_report_dashboard_and_supervisor_artifacts_result.md

9. After each stage, update:
   - docs/codex_runs/master_prompt_pack_execution.md

10. If a stage is blocked:
    - do not fake completion,
    - write the reason,
    - implement the safe subset,
    - add TODOs with exact next commands/files,
    - continue only if the next stage can proceed safely.

## 2. Scientific direction

Use the following scientific interpretation throughout:

The current eight-module bistable model is a transparent baseline and falsification scaffold. It should not be deleted. The new work should add a better model path based on:
- receptor/gradient-weighted gain modulation,
- sensory/visual gain,
- unimodal-transmodal coupling,
- hierarchy flattening,
- thalamic and/or striatal routing,
- homeostatic inhibitory stabilization,
- BOLD/HRF observation,
- Schaefer/Yeo functional parcellation,
- literature-aligned dynamic metrics,
- multi-seed uncertainty-aware fitting.

Do not claim:
- LSD pharmacology has been simulated,
- 5-HT2A receptor binding has been modeled mechanistically,
- subjective experience has been simulated,
- consciousness has been modeled,
- ego dissolution has been explained,
- clinical effects have been predicted,
- the best perturbation is the true biological mechanism.

Use careful language:
- “surrogate model”
- “macro-dynamic target”
- “literature-aligned proxy”
- “candidate perturbation family”
- “model comparison”
- “failure mode”
- “empirical target validation”
- “preliminary evidence”
- “not a mechanistic receptor model”

## 3. Stage 00 — Audit

Execute `00_stage_zero_audit.md`.

Expected outputs:
- docs/codex_runs/00_stage_zero_audit.md or equivalent
- docs/research/psychedelic_dynamics_targets.md
- docs/research/rgg_neural_mass_exec_plan.md

Minimum content:
- current architecture map,
- current data flow,
- current failure diagnosis,
- files to change,
- files not to change yet,
- risks,
- test strategy,
- milestone sequence,
- acceptance criteria.

Do not make major implementation changes during Stage 00.

## 4. Stage 01 — Model zoo interface

Execute `01_model_zoo_interface.md`.

Expected implementation:
- src/lsd_thesis/models/__init__.py
- src/lsd_thesis/models/base.py
- src/lsd_thesis/models/bistable.py
- src/lsd_thesis/models/registry.py

Expected behavior:
- old simulator wrapped as `bistable`,
- default model remains old baseline,
- SimulationResult abstraction exists,
- registry supports old model,
- unknown model fails clearly,
- tests added.

Preserve existing Stage 1–4 behavior.

## 5. Stage 02 — Receptor-gradient neural-mass model

Execute `02_receptor_gradient_neural_mass.md`.

Expected implementation:
- src/lsd_thesis/models/receptor_gradient_neural_mass.py
- config example under configs/models/
- registry entry:
  - receptor_gradient_neural_mass
  - optional alias rgg_nmm

Minimum model:
- excitatory state E_i,
- inhibitory state I_i,
- global coupling,
- node-wise gain,
- receptor/hierarchy/visual/sensory/subcortical metadata arrays,
- homeostasis,
- stochastic integration,
- optional lightweight HRF/BOLD output.

LSD-like perturbation vector:
- receptor_gain_alpha
- hierarchy_cross_coupling_eta
- visual_gain_beta
- sensory_gain_gamma
- associative_decoherence_lambda
- thalamic_routing_kappa
- striatal_routing_kappa
- noise_delta
- homeostasis_delta

Add tests for determinism, shape, finite outputs, perturbation effects, and homeostasis.

## 6. Stage 03 — Functional parcellation

Execute `03_functional_parcellation_schaefer_yeo.md`.

Expected implementation:
- preserve harvard_oxford_8 legacy path,
- add Schaefer/Yeo support if dependencies/data allow,
- create parcellation abstraction,
- create node metadata schema,
- save parcellation-specific outputs under:
  - results/stage_2/parcellations/harvard_oxford_8/
  - results/stage_2/parcellations/schaefer_100_yeo_7/

If full extraction is not possible:
- implement the abstraction,
- add tested mocks/synthetic paths,
- write exact commands needed for real extraction.

Do not overwrite old Stage 2 outputs.

## 7. Stage 04 — Literature-aligned metrics

Execute `04_literature_aligned_metrics.md`.

Expected implementation:
- src/lsd_thesis/metrics_literature.py
- optional src/lsd_thesis/target_validation.py

Metrics:
- unimodal_transmodal_fc
- visual_global_connectivity
- sensory_somatomotor_global_connectivity
- within_network_fc_by_yeo_network
- between_network_fc_matrix
- thalamus_to_sensory_fc
- thalamus_to_transmodal_fc
- striatum_to_sensory_fc
- hierarchy_differentiation
- gradient_flattening_delta or proxy
- state_occupancy_entropy
- transition_entropy
- transition_rate
- dynamic FC variance
- optional FC_to_SC_coupling

Add Stage 2b target validation if feasible:
- results/stage_2b/target_reliability_summary.json
- results/stage_2b/literature_metric_deltas.csv
- results/stage_2b/bootstrap_metric_cis.csv
- results/stage_2b/leave_one_subject_out.csv
- results/stage_2b/run_split_stability.csv
- docs/stage_reports/stage_2b.md

Add synthetic tests for metric behavior.

## 8. Stage 05 — Literature-weighted objective and fitting

Execute `05_literature_weighted_objective_and_fitting.md`.

Expected implementation:
- literature_weighted_lsd_objective
- multi-seed evaluation
- sign mismatch penalty
- overshoot penalty
- seed variance penalty
- sparsity penalty
- placebo baseline fit path
- LSD perturbation fit path
- ablation leaderboard

Expected outputs:
- results/stage_5/literature_weighted_fit_summary.json
- results/stage_5/placebo_fit_summary.json
- results/stage_5/lsd_perturbation_fit_summary.json
- results/stage_5/per_seed_metrics.csv
- results/stage_5/sign_match_table.csv
- results/stage_5/overshoot_table.csv
- results/stage_5/ablation_leaderboard.csv
- docs/stage_reports/stage_5.md

Use modest defaults:
- quick mode should be cheap,
- final/full mode may be heavier,
- do not launch expensive full extraction/fitting unless explicitly cheap and data are present.

## 9. Stage 06 — Reports, dashboard, supervisor artifacts

Execute `06_end_to_end_report_dashboard_and_supervisor_artifacts.md`.

Expected implementation:
- fix report/artifact inconsistencies,
- prevent duplicated section summaries,
- ensure Stage 4 narrative matches JSON,
- ensure benchmark winner text matches machine-readable summaries,
- add Stage 2b/Stage 5 reporting,
- optionally update dashboard if safe,
- generate supervisor-facing docs.

Expected docs:
- docs/supervisor_pitch.md
- docs/proposal_short.md
- docs/open_source_demo.md
- docs/next_month_research_plan.md
- docs/supervisor_pitch_10_slides.md
- docs/reproducibility_runbook.md
- docs/codex_runs/06_final_summary.md

Do not fabricate results. If Stage 5 did not run, say so clearly.

## 10. Final validation

At the end, run as much as feasible:

```bash
uv run pytest
uv run ruff check .
uv run mypy src