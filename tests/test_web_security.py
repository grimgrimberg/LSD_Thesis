from __future__ import annotations

from fastapi.testclient import TestClient

from lsd_thesis.web.app import REPO_ROOT, create_app
from lsd_thesis.web.artifacts import resolve_artifact_path


def test_dashboard_page_sets_browser_safety_headers() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cross-origin-resource-policy"] == "same-origin"
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


def test_figure_deck_page_uses_dashboard_safety_headers() -> None:
    client = TestClient(create_app())

    response = client.get("/figures")

    assert response.status_code == 200
    assert "Figure Deck" in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_artifact_route_rejects_project_files_and_subject_level_cache() -> None:
    client = TestClient(create_app())

    project_file = client.get("/artifacts/configs/regimes/baseline.yaml")
    traversal = client.get("/artifacts/%2e%2e/%2e%2e/AGENTS.md")

    assert project_file.status_code == 403
    assert traversal.status_code in (403, 404)
    assert resolve_artifact_path(
        "results/stage_2/empirical_viewer/subject_views/sub-001_run-01.json",
        REPO_ROOT,
    ) is None


def test_artifact_route_serves_allowed_reports_with_no_store_headers() -> None:
    client = TestClient(create_app())

    response = client.get("/artifacts/docs/stage_reports/stage_2.md")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"


def test_html_figure_artifacts_are_script_sandboxed() -> None:
    client = TestClient(create_app())

    response = client.get("/artifacts/results/stage_2/figures/sober_fit_history.html")

    assert response.status_code == 200
    csp = response.headers["content-security-policy"]
    assert "sandbox allow-scripts" in csp
    assert "https://cdn.plot.ly" in csp
    assert "allow-same-origin" not in csp
    assert response.headers["x-content-type-options"] == "nosniff"


def test_empirical_view_rejects_path_shaped_identifiers() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/empirical-view",
        params={"subject": "../../output/doc/defense_presentation", "run": "run-01"},
    )

    assert response.status_code == 400


def test_simulate_endpoint_rejects_invalid_interactive_parameters() -> None:
    client = TestClient(create_app())

    assert client.post("/api/simulate", json={"temperature": -1.0}).status_code == 422
    assert client.post("/api/simulate", json={"regime": "unknown"}).status_code == 422
    assert client.post("/api/simulate", json={"tau": 1e-12}).status_code == 422
    assert client.post("/api/simulate", json={"unexpected": 1}).status_code == 422
