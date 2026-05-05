from pathlib import Path

from lsd_thesis.data.targets import load_perturbation_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.perturbation import (
    apply_mechanism,
    evaluate_perturbation_seed_panel,
    rank_perturbation_mechanisms,
    rank_perturbation_mechanisms_seed_panel,
    seed_noise_null_summary,
)
from lsd_thesis.simulator import load_regime_config

ROOT = Path(__file__).resolve().parents[1]


def test_apply_mechanism_changes_expected_parameter_direction() -> None:
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    cross_talk = apply_mechanism(baseline, "more_cross_talk", 0.2)
    barrier = apply_mechanism(baseline, "lower_switching_barrier", 0.2)

    assert (
        cross_talk.global_parameters.cross_group_scale
        > baseline.global_parameters.cross_group_scale
    )
    assert barrier.module_defaults.barrier < baseline.module_defaults.barrier


def test_rank_perturbation_mechanisms_returns_all_core_mechanisms() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_perturbation_target_set(
        ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    )

    ranking = rank_perturbation_mechanisms(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        strengths=(0.1,),
    )

    mechanisms = {item.mechanism for item in ranking}
    assert mechanisms == {
        "more_cross_talk",
        "less_hierarchical_constraint",
        "more_stochasticity",
        "lower_switching_barrier",
    }
    assert ranking[0].score >= 0.0


def test_seed_panel_ranking_reports_uncertainty_and_null_summary() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_perturbation_target_set(
        ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    )
    seeds = (3, 4)

    evaluation = evaluate_perturbation_seed_panel(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        mechanism="more_cross_talk",
        strength=0.1,
        seeds=seeds,
    )
    ranking = rank_perturbation_mechanisms_seed_panel(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        strengths=(0.1,),
        seeds=seeds,
    )
    null_summary = seed_noise_null_summary(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        seeds=seeds,
    )

    assert evaluation.seed_count == 2
    assert evaluation.score_mean >= 0.0
    assert evaluation.score_std >= 0.0
    assert 0.0 <= evaluation.sign_agreement_fraction <= 1.0
    assert len(ranking) == 4
    assert null_summary["seed_count"] == 2
    assert null_summary["score_mean"] >= 0.0
