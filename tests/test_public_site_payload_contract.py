from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lsd_thesis.web.site_payload import build_public_site_payload

REPO_ROOT = Path(__file__).resolve().parents[1]


def _minimal_dashboard_payload() -> dict[str, Any]:
    return {
        "thesis_upgrade": {
            "readiness_summary": {
                "strict_complete_gates": 1,
                "strict_total_gates": 2,
                "completion_status": "research_demo_ready_not_completed_thesis",
                "thesis_status": "research_demo_ready_not_completed_thesis",
            },
            "strict_completion_requirements": [
                {
                    "requirement_id": "motion_confound_control_result",
                    "label": "Motion confound control result",
                    "status": "blocked",
                    "complete": False,
                    "evidence": "results/confound_controls/motion_confound_control_status.json",
                    "missing": "missing paired motion-control rows",
                    "next_action": "run an approved motion-control pass",
                    "claim_effect": "claim remains blocked",
                }
            ],
            "components": {
                "motion_confound": {"analysis_status": "blocked"},
                "reproducible_archive": {"publication_release_ready": True, "publication_doi_ready": False},
            },
        },
        "artifact_links": {
            "reports": [{"label": "Stage 2", "href": "/artifacts/docs/stage_reports/stage_2.md"}],
            "figures": [{"label": "Stage 2 figure", "href": "/artifacts/results/stage_2/figures/example.html"}],
        },
        "external_cortical_maps": {"analysis_status": "missing"},
        "dynamic_mechanism": {"analysis_status": "implemented_first_pass"},
        "cv5_validation": {"status": "complete", "completed_folds": 5, "total_folds": 5},
        "empirical_viewer": {"display_metadata": {"status": "cache_ready"}},
    }


def _assert_mapping(value: Any, label: str) -> Mapping[str, Any]:
    assert isinstance(value, Mapping), label
    return value


def _assert_records(value: Any, label: str) -> list[Mapping[str, Any]]:
    assert isinstance(value, list), label
    assert all(isinstance(item, Mapping) for item in value), label
    return value


def test_build_public_site_payload_exposes_public_schema_contract() -> None:
    payload = build_public_site_payload(REPO_ROOT, _minimal_dashboard_payload())

    assert {
        "appendix",
        "artifact_links",
        "claim_ladder",
        "dashboard",
        "empirical_viewer",
        "generated_at_utc",
        "methods",
        "pitch",
        "project",
        "schema_version",
        "source_dashboard",
    }.issubset(payload)
    assert payload["schema_version"] == "public_site.v1"

    project = _assert_mapping(payload["project"], "project")
    assert {"title", "subtitle", "one_sentence_claim", "audience", "guardrail"}.issubset(project)

    claim_ladder = _assert_mapping(payload["claim_ladder"], "claim_ladder")
    requirements = _assert_records(claim_ladder["requirements"], "claim_ladder.requirements")
    assert requirements
    for requirement in requirements:
        assert {"id", "title", "tier", "status", "evidence", "next_action", "q_value", "fdr_pass", "ci", "ci_crosses_zero"}.issubset(
            requirement
        )


def test_build_public_site_payload_keeps_dashboard_and_artifact_shapes() -> None:
    payload = build_public_site_payload(REPO_ROOT, _minimal_dashboard_payload())
    dashboard = _assert_mapping(payload["dashboard"], "dashboard")

    assert {"status_cards", "prior_art_cards", "viewer_modes", "primary_panels", "source_dashboard_key_count"}.issubset(dashboard)
    for card in _assert_records(dashboard["status_cards"], "dashboard.status_cards"):
        assert {"label", "value", "detail"}.issubset(card)

    for card in _assert_records(dashboard["prior_art_cards"], "dashboard.prior_art_cards"):
        assert {"prior_art_family", "maps_to_layers", "status", "artifact_path", "limitation"}.issubset(card)

    for mode in _assert_records(dashboard["viewer_modes"], "dashboard.viewer_modes"):
        assert {"title", "route", "works", "does_not_work"}.issubset(mode)
        assert isinstance(mode["route"], str) and mode["route"].startswith("/")

    appendix = _assert_mapping(payload["appendix"], "appendix")
    for artifact in _assert_records(appendix["all_artifacts"], "appendix.all_artifacts"):
        assert {"kind", "label", "href"}.issubset(artifact)
        assert artifact["kind"] in {"reports", "figures"}
        assert isinstance(artifact["href"], str) and artifact["href"].startswith("/artifacts/")
        assert "\\" not in artifact["href"]
