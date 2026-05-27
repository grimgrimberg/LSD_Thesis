# Life Science Research Review

Date: 2026-05-12

Scope: repo-grounded review after PASS 2A, using the Life Science Research router and NCBI Entrez skill for public literature checks. This is a review artifact only; it does not implement PASS 2B.

## Why This Review Was Added

PASS 2A was mostly a local implementation pass. It used PASS 1 literature and guardrails, but did not explicitly invoke the Life Science Research plugin during final implementation because no new scientific source lookup was required to write the safe empirical foundation.

That was too narrow for a thesis-facing scientific review. The Life Science Research plugin is appropriate here for public literature routing, PubMed checks, and evidence-boundary synthesis. It is not appropriate for private source-code indexing, raw neuroimaging data transfer, or subject-level artifact upload.

## Life Science Research Routing

Router lanes selected:

- Literature and public dataset discovery.
- Neuroimaging methods and evidence synthesis.
- Public-method support for network/control framing.

Lanes intentionally not selected:

- Genetics and variant interpretation.
- Protein structure.
- Chemistry/ligand binding.
- Omics and pathway enrichment.
- Clinical trial evidence.

Reason: this repository is currently a macro-scale fMRI surrogate and empirical module-time-series project. Receptor, ligand, gene, clinical, or omics claims are out of scope unless explicitly added as priors in a later pass.

## Tools Used

Life Science Research skills:

- `life-science-research:research-router-skill`
- `life-science-research:ncbi-entrez-skill`

NCBI Entrez searches were limited to public PubMed metadata. No private source code, file tree, raw data, local paths, subject-level results, generated arrays, secrets, or unpublished thesis drafts were sent.

Queries run:

| Query | Result |
|---|---:|
| `LSD fMRI thalamic connectivity` | 5 PubMed IDs returned |
| `LSD music fMRI setting psychedelic` | 0 PubMed IDs returned |
| `psychedelic fMRI dynamic functional connectivity entropy brain` | blocked by NCBI 429 on retry |
| `network control theory psychedelics fMRI brain` | 5 PubMed IDs returned |
| `OpenNeuro ds003059 LSD fMRI` | 0 PubMed IDs returned |

Public PubMed summary IDs retrieved:

- PMID 41942645: international mega-analysis of psychedelic drug effects on brain circuit function.
- PMID 40666257: scoping review of psychedelic fMRI studies.
- PMID 40200796: dorsolateral prefrontal cortex, ego dissolution, and emotional arousal during psychedelic state.
- PMID 39261671: large-scale brain connectivity after LSD, d-amphetamine, and MDMA.
- PMID 39165942: LSD and pain-related brain networks in healthy subjects.
- PMID 40251353: network control energy reductions under DMT.
- PMID 39735490: serotonergic psychedelic DPT in in vitro cortical circuits.
- PMID 39681243: advanced meditation neurophenomenology case study.
- PMID 39022924: integrated information decomposition and consciousness.
- PMID 37214949: DMT time-resolved network control preprint.

Only the psychedelic fMRI/connectivity/review and DMT network-control papers are directly useful to this thesis. Consciousness, meditation, in-vitro circuit, and clinical/pain papers are peripheral or out of scope unless clearly framed as methodological context.

## Repo Review

Current repo state:

- Branch: `codex/audit-cleanup-20260507`.
- Worktree: dirty before this review; unrelated existing changes were preserved.
- Stack: `uv`, Python 3.13, Hatchling, pytest, ruff, mypy.
- Dashboard: FastAPI/Uvicorn/Jinja2/vanilla JS/Plotly at `http://127.0.0.1:8000/`.
- Core source: `src/lsd_thesis`.
- New PASS 2A package: `src/lsd_thesis/setting_seed`.

Important source areas:

- `src/lsd_thesis/data/ds003059.py`: current empirical manifest/extraction path; explicitly filters out `run-02`.
- `src/lsd_thesis/target_validation.py`: Stage 2b target reliability machinery.
- `src/lsd_thesis/setting_seed/data.py`: PASS 2A cached data audit.
- `src/lsd_thesis/setting_seed/reliability.py`: PASS 2A reliability tiers and motion-gated eligibility.
- `src/lsd_thesis/setting_seed/latent.py`: descriptive rest-only PCA geometry.
- `src/lsd_thesis/setting_seed/control_input.py`: music-control scaffold, blocked while run-02 is missing.
- `src/lsd_thesis/setting_seed/dashboard_payload.py`: cached dashboard payload and static microsite.
- `src/lsd_thesis/web/app.py`: additive dashboard payload key and artifact link.

## Results Review

Stage 2:

- `results/stage_2/module_time_series`: 60 cached `.npy` module time series.
- Coverage: 15 subjects x 2 sessions x 2 rest runs.
- Sessions: `ses-LSD`, `ses-PLCB`.
- Runs: `run-01`, `run-03`.
- Timepoints: 217 per cached run.
- `run-02` music module time series: absent.
- Motion summaries: absent.
- Atlas audit: 108,814 assigned voxels; 8-module mapping is explicitly a transparent proxy, not a canonical atlas.
- Current sign conflicts: `entropy_diversity`, `metastability_proxy`, `within_network_stability`.

Stage 2b:

- Reliability artifacts exist in `results/stage_2b`.
- PASS 2A builds a separate `results/setting_seed/reliability` layer rather than rewriting Stage 2b semantics.

Stage 3:

- Root `results/stage_3/stage_3_summary.json` is not the approved CV5 validation artifact.
- It records candidate subject-disjoint configuration, but not completed held-out validation.
- It should not be cited as final subject-disjoint evidence.

Stage 5:

- `results/stage_5/literature_weighted_fit_summary.json` reports `thalamic_routing_only` as best candidate with loss `0.762443310660408`.
- This is a full-cohort proxy-ranking artifact, not biological proof and not subject-disjoint validation.

CV5 validation:

- Approved CV5 evidence lives under `output/validation/cv5_subject_disjoint/results`.
- `cv5_aggregate_validation.json` reports 5 completed folds, all subjects held out once, and zero selection/validation overlap per fold.
- The selected mechanism in the fold metrics is `more_cross_talk` with strength `0.1`.
- Interpretation should remain internal same-dataset proxy-objective validation.

PASS 2A `setting_seed`:

- Data audit: run-02 unavailable, motion summaries unavailable, music-control blocked.
- Reliability: Tier A rest targets are `cross_network_communication` and `thalamic_coupling`.
- Tier A metrics have `eligible_for_primary_fit=false` until motion sensitivity review exists.
- Latent analysis: descriptive PCA only, labeled visualization-only.
- Control scaffold: no empirical music-control effect is claimed.
- Dashboard: payload, static microsite, and Playwright screenshot exist.

## Scientific Review

The repo is aligned with a defensible macro-dynamics thesis if the current guardrails remain active:

- The current cache supports rest-only reliability and descriptive latent trajectory analysis.
- Routing-oriented metrics are better supported than entropy/metastability proxies in the current reliability layer.
- Music/control is scientifically interesting but empirically blocked until run-02 module time series are extracted and `sub-003`, `sub-012`, and `sub-015` are excluded for music-specific analyses.
- Motion sensitivity is not available and must not be treated as passed.
- Full-data PCA is acceptable for dashboard visualization but not for ML claims.
- Existing mechanism rankings are hypothesis-ordering artifacts, not proof of a thalamic or cross-talk biological mechanism.

The Life Science Research PubMed check reinforces these boundaries:

- Public literature supports broad psychedelic fMRI/network-connectivity heterogeneity and current interest in control-energy framing.
- The targeted music-setting query returned no PubMed hits, so this repo should not claim empirical music-control effects from current cached data.
- DMT network-control evidence can motivate the control-energy question, but it cannot be transferred as LSD-specific proof.
- Recent psychedelic fMRI reviews and mega-analyses support caution about methodological heterogeneity, small-N risks, and cross-study generalization.

## Main Findings

1. The PASS 2A implementation is scientifically conservative and correctly blocks run-02/music and motion claims.
2. The strongest current rest targets remain `cross_network_communication` and `thalamic_coupling`, but primary-fit eligibility is correctly motion-gated.
3. `hierarchical_compression` remains a candidate target, not a robust primary target.
4. `within_network_stability`, `entropy_diversity`, and `metastability_proxy` remain diagnostic because of sign conflicts or weak/contradictory behavior.
5. There is a documentation and citation hazard: root Stage 3 and Stage 5 outputs are easy to overread as validation. Only the approved CV5 output directory should be cited for subject-disjoint validation.
6. `results/setting_seed` contains useful JSON artifacts that are not globally ignored by the current `.gitignore`; decide deliberately whether these are intended tracked artifacts before staging.
7. Broader web tests and mypy remain blocked by local Windows temp/cache behavior, not by a confirmed code assertion failure.

## Recommended Next Work

Priority 1:

- Add an explicit run-02 extraction flag/path without changing default rest-only Stage 2 behavior.
- Keep default extraction rest-only.
- Prefer a separate first output root such as `results/setting_seed/run02_extraction`.
- Require user confirmation before download, expensive extraction, or mutation of legacy Stage 2 caches.

Priority 2:

- Locate or compute subject/run-level motion summaries from authorized local derivative/confound files.
- Add motion-gated target eligibility tests before any primary model-fitting claims.

Priority 3:

- Add a small source table to `docs/METHODS_RESEARCH.md` or a companion evidence file with the PubMed IDs above.
- Mark DMT network-control evidence as methodological support only, not LSD-specific validation.

Priority 4:

- Make Stage 5-style mechanism comparison consume the reliability layer and CV5 split policy before any new leaderboard is thesis-facing.

Priority 5:

- Resolve local pytest temp and mypy cache issues, then rerun the full repo validation command set.

## 2026-05-14 Update

The Life Science Research router was used again as the organizing layer for a targeted scholarly scan. Because the available plugin skills are local routing instructions rather than a private-code analysis tool, the pass used public scholarly web/PubMed-style lookup only and did not send source code, local paths, subject-level artifacts, or raw neuroimaging data to remote tools.

Most relevant additions were recorded in `docs/METHODS_RESEARCH.md`:

- Carhart-Harris and Friston 2019 REBUS: useful for predictive-processing and prior-precision framing, not direct evidence for this dataset.
- Carhart-Harris et al. 2016 multimodal LSD neuroimaging: useful background for LSD fMRI heterogeneity.
- Tagliazucchi et al. 2016 global functional connectivity under LSD: supports treating cross-network communication as a plausible rest target.
- Preller et al. 2018 thalamic/global connectivity under LSD: supports thalamocortical routing as a hypothesis, not receptor proof for this repo.
- Kaelen et al. 2016 LSD + music fMRI: supports run-02 as a high-value next extraction target, but does not justify a current music-control claim.
- Atasoy et al. 2017 connectome-harmonic LSD dynamics: supports dynamical-repertoire framing and the scientific relevance of music/stimulus conditions.
- Singleton et al. 2022 receptor-informed network control theory: supports control-energy landscape analysis as a method precedent, not proof that the repo's lower-barrier mechanism is true.
- Mediano et al. 2024 external stimulation and psychedelic neurodynamics: strengthens the setting/context rationale.
- Dynamic FC and small-N validation papers: reinforce subject-disjoint validation and conservative uncertainty language.

Current scientific recommendation:

- Treat `cross_network_communication` and `thalamic_coupling` as the best rest-only targets.
- Keep `hierarchical_compression` as candidate support.
- Keep entropy/metastability/barrier proxies diagnostic until metric reliability and sign conflicts are resolved.
- Prioritize PASS 2B-1 run-02 extraction plus motion summaries before any stronger music-control or control-energy claim.
