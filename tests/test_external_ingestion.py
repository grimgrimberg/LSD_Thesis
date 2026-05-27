from __future__ import annotations

import csv
from pathlib import Path

from lsd_thesis.data.ds003059 import MODULE_NAMES
from lsd_thesis.external_ingestion import (
    build_external_ingestion_status,
    ingest_receptor_prior,
    ingest_structural_connectome,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_ingest_structural_connectome_writes_macro_module_matrix(tmp_path: Path) -> None:
    source = tmp_path / "source_structural.csv"
    rows = []
    for source_module in MODULE_NAMES:
        row = {"module": source_module}
        for target_module in MODULE_NAMES:
            row[target_module] = 0.0 if source_module == target_module else 1.0
        rows.append(row)
    _write_csv(source, ["module", *MODULE_NAMES], rows)

    manifest = ingest_structural_connectome(source, repo_root=tmp_path)

    assert manifest["output_path"] == "data/hcp_structural_connectome/macro_modules.csv"
    assert (tmp_path / manifest["output_path"]).exists()
    assert (tmp_path / "data" / "hcp_structural_connectome" / "structural_connectome_ingestion_manifest.json").exists()


def test_ingest_receptor_prior_normalizes_weights_for_existing_contract(tmp_path: Path) -> None:
    source = tmp_path / "source_receptor.csv"
    rows = [
        {"module": module, "receptor_weight": index + 1, "source": "fixture"}
        for index, module in enumerate(MODULE_NAMES)
    ]
    _write_csv(source, ["module", "receptor_weight", "source"], rows)

    manifest = ingest_receptor_prior(source, repo_root=tmp_path)

    output = tmp_path / manifest["output_path"]
    written = list(csv.DictReader(output.open("r", encoding="utf-8", newline="")))
    values = [float(row["receptor_weight"]) for row in written]
    assert min(values) == 0.0
    assert max(values) == 1.0
    assert (tmp_path / "data" / "receptor_priors" / "receptor_prior_ingestion_manifest.json").exists()


def test_external_ingestion_status_reports_ready_layers(tmp_path: Path) -> None:
    (tmp_path / "data" / "ds006072").mkdir(parents=True)
    (tmp_path / "data" / "ds006072" / "ds006072_metadata_manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "results" / "receptor_priors").mkdir(parents=True)
    (tmp_path / "results" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv").write_text(
        "module,receptor_weight\n", encoding="utf-8"
    )

    status = build_external_ingestion_status(tmp_path)

    assert status["ready"]["ds006072_metadata"] is True
    assert status["analysis_status"]["receptor_prior"] == "ready"
    assert status["analysis_status"]["structural_connectome"] == "missing_local_structural_matrix"
    assert status["paths"]["receptor_prior"] == "results/receptor_priors/fs5ht_5ht2a_macro_modules.csv"
