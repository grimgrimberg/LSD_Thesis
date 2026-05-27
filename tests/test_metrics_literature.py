import csv
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest

from lsd_thesis.data.parcellations import NodeMetadata
from lsd_thesis.metrics_literature import (
    compute_literature_metrics,
    hierarchy_differentiation,
    safe_corrcoef,
    transition_entropy,
)
from lsd_thesis.target_validation import bootstrap_ci, generate_stage_2b_from_stage2, generate_stage_2b_outputs


def _test_root() -> Path:
    root = Path("codex_logs") / "metrics_literature_tests" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def _metadata() -> tuple[NodeMetadata, ...]:
    return (
        NodeMetadata("visual", 1, "Visual", "visual", 0.05, visual_weight=1.0, sensory_weight=1.0),
        NodeMetadata("somatomotor", 2, "SomMot", "somatomotor", 0.10, sensory_weight=1.0, somatomotor_weight=1.0),
        NodeMetadata("default", 3, "Default", "default", 0.95, transmodal_weight=1.0),
        NodeMetadata("control", 4, "Cont", "control", 0.80, transmodal_weight=1.0),
        NodeMetadata("thalamus", 5, None, "subcortical", 0.35, thalamus_weight=1.0),
        NodeMetadata("striatum", 6, None, "subcortical", 0.40, striatum_weight=1.0),
    )


def test_safe_corrcoef_handles_nans_and_constant_signals() -> None:
    time_series = np.asarray(
        [
            [1.0, np.nan, 2.0],
            [1.0, 0.0, 3.0],
            [1.0, 0.0, 4.0],
        ]
    )

    fc = safe_corrcoef(time_series)

    assert fc.shape == (3, 3)
    assert np.all(np.isfinite(fc))
    assert np.allclose(np.diag(fc), 1.0)


def test_literature_metrics_detect_unimodal_transmodal_and_visual_connectivity() -> None:
    t = np.linspace(0.0, 6.0, 160)
    visual = np.sin(t)
    somatomotor = visual + 0.02 * np.cos(t)
    default = visual + 0.01 * np.sin(2 * t)
    control = default + 0.02 * np.cos(2 * t)
    thalamus = visual + 0.03 * np.sin(3 * t)
    striatum = visual + 0.03 * np.cos(3 * t)
    time_series = np.column_stack([visual, somatomotor, default, control, thalamus, striatum])

    metrics = compute_literature_metrics(time_series, _metadata())

    assert metrics["unimodal_transmodal_fc"] > 0.95
    assert metrics["visual_global_connectivity"] > 0.95
    assert metrics["thalamus_to_sensory_fc"] > 0.95
    assert metrics["striatum_to_sensory_fc"] > 0.95


def test_hierarchy_differentiation_decreases_when_fc_is_flattened() -> None:
    metadata = _metadata()
    separated = np.eye(6)
    separated[0, 1] = separated[1, 0] = 0.9
    separated[2, 3] = separated[3, 2] = 0.9
    separated[0:2, 2:4] = 0.1
    separated[2:4, 0:2] = 0.1
    flattened = np.full((6, 6), 0.5)
    np.fill_diagonal(flattened, 1.0)

    assert hierarchy_differentiation(separated, metadata) > hierarchy_differentiation(flattened, metadata)


def test_transition_entropy_increases_with_diverse_transitions() -> None:
    simple = np.asarray([0, 1, 0, 1, 0, 1])
    diverse = np.asarray([0, 1, 2, 0, 2, 1, 0, 1])

    assert transition_entropy(diverse) > transition_entropy(simple)


def test_bootstrap_ci_is_deterministic_under_fixed_seed() -> None:
    values = [1.0, 2.0, 3.0, 4.0]

    assert bootstrap_ci(values, seed=123, n_bootstrap=64) == bootstrap_ci(values, seed=123, n_bootstrap=64)


def test_stage_2b_outputs_from_tiny_synthetic_records() -> None:
    records = [
        {"subject": "sub-001", "session": "ses-PLCB", "run": "run-01", "metrics": {"unimodal_transmodal_fc": 0.2}},
        {"subject": "sub-001", "session": "ses-LSD", "run": "run-01", "metrics": {"unimodal_transmodal_fc": 0.5}},
        {"subject": "sub-002", "session": "ses-PLCB", "run": "run-03", "metrics": {"unimodal_transmodal_fc": 0.3}},
        {"subject": "sub-002", "session": "ses-LSD", "run": "run-03", "metrics": {"unimodal_transmodal_fc": 0.6}},
    ]
    output_dir = _test_root() / "stage_2b"
    report_path = output_dir / "stage_2b.md"

    summary = generate_stage_2b_outputs(records, output_dir=output_dir, report_path=report_path, seed=1, n_bootstrap=64)

    assert summary["paired_subject_count"] == 2
    assert summary["metric_count"] == 1
    assert (output_dir / "target_reliability_summary.json").exists()
    assert (output_dir / "literature_metric_deltas.csv").exists()
    assert report_path.exists()
    with (output_dir / "literature_metric_deltas.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["metric"] == "unimodal_transmodal_fc"
    assert float(rows[0]["delta_mean"]) == 0.3
    assert json.loads((output_dir / "target_reliability_summary.json").read_text(encoding="utf-8"))["metric_count"] == 1


def test_stage_2b_from_stage2_rejects_time_series_paths_outside_stage_dir(tmp_path: Path) -> None:
    stage_2_dir = tmp_path / "stage_2"
    stage_2_dir.mkdir()
    outside_path = tmp_path / "outside.npy"
    np.save(outside_path, np.zeros((80, 8), dtype=float))
    (stage_2_dir / "empirical_run_summaries.json").write_text(
        json.dumps(
            [
                {
                    "subject": "sub-001",
                    "session": "ses-LSD",
                    "run": "run-01",
                    "time_series_path": "../outside.npy",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside the allowed root"):
        generate_stage_2b_from_stage2(
            stage_2_dir=stage_2_dir,
            output_dir=tmp_path / "stage_2b",
            report_path=tmp_path / "stage_2b.md",
        )
