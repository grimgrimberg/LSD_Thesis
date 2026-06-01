from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.web.thesis_payload import (
    build_thesis_expansion_payload,
    load_claim_status_payload,
    load_thesis_loop_status,
)


def test_claim_status_payload_keeps_pi_pitch_claim_boundaries(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "CLAIM_LADDER.md").write_text("# claims\n", encoding="utf-8")
    (repo_root / "PI_PITCH.md").write_text("# pitch\n", encoding="utf-8")

    payload = load_claim_status_payload(repo_root)

    assert payload["analysis_status"] == "pi_pitch_claim_ladder_ready"
    assert payload["audience"] == "prospective Master's PI"
    assert "altered transition/control dynamics" in payload["falsifiable_thesis_claim"]
    assert any(row["source"] == "ds003059 LSD-placebo" for row in payload["external_validation_status"])
    assert "without pretending to be a completed neuroscience" in payload["claim_guardrail"]


def test_claim_status_payload_fails_closed_when_pitch_docs_are_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    payload = load_claim_status_payload(repo_root)

    assert payload["analysis_status"] == "missing_pitch_or_claim_ladder"
    assert payload["source_path"] == "CLAIM_LADDER.md"
    assert payload["pi_pitch_path"] == "PI_PITCH.md"
    assert payload["claim_tiers"][0]["tier"] == "A"
    assert "without pretending to be a completed neuroscience" in payload["claim_guardrail"]


def test_thesis_loop_status_fails_closed_when_status_artifact_is_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    payload = load_thesis_loop_status(repo_root)

    assert payload == {
        "analysis_status": "missing",
        "source_path": "results/thesis_evidence_loop/thesis_evidence_loop_status.json",
        "status_rows": [],
        "claim_guardrail": "Run scripts/run_thesis_evidence_loop.py to populate the full evidence-loop status matrix.",
    }


def test_thesis_expansion_payload_uses_loop_status_when_available(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    loop_dir = repo_root / "results" / "thesis_evidence_loop"
    loop_dir.mkdir(parents=True)
    (loop_dir / "thesis_evidence_loop_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_loop_contract",
                "claim_guardrail": "Loop guardrail",
                "status_rows": [
                    {
                        "label": "LSD robustness",
                        "status": "implemented",
                        "evidence": "results/dynamic_mechanism_ranking/robustness",
                        "blocker": "none",
                    }
                ],
                "external_source_plan": [
                    {
                        "source_id": "fixture_source",
                        "source": "Fixture source",
                        "key_evidence": "Fixture evidence",
                        "use_in_project": "Fixture use",
                        "status": "implemented fixture",
                        "url": "https://example.test/source",
                        "current_component_status": "ready",
                    }
                ],
                "components": {
                    "fixture": {"analysis_status": "ready"},
                },
            }
        ),
        encoding="utf-8",
    )

    loop_status = load_thesis_loop_status(repo_root)
    payload = build_thesis_expansion_payload(repo_root)

    assert loop_status["source_path"] == "results/thesis_evidence_loop/thesis_evidence_loop_status.json"
    assert payload["loop_status"]["analysis_status"] == "implemented_loop_contract"
    assert payload["loop_steps"][0]["status"] == "implemented"
    assert payload["loop_steps"][0]["implementation_evidence"] == "results/dynamic_mechanism_ranking/robustness"
    assert payload["external_source_plan"][0]["source_id"] == "fixture_source"
    assert payload["scholarly_anchors"][0]["current_component_status"] == "ready"
    assert payload["claim_guardrail"] == "Loop guardrail"
