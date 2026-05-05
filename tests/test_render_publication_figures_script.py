from __future__ import annotations

import importlib.util
from pathlib import Path

from lsd_thesis.publication_figures import PublicationFigure


def _load_render_publication_figures_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "render_publication_figures.py"
    spec = importlib.util.spec_from_file_location("render_publication_figures", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_publication_figures_uses_default_results_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_render_publication_figures_module()
    evidence = object()
    captured: dict[str, object] = {}

    def fake_build_publication_evidence(repo_root: Path) -> object:
        captured["repo_root"] = repo_root
        return evidence

    def fake_generate_publication_figures(
        evidence_arg: object,
        output_dir: Path,
    ) -> dict[str, PublicationFigure]:
        captured["evidence"] = evidence_arg
        captured["output_dir"] = output_dir
        output_dir.mkdir(parents=True)
        figure_path = output_dir / "stage1_metric_shift.png"
        figure_path.write_text("figure", encoding="utf-8")
        return {
            "stage1_metric_shift": PublicationFigure(
                figure_id="stage1_metric_shift",
                path=figure_path,
                caption="Stage 1 compares baseline and perturbed proxy values.",
                limitations="Surrogate macro-dynamics only.",
            )
        }

    monkeypatch.setattr(module, "build_publication_evidence", fake_build_publication_evidence)
    monkeypatch.setattr(module, "generate_publication_figures", fake_generate_publication_figures)

    outputs = module.render_publication_figures(tmp_path)

    assert captured["repo_root"] == tmp_path
    assert captured["evidence"] is evidence
    assert captured["output_dir"] == tmp_path / "results" / "publication_figures"
    assert outputs == {"stage1_metric_shift": tmp_path / "results" / "publication_figures" / "stage1_metric_shift.png"}


def test_render_publication_figures_cli_accepts_all_and_output_dir(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = _load_render_publication_figures_module()
    output_dir = tmp_path / "custom_figures"
    figure_path = output_dir / "stage2_fit_robustness.png"

    def fake_render_publication_figures(
        repo_root: Path,
        *,
        output_dir: Path | None = None,
    ) -> dict[str, Path]:
        assert repo_root == module.REPO_ROOT
        assert output_dir == tmp_path / "custom_figures"
        output_dir.mkdir(parents=True)
        figure_path.write_text("figure", encoding="utf-8")
        return {"stage2_fit_robustness": figure_path}

    monkeypatch.setattr(module, "render_publication_figures", fake_render_publication_figures)

    module.main(["--all", "--output-dir", str(output_dir)])

    assert "stage2_fit_robustness:" in capsys.readouterr().out
    assert figure_path.exists()
