from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_dashboard_templates_expose_redesign_surfaces() -> None:
    overview = _read("src/lsd_thesis/templates/pages/overview.html")
    ranking = _read("src/lsd_thesis/templates/pages/mechanism_ranking.html")
    robustness = _read("src/lsd_thesis/templates/pages/robustness.html")
    empirical = _read("src/lsd_thesis/templates/pages/empirical.html")
    prior_art = _read("src/lsd_thesis/templates/pages/prior_art.html")
    submission = _read("src/lsd_thesis/templates/pages/submission.html")
    thesis = _read("src/lsd_thesis/templates/pages/thesis.html")
    figures = _read("src/lsd_thesis/templates/pages/figures.html")

    assert "evidence_flow" in overview
    assert "overview_pitch_cards" in overview
    assert "strict_gate_chart_explainer" in overview
    assert "overview_literature_chart_explainer" in overview
    assert "ranking_chart_explainer" in ranking
    assert "benchmark_chart_explainer" in ranking
    assert "ranking_unit_cards" in ranking
    assert "robustness_chart_explainer" in robustness
    assert "run_sensitivity_chart_explainer" in robustness
    assert "empirical_window" in empirical
    assert "empirical_fc_heatmap" in empirical
    assert "empirical_raw_json" in empirical
    assert "empirical_delta_chart_explainer" in empirical
    assert "empirical_fc_heatmap_explainer" in empirical
    assert "prior_art_paper_tabs" in prior_art
    assert "prior_art_paper_board" in prior_art
    assert "submission_insight_cards" in submission
    assert "submission_mechanism_chart" in submission
    assert "submission_mechanism_chart_explainer" in submission
    assert "submission_bootstrap_chart" in submission
    assert "submission_uncertainty_chart" in submission
    assert "submission_e_horizon_chart" in submission
    assert "submission_run_sensitivity_chart" in submission
    assert "submission_plot_notes" in submission
    assert "submission_benchmark_chart" in submission
    assert "submission_benchmark_chart_explainer" in submission
    assert "submission_cv5_fold_chart" in submission
    assert "submission_cv5_fold_chart_explainer" in submission
    assert "submission_strict_gate_chart" in submission
    assert "submission_strict_gate_chart_explainer" in submission
    assert "submission_decision_matrix" in submission
    assert "submission_unit_cards" in submission
    assert "submission_status_balance_chart" in submission
    assert "submission_dashboard_tour" in submission
    assert "submission_artifact_links" in submission
    assert "submission_next_track" in submission
    assert "submission_email_brief" in submission
    assert "thesis_mechanism_chart" in thesis
    assert "thesis_mechanism_chart_explainer" in thesis
    assert "thesis_claim_ladder" in thesis
    assert "thesis_pitch_cards" in thesis
    assert "thesis_status_balance_chart" in thesis
    assert "figure_deck_cards" in figures
    assert "figure_deck_status_cards" in figures
    assert "figure_unit_cards" in figures
    assert "figure_atlas_links" in figures


def test_dashboard_renderer_contracts_are_present() -> None:
    renderer = _read("src/lsd_thesis/static/dashboard.js")

    assert "function sanitizeSeries" in renderer
    assert "function sanitizeMatrix" in renderer
    assert "autosize: true" in renderer
    assert "compactLayoutForTarget" in renderer
    assert "nextConfig.displayModeBar = false" in renderer
    assert "window.Plotly.Plots?.resize?.(target)" in renderer
    assert "displayModeBar: true" in renderer
    assert "window.Plotly.purge" in renderer
    assert "isStaticDeployment" in renderer
    assert "/api/empirical-view" in renderer
    assert "function renderFigureExplainer" in renderer
    assert "function renderEvidenceFlow" in renderer
    assert "function renderFigureDeck" in renderer
    assert "function renderUnitGuide" in renderer
    assert "function renderPitchCards" in renderer
    assert "function renderStatusBalance" in renderer
    assert "function renderSubmission" in renderer
    assert "function renderSubmissionBootstrapChart" in renderer
    assert "function renderSubmissionUncertaintyChart" in renderer
    assert "function renderSubmissionEHorizonChart" in renderer
    assert "function renderSubmissionRunSensitivityChart" in renderer
    assert "function renderSubmissionCV5FoldChart" in renderer
    assert "function renderSubmissionStrictGateChart" in renderer
    assert "function renderSubmissionNextTrack" in renderer
    assert "motion-proof-first plan" in renderer
    assert "submission_next_track" in renderer
    assert 'pageId === "submission"' in renderer
    assert "How this plot was calculated" in renderer
    assert "textposition: \"auto\"" in renderer


def test_dashboard_css_removes_external_fonts_and_supports_print() -> None:
    css = _read("src/lsd_thesis/static/dashboard.css")

    assert "fonts.googleapis" not in css
    assert "radial-gradient" not in css
    assert "linear-gradient" not in css
    assert "letter-spacing: -" not in css
    assert "@media print" in css
    assert '.chart[data-plotly-rendered="true"]' in css
    assert ".chart .modebar" in css
    assert "  .chart {\n    min-width: 560px" not in css
    assert "  .matrix-chart {\n    min-width: 640px" not in css
    assert ".matrix-chart {\n  min-height: 480px;\n  min-width: 660px" not in css
    assert ".modebar" in css
    assert ".evidence-flow-track" in css
    assert ".figure-explainer-grid" in css
    assert ".figure-deck" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "evidence-rise" in css


def test_static_builder_knows_thesis_entrypoint_and_relative_paths() -> None:
    builder = _read("scripts/build_github_pages.py")

    assert "def _write_public_root_router" in builder
    assert "Start with the PI review summary" in builder
    assert "Technical evidence console" in builder
    assert '"submission": f"{prefix}submission.html"' in builder
    assert '"thesis": f"{prefix}thesis.html"' in builder
    assert '"figures": f"{prefix}figures.html"' in builder
    assert 'submission_html = site / "submission.html"' in builder
    assert 'thesis_html = site / "thesis.html"' in builder
    assert 'figures_html = site / "figures.html"' in builder
    assert '"pages/submission.html"' in builder
    assert '"pages/thesis.html"' in builder
    assert '"pages/figures.html"' in builder
    assert '"submission": "submission.html"' in builder
    assert '"thesis": "thesis.html"' in builder
    assert '"figures": "figures.html"' in builder
    assert '"pi_review": "pi-review/"' in builder
    assert '"pi_review_decision_gates": "pi-review/pages/decision-gates.html"' in builder
    assert '"pi_review_claim_ledger": "pi-review/pages/claim-ledger.html"' in builder
    assert "def _copy_pi_review_site" in builder
    assert "def _write_visual_atlas" in builder
    assert '<link rel="icon" href="data:,">' in builder
    assert "pitch-slides.html" in builder
    assert "root_prefix=prefix" in builder
    assert 'static_prefix=f"{prefix}static/"' in builder
    assert 'plotly_src=f"{prefix}assets/plotly.min.js"' in builder


def test_preview_preflight_knows_figure_deck_contract() -> None:
    preview = _read("scripts/preview_dashboard.py")

    assert '("/submission", "supervisor submission page' in preview
    assert '"src/lsd_thesis/templates/pages/submission.html"' in preview
    assert '("/figures", "publication figure-deck page' in preview
    assert '"src/lsd_thesis/templates/pages/figures.html"' in preview


def test_pi_review_package_presents_motion_proof_first_plan() -> None:
    start = _read("docs/reports/pi_thesis_share_package/deliverable_website/OPEN_ME_FIRST.html")
    slides = _read("docs/reports/pi_thesis_share_package/deliverable_website/pages/pitch-slides.html")
    next_steps = _read("docs/reports/pi_thesis_share_package/PROBLEMS_AND_NEXT_STEPS.md")
    email = _read("docs/reports/pi_thesis_share_package/EMAIL_TO_PI.md")

    public_package = "\n".join([start, slides, next_steps, email])

    assert "Motion-Proof First Plan" in public_package
    assert "FD/DVARS/censoring motion-proof pack" in public_package
    assert "Inputs to secure" in public_package
    assert "Outputs to produce" in public_package
    assert "Keep E caveated" in public_package
    assert "parcellation/null audit" in public_package

    forbidden_prompts = [
        "The decision I need from you",
        "which scientific blocker should become the next thesis milestone",
        "Ask which blocker should become",
    ]
    for prompt in forbidden_prompts:
        assert prompt not in public_package


def test_pi_review_start_page_is_executive_summary_not_full_appendix() -> None:
    start = _read("docs/reports/pi_thesis_share_package/deliverable_website/OPEN_ME_FIRST.html")

    assert "Executive Summary" in start
    assert "not thesis-complete" in start
    assert "Research-demo evidence package; not completed neuroscience thesis" in start
    assert "C: hierarchy/routing layer" in start
    assert "Subject-level FD/DVARS/censoring motion-confound proof absent" in start
    assert "GitHub release exists; Zenodo DOI/public reproducible archive gate pending" in start
    assert "Please evaluate whether the motion-proof-first validation plan is sufficient" in start
    assert "OpenNeuro ds003059" in start
    assert "15 subject/session averages" in start
    assert "cached public derived artifacts" in start
    assert "Claim-status legend" in start
    assert "Thirty-second read" in start
    assert "The whole project in four points" in start
    assert "Optional depth" in start
    assert "Motion-Proof First Plan" in start
    assert "FD/DVARS/censoring motion-proof pack" in start
    assert "Key Figures" in start
    assert "Evidence Notes" in start
    assert start.count("<section") <= 6

    cluttered_first_read_markers = [
        "Dashboard tour",
        "Six local screenshots",
        "Recommended order",
        "rubber-duck explanation",
        "Open Full Appendix",
        "Full package appendix",
    ]
    for marker in cluttered_first_read_markers:
        assert marker not in start


def test_pi_review_public_routes_surface_claim_gates() -> None:
    decision_gates = _read("docs/reports/pi_thesis_share_package/deliverable_website/pages/decision-gates.html")
    claim_ledger = _read("docs/reports/pi_thesis_share_package/deliverable_website/pages/claim-ledger.html")
    methods = _read("docs/reports/pi_thesis_share_package/deliverable_website/pages/methods.html")

    assert "Decision Gates And Next Validation" in decision_gates
    assert "motion/confound" in decision_gates
    assert "DOI/archive" in decision_gates
    assert "atlas replication" in decision_gates
    assert "external validation" in decision_gates

    assert "Claim Ledger" in claim_ledger
    assert "C is the provisional leading macro-dynamic proxy" in claim_ledger
    assert "E1 lower transition/control-energy proxy" in claim_ledger
    assert "E2 receptor-specific placement" in claim_ledger
    assert "B DMDc negative-control baseline" in claim_ledger
    assert "blocked" in claim_ledger

    assert "Methods And Limitations" in methods
    assert "What decisions the methods can support" in methods
    assert "Implemented pipeline" in methods
    assert "Current proxy limitations" in methods
    assert "Missing thesis-grade analyses" in methods
    assert "Future methods" in methods


def test_static_figure_atlas_surfaces_curated_review_route() -> None:
    builder = _read("scripts/build_github_pages.py")

    assert "Start With These Figures" in builder
    assert "Current A-E ranking" in builder
    assert "Rank stability" in builder
    assert "Run sensitivity" in builder
    assert "E proxy boundary" in builder
    assert "Motion/confound blocker" in builder
    assert "No new plots were generated for this atlas" in builder
    assert "Motion-proof-first plot route" in builder
    assert "metric_unit" in builder
    assert "claim_supported" in builder
    assert "figure_role" in builder
    assert "source_data" in builder
    assert "calculation_note" in builder
    assert "required_next_check" in builder
    assert "View figure" in builder
    assert "Source data" in builder
    assert "Calculation note" in builder
