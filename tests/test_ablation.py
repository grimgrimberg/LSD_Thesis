from pathlib import Path

from lsd_thesis.ablation import run_ablation_study
from lsd_thesis.data.targets import load_perturbation_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config

ROOT = Path(__file__).resolve().parents[1]


def test_ablation_study_produces_single_and_pairwise_results() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_perturbation_target_set(
        ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    )

    study = run_ablation_study(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        strengths={
            "more_cross_talk": 0.25,
            "less_hierarchical_constraint": 0.25,
            "more_stochasticity": 0.25,
            "lower_switching_barrier": 0.25,
        },
    )

    assert len(study.single_mechanisms) == 4
    assert len(study.pairwise_mechanisms) == 6
    assert study.single_mechanisms[0].score >= 0.0
