from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "pptx" / "build_defense_deck.mjs"


def _run_deck_builder(
    spec_path: Path,
    output_path: Path,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(SCRIPT), str(spec_path), str(output_path)],
        cwd=cwd or spec_path.parent,
        capture_output=True,
        text=True,
        check=False,
    )


def test_node_deck_generator_rejects_slide_without_title(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(json.dumps([{"bullets": ["valid bullet"]}]), encoding="utf-8")

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode != 0
    assert "slides[0].title" in result.stderr
    assert not output_path.exists()


def test_node_deck_generator_rejects_missing_image_by_default(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps(
            [
                {
                    "title": "Validated Slide",
                    "bullets": ["valid bullet"],
                    "image_path": "missing-image.png",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode != 0
    assert "slides[0].image_path" in result.stderr
    assert "allow_missing_images" in result.stderr
    assert not output_path.exists()


def test_node_deck_generator_rejects_spec_path_outside_working_root(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    spec_path.write_text(json.dumps([{"title": "Valid Slide"}]), encoding="utf-8")
    output_root = tmp_path / "out"
    output_root.mkdir()

    result = _run_deck_builder(spec_path, output_root / "deck.pptx", cwd=output_root)

    assert result.returncode != 0
    assert "specPath must resolve inside" in result.stderr
    assert not (output_root / "deck.pptx").exists()


def test_node_deck_generator_rejects_image_path_outside_spec_root(tmp_path: Path) -> None:
    spec_root = tmp_path / "spec"
    spec_root.mkdir()
    outside_image = tmp_path / "outside.png"
    outside_image.write_bytes(b"not a real png")
    spec_path = spec_root / "slides.json"
    output_path = spec_root / "deck.pptx"
    spec_path.write_text(
        json.dumps(
            [
                {
                    "title": "Validated Slide",
                    "bullets": ["valid bullet"],
                    "image_path": str(outside_image),
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode != 0
    assert "image_path must resolve inside" in result.stderr
    assert not output_path.exists()


def test_node_deck_generator_rejects_invalid_slide_position(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps([{"title": "Validated Slide", "position": "first", "bullets": ["valid bullet"]}]),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode != 0
    assert "slides[0].position" in result.stderr
    assert not output_path.exists()


def test_node_deck_generator_warns_on_stale_validation_claim(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps([{"title": "Validation", "bullets": ["uv run pytest: 57 tests passed"]}]),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode == 0
    assert "Potential stale validation claim" in result.stderr
    assert output_path.exists()


def test_node_deck_generator_warns_on_unqualified_held_out_validation_claim(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps(
            [
                {
                    "title": "Validation",
                    "bullets": ["Subject-disjoint held-out validation has been completed."],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode == 0
    assert "Potential stale held-out validation claim" in result.stderr
    assert output_path.exists()


def test_node_deck_generator_warns_on_candidate_completed_holdout_claim(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps(
            [
                {
                    "title": "Validation",
                    "bullets": ["Candidate split held-out validation has been completed."],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode != 0
    assert "Invalid candidate split validation claim" in result.stderr
    assert not output_path.exists()


def test_node_deck_generator_accepts_qualified_internal_holdout_claim(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps(
            [
                {
                    "title": "Validation",
                    "bullets": [
                        (
                            "Approved internal subject-disjoint held-out validation has been completed; "
                            "this is not external validation."
                        )
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode == 0
    assert "Potential stale held-out validation claim" not in result.stderr
    assert "Invalid candidate split validation claim" not in result.stderr
    assert output_path.exists()


def test_node_deck_generator_warns_on_external_or_clinical_validation_claims(tmp_path: Path) -> None:
    spec_path = tmp_path / "slides.json"
    output_path = tmp_path / "deck.pptx"
    spec_path.write_text(
        json.dumps(
            [
                {
                    "title": "Validation",
                    "bullets": [
                        "This provides external validation for the model.",
                        "This provides clinical validation for the model.",
                        "This is a validated model.",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = _run_deck_builder(spec_path, output_path)

    assert result.returncode == 0
    assert "Potential unsupported external validation claim" in result.stderr
    assert "Potential unsupported clinical validation claim" in result.stderr
    assert "Potential overclaim" in result.stderr
    assert output_path.exists()
