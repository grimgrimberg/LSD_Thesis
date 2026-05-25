import csv
from pathlib import Path
from uuid import uuid4

from lsd_thesis.thesis_loop import build_thesis_evidence_loop
from scripts.export_thesis_loop_tables import export_thesis_loop_tables


def _root() -> Path:
    root = Path("codex_logs") / "thesis_loop_tests" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_thesis_evidence_loop_writes_serious_blocked_statuses_without_fabricating_data() -> None:
    repo_root = _root()

    payload = build_thesis_evidence_loop(repo_root)

    rows = {row["label"]: row for row in payload["status_rows"]}
    assert payload["analysis_status"] == "implemented_loop_status_artifacts"
    assert rows["Psilocybin ds006072"]["status"] == "blocked_missing_local_ds006072_empirical_viewer"
    assert rows["HCP structural graph"]["status"] == "blocked_missing_hcp_structural_graph"
    assert rows["PET receptor priors"]["status"] == "blocked_missing_pet_receptor_prior"
    assert rows["Mega-analysis comparison"]["status"] == "blocked_missing_dynamic_summary"
    assert (repo_root / "results" / "thesis_evidence_loop" / "thesis_evidence_loop_status.json").exists()
    assert (repo_root / "results" / "psilocybin_ds006072" / "required_empirical_viewer_schema.json").exists()
    assert (repo_root / "results" / "structural_connectome" / "required_hcp_macro_modules_template.csv").exists()
    assert (repo_root / "results" / "receptor_priors" / "required_fs5ht_5ht2a_macro_modules_template.csv").exists()


def test_thesis_evidence_loop_writes_hiring_readiness_claim_matrix() -> None:
    repo_root = _root()

    payload = build_thesis_evidence_loop(repo_root)

    expected_columns = [
        "claim",
        "dataset",
        "model layer",
        "null/control",
        "figure",
        "csv/xlsx export",
        "citation",
        "limitation",
        "status",
    ]
    matrix = payload["claim_evidence_matrix"]
    assert payload["claim_evidence_matrix_columns"] == expected_columns
    assert payload["claim_evidence_matrix_paths"] == {
        "csv": "results/thesis_evidence_loop/claim_evidence_matrix.csv",
        "markdown": "results/thesis_evidence_loop/claim_evidence_matrix.md",
    }
    assert all(list(row) == expected_columns for row in matrix)
    assert any("C survives Schaefer/Yeo" in row["claim"] for row in matrix)
    assert any("E survives real structural-connectome" in row["claim"] for row in matrix)
    assert any("E survives PET receptor-map" in row["claim"] for row in matrix)
    assert any("ds006072 psilocybin reproduces" in row["claim"] for row in matrix)
    assert any("Failed literature checks" in row["claim"] for row in matrix)

    by_claim = {row["claim"]: row for row in matrix}
    assert by_claim["E survives real structural-connectome graph"]["status"] == "blocked_missing_hcp_structural_graph"
    assert by_claim["E survives PET receptor-map priors"]["status"] == "blocked_missing_pet_receptor_prior"
    assert (
        by_claim["ds006072 psilocybin reproduces the LSD A+B+C+D+E ranking"]["status"]
        == "blocked_missing_local_ds006072_empirical_viewer"
    )

    csv_path = repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.csv"
    markdown_path = repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.md"
    assert csv_path.exists()
    assert markdown_path.exists()
    csv_rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8", newline="")))
    assert csv_rows[0].keys() == set(expected_columns)
    assert "| claim | dataset | model layer | null/control | figure | csv/xlsx export | citation | limitation | status |" in markdown_path.read_text(
        encoding="utf-8"
    )


def test_export_thesis_loop_tables_includes_claim_matrix() -> None:
    repo_root = _root()
    build_thesis_evidence_loop(repo_root)

    outputs = export_thesis_loop_tables(repo_root, repo_root / "results" / "thesis_evidence_loop" / "exports")

    claim_csv = repo_root / "results" / "thesis_evidence_loop" / "exports" / "claim_evidence_matrix.csv"
    workbook_path = repo_root / "results" / "thesis_evidence_loop" / "exports" / "thesis_evidence_loop_tables.xlsx"
    assert outputs["claim_matrix_csv"] == claim_csv.as_posix()
    assert outputs["workbook_path"] == workbook_path.as_posix()
    assert claim_csv.exists()
    assert workbook_path.exists()
    header = claim_csv.read_text(encoding="utf-8").splitlines()[0]
    assert header == "claim,dataset,model layer,null/control,figure,csv/xlsx export,citation,limitation,status"
