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
    thesis = _read("src/lsd_thesis/templates/pages/thesis.html")
    figures = _read("src/lsd_thesis/templates/pages/figures.html")

    assert "evidence_flow" in overview
    assert "strict_gate_chart_explainer" in overview
    assert "overview_literature_chart_explainer" in overview
    assert "ranking_chart_explainer" in ranking
    assert "benchmark_chart_explainer" in ranking
    assert "robustness_chart_explainer" in robustness
    assert "run_sensitivity_chart_explainer" in robustness
    assert "empirical_window" in empirical
    assert "empirical_fc_heatmap" in empirical
    assert "empirical_raw_json" in empirical
    assert "empirical_delta_chart_explainer" in empirical
    assert "empirical_fc_heatmap_explainer" in empirical
    assert "prior_art_paper_tabs" in prior_art
    assert "prior_art_paper_board" in prior_art
    assert "thesis_mechanism_chart" in thesis
    assert "thesis_mechanism_chart_explainer" in thesis
    assert "thesis_claim_ladder" in thesis
    assert "figure_deck_cards" in figures
    assert "figure_deck_status_cards" in figures


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

    assert '"thesis": f"{prefix}thesis.html"' in builder
    assert '"figures": f"{prefix}figures.html"' in builder
    assert 'thesis_html = site / "thesis.html"' in builder
    assert 'figures_html = site / "figures.html"' in builder
    assert '"pages/thesis.html"' in builder
    assert '"pages/figures.html"' in builder
    assert '"thesis": "thesis.html"' in builder
    assert '"figures": "figures.html"' in builder
    assert 'static_prefix=f"{prefix}static/"' in builder
    assert 'plotly_src=f"{prefix}assets/plotly.min.js"' in builder


def test_preview_preflight_knows_figure_deck_contract() -> None:
    preview = _read("scripts/preview_dashboard.py")

    assert '("/figures", "publication figure-deck page' in preview
    assert '"src/lsd_thesis/templates/pages/figures.html"' in preview
