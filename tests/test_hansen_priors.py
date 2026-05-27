from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from lsd_thesis.data.ds003059 import MODULE_NAMES
from lsd_thesis.hansen_priors import (
    RECEPTOR_FILES,
    STRUCTURAL_FILE,
    derive_hansen_macro_priors,
    project_receptor_to_modules,
    project_structural_to_modules,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_project_hansen_receptor_and_structural_sources_cover_all_macro_modules() -> None:
    receptor_rows, receptor_meta = project_receptor_to_modules(
        [("5HT2a_cimbi_hc29_beliveau.csv", np.linspace(1.0, 2.0, 100))]
    )
    structural_rows, structural_meta = project_structural_to_modules(np.ones((100, 100), dtype=float))

    assert [row["module"] for row in receptor_rows] == list(MODULE_NAMES)
    assert [row["module"] for row in structural_rows] == list(MODULE_NAMES)
    assert receptor_meta["module_projection"]["auditory"]["projection_status"].startswith("imputed")
    assert structural_meta["module_projection"]["thalamic_gateway"]["projection_status"].startswith("imputed")


def test_derive_hansen_macro_priors_writes_results_ingestion_artifacts(tmp_path: Path) -> None:
    cache_dir = tmp_path / "source"
    for index, relative_path in enumerate(RECEPTOR_FILES, start=1):
        target = cache_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(",".join(str(value + index) for value in range(100)), encoding="utf-8")
    structural_path = cache_dir / STRUCTURAL_FILE
    structural_path.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.arange(10000, dtype=float).reshape(100, 100)
    matrix = (matrix + matrix.T) / 2.0
    np.save(structural_path, matrix)

    manifest = derive_hansen_macro_priors(repo_root=tmp_path, cache_dir=cache_dir, fetch_missing=False)

    receptor_path = tmp_path / "results" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv"
    structural_path = tmp_path / "results" / "structural_connectome" / "hcp_macro_modules.csv"
    assert receptor_path.exists()
    assert structural_path.exists()
    assert manifest["outputs"]["receptor_prior"] == "results/receptor_priors/fs5ht_5ht2a_macro_modules.csv"
    values = [float(row["receptor_weight"]) for row in _read_csv(receptor_path)]
    assert min(values) == 0.0
    assert max(values) == 1.0
    assert (tmp_path / "results" / "external_ingestion" / "hansen_receptors" / "hansen_macro_projection_manifest.json").exists()
