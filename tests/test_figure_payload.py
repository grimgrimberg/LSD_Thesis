from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.web.figure_payload import build_figure_payloads

REPO_ROOT = Path(__file__).resolve().parents[1]


def _minimal_dashboard_payload() -> dict:
    return {
        "thesis_upgrade": {
            "readiness_summary": {
                "strict_complete_gates": 4,
                "strict_total_gates": 6,
                "completion_status": "research_demo_ready_not_completed_thesis",
            },
            "components": {
                "motion_confound": {
                    "fmriprep_motion_control_ready": False,
                    "fmriprep_motion_preflight_next_action": "Supply authorized FD, DVARS, and censoring confounds.",
                },
                "reproducible_archive": {
                    "publication_release_ready": True,
                    "publication_doi_ready": False,
                },
            },
        },
        "dynamic_mechanism": {
            "analysis_status": "implemented_first_pass",
            "mechanism_ranking": [{"layer": "C", "rank": 1, "score": 0.8}],
            "robustness": {
                "subject_bootstrap": {"layer_summary": [{"layer": "C"}]},
                "run_sensitivity": {"run_rows": [{"run": "run-01"}]},
            },
        },
        "cv5_validation": {
            "held_out_validation_completed": True,
            "completed_folds": 5,
            "total_folds": 5,
        },
        "empirical_viewer": {
            "display_metadata": {"status": "cache_ready"},
        },
    }


def test_figure_payload_exposes_pipeline_explainers_and_deck() -> None:
    payload = build_figure_payloads(REPO_ROOT, _minimal_dashboard_payload())

    assert payload["evidence_flow"]["title"] == (
        "Data -> 8 modules -> A-E mechanisms -> robustness -> claim gates"
    )
    assert [node["id"] for node in payload["evidence_flow"]["nodes"]] == [
        "data",
        "modules",
        "mechanisms",
        "robustness",
        "claim_gates",
    ]
    assert {
        "strict_gate_chart",
        "ranking_chart",
        "robustness_chart",
        "empirical_delta_chart",
        "cv5_validation_summary",
        "archive_readiness_summary",
        "motion_proof_summary",
    }.issubset(payload["figure_explainers"])
    assert [figure["plot_id"] for figure in payload["figure_deck"]["figures"]] == [
        "strict_gate_chart",
        "ranking_chart",
        "robustness_chart",
        "overview_literature_chart",
        "empirical_delta_chart",
        "cv5_validation_summary",
        "archive_readiness_summary",
        "motion_proof_summary",
    ]


def test_every_major_figure_has_source_formula_caveat_and_claim_status() -> None:
    payload = build_figure_payloads(REPO_ROOT, _minimal_dashboard_payload())

    for plot_id, explainer in payload["figure_explainers"].items():
        assert explainer["plot_id"] == plot_id
        assert explainer["title"]
        assert explainer["metric_definition"]
        assert explainer["aggregation_level"]
        assert explainer["calculation"]
        assert explainer["caveat"]
        assert explainer["claim_status"] in {
            "implemented",
            "proxy-supported",
            "mixed",
            "blocked",
        }
        assert explainer["input_artifacts"], plot_id
        assert all(item["path"] for item in explainer["input_artifacts"])


def test_figure_payload_remains_claim_safe_and_fail_closed() -> None:
    payload = build_figure_payloads(REPO_ROOT, _minimal_dashboard_payload())
    serialized = json.dumps(payload).lower()

    assert "clinical proof" not in serialized
    assert "biological ground truth" not in serialized
    assert "subjective experience simulation" not in serialized
    assert payload["figure_explainers"]["archive_readiness_summary"]["claim_status"] == "blocked"
    assert payload["figure_explainers"]["motion_proof_summary"]["claim_status"] == "blocked"
