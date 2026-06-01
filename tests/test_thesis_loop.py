import csv
from pathlib import Path
from uuid import uuid4

from lsd_thesis.external_source_plan import EXTERNAL_SOURCE_PLAN_COLUMNS, external_source_plan_rows
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
    assert (repo_root / "results" / "thesis_evidence_loop" / "external_source_plan.csv").exists()
    assert (repo_root / "results" / "thesis_evidence_loop" / "external_source_plan.md").exists()


def test_thesis_evidence_loop_exports_requested_external_source_plan() -> None:
    repo_root = _root()

    payload = build_thesis_evidence_loop(repo_root)

    assert payload["external_source_plan_columns"] == EXTERNAL_SOURCE_PLAN_COLUMNS
    assert payload["external_source_plan_paths"] == {
        "csv": "results/thesis_evidence_loop/external_source_plan.csv",
        "markdown": "results/thesis_evidence_loop/external_source_plan.md",
    }
    by_source = {row["source_id"]: row for row in payload["external_source_plan"]}
    assert set(by_source) == {
        "girn_2026_mega_analysis",
        "dosenbach_siegel_ds006072_2025",
        "markello_neuromaps_2022",
        "hcp_young_adult",
        "schaefer_2018_local_global",
    }
    assert by_source["girn_2026_mega_analysis"]["status"] == "blocked_missing_dynamic_summary"
    assert by_source["girn_2026_mega_analysis"]["use_in_project"] == "Final external benchmark for C/D/E directionality."
    assert by_source["dosenbach_siegel_ds006072_2025"]["status"] == "blocked_missing_local_ds006072_empirical_viewer"
    assert by_source["dosenbach_siegel_ds006072_2025"]["component"] == "psilocybin_ds006072"
    assert by_source["markello_neuromaps_2022"]["status"] == "blocked_missing_pet_receptor_prior"
    assert "receptor PET annotations" in by_source["markello_neuromaps_2022"]["key_evidence"]
    assert by_source["hcp_young_adult"]["status"] == "blocked_missing_hcp_structural_graph"
    assert by_source["schaefer_2018_local_global"]["status"] == "blocked_missing_parcellation_viewers"
    assert by_source["schaefer_2018_local_global"]["target_layers"] == "C/D/E"


def test_external_source_plan_promotes_display_status_when_components_are_implemented() -> None:
    rows = external_source_plan_rows(
        {
            "literature_benchmark": "implemented_directional_proxy_benchmark",
            "psilocybin_ds006072": "implemented_ds006072_unchanged_scoring_validation",
            "receptor_priors": "implemented_pet_receptor_prior_sensitivity",
            "structural_connectome": "implemented_hcp_structural_graph_sensitivity",
            "parcellation_sensitivity": "implemented_status_matrix",
        }
    )
    by_source = {row["source_id"]: row for row in rows}

    assert by_source["girn_2026_mega_analysis"]["status"] == "implemented directional proxy benchmark"
    assert by_source["dosenbach_siegel_ds006072_2025"]["status"] == "implemented external stress test"
    assert by_source["markello_neuromaps_2022"]["status"] == "implemented PET receptor-prior sensitivity"
    assert by_source["hcp_young_adult"]["status"] == "implemented HCP structural graph sensitivity"
    assert by_source["schaefer_2018_local_global"]["status"] == "implemented Schaefer/Yeo sensitivity"
    assert by_source["markello_neuromaps_2022"]["current_component_status"] == (
        "implemented_pet_receptor_prior_sensitivity"
    )


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
    assert any("ds006072 psilocybin tests" in row["claim"] for row in matrix)
    assert any("Failed literature checks" in row["claim"] for row in matrix)

    by_claim = {row["claim"]: row for row in matrix}
    assert by_claim["E survives real structural-connectome graph"]["status"] == "blocked_missing_hcp_structural_graph"
    assert by_claim["E survives PET receptor-map priors"]["status"] == "blocked_missing_pet_receptor_prior"
    assert (
        by_claim["ds006072 psilocybin tests the LSD A+B+C+D+E ranking"]["status"]
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
    source_plan_csv = repo_root / "results" / "thesis_evidence_loop" / "exports" / "external_source_plan.csv"
    workbook_path = repo_root / "results" / "thesis_evidence_loop" / "exports" / "thesis_evidence_loop_tables.xlsx"
    assert outputs["claim_matrix_csv"] == claim_csv.as_posix()
    assert outputs["external_source_plan_csv"] == source_plan_csv.as_posix()
    assert outputs["workbook_path"] == workbook_path.as_posix()
    assert claim_csv.exists()
    assert source_plan_csv.exists()
    assert workbook_path.exists()
    header = claim_csv.read_text(encoding="utf-8").splitlines()[0]
    assert header == "claim,dataset,model layer,null/control,figure,csv/xlsx export,citation,limitation,status"
    source_header = source_plan_csv.read_text(encoding="utf-8").splitlines()[0]
    assert source_header == ",".join(EXTERNAL_SOURCE_PLAN_COLUMNS)
