import numpy as np

from lsd_thesis.setting_seed.control_input import (
    MUSIC_EXCLUDED_SUBJECTS,
    build_music_control_scaffold,
    context_memory_trace,
    difference_in_differences,
)


def test_missing_run_02_produces_blocked_scaffold_status() -> None:
    scaffold = build_music_control_scaffold(run_02_available=False)

    assert scaffold["status"] == "blocked_missing_run_02"
    assert scaffold["music_excluded_subjects"] == list(MUSIC_EXCLUDED_SUBJECTS)
    assert scaffold["unavailable_effects"] == [
        "setting_effect",
        "music_to_rest3_displacement",
        "drug_setting_interaction",
    ]
    assert "No music-control empirical claim is made" in scaffold["claim_guardrail"]


def test_difference_in_differences_sign_matches_synthetic_effect() -> None:
    effect = difference_in_differences(plcb_rest1=1.0, plcb_rest3=1.2, lsd_rest1=1.0, lsd_rest3=1.7)

    assert effect == 0.5


def test_context_memory_trace_decays_after_music() -> None:
    runs = ["run-01", "run-02", "run-03"]
    trace = context_memory_trace(runs, points_per_run=3, tau=2.0)

    assert trace["u_music"].tolist() == [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    assert np.max(trace["context_memory"]) > 0.0
    assert trace["context_memory"][-1] < trace["context_memory"][5]
