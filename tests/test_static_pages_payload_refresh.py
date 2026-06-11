from __future__ import annotations

import json
from pathlib import Path

from scripts.build_github_pages import _dashboard_payload_with_refreshed_thesis_status


def _dashboard_payload(strict_complete: int, strict_total: int) -> dict:
    return {
        "thesis_upgrade": {
            "readiness_summary": {
                "strict_complete_gates": strict_complete,
                "strict_total_gates": strict_total,
                "completion_status": "stale",
            },
            "components": {
                "motion_confound": {"fmriprep_motion_control_ready": False},
                "reproducible_archive": {
                    "publication_release_ready": True,
                    "publication_doi_ready": False,
                },
            },
        },
        "dynamic_mechanism": {
            "analysis_status": "implemented_first_pass",
            "mechanism_ranking": [{"layer": "C", "rank": 1, "score": 0.8}],
            "robustness": {"subject_bootstrap": {"layer_summary": []}, "run_sensitivity": {"run_rows": []}},
        },
        "cv5_validation": {"completed_folds": 5, "total_folds": 5, "held_out_validation_completed": True},
        "empirical_viewer": {},
        "figure_deck": {"status_cards": [{"label": "stale", "value": "stale", "claim_status": "blocked"}]},
        "figure_explainers": {
            "strict_gate_chart": {
                "plot_id": "strict_gate_chart",
                "title": "stale",
                "claim_status": "blocked",
            }
        },
        "evidence_flow": {"nodes": [{"id": "stale"}]},
    }


def test_refreshed_thesis_status_recomputes_derived_figure_payloads(tmp_path: Path) -> None:
    site = tmp_path / "_site"
    dashboard_dir = site / "dashboard"
    dashboard_dir.mkdir(parents=True)
    (dashboard_dir / "dashboard-data.json").write_text(
        json.dumps(_dashboard_payload(strict_complete=1, strict_total=6)),
        encoding="utf-8",
    )
    refreshed = _dashboard_payload(strict_complete=6, strict_total=6)["thesis_upgrade"]

    payload = _dashboard_payload_with_refreshed_thesis_status(site, refreshed, tmp_path)

    assert payload is not None
    assert payload["thesis_upgrade"] == refreshed
    assert payload["figure_explainers"]["strict_gate_chart"]["title"] == "Strict thesis gates"
    assert payload["figure_deck"]["status_cards"][0]["label"] == "Motion proof"
    assert payload["evidence_flow"]["nodes"][-1]["status"].startswith("6/6 strict gates complete")
