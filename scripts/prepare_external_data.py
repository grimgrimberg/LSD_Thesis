from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsd_thesis.data.parcellations import fetch_schaefer_labels_image

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NILEARN_DATA = REPO_ROOT / "results" / "nilearn_data"
DEFAULT_DS006072_ROOT = REPO_ROOT / "data" / "ds006072"
DEFAULT_HCP_ROOT = REPO_ROOT / "data" / "hcp_structural_connectome"
DEFAULT_RECEPTOR_ROOT = REPO_ROOT / "data" / "receptor_priors"
DEFAULT_MANIFEST = REPO_ROOT / "results" / "external_data" / "external_data_manifest.json"
SCHAEFER_TARGETS = (
    "schaefer_100_yeo_7",
    "schaefer_200_yeo_7",
    "schaefer_100_yeo_17",
    "schaefer_200_yeo_17",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path.as_posix()


def _prepare_roots(nilearn_data_dir: Path, ds006072_root: Path, hcp_root: Path, receptor_root: Path) -> dict[str, str]:
    for root in (nilearn_data_dir, ds006072_root, hcp_root, receptor_root):
        root.mkdir(parents=True, exist_ok=True)
    os.environ["NILEARN_DATA"] = str(nilearn_data_dir.resolve())
    return {
        "nilearn_data": str(nilearn_data_dir.resolve()),
        "ds006072": str(ds006072_root.resolve()),
        "hcp_structural_connectome": str(hcp_root.resolve()),
        "receptor_priors": str(receptor_root.resolve()),
    }


def _download_schaefer_atlases(nilearn_data_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for parcellation_id in SCHAEFER_TARGETS:
        last_error: str | None = None
        for _ in range(3):
            try:
                labels_img, labels, metadata = fetch_schaefer_labels_image(
                    parcellation_id,
                    nilearn_data_dir=nilearn_data_dir,
                )
                break
            except Exception as error:
                last_error = str(error)
        else:
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "blocked_fetch_error",
                    "error": last_error,
                }
            )
            continue
        rows.append(
            {
                "parcellation_id": parcellation_id,
                "status": "available",
                "shape": list(labels_img.shape),
                "label_count": len(labels),
                "maps_path": metadata.get("maps_path"),
                "labels_path": metadata.get("labels_path"),
                "cache_status": metadata.get("cache_status", "fetched_by_nilearn"),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare external-data roots and repo-local atlas caches for the thesis evidence loop."
    )
    parser.add_argument("--nilearn-data-dir", type=Path, default=DEFAULT_NILEARN_DATA)
    parser.add_argument("--ds006072-root", type=Path, default=DEFAULT_DS006072_ROOT)
    parser.add_argument("--hcp-root", type=Path, default=DEFAULT_HCP_ROOT)
    parser.add_argument("--receptor-root", type=Path, default=DEFAULT_RECEPTOR_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--skip-schaefer",
        action="store_true",
        help="Only create local roots and manifest; do not fetch Schaefer atlas files.",
    )
    args = parser.parse_args()

    roots = _prepare_roots(args.nilearn_data_dir, args.ds006072_root, args.hcp_root, args.receptor_root)
    schaefer_rows = [] if args.skip_schaefer else _download_schaefer_atlases(args.nilearn_data_dir)
    manifest = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "repo_root": str(REPO_ROOT.resolve()),
        "policy": "All new external data and package caches are targeted under D:\\LSD_Thesis by default.",
        "roots": roots,
        "schaefer_atlases": schaefer_rows,
        "openneuro_ds006072_target": str(args.ds006072_root.resolve()),
        "openneuro_ds006072_metadata_manifest": (
            str((args.ds006072_root / "ds006072_metadata_manifest.json").resolve())
            if (args.ds006072_root / "ds006072_metadata_manifest.json").exists()
            else None
        ),
        "openneuro_ds006072_metadata_command": ".venv\\Scripts\\python.exe scripts\\download_ds006072_metadata.py",
        "openneuro_ds006072_full_download_note": (
            "The installed openneuro-py downloader is not the preferred path in this repo because it currently queries "
            "the removed DatasetFile.key field. Use repo-owned download code or a patched downloader, and target "
            f"{args.ds006072_root}."
        ),
        "hcp_guardrail": "HCP structural connectivity requires authorized access/provenance before files are placed in this root.",
        "receptor_guardrail": "PET receptor priors must be documented map projections before files are placed in this root.",
    }
    manifest["source_path"] = _write_json(args.manifest, manifest)
    print(json.dumps({"source_path": manifest["source_path"], "roots": roots}, indent=2), flush=True)


if __name__ == "__main__":
    main()
