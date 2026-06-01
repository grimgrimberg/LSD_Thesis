from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from lsd_thesis.dynamic_mechanism_transitions import summarize_transition_proxy


def test_summarize_transition_proxy_is_public_and_schema_stable() -> None:
    t = np.linspace(0.0, 4.0, 48)
    pairs = [
        SimpleNamespace(
            subject="sub-001",
            run="run-01",
            modules=("visual", "default_mode", "thalamic_gateway"),
            placebo=np.column_stack([np.sin(t), np.cos(t), np.sin(t * 0.5)]),
            lsd=np.column_stack([np.sin(t * 1.2), np.cos(t * 0.7), np.sin(t * 0.6) + 0.1]),
        ),
        SimpleNamespace(
            subject="sub-002",
            run="run-01",
            modules=("visual", "default_mode", "thalamic_gateway"),
            placebo=np.column_stack([np.sin(t + 0.2), np.cos(t + 0.1), np.sin(t * 0.4)]),
            lsd=np.column_stack([np.sin(t * 1.1 + 0.2), np.cos(t * 0.8 + 0.1), np.sin(t * 0.7)]),
        ),
    ]

    summary = summarize_transition_proxy(pairs)

    assert summary["pair_count"] == 2
    assert len(summary["pair_rows"]) == 2
    assert len(summary["metric_deltas"]) == 6
    assert np.isfinite(summary["support_score"])
    assert "macro-state proxy summaries" in summary["claim_guardrail"]
