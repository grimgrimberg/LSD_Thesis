from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from lsd_thesis.dynamic_mechanism_repertoire import summarize_dynamic_repertoire


def test_summarize_dynamic_repertoire_is_public_and_schema_stable() -> None:
    t = np.linspace(0.0, 6.0, 72)
    modules = ("visual", "default_mode", "thalamic_gateway", "sensorimotor")
    pairs = [
        SimpleNamespace(
            subject="sub-001",
            run="run-01",
            modules=modules,
            placebo=np.column_stack([np.sin(t), np.cos(t * 0.5), np.sin(t * 0.3), np.cos(t * 0.2)]),
            lsd=np.column_stack([np.sin(t * 1.1), np.cos(t * 0.7), np.sin(t * 0.5), np.cos(t * 0.3)]),
        ),
        SimpleNamespace(
            subject="sub-002",
            run="run-02",
            modules=modules,
            placebo=np.column_stack(
                [np.sin(t + 0.2), np.cos(t * 0.4 + 0.1), np.sin(t * 0.25), np.cos(t * 0.25)]
            ),
            lsd=np.column_stack(
                [np.sin(t * 1.2 + 0.2), np.cos(t * 0.8 + 0.1), np.sin(t * 0.55), np.cos(t * 0.35)]
            ),
        ),
    ]

    summary = summarize_dynamic_repertoire(pairs, window_size=12)

    assert summary["status"] == "implemented_first_pass"
    assert summary["window_size"] == 12
    assert summary["pair_count"] == 2
    assert len(summary["pair_rows"]) == 2
    assert len(summary["metric_deltas"]) == 11
    assert len(summary["run_metric_deltas"]) == 22
    assert np.isfinite(summary["support_score"])
    assert "descriptive FC/time-series proxies" in summary["claim_guardrail"]
