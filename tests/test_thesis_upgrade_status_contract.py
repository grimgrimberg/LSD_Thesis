from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lsd_thesis.thesis_upgrade import build_thesis_upgrade_status
from lsd_thesis.thesis_upgrade.status import PACKAGE_REQUIREMENT_IDS, SCHEMA_VERSION, STRICT_REQUIREMENT_IDS

REPO_ROOT = Path(__file__).resolve().parents[1]


def _records(value: Any, label: str) -> list[Mapping[str, Any]]:
    assert isinstance(value, list), label
    assert all(isinstance(item, Mapping) for item in value), label
    return value


def test_build_thesis_upgrade_status_exposes_readiness_contract() -> None:
    payload = build_thesis_upgrade_status(REPO_ROOT)

    assert {
        "claim_guardrail",
        "components",
        "gates",
        "generated_at_utc",
        "package_readiness_requirements",
        "readiness_summary",
        "schema_version",
        "source_basis",
        "strict_completion_requirements",
        "visualization_plan",
    }.issubset(payload)
    assert payload["schema_version"] == SCHEMA_VERSION

    summary = payload["readiness_summary"]
    assert isinstance(summary, Mapping)
    assert {
        "ready_gates",
        "total_gates",
        "readiness_fraction",
        "strict_complete_gates",
        "strict_total_gates",
        "strict_completion_fraction",
        "strict_missing_gates",
        "strict_missing_requirement_ids",
        "package_complete_gates",
        "package_total_gates",
        "package_completion_fraction",
        "package_missing_gates",
        "package_missing_requirement_ids",
        "remaining_hard_requirements",
        "remaining_packaging_requirements",
        "completion_status",
        "thesis_status",
    }.issubset(summary)
    assert isinstance(summary["strict_missing_requirement_ids"], list)
    assert isinstance(summary["package_missing_requirement_ids"], list)
    assert isinstance(summary["completion_status"], str) and summary["completion_status"]
    assert summary["thesis_status"] == summary["completion_status"]


def test_build_thesis_upgrade_status_keeps_gate_and_requirement_shapes() -> None:
    payload = build_thesis_upgrade_status(REPO_ROOT)

    for gate in _records(payload["gates"], "thesis_upgrade.gates"):
        assert {"label", "status", "ready", "evidence", "blocker", "score"}.issubset(gate)
        assert isinstance(gate["label"], str) and gate["label"]
        assert isinstance(gate["status"], str) and gate["status"]
        assert isinstance(gate["ready"], bool)

    strict_requirements = _records(payload["strict_completion_requirements"], "thesis_upgrade.strict_completion_requirements")
    package_requirements = _records(payload["package_readiness_requirements"], "thesis_upgrade.package_readiness_requirements")
    requirement_fields = {"requirement_id", "label", "status", "complete", "evidence", "missing", "next_action", "claim_effect"}
    assert {str(row["requirement_id"]) for row in strict_requirements} == set(STRICT_REQUIREMENT_IDS)
    assert {str(row["requirement_id"]) for row in package_requirements} == set(PACKAGE_REQUIREMENT_IDS)

    for requirement in strict_requirements + package_requirements:
        assert requirement_fields.issubset(requirement)
        assert isinstance(requirement["requirement_id"], str) and requirement["requirement_id"]
        assert isinstance(requirement["label"], str) and requirement["label"]
        assert isinstance(requirement["status"], str) and requirement["status"]
        assert isinstance(requirement["complete"], bool)


def test_build_thesis_upgrade_status_keeps_component_keys() -> None:
    payload = build_thesis_upgrade_status(REPO_ROOT)
    components = payload["components"]

    assert isinstance(components, Mapping)
    assert {
        "motion_confound",
        "canonical_parcellation",
        "neuromaps_spatial_nulls",
        "rocket_strengthening",
        "public_dashboard",
        "external_validation",
        "receptor_structural",
        "receptor_myelin_gradient_claim",
        "reproducible_archive",
    }.issubset(components)
    for component in components.values():
        assert isinstance(component, Mapping)
        assert "gate" in component
