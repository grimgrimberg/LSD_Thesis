import json
from pathlib import Path

import numpy as np

from lsd_thesis.dynamic_mechanism import build_dynamic_mechanism_summary
from lsd_thesis.dynamic_robustness import build_dynamic_robustness_summary


def _viewer_fixture(root: Path) -> Path:
    viewer_root = root / "empirical_viewer"
    subject_views = viewer_root / "subject_views"
    subject_views.mkdir(parents=True)
    (viewer_root / "group_overview.json").write_text(
        json.dumps({"module_names": ["visual", "default_mode", "thalamic_gateway"]}),
        encoding="utf-8",
    )
    t = np.linspace(0.0, 8.0, 80)
    for offset, subject in enumerate(["sub-001", "sub-002", "sub-003"]):
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


def test_dynamic_robustness_summary_builds_stress_tests(tmp_path: Path) -> None:
    viewer_root = _viewer_fixture(tmp_path)
    summary = build_dynamic_mechanism_summary(viewer_root)

    robustness = build_dynamic_robustness_summary(summary, viewer_root)

    assert robustness["analysis_status"] == "implemented_first_pass_robustness"
    assert robustness["subject_count"] == 3
    assert robustness["subject_bootstrap"]["status"] == "implemented_subject_bootstrap"
    assert len(robustness["subject_bootstrap"]["layer_summary"]) == 5
    assert len(robustness["run_sensitivity"]["run_rows"]) == 4
    assert len(robustness["e_horizon_sensitivity"]["rows"]) == 4
    assert len(robustness["state_label_sensitivity"]["rows"]) == 8
    assert len(robustness["d_window_sensitivity"]["rows"]) == 4
    assert robustness["literature_benchmark"]["measurable_count"] >= 1
    assert len(robustness["claim_verdicts"]) >= 5
