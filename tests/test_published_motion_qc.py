from pathlib import Path

from lsd_thesis.published_motion_qc import build_published_motion_qc_status, write_published_motion_qc_status


def test_published_motion_qc_fails_closed_without_readme(tmp_path: Path) -> None:
    status = build_published_motion_qc_status(tmp_path)

    assert status["analysis_status"] == "blocked_missing_published_motion_qc_source"
    assert status["published_motion_qc_ready"] is False
    assert status["claim_status"] == "not_proven_motion_qc_context_missing"


def test_published_motion_qc_extracts_guardrailed_context(tmp_path: Path) -> None:
    readme = tmp_path / "data" / "ds003059" / "README"
    readme.parent.mkdir(parents=True)
    readme.write_text(
        "\n".join(
            [
                "four others were discarded from the group analyses due to excessive head movement",
                "subjects with >15%  scrubbed volumes when the scrubbing threshold is FD = 0.5",
                "for the 15 subjects that were used in the analysis the difference in mean FD was 0.046",
                "mean FD of placebo = 0.074",
                "mean percentage of volumes scrubbed for placebo and LSD was 0.4",
                "distance to FD-RSFC correlation was very close to zero",
            ]
        ),
        encoding="utf-8",
    )

    status = build_published_motion_qc_status(tmp_path)

    assert status["analysis_status"] == "implemented_published_ds003059_motion_qc_context"
    assert status["published_motion_qc_ready"] is True
    assert status["high_risk_motion_context"]["strict_subject_level_fd_gate_complete"] is False
    assert any(row["measure"] == "retained_between_condition_mean_fd_difference" for row in status["published_qc_rows"])


def test_write_published_motion_qc_status_writes_json_and_markdown(tmp_path: Path) -> None:
    status = write_published_motion_qc_status(tmp_path)

    assert status["status_path"] == "results/confound_controls/published_motion_qc_status.json"
    assert (tmp_path / status["status_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()
