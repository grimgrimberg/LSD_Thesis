from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lsd_thesis.thesis_loop import CLAIM_EVIDENCE_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]


def _json_object(relative_path: str) -> Mapping[str, Any]:
    path = REPO_ROOT / relative_path
    assert path.exists(), relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, Mapping), relative_path
    return payload


def _records(value: Any, label: str) -> list[Mapping[str, Any]]:
    assert isinstance(value, list), label
    assert all(isinstance(item, Mapping) for item in value), label
    return value


def _assert_required_fields(row: Mapping[str, Any], fields: set[str], label: str) -> None:
    assert fields.issubset(row), label


def test_stage_2_summary_and_empirical_viewer_schema_contract() -> None:
    summary = _json_object("results/stage_2/stage_2_summary.json")
    assert {
        "dataset_anchor",
        "empirical_subjects",
        "empirical_run_count",
        "empirical_validation_boundary",
        "empirical_viewer",
        "target_path",
        "perturbation_target_path",
    }.issubset(summary)
    assert isinstance(summary["dataset_anchor"], str) and summary["dataset_anchor"]
    assert isinstance(summary["empirical_subjects"], list)
    assert isinstance(summary["empirical_run_count"], int)
    assert isinstance(summary["empirical_validation_boundary"], Mapping)
    assert isinstance(summary["empirical_viewer"], Mapping)

    viewer = _json_object("results/stage_2/empirical_viewer/group_overview.json")
    assert {"conditions", "default_subject", "delta_metrics", "gallery", "module_names", "paired_subject_count", "runs", "subjects"}.issubset(
        viewer
    )
    assert isinstance(viewer["conditions"], Mapping)
    assert isinstance(viewer["default_subject"], str)
    assert isinstance(viewer["delta_metrics"], Mapping)
    assert isinstance(viewer["module_names"], list)
    assert isinstance(viewer["paired_subject_count"], int)
    assert isinstance(viewer["runs"], list)
    assert isinstance(viewer["subjects"], list)
    for gallery_item in _records(viewer["gallery"], "empirical_viewer.gallery"):
        _assert_required_fields(gallery_item, {"label", "path"}, "empirical_viewer.gallery item")
        assert isinstance(gallery_item["path"], str)
        assert Path(gallery_item["path"]).suffix in {".html", ".png", ".json"}


def test_dynamic_mechanism_summary_schema_contract() -> None:
    summary = _json_object("results/dynamic_mechanism_ranking/summary.json")
    assert {
        "analysis_status",
        "claim_guardrail",
        "claim_verdicts",
        "dataset_scope",
        "generated_at_utc",
        "literature_benchmark",
        "mechanism_ranking",
        "modules",
        "pair_count",
        "robustness",
        "schema_version",
        "source_path",
        "source_viewer_root",
        "subject_count",
    }.issubset(summary)
    assert isinstance(summary["schema_version"], int)
    assert isinstance(summary["analysis_status"], str) and summary["analysis_status"]
    assert isinstance(summary["pair_count"], int)
    assert isinstance(summary["subject_count"], int)
    assert isinstance(summary["source_path"], str) and summary["source_path"].endswith("results/dynamic_mechanism_ranking/summary.json")
    assert "\\" not in summary["source_path"]

    ranking_rows = _records(summary["mechanism_ranking"], "dynamic mechanism ranking rows")
    assert ranking_rows
    for row in ranking_rows:
        _assert_required_fields(row, {"rank", "layer", "mechanism", "status", "score", "evidence"}, "mechanism ranking row")
        assert isinstance(row["rank"], int)
        assert isinstance(row["layer"], str) and row["layer"]
        assert isinstance(row["mechanism"], str) and row["mechanism"]
        assert isinstance(row["status"], str) and row["status"]
        assert isinstance(row["score"], int | float)
        assert isinstance(row["evidence"], str) and row["evidence"]


def test_dynamic_mechanism_robustness_schema_contract() -> None:
    robustness = _json_object("results/dynamic_mechanism_ranking/robustness/robustness_summary.json")
    assert {
        "analysis_status",
        "claim_guardrail",
        "claim_verdicts",
        "d_window_sensitivity",
        "e_horizon_sensitivity",
        "generated_at_utc",
        "literature_benchmark",
        "pair_count",
        "run_sensitivity",
        "schema_version",
        "source_path",
        "source_viewer_root",
        "state_label_sensitivity",
        "subject_bootstrap",
        "subject_count",
    }.issubset(robustness)
    assert isinstance(robustness["schema_version"], int)
    assert isinstance(robustness["analysis_status"], str) and robustness["analysis_status"]
    assert isinstance(robustness["source_path"], str) and robustness["source_path"].endswith(
        "results/dynamic_mechanism_ranking/robustness/robustness_summary.json"
    )
    assert "\\" not in robustness["source_path"]

    row_specs = {
        "subject_bootstrap": (
            "layer_summary",
            {"layer", "current_score", "score_mean", "score_std", "score_ci_low", "score_ci_high", "median_rank", "rank_1_fraction"},
        ),
        "run_sensitivity": ("run_rows", {"layer", "run", "support_score", "metric_count"}),
        "e_horizon_sensitivity": (
            "rows",
            {
                "layer",
                "horizon",
                "support_score",
                "lsd_receptor_energy_reduction_pct",
                "lsd_uniform_energy_reduction_pct",
                "receptor_vs_random_energy_reduction_pct",
                "state_target_alignment_receptor",
            },
        ),
        "state_label_sensitivity": ("rows", {"layer", "state_method", "state_bins", "score_mode", "support_score"}),
        "d_window_sensitivity": (
            "rows",
            {
                "layer",
                "window_size",
                "support_score",
                "integration_segregation_balance_delta",
                "dynamic_fc_variance_delta",
                "dynamic_fc_path_length_delta",
                "global_efficiency_delta",
            },
        ),
    }
    for container_key, (rows_key, required_fields) in row_specs.items():
        container = robustness[container_key]
        assert isinstance(container, Mapping), container_key
        rows = _records(container[rows_key], f"{container_key}.{rows_key}")
        assert rows
        for row in rows:
            _assert_required_fields(row, required_fields, f"{container_key}.{rows_key} row")
            if container_key == "state_label_sensitivity":
                dynamic_delta_fields = {"transition_entropy_delta", "transition_rate_delta", "barrier_reduction_proxy_delta"}
                energy_fields = {
                    "lsd_receptor_energy_reduction_pct",
                    "receptor_vs_random_energy_reduction_pct",
                    "state_target_alignment_receptor",
                }
                assert dynamic_delta_fields.issubset(row) or energy_fields.issubset(row), "state_label_sensitivity metric fields"


def test_thesis_evidence_loop_status_schema_contract() -> None:
    payload = _json_object("results/thesis_evidence_loop/thesis_evidence_loop_status.json")
    assert {
        "analysis_status",
        "claim_evidence_matrix",
        "claim_evidence_matrix_columns",
        "claim_evidence_matrix_paths",
        "claim_guardrail",
        "components",
        "external_source_plan",
        "generated_at_utc",
        "schema_version",
        "status_rows",
    }.issubset(payload)
    assert payload["schema_version"] == 1
    assert payload["claim_evidence_matrix_columns"] == CLAIM_EVIDENCE_COLUMNS

    for row in _records(payload["status_rows"], "thesis_evidence_loop.status_rows"):
        _assert_required_fields(row, {"step", "label", "status", "artifact_target", "evidence", "blocker"}, "thesis evidence status row")
        assert isinstance(row["step"], str) and row["step"]
        assert isinstance(row["status"], str) and row["status"]

    for row in _records(payload["claim_evidence_matrix"], "thesis_evidence_loop.claim_evidence_matrix"):
        _assert_required_fields(row, set(CLAIM_EVIDENCE_COLUMNS), "claim evidence matrix row")

    matrix_paths = payload["claim_evidence_matrix_paths"]
    assert isinstance(matrix_paths, Mapping)
    csv_path = matrix_paths.get("csv")
    assert isinstance(csv_path, str) and csv_path.endswith(".csv")
    assert "\\" not in csv_path
    with (REPO_ROOT / csv_path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == CLAIM_EVIDENCE_COLUMNS
