from __future__ import annotations

import csv
import hashlib
import json
import platform
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "reproducible_archive_manifest.v1"

DEFAULT_INCLUDE_FILES = (
    "README.md",
    "GOAL.md",
    "THESIS_CONCEPT_AUDIT.md",
    "COMMANDS.md",
    "docs/GITHUB_PAGES.md",
    "docs/THESIS_READINESS_GATES.md",
    "docs/METHODS_RESEARCH.md",
    "docs/ARCHIVE_POLICY.md",
    "results/stage_2/stage_2_summary.json",
    "results/stage_2/empirical_perturbation_targets.yaml",
    "results/dynamic_mechanism_ranking/summary.json",
    "results/dynamic_mechanism_ranking/robustness/robustness_summary.json",
    "results/training/rocket_condition_benchmark/comparison_summary.json",
    "results/training/rocket_condition_benchmark/benchmark_report.md",
    "results/thesis_evidence_loop/thesis_evidence_loop_status.json",
    "results/thesis_evidence_loop/claim_evidence_matrix.md",
    "results/thesis_upgrade/thesis_upgrade_status.json",
    "results/thesis_upgrade/thesis_upgrade_status.md",
    "results/external_ingestion/external_ingestion_status.json",
    "data/ds006072/ds006072_metadata_manifest.json",
    "data/ds006072/ds006072_func_manifest.json",
    "data/hcp_structural_connectome/structural_connectome_ingestion_manifest.json",
    "data/receptor_priors/receptor_prior_ingestion_manifest.json",
    "output/doc/thesis_report_revised.md",
    "output/doc/thesis_microsite.html",
)

EXCLUDED_PATTERNS = (
    ".env",
    ".venv/",
    "data/",
    "node_modules/",
    "tmp/",
    ".codex/",
    ".superpowers/",
    ".npy",
    ".npz",
    ".nii",
    ".nii.gz",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_excluded(relative: str) -> bool:
    normalized = relative.replace("\\", "/")
    return any(pattern in normalized for pattern in EXCLUDED_PATTERNS)


def collect_archive_artifacts(repo_root: Path = REPO_ROOT, include_files: Iterable[str] = DEFAULT_INCLUDE_FILES) -> list[dict[str, Any]]:
    repo_root = repo_root.resolve()
    artifacts: list[dict[str, Any]] = []
    for relative in include_files:
        if _is_excluded(relative):
            continue
        path = repo_root / relative
        if not path.exists() or not path.is_file():
            continue
        artifacts.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return artifacts


def build_archive_manifest(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    artifacts = collect_archive_artifacts(repo_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "source_datasets": [
            {
                "id": "OpenNeuro ds003059 v1.0.0",
                "url": "https://openneuro.org/datasets/ds003059/versions/1.0.0",
                "role": "primary LSD/placebo fMRI source; raw imaging files are not bundled",
            },
            {
                "id": "OpenNeuro ds006072",
                "url": "https://openneuro.org/datasets/ds006072",
                "role": "planned external psilocybin validation source; manifest/status only unless comparable extraction exists",
            },
        ],
        "excluded_policy": {
            "raw_data": "Excluded. Cite OpenNeuro dataset IDs and versions instead.",
            "large_arrays": "Excluded by default unless explicitly curated as small derived artifacts.",
            "secrets": "Excluded. No .env, tokens, credentials, or local machine secrets belong in archive artifacts.",
        },
        "recommended_publication": {
            "code": "GitHub public repository release",
            "doi": "Zenodo DOI minted from GitHub release",
            "demo": "GitHub Pages static snapshot",
            "data": "Derived aggregate artifacts plus external source-dataset citations",
        },
        "claim_guardrail": (
            "This manifest improves reproducibility for code and derived aggregate artifacts. "
            "It is not a redistribution of raw OpenNeuro neuroimaging data."
        ),
    }


def write_archive_manifest(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "reproducible_archive"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_archive_manifest(repo_root)
    manifest_path = output_dir / "ARCHIVE_MANIFEST.json"
    csv_path = output_dir / "ARCHIVE_ARTIFACTS.csv"
    checksum_path = output_dir / "CHECKSUMS.sha256"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest["artifacts"])
    checksum_lines = [f"{row['sha256']}  {row['path']}" for row in manifest["artifacts"]]
    checksum_path.write_text("\n".join(checksum_lines) + ("\n" if checksum_lines else ""), encoding="utf-8")
    manifest["manifest_path"] = manifest_path.relative_to(repo_root).as_posix()
    manifest["artifact_csv_path"] = csv_path.relative_to(repo_root).as_posix()
    manifest["checksum_path"] = checksum_path.relative_to(repo_root).as_posix()
    return manifest
