from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np
from nilearn import datasets

from .constants import (
    HARVARD_OXFORD_CORTICAL_FILENAME,
    HARVARD_OXFORD_SUBCORTICAL_FILENAME,
    MODULE_ATLAS_LABELS,
    MODULE_NAMES,
)


def atlas_module_label_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for module_name, label_spec in MODULE_ATLAS_LABELS.items():
        for atlas_name, labels in label_spec.items():
            for label in labels:
                rows.append({"module": module_name, "atlas": atlas_name, "label": int(label)})
    return rows

def atlas_label_overlaps() -> dict[str, dict[int, tuple[str, ...]]]:
    label_to_modules: dict[str, dict[int, list[str]]] = {"cortical": {}, "subcortical": {}}
    for module_name, label_spec in MODULE_ATLAS_LABELS.items():
        for atlas_name, labels in label_spec.items():
            for label in labels:
                label_to_modules[atlas_name].setdefault(int(label), []).append(module_name)

    return {
        atlas_name: {
            label: tuple(module_names)
            for label, module_names in sorted(label_map.items())
            if len(module_names) > 1
        }
        for atlas_name, label_map in label_to_modules.items()
        if any(len(module_names) > 1 for module_names in label_map.values())
    }

def atlas_label_overlap_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for atlas_name, overlap_map in atlas_label_overlaps().items():
        for label, module_names in overlap_map.items():
            rows.append({"atlas": atlas_name, "label": label, "modules": list(module_names)})
    return rows

def _nilearn_data_roots(nilearn_data_dir: str | Path | None = None) -> tuple[Path, ...]:
    roots: list[Path] = []
    if nilearn_data_dir is not None:
        roots.append(Path(nilearn_data_dir))
    env_data = os.environ.get("NILEARN_DATA")
    if env_data:
        roots.extend(Path(item) for item in env_data.split(os.pathsep) if item)
    roots.append(Path(__file__).resolve().parents[3] / "results" / "nilearn_data")
    roots.append(Path.home() / "nilearn_data")
    deduped: list[Path] = []
    for root in roots:
        resolved = root.expanduser()
        if resolved not in deduped:
            deduped.append(resolved)
    return tuple(deduped)

def _load_cached_harvard_oxford_images(
    nilearn_data_dir: str | Path | None = None,
) -> tuple[nib.Nifti1Image, nib.Nifti1Image] | None:
    for root in _nilearn_data_roots(nilearn_data_dir):
        atlas_root = root / "fsl" / "data" / "atlases" / "HarvardOxford"
        cortical_path = atlas_root / HARVARD_OXFORD_CORTICAL_FILENAME
        subcortical_path = atlas_root / HARVARD_OXFORD_SUBCORTICAL_FILENAME
        if cortical_path.exists() and subcortical_path.exists():
            return cast(nib.Nifti1Image, nib.load(cortical_path)), cast(
                nib.Nifti1Image, nib.load(subcortical_path)
            )
    return None

def build_atlas_mapping_audit(
    labels_img: nib.Nifti1Image | None = None,
    include_voxel_counts: bool = True,
    nilearn_data_dir: str | Path | None = None,
    allow_fetch: bool = False,
) -> dict[str, Any]:
    module_voxel_counts: dict[str, int] = {}
    assigned_voxels: int | None = None
    unassigned_voxels: int | None = None
    if include_voxel_counts:
        try:
            resolved_labels_img = labels_img or _build_macro_module_labels_image(
                nilearn_data_dir=nilearn_data_dir,
                allow_fetch=allow_fetch,
            )
            label_volume = np.asarray(resolved_labels_img.dataobj, dtype=int)
            module_voxel_counts = {
                module_name: int(np.sum(label_volume == module_index))
                for module_index, module_name in enumerate(MODULE_NAMES, start=1)
            }
            assigned_voxels = int(np.sum(label_volume > 0))
            unassigned_voxels = int(np.sum(label_volume == 0))
        except OSError:
            module_voxel_counts = {}

    return {
        "mapping": atlas_module_label_rows(),
        "overlaps": atlas_label_overlap_rows(),
        "module_voxel_counts": module_voxel_counts,
        "assigned_voxels": assigned_voxels,
        "unassigned_voxels": unassigned_voxels,
        "notes": [
            "Voxel counts are after overlap resolution in MODULE_NAMES order.",
            "This Harvard-Oxford-derived 8-module mapping is a transparent proxy, not a canonical network atlas.",
            "Voxel counts are omitted when include_voxel_counts is false to keep cached Stage 2 reruns non-blocking.",
        ],
    }

def _build_macro_module_labels_image(
    nilearn_data_dir: str | Path | None = None,
    allow_fetch: bool = True,
) -> nib.Nifti1Image:
    cached_images = _load_cached_harvard_oxford_images(nilearn_data_dir)
    if cached_images is not None:
        cortical_img, subcortical_img = cached_images
    elif allow_fetch:
        fetch_data_dir = Path(nilearn_data_dir) if nilearn_data_dir is not None else _nilearn_data_roots(None)[0]
        fetch_kwargs = {"data_dir": str(fetch_data_dir)}
        cortical = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-2mm", **fetch_kwargs)
        subcortical = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-2mm", **fetch_kwargs)

        def _as_nifti_image(image_or_path: Any) -> nib.Nifti1Image:
            if isinstance(image_or_path, nib.Nifti1Image):
                return image_or_path
            return cast(nib.Nifti1Image, nib.load(image_or_path))

        cortical_img = _as_nifti_image(cortical.maps)
        subcortical_img = _as_nifti_image(subcortical.maps)
    else:
        raise FileNotFoundError("Cached Harvard-Oxford atlas files were not found.")

    cortical_data = np.asarray(cortical_img.dataobj)
    subcortical_data = np.asarray(subcortical_img.dataobj)
    module_data = np.zeros(cortical_data.shape, dtype=np.int16)

    # Overlapping source labels are resolved by MODULE_NAMES order; the audit
    # helpers above expose those overlaps so the proxy mapping stays explicit.
    for index, module_name in enumerate(MODULE_NAMES, start=1):
        label_spec = MODULE_ATLAS_LABELS[module_name]
        mask = np.zeros(cortical_data.shape, dtype=bool)
        if label_spec["cortical"]:
            mask |= np.isin(cortical_data, label_spec["cortical"])
        if label_spec["subcortical"]:
            mask |= np.isin(subcortical_data, label_spec["subcortical"])
        module_data[mask] = index

    return nib.Nifti1Image(module_data, cortical_img.affine)
