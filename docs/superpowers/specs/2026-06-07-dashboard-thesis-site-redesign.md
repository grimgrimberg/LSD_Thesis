# Dashboard And Thesis Site Redesign

Date: 2026-06-07

## Status

Approved for planning. Implementation follows this spec unless a later user note changes scope.

## Objective

Revamp the LSD thesis dashboard into a clean, lean, informative evidence console with richer plots, an empirical/raw-data viewer, a thesis presentation site, a static GitHub Pages mini version, and paper-inspired plot panels that are recreated only when the current repository artifacts can support them.

The design must preserve the project framing:

- Macro-dynamics surrogate model, not subjective-experience simulation.
- Proxy-level mechanism ranking, not receptor-level realism.
- Prior-art comparison as reproducibility landscape and inspiration, not copied external analysis.
- Explicit claim states: implemented, proxy-supported, mixed, unsupported, blocked, and future.
- Local FastAPI dashboard is the full interactive surface.
- GitHub Pages is a static derived-data presentation and mini dashboard.

## Current Evidence

Current dashboard implementation:

- Routes and payload orchestration live in `src/lsd_thesis/web/app.py`.
- Public/site payload helpers live in `src/lsd_thesis/web/site_payload.py`.
- Prior-art payload helpers live in `src/lsd_thesis/web/prior_art_payload.py`.
- Templates are split across `src/lsd_thesis/templates/base.html`, `templates/components/sidebar.html`, and `templates/pages/*.html`.
- Shared frontend assets are `src/lsd_thesis/static/dashboard.css` and `src/lsd_thesis/static/dashboard.js`.
- Static Pages build is `scripts/build_github_pages.py`.

Verified issues in the current UI:

- Google Fonts import is blocked by the dashboard Content Security Policy.
- Plotly axis labels can clip or rotate into unreadable states.
- Mobile navigation takes too much first-viewport height.
- The visual system relies too heavily on glass/card styling and decorative gradients.
- Empirical page only exposes a small subject-detail table, not a real fMRI-style matrix/window viewer.
- Presentation artifacts exist, but they are copied as artifacts rather than integrated as first-class site routes.
- Paper/literature benchmark data exist, but there is no explicit "paper plot recreation" reading path.

Available local data for richer views:

- `results/stage_2/empirical_viewer/group_overview.json`.
- `results/stage_2/empirical_viewer/subject_index.json`.
- `results/stage_2/empirical_viewer/subject_views/*_run-*.json`.
- `results/stage_2/figures/*.html`.
- `results/dynamic_mechanism_ranking/summary.json`.
- `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`.
- `results/dynamic_mechanism_ranking/exports/*.csv`.
- `results/dynamic_mechanism_ranking/figures/*.html`.
- `prior_art/comparison_extraction_plan.json` and `prior_art/runbooks/*.md`.

## Users And Reading Modes

Primary user modes:

- Thesis reviewer: wants the claim boundary, evidence path, limitations, and figures quickly.
- Research operator: wants to inspect artifacts, subject/run cache, matrices, ranking, robustness, and blockers.
- Public visitor: wants a static narrative and selected derived visuals without raw/private data or live backend assumptions.

The dashboard should start as a working surface, not a marketing homepage. The thesis presentation can carry the story and stronger editorial pacing.

## Visual Direction

Visual thesis: restrained scientific evidence console with high-density information, calm surfaces, crisp typography, direct labels, and status-aware color.

Use:

- System fonts only to avoid CSP and external dependency issues.
- Neutral dark base with off-white text and restrained borders.
- Teal for current/focal evidence.
- Amber for caution, proxy, or partial status.
- Rose/red for blocked, unsupported, or fail-closed status.
- Green/moss only for completed gates.
- Flat full-width sections and tool surfaces instead of nested cards.

Avoid:

- External font imports.
- Decorative radial gradients, bokeh/orbs, and glass effects.
- Hover movement that makes operational panels feel unstable.
- Hero-scale type inside dense dashboard panels.
- Presenting blocked or future prior-art families as completed work.

## Information Architecture

Keep the multi-page dashboard shell, but revise labels and content hierarchy:

1. Overview
   - Claim posture
   - Strict gate summary
   - Top mechanism result
   - Evidence read path
   - Artifact search
   - Mini literature alignment snapshot

2. Mechanism Ranking
   - Layer ranking
   - Layer score distribution
   - Claim verdicts
   - Literature benchmark alignment
   - Links to derived Plotly artifacts

3. Robustness
   - Bootstrap rank stability
   - Run sensitivity
   - E horizon sensitivity
   - D window sensitivity
   - Strict requirements table

4. Empirical Viewer
   - Group LSD-minus-placebo metric deltas
   - Subject/run selector
   - Window scrubber for cached subject views
   - FC delta heatmap for selected window
   - Metric delta table
   - Raw JSON/table view for the selected cache record
   - Static mode notice when Pages cannot call subject-level APIs

5. Prior Art
   - Family status summary
   - Repository/source matrix
   - Test/compare/extract matrix
   - Paper plot recreation board
   - Missing-input and claim-status labels

6. Simulator
   - Baseline/perturbed snapshots
   - Local parameter controls
   - Time-series plot
   - FC matrix plot
   - Static mode uses cached snapshots only

7. Thesis Presentation
   - First-class HTML route/page
   - Sections: thesis claim, dataset, model, empirical anchor, mechanism ranking, robustness, prior-art landscape, limitations, next work
   - Static Pages entrypoint included in `pages_manifest.json`

## Plot Inventory

Use Plotly for existing heatmaps and fast implementation where it already fits. Add small SVG islands only when direct labeling, compact custom geometry, or paper-inspired comparative layouts are more readable than Plotly.

Do not load D3 from a CDN in the first implementation pass. "SVG island" means vanilla JavaScript creating inline SVG elements with the browser DOM APIs. If a later pass needs D3, vendor the exact minified D3 bundle locally under `src/lsd_thesis/static/vendor/`, serve it through the same static asset path as `dashboard.js`, and keep the CSP self-only. Do not add a build step, npm package, or external script tag.

Required plots:

- Strict gate completion bar or dot-matrix.
- Mechanism ranking horizontal bars with direct labels.
- Literature benchmark alignment chart: aligned, weak/opposed, missing-required-region.
- Bootstrap rank stability view from `subject_bootstrap.layer_summary`.
- Run sensitivity grouped bars from `run_sensitivity.run_rows`.
- E horizon sensitivity line/bar chart from `e_horizon_sensitivity.rows`.
- D window sensitivity line/bar chart from `d_window_sensitivity.rows`.
- Group metric delta bars from `empirical.target_deltas`.
- Subject/window FC delta heatmap from selected `window_deltas[n].fc_matrix`.
- Simulator time-series and FC matrix, preserving current behavior.

Paper-inspired recreation board:

- FC placebo/LSD/delta matrices from stage 2 artifacts: feasible.
- Dynamic integration / repertoire plots from local dynamic mechanism exports: feasible as proxy recreation.
- Network control energy proxy from local E outputs: feasible with caveat.
- Literature benchmark alignment from local metric mapping: feasible.
- Receptor, PET, exact Nature Medicine atlas plots, striatal-unimodal plots, music/run-02 analyses, and external ds006072 reproductions: status-labeled as blocked/future/missing inputs unless current artifacts prove support.

Named first-pass paper targets:

| Source | Target figure or panel | Local recreation target | Status |
|---|---|---|---|
| Preller et al. 2018 eLife, Figure 1 | LSD effects on global brain connectivity, including hyper/hypo-connectivity maps, distributions, and subject-level relationship plots | Use current module-level LSD-minus-placebo FC/GBC-style proxy deltas and distributions; do not mimic cortex maps without voxel/surface data | proxy-supported |
| Girn et al. 2026 Nature Medicine, Figure 1 | All-drug mean network FC change matrix plus within-network and between-network integration summaries | Use current 8-module FC delta heatmaps, between-network integration proxy, and literature benchmark alignment rows | proxy-supported |
| Girn et al. 2026 Nature Medicine, Figure 2 | Drug-specific inter-regional/inter-network FC changes, especially LSD and psilocybin panels | Use LSD-only local stage-2 and dynamic-mechanism summaries; psilocybin rows remain readiness/static-status unless current comparable ds006072 artifacts are present | mixed |
| Girn et al. 2026 Nature Medicine, Figure 3 | Bayesian posterior distributions for between-network effects | Show as not recreated in first pass; current repo has directional proxy/effect rows, not the Bayesian posterior model | future |
| Singleton et al. 2022 Nature Communications, Figure 1 | Network-control energy landscape schematic and state transition framing | Use local transition-state and network-control proxy charts; label as schematic/proxy, not full structural-connectome NCT | proxy-supported |
| Singleton et al. 2022 Nature Communications, Figures 4-5 | Psychedelic transition-energy reduction and receptor-informed control input comparisons | Use local E horizon sensitivity, lower transition-energy proxy, and receptor-vs-random energy result; block receptor-specific claims when local result is negative | mixed |
| Singleton et al. 2022 Nature Communications, Figure 6 | Relationship between landscape flattening and entropy/temporal diversity | Use local transition entropy, state occupancy, and dynamic repertoire rows if present; otherwise mark missing required metric | proxy-supported / future |

Other papers in the prior-art inventory, including Deco-style whole-brain model or receptor/transcriptomic modeling papers, are second-pass targets unless the current dashboard payload already exposes the required metric, figure, or artifact. The board must state the missing input instead of using generic filler plots.

## Raw Data Viewer Contract

Local mode:

- Use `/api/dashboard-data` for overview metadata.
- Use `/api/empirical-view?subject=...&run=...` for subject/run detail.
- Selector must default to the validated `default_subject` and `default_run` pair.
- A window slider selects one of the available `window_deltas`.
- Heatmap renders the selected window FC delta matrix.
- Metric table renders selected window metrics.
- Raw view shows compact JSON for selected subject/run/window with copy/download affordance if simple to implement.
- Every fetch and heatmap redraw must set a visible loading state before work starts and clear it after success or failure.

Static mode:

- Show group overview and static artifact links.
- Do not call `/api/empirical-view`.
- Show a clear notice that subject-level previews require the local FastAPI dashboard.
- If a selected static subject cache is not copied to Pages, do not invent data.

## Static GitHub Pages Contract

Pages must remain derived/static only:

- No raw private data.
- No live-only controls that imply FastAPI is present.
- Static entrypoints include `index.html`, `ranking.html`, `robustness.html`, `prior-art.html`, `empirical.html`, `simulator.html`, `thesis.html`, and `dashboard/index.html`.
- `dashboard/dashboard-data.json` and `dashboard/prior-art-data.json` remain the static data spine.
- `pages_manifest.json` lists the new thesis entrypoint and selected static artifacts.
- Plotly asset remains local in `assets/plotly.min.js`.
- External fonts/scripts are not required.

Base URL and pathing:

- Local FastAPI routes render with root-relative paths: `/static/`, `/assets/plotly.min.js`, `/api/dashboard-data`, `/api/prior-art-data`, and `/artifacts/`.
- Static rendering must inject depth-aware prefixes through the existing template context: `static_prefix`, `plotly_src`, `data_url`, `prior_art_data_url`, `artifact_prefix`, `home_href`, and static nav links.
- Static root pages use relative paths such as `static/dashboard.css`, `assets/plotly.min.js`, and `dashboard/dashboard-data.json`.
- Static nested pages such as `dashboard/index.html` use `../static/`, `../assets/plotly.min.js`, and local `dashboard-data.json`.
- No static template or JavaScript path may assume a leading `/` except for local deployment mode.
- The Pages builder must be the path-prefix authority; do not hard-code the repository name `LSD_Thesis` into templates.
- Verification must search the generated `_site` HTML for accidental `href="/static`, `src="/static`, `fetch('/api`, `fetch("/api`, and root-relative `/artifacts/` links.

Loading states:

- Chart containers start with a short `Loading...` label or skeleton line.
- Async actions set `aria-busy="true"` on the affected panel and add an `.is-loading` class that dims stale content without hiding it.
- Simulator runs show `running` in the status token and disable the run button until the response returns.
- Empirical subject/run loads show `loading subject/run` in the notice region and keep the previous heatmap visible at reduced opacity.
- Errors replace the loading text with the exact failed action, while preserving any previously rendered evidence.

Export and download affordances:

- Plotly charts that are user-facing evidence must enable the modebar camera export button.
- Tables backed by local CSV artifacts should include an "Open CSV" or "Download CSV" link when an artifact path exists in the payload.
- The raw empirical JSON viewer should provide "Copy JSON" and "Open source artifact" where the source path is available.
- Static Pages can link to copied CSV/HTML artifacts but must not promise live export generation.

## Architecture And Data Flow

Keep existing architecture:

- `web/app.py` owns routes.
- `web/site_payload.py` owns public/presentation payload assembly.
- `web/prior_art_payload.py` owns prior-art dashboard data.
- `templates/pages/*.html` define page surfaces.
- `static/dashboard.js` owns rendering functions and static/local mode branching.
- `static/dashboard.css` owns the visual system.
- `scripts/build_github_pages.py` renders static templates and copies allowlisted artifacts.

Add only small helper modules if a file would otherwise become tangled. The first implementation pass should avoid a new frontend framework, build system, or dependency.

## Error Handling

- If a JSON payload is missing or malformed, show a local page-level status message rather than blank panels.
- If Plotly is unavailable, leave text fallback in each chart container.
- If subject-level detail fails, preserve the group view and show the failing subject/run message.
- If a literature recreation target is unsupported, render its blocker and missing inputs.
- Loading, empty, stale, and error states are distinct: loading means work is in progress, empty means the current artifact does not contain rows, stale means previous content is still visible during a refresh, and error means a fetch/render operation failed.

## Accessibility And Mobile

- All charts need visible titles and non-hover essential values.
- Tables must remain horizontally scrollable when needed.
- Mobile nav should collapse or compact so the first content panel appears quickly.
- Hover-only interaction must have click/tap equivalents.
- Use high contrast and redundant text labels for status colors.
- Respect reduced motion by avoiding ornamental motion in the dashboard.
- Dense heatmaps and matrices must sit inside horizontally scrollable plot frames on narrow screens, with sticky row/column context where practical.
- Long mechanism and benchmark labels must wrap to multiple lines or move into direct annotations below the plot on mobile; do not rely on rotated tick labels at 390 px width.
- FC heatmaps below 520 px viewport width should use a square minimum plotting area and allow horizontal pan rather than shrinking text to unreadable sizes.
- If a plot cannot be made readable on mobile without misrepresenting it, show a compact summary plus a "Use a wider screen for full matrix" notice, while still exposing the source table/link.
- Mobile QA must include 390 x 844 and desktop QA must include at least 1440 x 900.

## Verification Plan

Focused automated checks:

- Payload import/smoke tests for dashboard and prior-art payloads.
- Static build smoke test for required entrypoints and manifest keys.
- Template/HTML smoke tests for expected IDs used by the JS renderer.
- Existing focused tests: `uv run pytest --no-cov tests/test_prior_art_payload.py tests/test_pipeline.py tests/test_dynamic_mechanism.py tests/test_metrics.py`.

Manual/browser checks:

- Start local dashboard with `uv run python scripts/run_dashboard.py`.
- Open `http://127.0.0.1:8000/`, `/ranking`, `/robustness`, `/prior-art`, `/empirical`, `/simulator`, `/thesis`.
- Check desktop and mobile viewports.
- Check console has no CSP font error.
- Check empirical subject/run detail loads in local mode.
- Build static Pages with `uv run python scripts/build_github_pages.py --site-dir _site`.
- Open static `index.html`, `empirical.html`, and `thesis.html`.
- Verify static empirical page does not call local-only APIs.
- Search generated `_site` HTML for root-relative static/API/artifact paths that would break under `https://grimgrimberg.github.io/LSD_Thesis/`.
- On mobile, verify mechanism labels, FC heatmaps, and benchmark rows remain readable or expose the approved wider-screen fallback.

## Risks

- The current worktree is heavily dirty. Implementation must avoid reverting unrelated deletions/refactors.
- Some prior-art paper plots cannot be recreated from current data. They must be presented as blocked/future rather than simulated.
- Full Pages build may refresh many generated status files. Use focused static-render checks before broad publishing work.
- Browser screenshot operations may be slow on dense Plotly pages. Prefer DOM/API checks first, then targeted screenshots.

## Non-Goals

- No new raw data downloads.
- No run-02/music extraction.
- No external code copied from prior-art repositories.
- No migration to React/Next/Vite.
- No strengthened receptor, subjective, clinical, or external-validation claims.
- No destructive cleanup of the dirty worktree.

## Approval Notes

The user approved the direction after the design summary. This spec turns that direction into implementation constraints and verification gates.
