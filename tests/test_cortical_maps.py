from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.cortical_maps import write_cortical_map_alignment_status
from lsd_thesis.core import MODULE_NAMES


def test_cortical_map_alignment_writes_q_value_and_guardrails(tmp_path: Path) -> None:
    dynamic_dir = tmp_path / "results" / "dynamic_mechanism_ranking"
    dynamic_dir.mkdir(parents=True)
    interaction = [{"module": module, "coefficient": index / 10.0} for index, module in enumerate(MODULE_NAMES)]
    condition_input = [{"module": module, "coefficient": (len(MODULE_NAMES) - index) / 10.0} for index, module in enumerate(MODULE_NAMES)]
    (dynamic_dir / "summary.json").write_text(
        json.dumps(
            {
                "modules": list(MODULE_NAMES),
                "dmdc": {
                    "condition_interaction_vector": interaction,
                    "condition_input_vector": condition_input,
                },
            }
        ),
        encoding="utf-8",
    )

    receptor_dir = tmp_path / "results" / "receptor_priors"
    receptor_dir.mkdir(parents=True)
    receptor_rows = ["module,receptor_weight,raw_receptor_weight,source"]
    receptor_rows.extend(f"{module},{index / 10.0},{index / 10.0},fixture" for index, module in enumerate(MODULE_NAMES))
    (receptor_dir / "fs5ht_5ht2a_macro_modules.csv").write_text("\n".join(receptor_rows) + "\n", encoding="utf-8")

    payload = write_cortical_map_alignment_status(tmp_path)

    assert payload["analysis_status"] == "implemented_module_level_external_map_alignment"
    assert payload["neuromaps_status"]["analysis_status"] == "not_run_module_level_only"
    assert payload["claim_readiness"]["strong_receptor_myelin_gradient_claim"] == "not_supported_yet"
    assert payload["parcellation_upgrade"]["recommended_next_contract"].startswith("Schaefer")
    assert payload["recent_psilocybin_benchmark"]["published"] == "2026-05-05"
    assert payload["recent_psilocybin_benchmark"]["doi"] == "10.1038/s41467-026-71962-3"
    assert payload["future_external_dataset_context"]["status"] == "candidate_future_authorized_external_dataset_not_ingested"
    assert any(row["q_value"] is not None for row in payload["alignment_rows"])
    assert "not receptor pharmacology" in payload["claim_guardrail"]
    assert (tmp_path / "results" / "cortical_maps" / "cortical_map_alignment_status.json").exists()
    assert (tmp_path / "results" / "cortical_maps" / "cortical_map_alignment.md").exists()
