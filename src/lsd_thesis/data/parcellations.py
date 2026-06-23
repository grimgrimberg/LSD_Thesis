from __future__ import annotations

import json
import re
import shutil
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np
from nilearn import datasets
from nilearn.maskers import NiftiLabelsMasker

from lsd_thesis.core import MODULE_GROUPS, MODULE_NAMES
from lsd_thesis.data.ds003059 import DS003059_SESSIONS, normalize_ds003059_runs
from lsd_thesis.data.ds003059.atlas import _load_cached_harvard_oxford_images
from lsd_thesis.dynamic_mechanism.core import write_dynamic_mechanism_summary

HARVARD_OXFORD_PROXY_RECEPTOR_WEIGHTS = {
    "visual": 0.65,
    "auditory": 0.45,
    "salience": 0.70,
    "default_mode": 1.00,
    "executive_frontoparietal": 0.85,
    "limbic_affective": 0.70,
    "thalamic_gateway": 0.50,
    "sensorimotor": 0.35,
}
SCHAEFER_YEO_PROXY_RECEPTOR_WEIGHTS = {
    "Visual": 0.65,
    "SomMot": 0.35,
    "DorsAttn": 0.70,
    "SalVentAttn": 0.70,
    "Limbic": 0.70,
    "Cont": 0.85,
    "Default": 1.00,
}
PROXY_RECEPTOR_SOURCE = "coarse_literature_proxy_not_pet_map"
SCHAEFER_ID_PATTERN = re.compile(r"^schaefer_(?P<n_rois>100|200)_yeo_(?P<yeo_networks>7|17)$")
SCHAEFER_STRIATAL_ID_PATTERN = re.compile(
    r"^schaefer_(?P<n_rois>100|200)_yeo_(?P<yeo_networks>7|17)_striatal$"
)
HARVARD_OXFORD_THALAMUS_LABELS = (4, 15)
HARVARD_OXFORD_STRIATUM_LABELS = (5, 6, 7, 11, 16, 17, 18, 21)
SCHAEFER_NETWORKS = {
    7: ("Visual", "SomMot", "DorsAttn", "SalVentAttn", "Limbic", "Cont", "Default"),
    17: (
        "VisCent",
        "VisPeri",
        "SomMotA",
        "SomMotB",
        "DorsAttnA",
        "DorsAttnB",
        "SalVentAttnA",
        "SalVentAttnB",
        "LimbicA",
        "LimbicB",
        "ContA",
        "ContB",
        "ContC",
        "DefaultA",
        "DefaultB",
        "DefaultC",
        "TempPar",
    ),
}


@dataclass(frozen=True)
class NodeMetadata:
    node_label: str
    parcel_index: int
    yeo_network_label: str | None
    coarse_class: str
    hierarchy_value: float
    receptor_weight: float = 0.0
    receptor_weight_source: str = "neutral_placeholder"
    visual_weight: float = 0.0
    sensory_weight: float = 0.0
    somatomotor_weight: float = 0.0
    transmodal_weight: float = 0.0
    thalamus_weight: float = 0.0
    striatum_weight: float = 0.0
    metadata_source: str = "synthetic_schema"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParcellationSpec:
    parcellation_id: str
    description: str
    node_metadata: tuple[NodeMetadata, ...]
    atlas_metadata: dict[str, Any]

    @property
    def node_count(self) -> int:
        return len(self.node_metadata)

    def node_metadata_payload(self) -> dict[str, Any]:
        return {
            "parcellation_id": self.parcellation_id,
            "description": self.description,
            "nodes": [node.to_dict() for node in self.node_metadata],
            "notes": [
                "Receptor weights are coarse proxy priors unless a source field names a quantitative receptor map.",
                "Node metadata supports model comparison and target extraction; it is not a PET receptor map.",
            ],
        }


def _legacy_harvard_oxford_8_spec() -> ParcellationSpec:
    nodes = []
    for index, label in enumerate(MODULE_NAMES, start=1):
        group = MODULE_GROUPS[label]
        nodes.append(
            NodeMetadata(
                node_label=label,
                parcel_index=index,
                yeo_network_label=None,
                coarse_class=label if label in {"visual", "sensorimotor"} else group,
                receptor_weight=HARVARD_OXFORD_PROXY_RECEPTOR_WEIGHTS[label],
                receptor_weight_source=PROXY_RECEPTOR_SOURCE,
                hierarchy_value={
                    "sensory": 0.10,
                    "associative": 0.75,
                    "gateway": 0.35,
                }.get(group, 0.50),
                visual_weight=1.0 if label == "visual" else 0.0,
                sensory_weight=1.0 if group == "sensory" else 0.0,
                somatomotor_weight=1.0 if label == "sensorimotor" else 0.0,
                transmodal_weight=1.0 if group == "associative" else 0.0,
                thalamus_weight=1.0 if label == "thalamic_gateway" else 0.0,
                metadata_source="legacy_harvard_oxford_proxy",
            )
        )
    return ParcellationSpec(
        parcellation_id="harvard_oxford_8",
        description="Legacy eight-module Harvard-Oxford anatomical proxy.",
        node_metadata=tuple(nodes),
        atlas_metadata={
            "atlas": "Harvard-Oxford cortical/subcortical proxy",
            "legacy_extraction": True,
            "node_count": 8,
            "status": "implemented_legacy_path",
            "source_module": "src/lsd_thesis/data/ds003059.py",
        },
    )


def _schaefer_spec(n_rois: int, yeo_networks: int) -> ParcellationSpec:
    networks = SCHAEFER_NETWORKS[yeo_networks]
    base_count = n_rois // len(networks)
    remainder = n_rois % len(networks)
    network_counts = {
        network: base_count + (1 if index < remainder else 0)
        for index, network in enumerate(networks)
    }
    coarse_class = {
        "Visual": "visual",
        "VisCent": "visual",
        "VisPeri": "visual",
        "SomMot": "somatomotor",
        "SomMotA": "somatomotor",
        "SomMotB": "somatomotor",
        "DorsAttn": "control",
        "DorsAttnA": "control",
        "DorsAttnB": "control",
        "SalVentAttn": "salience_ventral_attention",
        "SalVentAttnA": "salience_ventral_attention",
        "SalVentAttnB": "salience_ventral_attention",
        "Limbic": "limbic",
        "LimbicA": "limbic",
        "LimbicB": "limbic",
        "Cont": "control",
        "ContA": "control",
        "ContB": "control",
        "ContC": "control",
        "Default": "default",
        "DefaultA": "default",
        "DefaultB": "default",
        "DefaultC": "default",
        "TempPar": "temporoparietal",
    }
    hierarchy = {
        "Visual": 0.05,
        "VisCent": 0.05,
        "VisPeri": 0.08,
        "SomMot": 0.10,
        "SomMotA": 0.10,
        "SomMotB": 0.12,
        "DorsAttn": 0.45,
        "DorsAttnA": 0.45,
        "DorsAttnB": 0.48,
        "SalVentAttn": 0.55,
        "SalVentAttnA": 0.55,
        "SalVentAttnB": 0.58,
        "Limbic": 0.65,
        "LimbicA": 0.65,
        "LimbicB": 0.68,
        "Cont": 0.75,
        "ContA": 0.75,
        "ContB": 0.78,
        "ContC": 0.80,
        "Default": 0.95,
        "DefaultA": 0.92,
        "DefaultB": 0.95,
        "DefaultC": 0.97,
        "TempPar": 0.82,
    }
    nodes: list[NodeMetadata] = []
    parcel_index = 1
    for network, count in network_counts.items():
        for network_index in range(1, count + 1):
            is_visual = network in {"Visual", "VisCent", "VisPeri"}
            is_somatomotor = network in {"SomMot", "SomMotA", "SomMotB"}
            is_sensory = is_visual or is_somatomotor
            is_transmodal = network.startswith("Default") or network.startswith("Cont") or network == "TempPar"
            nodes.append(
                NodeMetadata(
                    node_label=f"Schaefer{n_rois}_{network}_{network_index:03d}",
                    parcel_index=parcel_index,
                    yeo_network_label=network,
                    coarse_class=coarse_class[network],
                    hierarchy_value=hierarchy[network],
                    receptor_weight=SCHAEFER_YEO_PROXY_RECEPTOR_WEIGHTS.get(
                        network.removesuffix("A").removesuffix("B").removesuffix("C"),
                        0.65 if is_visual else 0.35 if is_somatomotor else 0.70,
                    ),
                    receptor_weight_source=PROXY_RECEPTOR_SOURCE,
                    visual_weight=1.0 if is_visual else 0.0,
                    sensory_weight=1.0 if is_sensory else 0.0,
                    somatomotor_weight=1.0 if is_somatomotor else 0.0,
                    transmodal_weight=1.0 if is_transmodal else 0.0,
                    metadata_source=f"schaefer_2018_yeo_{yeo_networks}_schema",
                )
            )
            parcel_index += 1
    return ParcellationSpec(
        parcellation_id=f"schaefer_{n_rois}_yeo_{yeo_networks}",
        description=f"Prepared Schaefer 2018 {n_rois}-parcel cortical target space labeled by Yeo {yeo_networks} networks.",
        node_metadata=tuple(nodes),
        atlas_metadata={
            "atlas": "Schaefer 2018",
            "n_rois": n_rois,
            "yeo_networks": yeo_networks,
            "resolution_mm": 2,
            "subcortical_status": "not_extracted_yet_thalamus_caudate_putamen_todo",
            "legacy_extraction": False,
            "status": "metadata_ready_extraction_not_run",
            "fetch_function": "nilearn.datasets.fetch_atlas_schaefer_2018",
        },
    )


def _schaefer_striatal_spec(n_rois: int, yeo_networks: int) -> ParcellationSpec:
    base = _schaefer_spec(n_rois, yeo_networks)
    nodes = list(base.node_metadata)
    nodes.extend(
        [
            NodeMetadata(
                node_label="HarvardOxford_thalamus_bilateral",
                parcel_index=n_rois + 1,
                yeo_network_label=None,
                coarse_class="thalamic_gateway",
                hierarchy_value=0.35,
                receptor_weight=0.50,
                receptor_weight_source=PROXY_RECEPTOR_SOURCE,
                thalamus_weight=1.0,
                metadata_source="harvard_oxford_subcortical_proxy",
            ),
            NodeMetadata(
                node_label="HarvardOxford_striatum_bilateral",
                parcel_index=n_rois + 2,
                yeo_network_label=None,
                coarse_class="striatal_basal_ganglia",
                hierarchy_value=0.25,
                receptor_weight=0.45,
                receptor_weight_source=PROXY_RECEPTOR_SOURCE,
                striatum_weight=1.0,
                metadata_source="harvard_oxford_subcortical_proxy",
            ),
        ]
    )
    return ParcellationSpec(
        parcellation_id=f"schaefer_{n_rois}_yeo_{yeo_networks}_striatal",
        description=(
            f"Schaefer 2018 {n_rois}-parcel cortical target space labeled by Yeo {yeo_networks} networks, "
            "augmented with bilateral Harvard-Oxford thalamus and striatum proxy parcels."
        ),
        node_metadata=tuple(nodes),
        atlas_metadata={
            **base.atlas_metadata,
            "node_count": len(nodes),
            "subcortical_status": "implemented_harvard_oxford_thalamus_striatum_proxy_parcels",
            "subcortical_atlas": "Harvard-Oxford subcortical maxprob thr25 2mm",
            "thalamus_labels": list(HARVARD_OXFORD_THALAMUS_LABELS),
            "striatum_labels": list(HARVARD_OXFORD_STRIATUM_LABELS),
            "status": "metadata_ready_extraction_not_run",
        },
    )


_PARCELLATION_BUILDERS = {
    "harvard_oxford_8": _legacy_harvard_oxford_8_spec,
    "schaefer_100_yeo_7": lambda: _schaefer_spec(100, 7),
    "schaefer_100_yeo_7_striatal": lambda: _schaefer_striatal_spec(100, 7),
    "schaefer_200_yeo_7": lambda: _schaefer_spec(200, 7),
    "schaefer_100_yeo_17": lambda: _schaefer_spec(100, 17),
    "schaefer_200_yeo_17": lambda: _schaefer_spec(200, 17),
}


def available_parcellations() -> tuple[str, ...]:
    return tuple(sorted(_PARCELLATION_BUILDERS))


def get_parcellation_spec(parcellation_id: str) -> ParcellationSpec:
    try:
        return _PARCELLATION_BUILDERS[parcellation_id]()
    except KeyError as error:
        available = ", ".join(available_parcellations())
        raise ValueError(f"Unknown parcellation '{parcellation_id}'. Available parcellations: {available}.") from error


def parcellation_output_dir(stage_2_dir: str | Path, parcellation_id: str) -> Path:
    return Path(stage_2_dir) / "parcellations" / parcellation_id


def write_parcellation_metadata(spec: ParcellationSpec, stage_2_dir: str | Path) -> Path:
    output_dir = parcellation_output_dir(stage_2_dir, spec.parcellation_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "node_metadata.json").write_text(
        json.dumps(spec.node_metadata_payload(), indent=2),
        encoding="utf-8",
    )
    (output_dir / "atlas_metadata.json").write_text(
        json.dumps(
            {
                "parcellation_id": spec.parcellation_id,
                **spec.atlas_metadata,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_dir


def prepare_parcellation_outputs(
    stage_2_dir: str | Path,
    parcellation_id: str,
    dry_run: bool = True,
) -> Path:
    spec = get_parcellation_spec(parcellation_id)
    output_dir = write_parcellation_metadata(spec, stage_2_dir)
    status = "dry_run_metadata_only" if dry_run else "metadata_ready_extraction_not_run"
    plan = {
        "parcellation_id": parcellation_id,
        "status": status,
        "output_dir": str(output_dir),
        "next_commands": [
            (
                "python -c \"from nilearn import datasets; "
                f"datasets.fetch_atlas_schaefer_2018(n_rois={spec.atlas_metadata.get('n_rois', 100)}, "
                f"yeo_networks={spec.atlas_metadata.get('yeo_networks', 7)}, resolution_mm=2)\""
            ),
            f"uv run python scripts/run_parcellation_sensitivity.py --parcellation {parcellation_id}",
        ],
        "notes": [
            "Dry run writes metadata only and does not overwrite legacy Stage 2 targets.",
            "Full Schaefer/Yeo extraction should be run only when atlas/data access and runtime are acceptable.",
            "The schaefer_100_yeo_7_striatal target adds bilateral Harvard-Oxford thalamus and striatum proxy parcels.",
        ],
    }
    (output_dir / "dry_run_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return output_dir


def _parse_schaefer_id(parcellation_id: str) -> tuple[int, int]:
    match = SCHAEFER_ID_PATTERN.match(parcellation_id)
    if not match:
        raise ValueError(f"Parcellation '{parcellation_id}' is not a supported Schaefer/Yeo extraction target.")
    return int(match.group("n_rois")), int(match.group("yeo_networks"))


def _parse_schaefer_extraction_id(parcellation_id: str) -> tuple[int, int, bool]:
    match = SCHAEFER_ID_PATTERN.match(parcellation_id)
    if match:
        return int(match.group("n_rois")), int(match.group("yeo_networks")), False
    striatal_match = SCHAEFER_STRIATAL_ID_PATTERN.match(parcellation_id)
    if striatal_match:
        return int(striatal_match.group("n_rois")), int(striatal_match.group("yeo_networks")), True
    raise ValueError(f"Parcellation '{parcellation_id}' is not a supported Schaefer/Yeo extraction target.")


def _coerce_atlas_label(label: Any) -> str:
    if isinstance(label, bytes):
        return label.decode("utf-8")
    return str(label)


def _atlas_module_names(labels: Sequence[Any], n_rois: int) -> tuple[str, ...]:
    coerced = tuple(_coerce_atlas_label(label) for label in labels)
    if len(coerced) == n_rois + 1 and coerced[0].lower() in {"background", "0", "b'background'"}:
        coerced = coerced[1:]
    if len(coerced) > n_rois:
        coerced = coerced[-n_rois:]
    if len(coerced) != n_rois:
        return tuple(f"Schaefer{n_rois}_parcel_{index + 1:03d}" for index in range(n_rois))
    return coerced


def _read_schaefer_label_file(path: Path) -> tuple[str, ...]:
    labels: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            labels.append(parts[1])
    return tuple(labels)


def _complete_nilearn_part_file(path: Path) -> Path | None:
    part_path = Path(str(path) + ".part")
    if path.exists():
        return path
    if not part_path.exists():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(part_path, path)
    return path if path.exists() else None


def _load_cached_schaefer_files(
    nilearn_data_dir: str | Path,
    *,
    n_rois: int,
    yeo_networks: int,
) -> tuple[nib.Nifti1Image, tuple[str, ...], dict[str, Any]] | None:
    cache_root = Path(nilearn_data_dir) / "schaefer_2018"
    label_name = f"Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order.txt"
    image_name = f"Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order_FSLMNI152_2mm.nii.gz"
    candidate_label_paths = sorted(cache_root.rglob(label_name)) + [
        Path(str(path).removesuffix(".part")) for path in sorted(cache_root.rglob(label_name + ".part"))
    ]
    for label_path in candidate_label_paths:
        completed_label_path = _complete_nilearn_part_file(label_path)
        image_path = _complete_nilearn_part_file(label_path.with_name(image_name))
        if completed_label_path is None or image_path is None:
            continue
        labels = _read_schaefer_label_file(completed_label_path)
        if len(labels) != n_rois:
            continue
        return (
            cast(nib.Nifti1Image, nib.load(str(image_path))),
            labels,
            {
                "atlas": "Schaefer 2018",
                "n_rois": n_rois,
                "yeo_networks": yeo_networks,
                "resolution_mm": 2,
                "labels_count": len(labels),
                "maps_path": str(image_path),
                "labels_path": str(completed_label_path),
                "cache_status": "loaded_from_existing_nilearn_cache_file",
            },
        )
    return None


def _as_nifti_image(image_or_path: Any) -> nib.Nifti1Image:
    if isinstance(image_or_path, nib.Nifti1Image):
        return image_or_path
    return cast(nib.Nifti1Image, nib.load(str(image_or_path)))


def _load_harvard_oxford_subcortical_image(nilearn_data_dir: str | Path | None) -> tuple[nib.Nifti1Image, str]:
    cached_images = _load_cached_harvard_oxford_images(nilearn_data_dir)
    if cached_images is not None:
        return cached_images[1], "loaded_from_existing_nilearn_cache_file"
    fetch_data_dir = Path(nilearn_data_dir) if nilearn_data_dir is not None else None
    atlas = datasets.fetch_atlas_harvard_oxford(
        "sub-maxprob-thr25-2mm",
        data_dir=str(fetch_data_dir) if fetch_data_dir is not None else None,
    )
    return _as_nifti_image(atlas.maps), "fetched_with_nilearn"


def _augment_schaefer_with_subcortical_parcels(
    labels_img: nib.Nifti1Image,
    module_names: tuple[str, ...],
    metadata: dict[str, Any],
    *,
    nilearn_data_dir: str | Path | None,
) -> tuple[nib.Nifti1Image, tuple[str, ...], dict[str, Any]]:
    n_rois = len(module_names)
    subcortical_img, subcortical_cache_status = _load_harvard_oxford_subcortical_image(nilearn_data_dir)
    schaefer_data = np.asarray(labels_img.dataobj, dtype=np.int16)
    subcortical_data = np.asarray(subcortical_img.dataobj)
    if schaefer_data.shape != subcortical_data.shape:
        raise ValueError(
            "Schaefer and Harvard-Oxford images have different shapes: "
            f"{schaefer_data.shape} vs {subcortical_data.shape}."
        )
    if not np.allclose(labels_img.affine, subcortical_img.affine):
        raise ValueError("Schaefer and Harvard-Oxford images have different affines.")

    combined = schaefer_data.copy()
    combined[np.isin(subcortical_data, HARVARD_OXFORD_THALAMUS_LABELS)] = n_rois + 1
    combined[np.isin(subcortical_data, HARVARD_OXFORD_STRIATUM_LABELS)] = n_rois + 2
    header = labels_img.header.copy()
    header.set_data_dtype(np.int16)
    combined_img = nib.Nifti1Image(combined, labels_img.affine, header)
    augmented_names = module_names + (
        "HarvardOxford_thalamus_bilateral",
        "HarvardOxford_striatum_bilateral",
    )
    augmented_metadata = {
        **metadata,
        "labels_count": len(augmented_names),
        "subcortical_status": "implemented_harvard_oxford_thalamus_striatum_proxy_parcels",
        "subcortical_cache_status": subcortical_cache_status,
        "thalamus_labels": list(HARVARD_OXFORD_THALAMUS_LABELS),
        "striatum_labels": list(HARVARD_OXFORD_STRIATUM_LABELS),
        "subcortical_guardrail": (
            "Bilateral Harvard-Oxford thalamus and striatum parcels are proxy parcels for benchmark testing; "
            "they are not nucleus-level or PET receptor-resolved regions."
        ),
    }
    return combined_img, augmented_names, augmented_metadata


def fetch_schaefer_labels_image(
    parcellation_id: str,
    *,
    nilearn_data_dir: str | Path | None = None,
) -> tuple[nib.Nifti1Image, tuple[str, ...], dict[str, Any]]:
    n_rois, yeo_networks, include_striatum = _parse_schaefer_extraction_id(parcellation_id)
    if nilearn_data_dir is not None:
        cached = _load_cached_schaefer_files(nilearn_data_dir, n_rois=n_rois, yeo_networks=yeo_networks)
        if cached is not None:
            if include_striatum:
                return _augment_schaefer_with_subcortical_parcels(
                    *cached,
                    nilearn_data_dir=nilearn_data_dir,
                )
            return cached
    try:
        atlas = datasets.fetch_atlas_schaefer_2018(
            n_rois=n_rois,
            yeo_networks=yeo_networks,
            resolution_mm=2,
            data_dir=str(nilearn_data_dir) if nilearn_data_dir is not None else None,
            verbose=0,
        )
    except Exception:
        if nilearn_data_dir is not None:
            cached = _load_cached_schaefer_files(nilearn_data_dir, n_rois=n_rois, yeo_networks=yeo_networks)
            if cached is not None:
                labels_img, module_names, metadata = cached
                metadata["cache_status"] = "loaded_from_partial_nilearn_cache_after_fetch_error"
                if include_striatum:
                    return _augment_schaefer_with_subcortical_parcels(
                        labels_img,
                        module_names,
                        metadata,
                        nilearn_data_dir=nilearn_data_dir,
                    )
                return labels_img, module_names, metadata
        raise
    labels_img = _as_nifti_image(atlas.maps)
    module_names = _atlas_module_names(atlas.labels, n_rois)
    metadata = {
        "atlas": "Schaefer 2018",
        "n_rois": n_rois,
        "yeo_networks": yeo_networks,
        "resolution_mm": 2,
        "labels_count": len(module_names),
        "maps_path": str(atlas.maps),
    }
    if include_striatum:
        return _augment_schaefer_with_subcortical_parcels(
            labels_img,
            module_names,
            metadata,
            nilearn_data_dir=nilearn_data_dir,
        )
    return labels_img, module_names, metadata


def _bold_path(dataset_root: Path, subject: str, session: str, run: str) -> Path:
    return dataset_root / subject / session / "func" / f"{subject}_{session}_task-rest_{run}_bold.nii.gz"


def _available_subjects(dataset_root: Path, selected_runs: tuple[str, ...]) -> list[str]:
    subjects: list[str] = []
    for subject_dir in sorted(dataset_root.glob("sub-*")):
        if not subject_dir.is_dir():
            continue
        subject = subject_dir.name
        has_all = all(
            _bold_path(dataset_root, subject, session, run).exists()
            for session in DS003059_SESSIONS
            for run in selected_runs
        )
        if has_all:
            subjects.append(subject)
    return subjects


def _standardize_columns(time_series: np.ndarray) -> np.ndarray:
    array = np.asarray(time_series, dtype=float)
    centered = array - np.mean(array, axis=0, keepdims=True)
    std = np.std(centered, axis=0, ddof=1, keepdims=True) if len(centered) > 1 else np.ones((1, centered.shape[1]))
    safe_std = np.where(std > 1e-8, std, 1.0)
    return cast(np.ndarray, (centered / safe_std).astype(float, copy=False))


def extract_schaefer_time_series(
    bold_path: str | Path,
    labels_img: nib.Nifti1Image,
) -> np.ndarray:
    masker = NiftiLabelsMasker(
        labels_img=labels_img,
        standardize="zscore_sample",
        verbose=0,
    )
    time_series = np.asarray(masker.fit_transform(str(bold_path)), dtype=float)
    return _standardize_columns(np.nan_to_num(time_series, nan=0.0, posinf=0.0, neginf=0.0))


def _write_minimal_viewer(
    *,
    output_dir: Path,
    records: list[dict[str, Any]],
    module_names: tuple[str, ...],
) -> Path:
    viewer_root = output_dir / "empirical_viewer"
    subject_views_dir = viewer_root / "subject_views"
    subject_views_dir.mkdir(parents=True, exist_ok=True)
    subjects = sorted({str(record["subject"]) for record in records})
    runs = sorted({str(record["run"]) for record in records})
    by_key = {
        (str(record["subject"]), str(record["run"]), str(record["session"])): record
        for record in records
    }
    subject_index: dict[str, list[str]] = {}
    paired_count = 0
    for subject in subjects:
        subject_index[subject] = []
        for run in runs:
            placebo = by_key.get((subject, run, "ses-PLCB"))
            lsd = by_key.get((subject, run, "ses-LSD"))
            if placebo is None or lsd is None:
                continue
            subject_index[subject].append(run)
            paired_count += 1
            detail = {
                "subject": subject,
                "run": run,
                "conditions": {
                    "ses-PLCB": {
                        "module_time_series": np.load(str(placebo["time_series_path"])).astype(float).tolist(),
                    },
                    "ses-LSD": {
                        "module_time_series": np.load(str(lsd["time_series_path"])).astype(float).tolist(),
                    },
                },
            }
            (subject_views_dir / f"{subject}_{run}.json").write_text(json.dumps(detail), encoding="utf-8")
    group_overview: dict[str, Any] = {
        "subjects": subjects,
        "runs": runs,
        "default_subject": subjects[0] if subjects else None,
        "module_names": list(module_names),
        "paired_subject_count": len([subject for subject, run_list in subject_index.items() if run_list]),
        "paired_record_count": paired_count,
        "conditions": {},
        "gallery": [],
        "viewer_note": "Minimal parcellation viewer for mechanism-proxy ranking; it intentionally omits raw-image previews.",
    }
    (viewer_root / "group_overview.json").write_text(json.dumps(group_overview, indent=2), encoding="utf-8")
    (viewer_root / "subject_index.json").write_text(json.dumps(subject_index, indent=2), encoding="utf-8")
    return viewer_root


def extract_schaefer_empirical_viewer(
    *,
    dataset_dir: str | Path,
    stage_2_dir: str | Path,
    parcellation_id: str,
    runs: Sequence[str] | None = None,
    include_music: bool = False,
    subjects: Sequence[str] | None = None,
    max_subjects: int | None = None,
    nilearn_data_dir: str | Path | None = None,
    force: bool = False,
    control_null_count: int = 16,
) -> dict[str, Any]:
    spec = get_parcellation_spec(parcellation_id)
    _parse_schaefer_extraction_id(parcellation_id)
    dataset_root = Path(dataset_dir)
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_root}")
    selected_runs = normalize_ds003059_runs(runs, include_music=include_music)
    stage_2_path = Path(stage_2_dir)
    output_dir = write_parcellation_metadata(spec, stage_2_path)
    summary_path = output_dir / "parcellation_extraction_summary.json"
    ranking_output_dir = stage_2_path.parent / "parcellation_sensitivity" / parcellation_id
    if summary_path.exists() and not force:
        return cast(dict[str, Any], json.loads(summary_path.read_text(encoding="utf-8")))

    atlas_cache_dir = Path(nilearn_data_dir) if nilearn_data_dir is not None else stage_2_path.parent / "nilearn_data"
    labels_img, module_names, atlas_metadata = fetch_schaefer_labels_image(
        parcellation_id,
        nilearn_data_dir=atlas_cache_dir,
    )
    selected_subjects = list(subjects) if subjects is not None else _available_subjects(dataset_root, selected_runs)
    selected_subjects = sorted(dict.fromkeys(selected_subjects))
    if max_subjects is not None:
        selected_subjects = selected_subjects[:max_subjects]
    if not selected_subjects:
        raise ValueError("No subjects with paired ses-PLCB/ses-LSD BOLD files were found for the selected runs.")

    series_dir = output_dir / "module_time_series"
    series_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for subject in selected_subjects:
        for session in DS003059_SESSIONS:
            for run in selected_runs:
                bold = _bold_path(dataset_root, subject, session, run)
                if not bold.exists():
                    continue
                time_series = extract_schaefer_time_series(bold, labels_img)
                series_path = series_dir / f"{subject}_{session}_{run}_{parcellation_id}.npy"
                np.save(series_path, time_series)
                records.append(
                    {
                        "subject": subject,
                        "session": session,
                        "run": run,
                        "relative_path": bold.relative_to(dataset_root).as_posix(),
                        "timepoints": int(time_series.shape[0]),
                        "node_count": int(time_series.shape[1]),
                        "time_series_path": series_path.as_posix(),
                    }
                )

    viewer_root = _write_minimal_viewer(output_dir=output_dir, records=records, module_names=module_names)
    ranking_summary = write_dynamic_mechanism_summary(
        viewer_root,
        ranking_output_dir,
        network_control_kwargs={"random_null_count": control_null_count},
    )
    extraction_summary = {
        "schema_version": 1,
        "analysis_status": "implemented_schaefer_empirical_viewer",
        "parcellation_id": parcellation_id,
        "dataset": "ds003059 LSD/placebo local BOLD files",
        "dataset_dir": str(dataset_root),
        "output_dir": str(output_dir),
        "viewer_root": str(viewer_root),
        "runs": list(selected_runs),
        "include_music": include_music,
        "subjects": selected_subjects,
        "subject_count": len(selected_subjects),
        "record_count": len(records),
        "module_count": len(module_names),
        "atlas_metadata": atlas_metadata,
        "ranking_summary_path": str((ranking_output_dir / "summary.json").as_posix()),
        "ranking_pair_count": ranking_summary.get("pair_count", 0),
        "ranking_top_layer": ranking_summary.get("mechanism_ranking", [{}])[0].get("layer"),
        "control_null_count": control_null_count,
        "guardrail": (
            "This is parcellation sensitivity for local ds003059 LSD data. It does not add psilocybin, HCP structural connectivity, or PET receptor maps."
        ),
    }
    summary_path.write_text(json.dumps(extraction_summary, indent=2), encoding="utf-8")
    return extraction_summary
