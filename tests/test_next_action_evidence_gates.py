from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.data.parcellations import available_parcellations, get_parcellation_spec
from lsd_thesis.dynamic_mechanism.priors import module_masks

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_next_action_gates_are_statused_without_overclaiming() -> None:
    loop = _load_json("results/thesis_evidence_loop/thesis_evidence_loop_status.json")
    rows = {row["label"]: row for row in loop["status_rows"]}

    assert rows["Motion-sensitive C gate"]["status"] == (
        "blocked_motion_sensitive_c_claim_requires_authorized_confound_exclusions"
    )
    assert rows["HCP structural graph"]["status"] == "implemented_hcp_structural_graph_sensitivity"
    assert "rewires=implemented_hcp_structural_graph_rewire_nulls" in rows["HCP structural graph"]["evidence"]
    assert rows["PET receptor priors"]["status"] == "implemented_pet_receptor_prior_sensitivity"
    assert "claim gate=not_supported_after_pet_spatial_nulls" in rows["PET receptor priors"]["evidence"]
    assert "Striatal gate=implemented_striatal_unimodal_proxy_benchmark" in rows["Mega-analysis comparison"]["evidence"]

    assert rows["Psilocybin ds006072"]["status"] == "implemented_ds006072_unchanged_scoring_validation"
    assert "ds006072 top=E, LSD reference top=C" in rows["Psilocybin ds006072"]["evidence"]


def test_ds006072_aggregates_embed_current_readiness_snapshot() -> None:
    readiness = _load_json("results/psilocybin_ds006072/external_validation_readiness.json")
    status = _load_json("results/psilocybin_ds006072/psilocybin_ds006072_status.json")
    loop = _load_json("results/thesis_evidence_loop/thesis_evidence_loop_status.json")

    assert status["external_validation_readiness"]["generated_at_utc"] == readiness["generated_at_utc"]
    assert (
        loop["components"]["psilocybin_ds006072"]["external_validation_readiness"]["generated_at_utc"]
        == readiness["generated_at_utc"]
    )


def test_ds006072_scoring_lock_tracks_dynamic_mechanism_core() -> None:
    from lsd_thesis.dynamic_mechanism import build_dynamic_mechanism_summary

    scoring_spec = _load_json("results/psilocybin_ds006072/unchanged_scoring_spec.json")
    scoring_files = scoring_spec["scoring_code_files"]
    paths = {row["path"].replace("\\", "/") for row in scoring_files.values()}

    assert callable(build_dynamic_mechanism_summary)
    assert any(path.endswith("dynamic_mechanism/core.py") for path in paths)
    assert scoring_files["dynamic_mechanism_core"]["entrypoint"] == (
        "lsd_thesis.dynamic_mechanism.build_dynamic_mechanism_summary"
    )


def test_structural_rewire_and_receptor_spatial_null_outputs_exist() -> None:
    structural = _load_json("results/structural_connectome/structural_connectome_status.json")
    receptor = _load_json("results/receptor_priors/receptor_prior_status.json")
    literature = _load_json("results/literature_benchmark/literature_benchmark_status.json")

    assert structural["graph_rewire_null_status"] == "implemented_hcp_structural_graph_rewire_nulls"
    assert any(row["graph_control"] == "edge_weight_rewire_null" for row in structural["graph_rewire_null_rows"])
    assert isinstance(structural["graph_rewire_null_path"], str)
    assert structural["graph_rewire_null_path"].endswith(".csv")
    assert "\\" not in structural["graph_rewire_null_path"]

    assert receptor["receptor_spatial_nulls_complete"] is True
    assert receptor["claim_promotion_status"] == "not_supported_after_pet_spatial_nulls"
    assert receptor["receptor_spatial_null_fdr_supported_count"] == 0

    assert literature["striatal_unimodal_gate"]["analysis_status"] == "implemented_striatal_unimodal_proxy_benchmark"
    striatal_rows = [row for row in literature["rows"] if "striatal" in row["benchmark"].lower()]
    assert striatal_rows
    assert striatal_rows[0]["project_metric"] == "striatal_sensory_coupling"
    assert striatal_rows[0]["status"] == "aligned"


def test_claim_matrix_contains_motion_receptor_and_striatal_gates() -> None:
    loop = _load_json("results/thesis_evidence_loop/thesis_evidence_loop_status.json")
    rows = {row["claim"]: row for row in loop["claim_evidence_matrix"]}

    assert rows["C final thesis claim passes motion-sensitive exclusions"]["status"] == (
        "blocked_motion_sensitive_c_claim_requires_authorized_confound_exclusions"
    )
    assert rows["E survives PET receptor-map priors"]["status"] == "not_supported_after_pet_spatial_nulls"
    assert rows["Nature Medicine striatal-unimodal benchmark is testable"]["status"] == (
        "implemented_striatal_unimodal_proxy_benchmark"
    )


def test_striatal_parcellation_exposes_dedicated_proxy_nodes_and_metric() -> None:
    parcellation_id = "schaefer_100_yeo_7_striatal"
    assert parcellation_id in available_parcellations()

    spec = get_parcellation_spec(parcellation_id)
    assert spec.node_count == 102
    assert spec.node_metadata[-2].node_label == "HarvardOxford_thalamus_bilateral"
    assert spec.node_metadata[-1].node_label == "HarvardOxford_striatum_bilateral"
    assert spec.node_metadata[-1].striatum_weight == 1.0

    masks = module_masks(tuple(node.node_label for node in spec.node_metadata[-2:]))
    assert masks["gateway"].tolist() == [True, False]
    assert masks["striatum"].tolist() == [False, True]

    summary = _load_json("results/parcellation_sensitivity/schaefer_100_yeo_7_striatal/summary.json")
    assert summary["pair_count"] == 30
    assert summary["mechanism_ranking"][0]["layer"] == "C"
    striatal_metrics = [
        row
        for row in summary["hierarchy_routing"]["metric_deltas"]
        if row["metric"] == "striatal_sensory_coupling"
    ]
    assert striatal_metrics
    assert striatal_metrics[0]["mean_delta"] > 0


def test_b_dmdc_remains_negative_sanity_baseline() -> None:
    summary = _load_json("results/dynamic_mechanism_ranking/summary.json")
    verdicts = {
        row["claim"]: row
        for row in summary["robustness"]["claim_verdicts"]
    }
    b_verdict = verdicts["Rejected candidate: B DMDc as the main control-theory result."]
    assert b_verdict["verdict"] == "unsupported"
    assert "Keep B as a negative/sanity baseline" in b_verdict["next_action"]
