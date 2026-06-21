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
