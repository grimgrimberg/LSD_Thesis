from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from lsd_thesis.dynamic_mechanism_hierarchy import summarize_hierarchy_routing


def test_summarize_hierarchy_routing_is_public_and_schema_stable() -> None:
    t = np.linspace(0.0, 5.0, 64)
    modules = ("visual", "default_mode", "thalamic_gateway", "sensorimotor")
    pairs = [
        SimpleNamespace(
            subject="sub-001",
            run="run-01",
            modules=modules,
            placebo=np.column_stack([np.sin(t), np.cos(t), np.sin(t * 0.4), np.cos(t * 0.3)]),
            lsd=np.column_stack([np.sin(t * 1.1), np.cos(t * 0.8), np.sin(t * 0.6), np.cos(t * 0.4)]),
        ),
        SimpleNamespace(
            subject="sub-002",
            run="run-01",
            modules=modules,
            placebo=np.column_stack([np.sin(t + 0.2), np.cos(t + 0.1), np.sin(t * 0.5), np.cos(t * 0.2)]),
            lsd=np.column_stack(
                [np.sin(t * 1.2 + 0.2), np.cos(t * 0.7 + 0.1), np.sin(t * 0.7), np.cos(t * 0.35)]
            ),
        ),
    ]

    summary = summarize_hierarchy_routing(pairs)

    assert summary["status"] == "implemented_first_pass"
    assert summary["pair_count"] == 2
    assert len(summary["pair_rows"]) == 2
    assert len(summary["metric_deltas"]) == 12
    assert np.isfinite(summary["support_score"])
    assert "coarse FC proxies" in summary["claim_guardrail"]
