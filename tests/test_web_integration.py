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


def test_artifacts_rejects_path_traversal(client: TestClient) -> None:
    response = client.get("/artifacts/../../etc/passwd")
    assert response.status_code in (403, 404)


def test_artifacts_serves_allowed_files_without_browser_cache(client: TestClient) -> None:
    response = client.get("/artifacts/docs/stage_reports/stage_2.md")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_favicon_returns_no_content(client: TestClient) -> None:
    response = client.get("/favicon.ico")
    assert response.status_code == 204
