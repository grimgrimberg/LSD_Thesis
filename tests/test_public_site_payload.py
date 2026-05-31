from __future__ import annotations

from pathlib import Path

from lsd_thesis.web.site_payload import build_public_site_payload, build_route_links


def test_public_site_payload_separates_claim_tiers_and_uncertainty_fields(tmp_path: Path) -> None:
    dashboard_payload = {
        "thesis_upgrade": {
            "readiness_summary": {
                "strict_complete_gates": 1,
                "strict_total_gates": 2,
                "thesis_status": "proposal_ready_not_thesis_complete",
            },
            "components": {
                "motion_confound": {
                    "strict_requirement": {"status": "blocked_missing_motion_file"}
                }
            },
            "strict_completion_requirements": [
                {
                    "requirement_id": "cv5",
                    "label": "Subject-disjoint CV5",
                    "complete": True,
                    "claim_effect": "No window-random reporting.",
                    "q_value": 0.04,
                    "fdr_pass": True,
                    "ci": "0.10 to 0.30",
                    "ci_crosses_zero": False,
                },
                {
                    "requirement_id": "receptor_pet",
                    "label": "PET receptor prior",
                    "complete": False,
                    "missing": "Supply authorized receptor map projection.",
                },
            ],
        },
        "artifact_links": {
            "reports": [
                {"label": "Claim Evidence Matrix", "href": "/artifacts/results/thesis_evidence_loop/claim_evidence_matrix.csv"},
                {"label": "ROCKET benchmark", "href": "/artifacts/results/training/rocket_condition_benchmark/benchmark_report.md"},
            ],
            "figures": [],
        },
        "cv5_validation": {"analysis_status": "ready"},
        "dynamic_mechanism": {"analysis_status": "ready"},
        "external_cortical_maps": {"analysis_status": "exploratory"},
    }

    payload = build_public_site_payload(tmp_path, dashboard_payload)

    assert payload["project"]["one_sentence_claim"].startswith("This project tests whether LSD-like")
    assert payload["dashboard"]["status_cards"][0]["value"] == "1/2 strict gates"
    assert payload["claim_ladder"]["requirements"][0]["status"] == "supported_now"
    assert payload["claim_ladder"]["requirements"][0]["q_value"] == "0.04"
    assert payload["claim_ladder"]["requirements"][1]["status"] == "not_supported_yet"
    assert payload["claim_ladder"]["tiers"][-1]["tier"] == "blocked_future"
    assert payload["appendix"]["priority_reports"][0]["label"] == "Claim Evidence Matrix"


def test_public_site_route_links_static_and_local() -> None:
    assert build_route_links(static=False)["dashboard"] == "/dashboard"
    assert build_route_links(static=True, depth=0)["methods"] == "methods.html"
    assert build_route_links(static=True, depth=1)["appendix"] == "../appendix.html"
