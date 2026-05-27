from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from lsd_thesis.subject_split import (
    build_subject_validation_boundary,
    create_candidate_subject_split,
    create_cv5_subject_split_package,
    load_subject_split_file,
    resolve_subject_split_path,
    subject_split_json_payload,
    validate_cv5_subject_split_manifest,
    validate_subject_split_against_available_subjects,
)

ROOT = Path(__file__).resolve().parents[1]
CV5_TEST_SUBJECTS = (
    "sub-001",
    "sub-002",
    "sub-003",
    "sub-004",
    "sub-006",
    "sub-009",
    "sub-010",
    "sub-011",
    "sub-012",
    "sub-013",
    "sub-015",
    "sub-017",
    "sub-018",
    "sub-019",
    "sub-020",
)


def _write_split(path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema_version": 1,
        "split_id": "fixture_split",
        "strategy": "subject_disjoint",
        "selection_subjects": [" sub-001 ", "SUB-002"],
        "validation_subjects": ["sub-003"],
        "split_seed": 123,
        "notes": "fixture only",
        "created_by": "pytest",
        "created_at": "2026-05-10T00:00:00Z",
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_valid_subject_split_file_is_normalized_and_builds_honest_boundary(tmp_path: Path) -> None:
    split_path = _write_split(tmp_path / "split.json")

    split = load_subject_split_file(split_path)
    boundary = build_subject_validation_boundary(split, split_file_path=split_path)

    assert split.selection_subjects == ("sub-001", "sub-002")
    assert split.validation_subjects == ("sub-003",)
    assert boundary["split_schema_version"] == 1
    assert boundary["held_out_validation_configured"] is True
    assert boundary["held_out_validation_completed"] is False
    assert boundary["held_out"] is False
    assert boundary["approval_status"] == "candidate"
    assert boundary["boundary_type"] == "subject_disjoint_candidate_configured_not_completed"
    assert boundary["selection_subject_count"] == 2
    assert boundary["validation_subject_count"] == 1
    assert boundary["overlap_count"] == 0
    assert "not approved" in boundary["claim_guardrail"]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"selection_subjects": ["sub-001", "sub-001"]}, "duplicate"),
        ({"validation_subjects": ["sub-003", "sub-003"]}, "duplicate"),
        ({"selection_subjects": ["sub-001"], "validation_subjects": ["sub-001"]}, "overlap"),
        ({"selection_subjects": []}, "selection_subjects"),
        ({"validation_subjects": []}, "validation_subjects"),
        ({"approval_status": "approved"}, "approved_by"),
        ({"approved_by": "reviewer"}, "candidate"),
    ],
)
def test_subject_split_rejects_leakage_or_empty_roles(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    split_path = _write_split(tmp_path / "split.json", **overrides)

    with pytest.raises(ValueError, match=message):
        load_subject_split_file(split_path)


def test_subject_split_rejects_missing_required_fields(tmp_path: Path) -> None:
    split_path = tmp_path / "split.json"
    split_path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    with pytest.raises(ValueError, match="split_id"):
        load_subject_split_file(split_path)


def test_candidate_subject_split_generation_is_deterministic_and_not_approved() -> None:
    subjects = ["sub-003", "sub-001", "sub-002", "sub-004", "sub-005"]

    first = create_candidate_subject_split(
        subjects,
        split_id="candidate_fixture",
        seed=123,
        validation_fraction=0.4,
        dataset_id="ds003059",
        dataset_version="1.0.0",
        source_label="fixture",
    )
    second = create_candidate_subject_split(
        reversed(subjects),
        split_id="candidate_fixture",
        seed=123,
        validation_fraction=0.4,
        dataset_id="ds003059",
        dataset_version="1.0.0",
        source_label="fixture",
    )

    assert subject_split_json_payload(first) == subject_split_json_payload(second)
    assert first.approval_status == "candidate"
    assert len(first.selection_subjects) == 3
    assert len(first.validation_subjects) == 2
    assert not set(first.selection_subjects).intersection(first.validation_subjects)
    assert first.holdout_policy is not None
    assert first.holdout_policy["validation_fraction"] == 0.4


def test_candidate_split_cannot_be_marked_completed() -> None:
    split = create_candidate_subject_split(
        ["sub-001", "sub-002", "sub-003"],
        split_id="candidate_fixture",
        seed=123,
    )

    with pytest.raises(ValueError, match="candidate"):
        build_subject_validation_boundary(split, held_out_validation_completed=True)


def test_approved_split_can_represent_completed_boundary(tmp_path: Path) -> None:
    split_path = _write_split(
        tmp_path / "approved_split.json",
        approval_status="approved",
        approved_by="thesis-reviewer",
        approved_at="2026-05-10T00:00:00Z",
    )

    split = load_subject_split_file(split_path)
    boundary = build_subject_validation_boundary(split, held_out_validation_completed=True)

    assert boundary["held_out"] is True
    assert boundary["held_out_validation_completed"] is True
    assert boundary["approval_status"] == "approved"
    assert boundary["boundary_type"] == "subject_disjoint_approved_completed"


def test_validate_subject_split_against_available_subjects_rejects_missing() -> None:
    split = create_candidate_subject_split(
        ["sub-001", "sub-002", "sub-003"],
        split_id="candidate_fixture",
        seed=123,
    )

    with pytest.raises(ValueError, match="not available"):
        validate_subject_split_against_available_subjects(split, {"sub-001", "sub-002"})


def test_resolve_subject_split_path_rejects_path_traversal(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    with pytest.raises(ValueError, match="inside the repository"):
        resolve_subject_split_path("../outside.json", repo_root=repo_root)


def test_validate_subject_split_script_reports_configured_not_completed(tmp_path: Path) -> None:
    split_path = _write_split(tmp_path / "split.json")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_subject_split.py"), str(split_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Subject split valid" in result.stdout
    assert "Approval status: candidate" in result.stdout
    assert "Selection subjects: 2" in result.stdout
    assert "Held-out validation subjects: 1" in result.stdout
    assert "Held-out validation completed: no" in result.stdout


def test_validate_subject_split_script_fails_on_overlap(tmp_path: Path) -> None:
    split_path = _write_split(
        tmp_path / "split.json",
        selection_subjects=["sub-001"],
        validation_subjects=["sub-001"],
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_subject_split.py"), str(split_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "overlap" in result.stderr


def test_validate_subject_split_script_generates_candidate_from_cached_qc(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    quality_dir = repo_root / "results" / "stage_2"
    quality_dir.mkdir(parents=True)
    (quality_dir / "empirical_data_quality.json").write_text(
        json.dumps(
            {
                "subjects": ["sub-001", "sub-002", "sub-003", "sub-004", "sub-005"],
                "subject_count": 5,
                "complete_subjects": ["sub-001", "sub-002", "sub-003", "sub-004", "sub-005"],
                "complete_subject_count": 5,
            }
        ),
        encoding="utf-8",
    )
    output_path = repo_root / "output" / "validation" / "subject_split_candidate.json"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_subject_split.py"),
            "--repo-root",
            str(repo_root),
            "--generate-candidate",
            str(output_path),
            "--seed",
            "123",
            "--validation-fraction",
            "0.4",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()
    generated = load_subject_split_file(output_path)
    assert generated.split_id == "thesis_subject_disjoint_v1_candidate"
    assert generated.approval_status == "candidate"
    assert len(generated.selection_subjects) == 3
    assert len(generated.validation_subjects) == 2
    assert "Candidate subject split written" in result.stdout
    assert "Next command: after human approval" in result.stdout


def _write_cv5_fixture_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    quality_dir = repo_root / "results" / "stage_2"
    quality_dir.mkdir(parents=True)
    (quality_dir / "empirical_data_quality.json").write_text(
        json.dumps(
            {
                "subjects": list(CV5_TEST_SUBJECTS),
                "subject_count": len(CV5_TEST_SUBJECTS),
                "complete_subjects": list(CV5_TEST_SUBJECTS),
                "complete_subject_count": len(CV5_TEST_SUBJECTS),
            }
        ),
        encoding="utf-8",
    )
    return repo_root


def test_cv5_subject_split_package_generation_is_deterministic_and_complete() -> None:
    fold_paths = [f"fold_{fold_index:02d}.json" for fold_index in range(1, 6)]

    first_folds, first_manifest = create_cv5_subject_split_package(
        CV5_TEST_SUBJECTS,
        split_set_id="cv5_fixture",
        seed=123,
        fold_file_paths=fold_paths,
    )
    second_folds, second_manifest = create_cv5_subject_split_package(
        tuple(reversed(CV5_TEST_SUBJECTS)),
        split_set_id="cv5_fixture",
        seed=123,
        fold_file_paths=fold_paths,
    )

    assert [subject_split_json_payload(split) for split in first_folds] == [
        subject_split_json_payload(split) for split in second_folds
    ]
    assert first_manifest == second_manifest
    assert len(first_folds) == 5
    validation_counts: dict[str, int] = {subject: 0 for subject in CV5_TEST_SUBJECTS}
    for fold in first_folds:
        assert fold.approval_status == "candidate"
        assert fold.strategy == "subject_disjoint_cv5_fold"
        assert len(fold.selection_subjects) == 12
        assert len(fold.validation_subjects) == 3
        assert not set(fold.selection_subjects).intersection(fold.validation_subjects)
        assert set(fold.selection_subjects).union(fold.validation_subjects) == set(CV5_TEST_SUBJECTS)
        for subject in fold.validation_subjects:
            validation_counts[subject] += 1

    assert set(validation_counts.values()) == {1}
    assert first_manifest["number_of_subjects"] == 15
    assert first_manifest["number_of_folds"] == 5
    assert first_manifest["selection_subjects_per_fold"] == 12
    assert first_manifest["validation_subjects_per_fold"] == 3
    assert first_manifest["held_out_validation_completed"] is False
    assert first_manifest["validation_coverage_summary"]["every_subject_held_out_exactly_once"] is True


def test_cv5_candidate_fold_cannot_be_marked_completed() -> None:
    folds, _manifest = create_cv5_subject_split_package(
        CV5_TEST_SUBJECTS,
        split_set_id="cv5_fixture",
        seed=123,
    )

    with pytest.raises(ValueError, match="candidate"):
        build_subject_validation_boundary(folds[0], held_out_validation_completed=True)


def test_validate_subject_split_script_generates_and_validates_cv5_package(tmp_path: Path) -> None:
    repo_root = _write_cv5_fixture_repo(tmp_path)
    output_dir = repo_root / "output" / "validation" / "cv5_subject_disjoint"
    manifest_path = output_dir / "subject_split_cv5_manifest_candidate.json"

    generate_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_subject_split.py"),
            "--repo-root",
            str(repo_root),
            "--generate-cv5",
            str(output_dir),
            "--seed",
            "123",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert generate_result.returncode == 0, generate_result.stderr
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["fold_file_paths"]) == 5
    assert all((repo_root / path).exists() for path in manifest["fold_file_paths"])

    summary = validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    assert summary["approval_status"] == "candidate"
    assert summary["held_out_validation_completed"] is False
    assert summary["validation_coverage_summary"]["every_subject_held_out_exactly_once"] is True

    validate_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_subject_split.py"),
            "--repo-root",
            str(repo_root),
            "--validate-cv5",
            str(manifest_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert validate_result.returncode == 0, validate_result.stderr
    assert "CV5 subject split package valid" in validate_result.stdout
    assert "Every subject held out exactly once: yes" in validate_result.stdout
    assert "Held-out validation completed: no" in validate_result.stdout


def test_validate_subject_split_script_fails_invalid_cv5_package(tmp_path: Path) -> None:
    repo_root = _write_cv5_fixture_repo(tmp_path)
    output_dir = repo_root / "output" / "validation" / "cv5_subject_disjoint"
    manifest_path = output_dir / "subject_split_cv5_manifest_candidate.json"
    generate_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_subject_split.py"),
            "--repo-root",
            str(repo_root),
            "--generate-cv5",
            str(output_dir),
            "--seed",
            "123",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert generate_result.returncode == 0, generate_result.stderr

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_fold_path = repo_root / manifest["fold_file_paths"][0]
    second_fold_path = repo_root / manifest["fold_file_paths"][1]
    first_fold = json.loads(first_fold_path.read_text(encoding="utf-8"))
    second_fold = json.loads(second_fold_path.read_text(encoding="utf-8"))
    first_fold["validation_subjects"] = second_fold["validation_subjects"]
    first_fold["selection_subjects"] = [
        subject for subject in manifest["subjects"] if subject not in second_fold["validation_subjects"]
    ]
    first_fold_path.write_text(json.dumps(first_fold), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_subject_split.py"),
            "--repo-root",
            str(repo_root),
            "--validate-cv5",
            str(manifest_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "exactly once" in result.stderr
