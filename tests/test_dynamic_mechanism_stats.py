from __future__ import annotations

from types import SimpleNamespace

from lsd_thesis.dynamic_mechanism_stats import collect_paired_metric_rows


def test_collect_paired_metric_rows_builds_rows_and_deltas() -> None:
    pairs = [
        SimpleNamespace(subject="sub-001", run="run-01", placebo_value=1.0, lsd_value=3.0),
        SimpleNamespace(subject="sub-002", run="run-03", placebo_value=4.0, lsd_value=5.5),
    ]

    rows, metric_deltas = collect_paired_metric_rows(
        pairs,
        ["metric_a", "metric_b"],
        lambda pair: (
            {"metric_a": pair.placebo_value, "metric_b": pair.placebo_value * 2.0},
            {"metric_a": pair.lsd_value, "metric_b": pair.lsd_value * 2.0},
        ),
    )

    assert metric_deltas == {
        "metric_a": [2.0, 1.5],
        "metric_b": [4.0, 3.0],
    }
    assert rows[0] == {
        "subject": "sub-001",
        "run": "run-01",
        "placebo": {"metric_a": 1.0, "metric_b": 2.0},
        "lsd": {"metric_a": 3.0, "metric_b": 6.0},
        "delta": {"metric_a": 2.0, "metric_b": 4.0},
    }
