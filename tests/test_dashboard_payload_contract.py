from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from lsd_thesis.web.app import build_dashboard_payload

REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_CLAIM_STATUSES = {
    "implemented",
    "proxy-supported",
    "mixed",
    "unsupported",
    "blocked",
    "future",
}


@pytest.fixture(scope="module")
def dashboard_payload() -> dict[str, Any]:
    return build_dashboard_payload(REPO_ROOT)


def _assert_mapping(value: Any, label: str) -> Mapping[str, Any]:
    assert isinstance(value, Mapping), label
    return value


def _assert_records(value: Any, label: str) -> list[Mapping[str, Any]]:
    assert isinstance(value, list), label
    assert all(isinstance(item, Mapping) for item in value), label
    return value


def test_build_dashboard_payload_exposes_required_top_level_contract(dashboard_payload: dict[str, Any]) -> None:
    assert {
        "artifact_links",
        "audit_status",
        "baseline",
        "baseline_parameters",
        "claim_status",
        "cv5_validation",
        "dynamic_mechanism",
        "empirical",
        "empirical_validation",
        "empirical_viewer",
        "evidence_flow",
        "external_cortical_maps",
        "figure_deck",
        "figure_explainers",
        "graph",
        "model_selection",
        "perturbed",
        "provenance",
        "set_setting_seed",
        "stage_summaries",
        "structural_dti",
        "thesis_expansion",
        "thesis_upgrade",
    }.issubset(dashboard_payload)

    graph = _assert_mapping(dashboard_payload["graph"], "graph")
    nodes = _assert_records(graph.get("nodes"), "graph.nodes")
    assert nodes
    for node in nodes:
        assert {"name", "group", "x", "y"}.issubset(node)
        assert isinstance(node["name"], str) and node["name"]

    edges = _assert_records(graph.get("edges"), "graph.edges")
    assert edges
    for edge in edges:
        assert {"source", "target", "weight"}.issubset(edge)

    assert isinstance(dashboard_payload["stage_summaries"], Mapping)
    assert isinstance(dashboard_payload["baseline_parameters"], Mapping)


def test_build_dashboard_payload_keeps_figure_deck_schema(dashboard_payload: dict[str, Any]) -> None:
    figure_deck = _assert_mapping(dashboard_payload["figure_deck"], "figure_deck")

    assert {"title", "subtitle", "status_cards", "figures"}.issubset(figure_deck)

    status_cards = _assert_records(figure_deck["status_cards"], "figure_deck.status_cards")
    assert status_cards
    for card in status_cards:
        assert {"label", "value", "claim_status"}.issubset(card)
        assert card["claim_status"] in ALLOWED_CLAIM_STATUSES

    figures = _assert_records(figure_deck["figures"], "figure_deck.figures")
    assert figures
    for figure in figures:
        assert {"plot_id", "title", "subtitle", "claim_status", "input_artifacts", "source_paths"}.issubset(figure)
        assert isinstance(figure["plot_id"], str) and figure["plot_id"]
        assert figure["claim_status"] in ALLOWED_CLAIM_STATUSES
        _assert_records(figure["input_artifacts"], f"{figure['plot_id']}.input_artifacts")
        assert isinstance(figure["source_paths"], list)


def test_build_dashboard_payload_keeps_public_artifact_href_conventions(dashboard_payload: dict[str, Any]) -> None:
    artifact_links = _assert_mapping(dashboard_payload["artifact_links"], "artifact_links")

    assert {"reports", "figures"}.issubset(artifact_links)
    for bucket_name in ("reports", "figures"):
        items = _assert_records(artifact_links[bucket_name], f"artifact_links.{bucket_name}")
        if bucket_name == "reports":
            assert items
        for item in items:
            assert {"label", "href"}.issubset(item)
            assert isinstance(item["label"], str) and item["label"]
            assert isinstance(item["href"], str) and item["href"].startswith("/artifacts/")
            assert "\\" not in item["href"]
