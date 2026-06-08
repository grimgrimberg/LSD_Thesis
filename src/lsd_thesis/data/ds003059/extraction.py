from __future__ import annotations

from pathlib import Path
from typing import cast

import nibabel as nib
import numpy as np
from nilearn.maskers import NiftiLabelsMasker

from lsd_thesis.metrics import compute_observable_summary

from .atlas import _build_macro_module_labels_image
from .constants import MODULE_NAMES
from .models import Ds003059EmpiricalRecord, Ds003059RestManifest


def _standardize_time_series(time_series: np.ndarray) -> np.ndarray:
    centered = time_series - np.mean(time_series, axis=0, keepdims=True)
    if time_series.shape[0] < 2:
        return cast(np.ndarray, centered.astype(float, copy=False))
    sample_std = np.std(time_series, axis=0, ddof=1, keepdims=True)
    safe_std = np.where(sample_std < 1e-8, 1.0, sample_std)
    return cast(np.ndarray, (centered / safe_std).astype(float, copy=False))

def _extract_module_time_series_manually(
    bold_image: nib.Nifti1Image,
    labels_img: nib.Nifti1Image,
) -> np.ndarray:
    volume = np.asarray(bold_image.dataobj, dtype=float)
    if volume.ndim != 4:
        raise ValueError("BOLD image must be 4D.")

    label_volume = np.asarray(labels_img.dataobj, dtype=int)
    if label_volume.shape != volume.shape[:3]:
        raise ValueError("Label image shape must match the first three BOLD dimensions.")

    module_count = int(label_volume.max())
    time_series = np.zeros((volume.shape[3], module_count), dtype=float)
    for label_index in range(1, module_count + 1):
        mask = label_volume == label_index
        if not np.any(mask):
            continue
        time_series[:, label_index - 1] = volume[mask].mean(axis=0)

    return _standardize_time_series(time_series)

def extract_module_time_series(run_path: str | Path, labels_img: nib.Nifti1Image | None = None) -> np.ndarray:
    resolved_labels = labels_img or _build_macro_module_labels_image()
    resolved_run_path = Path(run_path)
    for attempt in range(3):
        masker = NiftiLabelsMasker(
            labels_img=resolved_labels,
            standardize="zscore_sample",
        )
        try:
            bold_image = cast(nib.Nifti1Image, nib.load(str(resolved_run_path)))
            materialized_image = nib.Nifti1Image(
                np.asarray(bold_image.dataobj),
                bold_image.affine,
                bold_image.header.copy(),
            )
            return np.asarray(masker.fit_transform(materialized_image), dtype=float)
        except OSError:
            if attempt == 2:
                break
        except ValueError as error:
            if "File not found:" not in str(error) or attempt == 2:
                break
    bold_image = cast(nib.Nifti1Image, nib.load(str(resolved_run_path)))
    return _extract_module_time_series_manually(bold_image, resolved_labels)

def extract_empirical_run_records(
    manifest: Ds003059RestManifest,
    dataset_dir: str | Path,
    output_dir: str | Path,
) -> tuple[Ds003059EmpiricalRecord, ...]:
    labels_img = _build_macro_module_labels_image()
    dataset_root = Path(dataset_dir)
    output_root = Path(output_dir)
    series_root = output_root / "module_time_series"
    series_root.mkdir(parents=True, exist_ok=True)

    records: list[Ds003059EmpiricalRecord] = []
    for run in manifest.runs:
        run_path = dataset_root / run.relative_path
        time_series = extract_module_time_series(run_path, labels_img=labels_img)
        observable = compute_observable_summary(time_series, MODULE_NAMES)
        series_path = series_root / f"{run.subject}_{run.session}_{run.run}_modules.npy"
        np.save(series_path, time_series)
        # Store path relative to output_dir for portability
        relative_series_path = series_path.relative_to(output_root)
        records.append(
            Ds003059EmpiricalRecord(
                subject=run.subject,
                session=run.session,
                run=run.run,
                relative_path=run.relative_path,
                timepoints=int(time_series.shape[0]),
                metrics=observable.metric_map(),
                fc_matrix=observable.fc_matrix,
                time_series_path=relative_series_path.as_posix(),
            )
        )

    return tuple(records)
