# Results Artifact Inventory

Date: 2026-06-15

## 1. Purpose and scope

This is an inventory/report only. It documents the current artifact and results layout so future cleanup can be reviewed manually before any destructive or schema-changing work.

No artifacts were moved, deleted, regenerated, rewritten, compressed, normalized, or reclassified by this pass. The report was created from read-only Git, ignore-rule, directory, and reference scans.

Scope includes tracked and ignored surfaces under `results/`, `output/`, `_site/`, dashboard/public artifact consumers, selected producer scripts, tests that protect artifact contracts, and docs that reference generated artifacts. The historical archive under `docs/reference/` was not edited.

Inspection commands used:

```powershell
git status --short
git ls-files results docs output _site src scripts tests
git ls-files --others --exclude-standard results docs output _site src scripts tests
git ls-files --others --ignored --exclude-standard results docs output _site src scripts tests
git check-ignore -v <selected-path>
rg -l "results/|results\\|output/|output\\|_site|/artifacts/|dashboard-data\.json|ARCHIVE_MANIFEST|thesis_upgrade_status|dynamic_mechanism_ranking|empirical_viewer|claim_evidence_matrix" src scripts tests docs -g "!docs/reference/**"
```

## 2. Artifact policy summary

| Class | Examples in this checkout | Current handling | Future default |
|---|---|---|---|
| Curated tracked evidence | `results/*/*_status.json`, `results/stage_2/*summary*.json`, `results/reproducible_archive/ARCHIVE_MANIFEST.json`, `results/thesis_upgrade/thesis_upgrade_status.json` | Tracked and consumed by dashboard/tests/docs | Keep tracked unless a separate approval pass reclassifies them |
| Generated but intentionally tracked outputs | `results/dynamic_mechanism_ranking/exports/dynamic_mechanism_results.xlsx`, `results/thesis_evidence_loop/exports/thesis_evidence_loop_tables.xlsx`, neuromaps annotation `.gii` files | Tracked evidence bundles or public annotation inputs | Keep tracked, document producer and schema before changing |
| Ignored generated outputs | `results/**/*.csv`, `results/**/*.html`, `results/**/*.png`, `results/**/*.npy`, `results/**/empirical_viewer/`, `_site/`, `output/` | Ignored by `.gitignore`; some are still consumed locally | Leave untouched until reviewed by artifact family |
| Historical reference/archive material | `docs/reference/**` including old prompts, screenshots, run logs, historical commands | Tracked archive | Preserve as historical unless a separate archive policy is approved |
| Raw/private/cache/data-dependent material | `/data/`, `results/nilearn_data/`, `results/external_data/`, `.neuromaps-data/`, raw empirical caches, `results/pytest_tmp_*`, `results/test_runs/` | Ignored or excluded | Never commit; do not regenerate or delete without explicit approval |
| Unknown or needs manual review | Probe folders, old temp outputs, generated reports with uncertain current producer | Mostly ignored | Investigate producer, consumer, and reproducibility before cleanup |

Repository counts from read-only scans:

| Surface | Tracked files | Untracked nonignored files | Ignored files | Approx size |
|---|---:|---:|---:|---:|
| `results/` | 107 | 0 | 9235 | 422 MB |
| `output/` | 0 | 0 | 453 | 6.8 MB |
| `_site/` | 0 | 0 | 198 | 16.7 MB |
| `docs/` | 99 | pending new report | 1 | not measured |
| `tests/` | 13 | 5 Pass 2 tests | 18 | not measured |

## 3. Results directory inventory

| Path or pattern | Status | Apparent producer | Apparent consumer | Risk | Safe future action |
|---|---|---|---|---|---|
| `results/confound_controls/*.json` | 7 tracked JSON; 12 ignored CSV/MD | `scripts/build_motion_confound_controls.py`, `scripts/build_fmriprep_motion_proof_plan.py`, related modules | Thesis gates, dashboard, tests, claim matrix | High | Keep; regenerate only with approval because motion gates affect claim readiness |
| `results/cortical_maps/` | 9 tracked, including status JSON, report MD, `.gii`; 5 ignored CSV/MD | `src/lsd_thesis/cortical_maps.py`, neuromaps-related scripts/modules | Thesis upgrade, dashboard status, public artifact copy | High | Keep tracked status and annotation files; investigate ignored CSV/MD before any move |
| `results/dynamic_mechanism_ranking/summary.json` and `robustness/robustness_summary.json` | Tracked JSON | `scripts/run_dynamic_mechanism_ranking.py` | Dashboard, figure payload, tests, reports, archive manifest | High | Keep; regenerate only in an approved dynamic-mechanism pass |
| `results/dynamic_mechanism_ranking/exports/*.csv`, `figures/*.html` | Ignored generated outputs | `scripts/run_dynamic_mechanism_ranking.py`, `scripts/export_dynamic_mechanism_tables.py` | Figure payload, local dashboard, static Pages artifact copy | Medium | Leave untouched; add manifest/docs before pruning |
| `results/dynamic_mechanism_ranking/exports/dynamic_mechanism_results.xlsx` | Tracked XLSX | `scripts/export_dynamic_mechanism_tables.py` | Thesis evidence bundle/manual review | Medium | Keep; verify freshness against JSON/CSV before citing |
| `results/external_ingestion/` | 2 tracked JSON; 7 ignored CSV/MD/NPY | `scripts/ingest_external_priors.py`, `src/lsd_thesis/external_ingestion.py` | Thesis loop, docs, dashboard status | Medium | Keep status manifests; inspect ignored inputs before any reclassification |
| `results/external_data/` | Ignored | `scripts/prepare_external_data.py` or manual external-data staging | Unknown/currently data-dependent | High | Do not touch without data-source review |
| `results/literature_benchmark/` | 1 tracked JSON; 1 ignored CSV | Thesis evidence loop/literature benchmark components | Claim matrix, docs, dashboard | Medium | Keep tracked status; preserve CSV until consumer map is reviewed |
| `results/nilearn_data/` | Ignored | Nilearn/download cache | Data/cache only | High | Never commit; do not delete in automated cleanup |
| `results/parcellation_sensitivity/` | 6 tracked JSON; 2 ignored CSV | `scripts/run_parcellation_sensitivity.py` | Thesis loop, tests, dashboard | High | Keep; changes need parcellation-specific approval |
| `results/psilocybin_ds006072/` | 7 tracked JSON; 14 ignored JSON/MD/CSV | ds006072 validation/extraction modules | Tests, thesis loop, future external validation review | High | Keep tracked readiness/status files; do not run or prune ds006072 outputs here |
| `results/publication_figures/` | Ignored PNG | `scripts/render_publication_figures.py` | Publication package/manual figures | Low to medium | Leave untouched; document intended publication surface first |
| `results/pytest_tmp_full_20260514/` | Ignored temp tree | Historical pytest/temp run | None intended | Medium | Candidate for manual cleanup only after confirming no active references |
| `results/receptor_priors/` | 2 tracked JSON; 5 ignored CSV | receptor prior ingestion modules | Thesis loop, dashboard, claim matrix | High | Keep; receptor-prior changes require scientific approval |
| `results/reproducible_archive/ARCHIVE_MANIFEST.json` and `CHECKSUMS.sha256` | Tracked | `scripts/build_reproducible_archive.py`, `src/lsd_thesis/reproducible_archive.py` | Archive gate, dashboard, public site, tests | High | Keep; regenerate only in archive-specific approval pass |
| `results/setting_seed/` | 15 tracked JSON/YAML; 7314 ignored files | setting-seed modules and motion summary script | Dashboard payload, docs, run-02 readiness review | High | Do not prune automatically; huge ignored tree needs manual run-02/cache review |
| `results/setting_seed/run02_extraction/` | Mix of tracked status/plans and many ignored caches | Prior guarded run-02/music extraction work | Audit only unless explicitly approved | High | Leave untouched; no run-02/music workflow without approval |
| `results/stage_1/` | 1 tracked JSON; 7 ignored HTML | `scripts/run_pipeline.py` | Stage reports/dashboard | Medium | Keep summary; ignored figures can be inventoried separately |
| `results/stage_2/` | 29 tracked JSON/YAML; 561 ignored, including `empirical_viewer/` and NPY caches | ds003059 extraction/cache/stage 2 pipeline | Dashboard, tests, dynamic mechanism, claims | High | Keep tracked summaries; do not delete local viewer/cache without data approval |
| `results/stage_2/parcellations/**` | Tracked metadata/summaries | parcellation extraction paths | Tests, thesis gates, docs | High | Keep; changes require parcellation approval |
| `results/stage_2_probe*` | Ignored NPY probe outputs | likely exploratory stage-2 probes | Unknown | Medium | Manual review candidate; do not delete in automated cleanup |
| `results/stage_2_smoke/` | 4 tracked JSON/YAML; 4 ignored NPY | smoke Stage 2 pipeline | Tests/docs as lightweight fixture-like output | Low to medium | Keep until fixture policy is explicit |
| `results/stage_2b/`, `stage_3/`, `stage_4/`, `stage_5/` | Tracked summaries plus ignored CSV/HTML | `scripts/run_pipeline.py` and stage modules | Dashboard/stage reports | Medium | Keep tracked summaries; regenerate only in approved pipeline pass |
| `results/structural_connectome/` | 2 tracked JSON; 6 ignored CSV | structural-connectome ingestion/status modules | Thesis loop, claim matrix | High | Keep; structural-connectome changes require approval |
| `results/test_runs/` | Ignored temp tree | tests/manual experiments | None intended | Medium | Candidate for manual cleanup after confirming no active refs |
| `results/thesis_evidence_loop/` | 2 tracked files, including status JSON and XLSX; 13 ignored CSV/MD | `scripts/run_thesis_evidence_loop.py`, `scripts/export_thesis_loop_tables.py` | Claim matrix, tests, dashboard/public site | High | Keep; schema changes need tests/migration |
| `results/thesis_upgrade/thesis_upgrade_status.json` | Tracked JSON; ignored MD sidecar | `scripts/build_thesis_upgrade_status.py` | Dashboard, Pages gate, tests, archive | High | Keep; gate/status semantics require approval |
| `results/training/` | 6 tracked benchmark JSON; 21 ignored CSV/MD/NPZ | benchmark scripts | CV/ML evidence, dashboard/docs | Medium | Keep summaries; do not prune model outputs without benchmark review |
| `results/validation/cv5_subject_disjoint/` | 1 tracked JSON | CV5 validation script/status payload | Dashboard, tests, figure payload | High | Keep; validation-state changes require explicit approval |

## 4. Generated output inventory

| Surface | Current evidence | Should remain untouched for now |
|---|---|---|
| `_site/` public/static output | Ignored by `.gitignore`; 198 files; subdirs include `artifacts/`, `dashboard/`, `figures/`, `static/`, `assets/`; produced by `scripts/build_github_pages.py` | Yes. Rebuilds can rewrite routes and static JSON, so only rebuild in a Pages-specific pass |
| `output/` report/build output | Ignored by `.gitignore`; 453 files, mostly `output/validation/` and `output/doc/`; referenced by archive manifest and figure payload | Yes. It is generated and may include validation or report artifacts with separate freshness state |
| Dashboard preview/build output | Local FastAPI reads from source/results; static build writes `_site/dashboard/dashboard-data.json` and public-site payload files | Yes. Preview check is read-only, but build scripts are not allowed in this pass |
| Figure/image outputs | Ignored patterns include `results/**/*.html`, `results/**/*.png`, `output/**/*.png`; dashboard and public site may link to them | Yes. Figure regeneration can change visual evidence and artifact href expectations |
| Ignored CSV/XLSX/MD sidecars | Many ignored CSV/MD outputs remain linked by figure payload or copied into `_site/artifacts/`; selected XLSX files are tracked | Yes. Review per artifact family before changing track/ignore policy |
| Empirical caches and data-dependent outputs | `results/**/empirical_viewer/`, NPY arrays, `results/nilearn_data/`, `results/external_data/`, `data/` | Yes. These are the highest-risk cleanup target and should remain manual-only |

## 5. Artifact reference map

Important producer scripts and modules:

- `scripts/run_pipeline.py`: staged outputs under `results/stage_*`.
- `scripts/run_dynamic_mechanism_ranking.py`: dynamic-mechanism summaries, CSV exports, robustness, figures, and report.
- `scripts/export_dynamic_mechanism_tables.py`: dynamic mechanism XLSX/table exports.
- `scripts/run_thesis_evidence_loop.py` and `scripts/export_thesis_loop_tables.py`: thesis evidence loop JSON, CSV/MD sidecars, and XLSX bundle.
- `scripts/build_thesis_upgrade_status.py`: `results/thesis_upgrade/thesis_upgrade_status.json`.
- `scripts/build_reproducible_archive.py`: archive manifest and checksums.
- `scripts/build_github_pages.py`: ignored `_site/` static site and copied public artifacts.
- `scripts/preview_dashboard.py`: read-only dashboard preflight; validates required files and gate contracts.
- `scripts/build_motion_confound_controls.py`, `scripts/build_fmriprep_motion_proof_plan.py`, `scripts/run_setting_seed_motion_summary.py`: motion and setting-seed status artifacts.
- `scripts/run_parcellation_sensitivity.py`: parcellation sensitivity results and optional thesis-loop refresh.
- `scripts/benchmark_*`: training/benchmark summaries and sidecars.
- `src/lsd_thesis/data/ds003059/*`: stage-2 empirical cache metadata, targets, and viewer-oriented data.
- `src/lsd_thesis/thesis_upgrade/*`, `src/lsd_thesis/thesis_loop/*`, `src/lsd_thesis/reproducible_archive.py`: status and evidence artifact assembly.

Important consumers:

- `src/lsd_thesis/web/app.py`: builds the dashboard payload from configs, results, status artifacts, empirical viewer, and figure payload.
- `src/lsd_thesis/web/artifacts.py`: constructs allowlisted `/artifacts/...` links and filters public-serving extensions.
- `src/lsd_thesis/web/figure_payload.py`: references dynamic, robustness, empirical, CV5, archive, and motion artifacts for the figure deck.
- `src/lsd_thesis/web/site_payload.py`: builds `public_site.v1` from dashboard payload and artifact links.
- `src/lsd_thesis/web/status_payload.py`, `src/lsd_thesis/web/thesis_payload.py`, `src/lsd_thesis/web/empirical_viewer.py`, `src/lsd_thesis/web/structural_dti.py`: consume tracked and ignored local results.
- `src/lsd_thesis/thesis_upgrade/gates.py`: reads `_site/` and archive artifacts for readiness checks.
- `src/lsd_thesis/reproducible_archive.py`: has an explicit derived-artifact inclusion list spanning `results/` and `output/`.

Docs that reference artifacts:

- `docs/stage_reports/*`
- `docs/VALIDATION.md`
- `docs/THESIS_READINESS_GATES.md`
- `docs/GITHUB_PAGES.md`
- `docs/DASHBOARD_GUIDE.md`
- `docs/open_source_demo.md`
- `docs/research/*`
- `docs/reference/**` as historical archive only

Tests that protect artifact schemas and href conventions:

- `tests/test_result_artifact_schema_contract.py`
- `tests/test_dashboard_payload_contract.py`
- `tests/test_public_site_payload_contract.py`
- `tests/test_dashboard_route_contract.py`
- `tests/test_figure_payload.py`
- `tests/test_web_security.py`
- `tests/test_next_action_evidence_gates.py`
- `tests/test_static_pages_payload_refresh.py`
- `tests/test_validation_status.py`

## 6. Risk register

| Risk | Why it matters | Current mitigation | Cleanup guidance |
|---|---|---|---|
| Breaking dashboard or public-site hrefs | `/artifacts/...` links are route-facing and copied into `_site/` | Contract tests cover href shape and routes | Do not move artifacts without route/href migration tests |
| Modifying curated evidence | Tracked JSON/XLSX/GII files encode thesis gate, claim, validation, or public evidence state | Files are tracked and referenced by tests/docs | Treat tracked `results/` as curated evidence until reclassified |
| Regenerating with a different environment | Versions, caches, random seeds, and local data availability can alter outputs | Current pass avoids generation | Regenerate only in scoped pipeline passes with baseline and post-run diffs |
| Confusing historical archive with current source of truth | `docs/reference/**` contains old commands and paths by design | Archive preserved and excluded from edits | Add archive policy before pruning or rewriting |
| Changing artifact schemas without migration | Dashboard/public site/tests expect current keys and shape | Characterization tests now cover major contracts | Add schema-version tests and migration notes before format changes |
| Accidentally committing ignored/private/generated data | Ignored tree contains NPY arrays, caches, temp runs, `_site/`, `output/` | `.gitignore` blocks broad generated surfaces | Use `git status --ignored=matching` and `git check-ignore -v` before staging |
| Treating ignored as unused | Some ignored CSV/HTML/viewer files are consumed locally or copied to public static artifacts | Figure payload and Pages builder reference ignored paths | Map consumers before deleting ignored files |
| Run-02/music and external-data drift | These paths are high-risk, data-dependent, and manually reserved | Current policy keeps them audit-only | Do not touch without explicit approval and dedicated tests |

## 7. Recommended future policy

Do not implement these policies in this pass. They are proposed for manual review only.

| Policy area | Recommendation |
|---|---|
| What stays tracked | Keep status JSON, schema-bearing summaries, curated evidence manifests, public annotation inputs, selected XLSX bundles, archive manifest/checksums, and tests/docs that protect them |
| What stays ignored | Keep raw data, local caches, NPY/NPZ arrays, generated figures, generated CSV/HTML/MD sidecars, `_site/`, `output/`, temp pytest/test-run trees, and external downloaded data ignored |
| README documentation needed | Add a concise artifact-tier README or section explaining Tier A tracked evidence, Tier B generated outputs, and Tier C raw/private/cache files |
| Schema tests needed | Preserve and extend tests for dashboard payload, public-site payload, thesis upgrade status, result artifact JSON shape, figure payload, artifact hrefs, and archive manifest |
| Requires explicit manual approval | Any move/delete/regeneration under `results/`, `_site/`, `output/`, run-02/music, ds006072, neuromaps/PET/structural-connectome, tracked XLSX/GII files, archive manifest, or claim/gate/status artifacts |
| Should never be automated cleanup | Raw data, private caches, `.env`/secrets, external repositories, downloaded data, and any artifact whose producer needs network/private data |

## 8. Manual cleanup checklist

Use this checklist before deletion, move, regeneration, or tracking-policy changes.

- Inspect Git status:
  - Command: `git status --short`
  - Evidence to check: no unrelated user changes will be overwritten.
  - Do not touch: existing unstaged work unless it belongs to the approved pass.

- Identify track/ignore state:
  - Commands: `git ls-files <path>`, `git ls-files --others --ignored --exclude-standard <path>`, `git check-ignore -v <path>`
  - Evidence to check: whether the file is curated/tracked, ignored generated, or untracked stray output.
  - Separate approval needed: reclassifying ignored output as tracked or tracked evidence as ignored.

- Map producers:
  - Command: `rg -n "<artifact-or-dir>" scripts src docs tests -g "!docs/reference/**"`
  - Evidence to check: producer script, module, or manual workflow; whether producer requires private data, network, raw cache, or long runtime.
  - Do not touch: producers in Stage 2, dynamic mechanism, parcellation, data-fetch, run-02/music, PET/neuromaps, or structural-connectome without a dedicated pass.

- Map consumers:
  - Command: `rg -n "<artifact-or-dir>|/artifacts/" src scripts tests docs -g "!docs/reference/**"`
  - Evidence to check: dashboard payload, public site, tests, docs, archive manifest, thesis report.
  - Separate approval needed: changes that alter hrefs, schema keys, routes, claim labels, gate/status semantics, or public JSON shape.

- Verify schema coverage:
  - Commands: `uv run --frozen pytest tests/test_result_artifact_schema_contract.py -q -o addopts=`, plus relevant dashboard/public contract tests.
  - Evidence to check: tests cover top-level keys, schema versions, required fields, route/href conventions, and allowed vocabulary.
  - Do not weaken tests merely to permit cleanup.

- Confirm freshness before citing:
  - Commands: compare tracked JSON/CSV/XLSX timestamps and producer manifests; inspect archive checksums when relevant.
  - Evidence to check: JSON/CSV and XLSX bundles may have different freshness.
  - Separate approval needed: regenerating XLSX bundles or archive checksums.

- Keep high-risk data surfaces out of automated cleanup:
  - Paths: `data/`, `results/nilearn_data/`, `results/external_data/`, `results/**/empirical_viewer/`, `results/**/*.npy`, `results/**/*.npz`, `results/setting_seed/run02_extraction/`, `output/`, `_site/`.
  - Evidence to check: whether they are raw/private/cache/generated and whether consumers still depend on them.
  - Do not touch: any raw, private, or data-dependent file without explicit user approval.

## 9. Proposed next pass

Recommended next implementation pass: Pass 5, gate/status helper extraction, only after reviewing this inventory and confirming the characterization tests still cover gate/status output shape and vocabulary.

Do not start Pass 5 until explicitly approved. Pass 5 should preserve claim wording, claim labels, gate/status semantics, dashboard interpretation text, public JSON schemas, and route/file compatibility.
