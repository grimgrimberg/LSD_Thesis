from pathlib import Path

from lsd_thesis.reporting import generate_stage_1_outputs

ROOT = Path(__file__).resolve().parents[1]


def test_stage_1_output_generation_creates_expected_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "stage_1"
    report_path = tmp_path / "stage_1.md"

    summary = generate_stage_1_outputs(
        graph_path=ROOT / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=ROOT / "configs" / "regimes" / "baseline.yaml",
        perturbed_path=ROOT / "configs" / "regimes" / "perturbed.yaml",
        output_dir=output_dir,
        report_path=report_path,
    )

    assert (output_dir / "figures" / "graph_overview.html").exists()
    assert (output_dir / "figures" / "baseline_node_activity.html").exists()
    assert (output_dir / "figures" / "perturbed_fc_matrix.html").exists()
    assert (output_dir / "figures" / "diversity_comparison.html").exists()
    assert (output_dir / "figures" / "switching_rate_comparison.html").exists()
    assert (output_dir / "stage_1_summary.json").exists()
    assert report_path.exists()
    assert "baseline" in summary
    assert "perturbed" in summary
