from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.web.structural_dti import load_structural_dti_payload


def test_structural_dti_payload_reports_missing_matrix(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    payload = load_structural_dti_payload(repo_root)

    assert payload["analysis_status"] == "missing_structural_connectome_matrix"
    assert payload["modules"] == []
    assert payload["matrix"] == []
    assert payload["edges"] == []
    assert "anatomical coupling context" in payload["claim_guardrail"]


def test_structural_dti_payload_builds_symmetric_graph_from_matrix(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    status_dir = repo_root / "results" / "structural_connectome"
    status_dir.mkdir(parents=True)
    (status_dir / "structural_connectome_status.json").write_text(
        json.dumps({"analysis_status": "implemented_structural_proxy"}),
        encoding="utf-8",
    )
    (status_dir / "hcp_macro_modules.csv").write_text(
        "\n".join(
            [
                "module,visual,default,control",
                "visual,0,2,4",
                "default,6,0,8",
                "control,10,bad,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload = load_structural_dti_payload(repo_root)

    assert payload["analysis_status"] == "implemented_structural_proxy"
    assert payload["modules"] == ["visual", "default", "control"]
    assert payload["matrix"] == [
        [0.0, 4.0, 7.0],
        [4.0, 0.0, 4.0],
        [7.0, 4.0, 0.0],
    ]
    assert payload["edge_count"] == 3
    assert payload["strongest_edge"]["source"] == "visual"
    assert payload["strongest_edge"]["target"] == "control"
    assert payload["strongest_edge"]["normalized_weight"] == 1.0
    assert payload["nodes"][0]["name"] == "visual"
    assert payload["nodes"][0]["normalized_strength"] == 1.0
    assert "dynamics prior" in payload["claim_guardrail"]
