from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class OpenNeuroSubsetSpec(BaseModel):
    dataset_id: str
    version: str
    subject: str
    include_paths: tuple[str, ...]
    notes: tuple[str, ...]


def ds003059_subset_spec(subject: str = "sub-001") -> OpenNeuroSubsetSpec:
    include_paths = (
        "dataset_description.json",
        "README",
        "CHANGES",
        f"{subject}/ses-LSD/func/{subject}_ses-LSD_task-rest_bold.json",
        f"{subject}/ses-LSD/func/{subject}_ses-LSD_task-rest_run-01_bold.nii.gz",
        f"{subject}/ses-LSD/func/{subject}_ses-LSD_task-rest_run-03_bold.nii.gz",
        f"{subject}/ses-PLCB/func/{subject}_ses-PLCB_task-rest_bold.json",
        f"{subject}/ses-PLCB/func/{subject}_ses-PLCB_task-rest_run-01_bold.nii.gz",
        f"{subject}/ses-PLCB/func/{subject}_ses-PLCB_task-rest_run-03_bold.nii.gz",
        f"{subject}/anat/{subject}_T1w.nii.gz",
    )
    notes = (
        "OpenNeuro ds003059 v1.0.0 is a derivative dataset.",
        "run-01 and run-03 are resting-state runs; run-02 is music and excluded from the MVP subset.",
        "The default MVP path is summary-first, but these include paths define the smallest useful download slice.",
    )
    return OpenNeuroSubsetSpec(
        dataset_id="ds003059",
        version="1.0.0",
        subject=subject,
        include_paths=include_paths,
        notes=notes,
    )


def build_openneuro_download_command(spec: OpenNeuroSubsetSpec, target_dir: str | Path) -> str:
    include_flags = " ".join(f"--include {path}" for path in spec.include_paths)
    return (
        "uvx openneuro-py@latest download "
        f"--dataset={spec.dataset_id} "
        f"--tag={spec.version} "
        f"--target-dir {Path(target_dir)} "
        f"{include_flags}"
    )

