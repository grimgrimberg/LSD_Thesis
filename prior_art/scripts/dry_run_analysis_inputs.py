#!/usr/bin/env python3
"""Dry-run prior-art analysis input checks.

This script only checks configured paths and expected inputs. It does not
download datasets, run neuroimaging pipelines, modify cloned repositories, or
execute upstream analysis code.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PathConfig:
    bids_root: Path
    derivatives_root: Path
    parcellations_root: Path
    receptor_maps_root: Path
    structural_connectome_root: Path
    output_root: Path


FAMILIES: dict[str, dict[str, list[str]]] = {
    "ising_temperature_and_algorithmic_complexity": {
        "required": ["derivatives_root"],
        "outputs": ["output_root"],
        "notes": ["Requires condition-specific BOLD time series and a binarization rule."],
    },
    "entropy_copbet": {
        "required": ["derivatives_root", "parcellations_root"],
        "outputs": ["output_root"],
        "notes": ["Requires ROI or voxel data in the format expected by CopBET scripts."],
    },
    "energy_landscape_network_control": {
        "required": ["derivatives_root", "structural_connectome_root"],
        "outputs": ["output_root"],
        "notes": ["Requires brain-state definitions and a structural connectome."],
    },
    "react_receptor_connectivity": {
        "required": ["derivatives_root", "receptor_maps_root"],
        "outputs": ["output_root"],
        "notes": ["Requires PET/receptor templates and an FSL-compatible environment."],
    },
    "neuroreceptor_eigenmodes": {
        "required": ["receptor_maps_root", "parcellations_root"],
        "outputs": ["output_root"],
        "notes": ["Requires receptor density maps aligned to the chosen cortical surface or parcellation."],
    },
    "dynamic_integration_segregation": {
        "required": ["derivatives_root"],
        "outputs": ["output_root"],
        "notes": ["Requires time-varying functional connectivity choices and MATLAB/BCT for upstream code."],
    },
    "cortical_gradients_brainspace": {
        "required": ["derivatives_root", "parcellations_root"],
        "outputs": ["output_root"],
        "notes": ["Requires functional connectivity matrices and gradient alignment choices."],
    },
    "lsd_music_brainstates": {
        "required": ["derivatives_root", "parcellations_root"],
        "outputs": ["output_root"],
        "notes": ["Run-02/music claims are gated until local music-run exclusions and artifacts are ready."],
    },
    "gnw_iit_consciousness": {
        "required": ["derivatives_root"],
        "outputs": ["output_root"],
        "notes": ["Requires cross-dataset feature alignment if sleep/sedation comparisons are reproduced."],
    },
    "mesoscale_reho": {
        "required": ["bids_root", "derivatives_root"],
        "outputs": ["output_root"],
        "notes": ["Requires AFNI/JASP/MATLAB method reconstruction; public scripts are not verified."],
    },
    "traveling_waves": {
        "required": ["derivatives_root"],
        "outputs": ["output_root"],
        "notes": ["neuromaps is a supporting dependency, not verified full analysis code."],
    },
    "dlpfc_granger_causality": {
        "required": ["derivatives_root"],
        "outputs": ["output_root"],
        "notes": ["Author-only code; fMRI/MEG fusion requirements remain unresolved."],
    },
    "translational_neuromodeling_teaching": {
        "required": ["bids_root"],
        "outputs": ["output_root"],
        "notes": ["Secondary teaching resource; use as setup reference, not as a primary prior-art claim."],
    },
}


def default_path(env_name: str, relative: str) -> Path:
    value = os.environ.get(env_name)
    if value:
        return Path(value).expanduser().resolve()
    return (REPO_ROOT / relative).resolve()


def build_config(args: argparse.Namespace) -> PathConfig:
    return PathConfig(
        bids_root=Path(args.bids_root).resolve() if args.bids_root else default_path("DS003059_BIDS_ROOT", "data/ds003059"),
        derivatives_root=Path(args.derivatives_root).resolve()
        if args.derivatives_root
        else default_path("DS003059_DERIVATIVES_ROOT", "results/stage_2"),
        parcellations_root=Path(args.parcellations_root).resolve()
        if args.parcellations_root
        else default_path("PARCELLATIONS_ROOT", "results/stage_2/parcellations"),
        receptor_maps_root=Path(args.receptor_maps_root).resolve()
        if args.receptor_maps_root
        else default_path("RECEPTOR_MAPS_ROOT", "results/cortical_maps/neuromaps_annotations"),
        structural_connectome_root=Path(args.structural_connectome_root).resolve()
        if args.structural_connectome_root
        else default_path("STRUCTURAL_CONNECTOME_ROOT", "results/structural_connectome"),
        output_root=Path(args.output_root).resolve() if args.output_root else default_path("PRIOR_ART_OUTPUT_ROOT", "results/prior_art"),
    )


def print_family_check(family: str, config: PathConfig) -> bool:
    info = FAMILIES[family]
    print(f"\n## {family}")
    all_present = True
    for field_name in info["required"]:
        path = getattr(config, field_name)
        exists = path.exists()
        all_present = all_present and exists
        status = "present" if exists else "missing"
        print(f"- {field_name}: {path} [{status}]")
    for field_name in info.get("outputs", []):
        path = getattr(config, field_name)
        status = "present" if path.exists() else "missing, creatable"
        print(f"- output_target {field_name}: {path} [{status}]")
    for note in info["notes"]:
        print(f"- note: {note}")
    return all_present


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=["all", *sorted(FAMILIES)], help="Analysis family to dry-run")
    parser.add_argument("--bids-root")
    parser.add_argument("--derivatives-root")
    parser.add_argument("--parcellations-root")
    parser.add_argument("--receptor-maps-root")
    parser.add_argument("--structural-connectome-root")
    parser.add_argument("--output-root")
    parser.add_argument("--strict", action="store_true", help="Exit 2 if any required path is missing")
    args = parser.parse_args()

    config = build_config(args)
    families = sorted(FAMILIES) if args.family == "all" else [args.family]
    results = [print_family_check(family, config) for family in families]

    if args.strict and not all(results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
