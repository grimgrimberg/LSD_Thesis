import json
from pathlib import Path

import numpy as np

from lsd_thesis.dynamic_mechanism import build_dynamic_mechanism_summary, write_dynamic_mechanism_summary
from lsd_thesis.dynamic_mechanism_stats import benjamini_hochberg, bootstrap_ci


def _viewer_fixture(root: Path) -> Path:
    viewer_root = root / "empirical_viewer"
    subject_views = viewer_root / "subject_views"
    subject_views.mkdir(parents=True)
    (viewer_root / "group_overview.json").write_text(
        json.dumps({"module_names": ["visual", "default_mode", "thalamic_gateway"]}),
        encoding="utf-8",
    )
    t = np.linspace(0.0, 8.0, 80)
    for offset, subject in enumerate(["sub-001", "sub-002"]):
        placebo = np.column_stack(
            [
                np.sin(t + offset * 0.1),
                np.cos(t * 0.5 + offset * 0.2),
                np.sin(t * 0.25),
            ]
        )
        lsd = np.column_stack(
            [
                np.sin(t * 1.2 + offset * 0.1),
                np.cos(t * 0.7 + offset * 0.2),
                np.sin(t * 0.35) + 0.05,
            ]
        )
        detail = {
            "subject": subject,
            "run": "run-01",
            "conditions": {
                "ses-PLCB": {"module_time_series": placebo.tolist()},
                "ses-LSD": {"module_time_series": lsd.tolist()},
            },
        }
        (subject_views / f"{subject}_run-01.json").write_text(json.dumps(detail), encoding="utf-8")
    return viewer_root


def test_dynamic_mechanism_summary_builds_transition_and_dmdc_results(tmp_path: Path) -> None:
    viewer_root = _viewer_fixture(tmp_path)

    summary = build_dynamic_mechanism_summary(viewer_root)

    assert summary["analysis_status"] == "implemented_first_pass"
    assert summary["pair_count"] == 2
    assert summary["subject_count"] == 2
    assert summary["modules"] == ["visual", "default_mode", "thalamic_gateway"]
    assert len(summary["transition_proxy"]["metric_deltas"]) == 6
    assert summary["dmdc"]["fold_count"] == 2
    assert len(summary["dmdc"]["condition_input_vector"]) == 3
    assert len(summary["dmdc"]["condition_interaction_vector"]) == 3
    assert summary["hierarchy_routing"]["status"] == "implemented_first_pass"
    assert summary["dynamic_repertoire"]["status"] == "implemented_first_pass"
    assert summary["network_control_energy"]["status"] == "implemented_proxy_control_energy"
    assert summary["network_control_energy"]["graph_is_structural_connectome"] is False
    assert len(summary["network_control_energy"]["metric_deltas"]) == 7
    assert len(summary["network_control_energy"]["energy_rows"]) > 0
    assert summary["inference_metadata"]["metric_bootstrap_iterations"] == 1024
    assert len(summary["mechanism_ranking"]) == 5
    assert str(summary["mechanism_ranking"][0]["status"]).startswith("implemented")
    assert np.isfinite(summary["dmdc"]["condition_interaction_relative_improvement_pct_mean"])
    assert np.isfinite(summary["dmdc"]["relative_improvement_pct_mean"])

    for row in summary["transition_proxy"]["metric_deltas"]:
        assert row["n_pairs"] == 2
        assert float(row["ci_low"]) <= float(row["ci_high"])
        assert "sign_flip_q_value" in row
        assert "significant_after_fdr_0_05" in row

    for row in summary["network_control_energy"]["metric_deltas"]:
        assert row["n_pairs"] == 2
        assert float(row["ci_low"]) <= float(row["ci_high"])
        assert "sign_flip_q_value" in row
        assert "significant_after_fdr_0_05" in row


def test_dynamic_mechanism_summary_writer_persists_json(tmp_path: Path) -> None:
    viewer_root = _viewer_fixture(tmp_path)
    output_dir = tmp_path / "dynamic_mechanism_ranking"

    summary = write_dynamic_mechanism_summary(viewer_root, output_dir)

    summary_path = output_dir / "summary.json"
    assert summary_path.exists()
    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["pair_count"] == summary["pair_count"]
    assert loaded["source_path"].endswith("summary.json")


def test_benjamini_hochberg_monotone_and_bounded() -> None:
    q_values = benjamini_hochberg([0.01, 0.04, 0.03, 0.20, 0.50])

    assert len(q_values) == 5
    assert all(0.0 <= value <= 1.0 for value in q_values)
    sorted_pairs = sorted(zip([0.01, 0.04, 0.03, 0.20, 0.50], q_values, strict=True))
    assert [value for _, value in sorted_pairs] == sorted(value for _, value in sorted_pairs)


def test_bootstrap_ci_is_deterministic() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    first = bootstrap_ci(values, seed=20260520, n_bootstrap=128, alpha=0.05)
    second = bootstrap_ci(values, seed=20260520, n_bootstrap=128, alpha=0.05)

    assert first == second
    assert first["ci_low"] <= first["mean"] <= first["ci_high"]
