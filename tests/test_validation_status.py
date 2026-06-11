from __future__ import annotations

import json
from typing import Any

from lsd_thesis.web.status_payload import (
    CV5_AGGREGATE_RELATIVE_PATH,
    CV5_CURATED_AGGREGATE_RELATIVE_PATH,
    build_empirical_validation_payload,
    cv5_validation_integrity_errors,
    load_cv5_validation_payload,
)


def _complete_cv5_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "complete",
        "held_out_validation_completed": True,
        "approval_status": "approved",
        "all_folds_completed": True,
        "all_subjects_held_out_once": True,
        "completed_folds": 5,
        "total_folds": 5,
        "per_fold_subject_counts": [
            {"fold_id": f"fold_{index:02d}", "overlap_count": 0}
            for index in range(1, 6)
        ],
        "validation_claim_scope": "internal subject-disjoint CV5 validation only",
        "limitations": [
            (
                "Internal CV5 is not external validation; each fold uses n=3 held-out "
                "subjects; motion and FD/DVARS sensitivity remain separate caveats."
            )
        ],
        "warnings": [],
    }
    payload.update(overrides)
    return payload


def test_cv5_integrity_accepts_only_approved_complete_internal_aggregate() -> None:
    assert cv5_validation_integrity_errors(_complete_cv5_payload()) == ()


def test_cv5_integrity_rejects_unapproved_complete_metadata() -> None:
    errors = cv5_validation_integrity_errors(_complete_cv5_payload(approval_status="candidate"))

    assert "completed CV5 validation requires an approved split package" in errors


def test_load_cv5_payload_downgrades_invalid_complete_metadata(tmp_path) -> None:
    aggregate_path = tmp_path / CV5_AGGREGATE_RELATIVE_PATH
    aggregate_path.parent.mkdir(parents=True)
    aggregate_path.write_text(
        json.dumps(_complete_cv5_payload(approval_status="candidate")),
        encoding="utf-8",
    )

    payload = load_cv5_validation_payload(tmp_path)

    assert payload is not None
    assert payload["held_out_validation_completed"] is False
    assert payload["status"] == "invalid_complete_metadata"
    assert payload["validation_integrity_status"] == "invalid_or_incomplete"


def test_load_cv5_payload_uses_curated_fallback_when_output_is_absent(tmp_path) -> None:
    aggregate_path = tmp_path / CV5_CURATED_AGGREGATE_RELATIVE_PATH
    aggregate_path.parent.mkdir(parents=True)
    aggregate_path.write_text(json.dumps(_complete_cv5_payload()), encoding="utf-8")

    payload = load_cv5_validation_payload(tmp_path)

    assert payload is not None
    assert payload["validation_integrity_status"] == "verified_internal_cv5"
    assert payload["source_path"] == CV5_CURATED_AGGREGATE_RELATIVE_PATH.as_posix()


def test_empirical_validation_boundary_ignores_legacy_held_out_without_completion() -> None:
    payload = build_empirical_validation_payload(
        {
            "stage_2": {
                "dataset_anchor": "ds003059_cached_proxy",
                "empirical_validation_boundary": {
                    "held_out": True,
                    "held_out_validation_configured": True,
                    "approval_status": "candidate",
                    "warnings": [],
                },
            }
        }
    )

    assert payload["held_out"] is False
    assert payload["held_out_validation_completed"] is False
    assert "Legacy held_out=true flag ignored" in payload["warnings"][0]
