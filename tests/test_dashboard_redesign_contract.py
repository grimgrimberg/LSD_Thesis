from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_dashboard_templates_expose_redesign_surfaces() -> None:
    empirical = _read("src/lsd_thesis/templates/pages/empirical.html")
    prior_art = _read("src/lsd_thesis/templates/pages/prior_art.html")
    thesis = _read("src/lsd_thesis/templates/pages/thesis.html")

    assert "empirical_window" in empirical
    assert "empirical_fc_heatmap" in empirical
    assert "empirical_raw_json" in empirical
    assert "prior_art_paper_tabs" in prior_art
    assert "prior_art_paper_board" in prior_art
    assert "thesis_mechanism_chart" in thesis
    assert "thesis_claim_ladder" in thesis


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


def test_static_builder_knows_thesis_entrypoint_and_relative_paths() -> None:
    builder = _read("scripts/build_github_pages.py")

    assert '"thesis": f"{prefix}thesis.html"' in builder
    assert 'thesis_html = site / "thesis.html"' in builder
    assert '"pages/thesis.html"' in builder
    assert '"thesis": "thesis.html"' in builder
    assert 'static_prefix=f"{prefix}static/"' in builder
    assert 'plotly_src=f"{prefix}assets/plotly.min.js"' in builder
