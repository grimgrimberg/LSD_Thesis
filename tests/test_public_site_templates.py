from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from lsd_thesis.web.site_payload import build_route_links

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "src" / "lsd_thesis" / "templates"


def _payload() -> dict:
    return {
        "generated_at_utc": "2026-05-31T00:00:00+00:00",
        "project": {
            "title": "Fixture LSD Thesis",
            "one_sentence_claim": "This project tests transition/control dynamics.",
            "guardrail": "This is a conservative surrogate-analysis site.",
        },
        "pitch": {
            "meeting_script": ["Start with the one-sentence claim."],
            "what_to_open": [{"label": "Evidence dashboard", "why": "shows claim gates"}],
            "pi_fit": ["AI/data-science angle"],
            "why_now": ["Dashboard-first communication"],
        },
        "dashboard": {
            "status_cards": [
                {"label": "Motion/confounds", "value": "blocked", "detail": "explicitly gated"}
            ],
            "viewer_modes": [
                {
                    "title": "Public/static dashboard",
                    "route": "/dashboard/",
                    "works": "Claim status",
                    "does_not_work": "Live simulation",
                }
            ],
        },
        "claim_ladder": {
            "primary_claim": "This project tests transition/control dynamics.",
            "tiers": [
                {"tier": "supported_now", "title": "Supported now", "claim": "Macro-dynamics", "items": ["CV5"]},
                {"tier": "blocked_future", "title": "Blocked / future work", "claim": "Spatial nulls", "items": ["PET"]},
            ],
            "requirements": [
                {
                    "status": "not_supported_yet",
                    "title": "Receptor prior",
                    "q_value": "not reported",
                    "fdr_pass": "not reported",
                    "ci": "not reported",
                    "ci_crosses_zero": "not reported",
                    "evidence": "Exploratory only",
                    "next_action": "Run spatial nulls",
                }
            ],
        },
        "methods": {
            "local_runtime": {
                "static_boundary": "GitHub Pages is static and cannot run backend API features.",
                "local_boundary": "The local FastAPI app can call /api/dashboard-data, /api/simulate, and /api/empirical-view.",
                "features": ["Interactive simulation", "Subject viewer"],
                "command": "uv run python scripts/run_dashboard.py",
            },
            "pipeline_steps": ["Raw fMRI", "Dynamic features"],
            "limitations": ["8-module layer is for explanation"],
            "controls": ["Subject-disjoint CV"],
        },
        "appendix": {
            "priority_reports": [{"label": "Claim Evidence Matrix", "href": "/artifacts/results/thesis_evidence_loop/claim_evidence_matrix.csv"}],
            "all_artifacts": [{"kind": "reports", "label": "Claim Evidence Matrix", "href": "/artifacts/results/thesis_evidence_loop/claim_evidence_matrix.csv"}],
        },
    }


def _render(template_name: str) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_ROOT)), autoescape=select_autoescape(("html", "xml")))
    return env.get_template(template_name).render(
        payload=_payload(),
        links=build_route_links(static=True),
        artifact_prefix="artifacts/",
        data_url="dashboard/dashboard-data.json",
        deployment_mode="static",
    )


@pytest.mark.parametrize(
    ("template_name", "required_text"),
    [
        ("public_site.html", "Macro-dynamics, not mysticism."),
        ("thesis_story.html", "q-value"),
        ("evidence_dashboard.html", "Claim Status"),
        ("methods_reproducibility.html", "Plain-language DTI framing"),
        ("appendix.html", "Artifacts, not raw data."),
    ],
)
def test_public_site_templates_render_pitch_and_defense_language(template_name: str, required_text: str) -> None:
    html = _render(template_name)

    assert required_text in html


def test_static_templates_do_not_link_to_backend_only_local_route() -> None:
    for template_name in (
        "public_site.html",
        "thesis_story.html",
        "evidence_dashboard.html",
        "methods_reproducibility.html",
        "appendix.html",
    ):
        html = _render(template_name)
        assert 'href="/local-dashboard"' not in html
        assert "methods.html#local-dashboard" in html

    methods_html = _render("methods_reproducibility.html")
    assert "GitHub Pages is static" in methods_html
    assert "/api/simulate" in methods_html
    assert 'href="/local-dashboard"' not in methods_html
    assert "Start the local server" in methods_html


def test_evidence_dashboard_inline_javascript_passes_node_syntax_check(tmp_path: Path) -> None:
    html = _render("evidence_dashboard.html")
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
    assert scripts
    script_path = tmp_path / "dashboard-script.js"
    script_path.write_text("\n".join(scripts), encoding="utf-8")

    try:
        subprocess.run(["node", "--check", str(script_path)], check=True, capture_output=True, text=True)
    except FileNotFoundError:
        pytest.skip("node is not installed")
