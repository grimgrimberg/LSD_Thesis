from __future__ import annotations

import json
import runpy

from lsd_thesis.web.prior_art_payload import REPO_ROOT, build_prior_art_payload


def test_prior_art_comparison_plan_is_covered_by_dry_run_families() -> None:
    plan_path = REPO_ROOT / "prior_art" / "comparison_extraction_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_families = {row["family"] for row in plan["families"]}

    dry_run_globals = runpy.run_path(str(REPO_ROOT / "prior_art" / "scripts" / "dry_run_analysis_inputs.py"))
    dry_run_families = set(dry_run_globals["FAMILIES"])

    assert plan_families == dry_run_families


def test_prior_art_payload_exposes_test_compare_extract_section() -> None:
    payload = build_prior_art_payload(REPO_ROOT)

    assert payload["summary"]["comparison_family_count"] == 13
    assert payload["comparison_plan"]
    assert payload["input_status"]

    entropy = next(row for row in payload["comparison_plan"] if row["family"] == "entropy_copbet")
    assert entropy["dry_run_command"] == "uv run python prior_art/scripts/dry_run_analysis_inputs.py entropy_copbet"
    assert "derivatives_root" in entropy["required_inputs"]
    assert "entropy" in entropy["comparison_target"].lower()
    assert entropy["extract_targets"]
    assert entropy["output_target"] == "results/prior_art/entropy_copbet/"

    assert any(document["label"] == "Comparison/extraction plan" for document in payload["documents"])
