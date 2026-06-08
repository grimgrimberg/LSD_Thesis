from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .cache import (
    build_empirical_cache_metadata,
    build_empirical_target_payloads,
    sanitize_rest_manifest_for_cache,
    validate_empirical_cache_metadata,
)
from .constants import DS003059_DEFAULT_RUNS, EMPIRICAL_CACHE_METADATA_FILENAME, MODULE_NAMES
from .extraction import extract_empirical_run_records
from .models import Ds003059EmpiricalRecord, Ds003059RestManifest
from .openneuro import download_ds003059_rest_runs, fetch_ds003059_rest_manifest
from .runs import normalize_ds003059_runs
from .serialization import _to_plain_python


def generate_empirical_targets(
    dataset_dir: str | Path,
    output_dir: str | Path,
    subjects: tuple[str, ...] | None = None,
    runs: Sequence[str] | None = None,
    *,
    include_music: bool = False,
) -> dict[str, Any]:
    selected_runs = normalize_ds003059_runs(runs, include_music=include_music)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    sober_path = output_path / "empirical_sober_targets.yaml"
    perturbation_path = output_path / "empirical_perturbation_targets.yaml"
    manifest_path = output_path / "ds003059_rest_manifest.json"
    records_path = output_path / "empirical_run_summaries.json"
    cache_metadata_path = output_path / EMPIRICAL_CACHE_METADATA_FILENAME

    if sober_path.exists() and perturbation_path.exists() and manifest_path.exists() and records_path.exists():
        try:
            cache_metadata = validate_empirical_cache_metadata(
                output_path,
                requested_subjects=subjects,
                selected_runs=selected_runs,
                include_music=include_music,
                dataset_dir=dataset_dir,
            )
        except ValueError:
            cache_metadata = None
        else:
            manifest = Ds003059RestManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
            run_records = tuple(
                Ds003059EmpiricalRecord.model_validate(
                    {
                        **record,
                        "fc_matrix": np.asarray(record["fc_matrix"], dtype=float),
                    }
                )
                for record in json.loads(records_path.read_text(encoding="utf-8"))
            )
            return {
                "manifest": manifest,
                "run_records": run_records,
                "sober_target_path": str(sober_path),
                "perturbation_target_path": str(perturbation_path),
                "cache_metadata": cache_metadata,
            }

    manifest = fetch_ds003059_rest_manifest(subjects=subjects, runs=selected_runs, include_music=include_music)
    download_ds003059_rest_runs(manifest, target_dir=dataset_dir)
    cache_manifest = sanitize_rest_manifest_for_cache(manifest)
    run_records = extract_empirical_run_records(
        manifest=cache_manifest,
        dataset_dir=dataset_dir,
        output_dir=output_dir,
    )
    serialized_records = [
        {
            "subject": record.subject,
            "session": record.session,
            "run": record.run,
            "relative_path": record.relative_path,
            "timepoints": record.timepoints,
            "metrics": record.metrics,
            "fc_matrix": record.fc_matrix,
            "time_series_path": Path(record.time_series_path).as_posix(),
        }
        for record in run_records
    ]
    sober_payload, perturbation_payload = build_empirical_target_payloads(
        records=serialized_records,
        module_names=MODULE_NAMES,
        target_runs=DS003059_DEFAULT_RUNS,
    )

    sober_path.write_text(yaml.safe_dump(_to_plain_python(sober_payload), sort_keys=False), encoding="utf-8")
    perturbation_path.write_text(
        yaml.safe_dump(_to_plain_python(perturbation_payload), sort_keys=False),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(_to_plain_python(cache_manifest.model_dump()), indent=2), encoding="utf-8")
    records_path.write_text(json.dumps(_to_plain_python(serialized_records), indent=2), encoding="utf-8")
    cache_metadata = build_empirical_cache_metadata(
        output_path=output_path,
        manifest=cache_manifest,
        records=serialized_records,
        requested_subjects=subjects,
        selected_runs=selected_runs,
        include_music=include_music,
        dataset_dir=dataset_dir,
    )
    cache_metadata_path.write_text(json.dumps(_to_plain_python(cache_metadata), indent=2), encoding="utf-8")

    return {
        "manifest": cache_manifest,
        "run_records": run_records,
        "sober_target_path": str(sober_path),
        "perturbation_target_path": str(perturbation_path),
        "cache_metadata": cache_metadata,
    }
