"""Integration tests for the FastAPI web endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lsd_thesis.web.app import app

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_dashboard_page_returns_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_dashboard_page_sets_browser_safety_headers(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "frame-ancestors 'none'" in csp


def test_dashboard_serves_local_plotly_asset(client: TestClient) -> None:
    response = client.get("/assets/plotly.min.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers.get("content-type", "")
    assert "Plotly" in response.text[:5000]


def test_dashboard_data_returns_expected_keys(client: TestClient) -> None:
    response = client.get("/api/dashboard-data")
    assert response.status_code == 200
    data = response.json()
    assert "graph" in data
    assert "baseline" in data
    assert "perturbed" in data


def test_simulate_endpoint_returns_valid_payload(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"regime": "baseline"})
    assert response.status_code == 200
    data = response.json()
    assert "time_series" in data
    assert "modules" in data


def test_simulate_endpoint_rejects_negative_temperature(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"temperature": -1.0})
    assert response.status_code == 422


def test_simulate_endpoint_rejects_extreme_values(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"barrier": 999.0})
    assert response.status_code == 422


def test_simulate_endpoint_rejects_unknown_regime(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"regime": "unknown"})
    assert response.status_code == 422


def test_simulate_endpoint_rejects_tiny_tau(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"tau": 1e-12})
    assert response.status_code == 422


def test_simulate_endpoint_accepts_zero_constraint_scale(client: TestClient) -> None:
    response = client.post("/api/simulate", json={"constraint_scale": 0.0})
    assert response.status_code == 200


def test_artifacts_rejects_path_traversal(client: TestClient) -> None:
    response = client.get("/artifacts/../../etc/passwd")
    assert response.status_code in (403, 404)


def test_artifacts_rejects_non_artifact_project_files(client: TestClient) -> None:
    response = client.get("/artifacts/configs/regimes/baseline.yaml")
    assert response.status_code == 403


def test_artifacts_serves_allowed_files_without_browser_cache(client: TestClient) -> None:
    response = client.get("/artifacts/docs/stage_reports/stage_2.md")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"


def test_html_artifacts_are_served_with_active_content_sandbox(client: TestClient) -> None:
    response = client.get("/artifacts/results/stage_2/figures/sober_fit_history.html")
    assert response.status_code == 200
    csp = response.headers["content-security-policy"]
    assert "sandbox allow-scripts" in csp
    assert "https://cdn.plot.ly" in csp
    assert "allow-same-origin" not in csp
    assert response.headers["x-content-type-options"] == "nosniff"


def test_static_report_html_artifacts_disable_scripts(client: TestClient) -> None:
    response = client.get("/artifacts/output/doc/thesis_microsite.html")
    assert response.status_code == 200
    csp = response.headers["content-security-policy"]
    assert "script-src 'none'" in csp
    assert "sandbox allow-same-origin" in csp
    assert "allow-scripts" not in csp


def test_empirical_view_rejects_path_shaped_identifiers(client: TestClient) -> None:
    response = client.get("/api/empirical-view", params={"subject": "../../output/doc/defense_presentation", "run": "run-01"})
    assert response.status_code == 400


def test_empirical_view_returns_not_found_for_unknown_safe_selection(client: TestClient) -> None:
    response = client.get("/api/empirical-view", params={"subject": "sub-999", "run": "run-99"})
    assert response.status_code == 404


def test_favicon_returns_no_content(client: TestClient) -> None:
    response = client.get("/favicon.ico")
    assert response.status_code == 204
