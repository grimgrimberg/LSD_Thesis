import json
from pathlib import Path
from uuid import uuid4

import pytest

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.data.parcellations import (
    get_parcellation_spec,
    parcellation_output_dir,
    prepare_parcellation_outputs,
    write_parcellation_metadata,
)


def test_harvard_oxford_8_spec_preserves_legacy_nodes() -> None:
    spec = get_parcellation_spec("harvard_oxford_8")

    assert spec.parcellation_id == "harvard_oxford_8"
    assert tuple(node.node_label for node in spec.node_metadata) == MODULE_NAMES
    assert spec.atlas_metadata["legacy_extraction"] is True
    assert spec.node_metadata[0].coarse_class == "visual"


def test_schaefer_100_yeo_7_spec_has_valid_node_metadata_schema() -> None:
    spec = get_parcellation_spec("schaefer_100_yeo_7")

    assert spec.node_count == 100
    assert spec.atlas_metadata["atlas"] == "Schaefer 2018"
    assert spec.atlas_metadata["subcortical_status"].startswith("not_extracted")
    assert {node.yeo_network_label for node in spec.node_metadata} == {
        "Visual",
        "SomMot",
        "DorsAttn",
        "SalVentAttn",
        "Limbic",
        "Cont",
        "Default",
    }
    visual_node = spec.node_metadata[0]
    default_node = next(node for node in spec.node_metadata if node.yeo_network_label == "Default")
    assert visual_node.visual_weight == 1.0
    assert default_node.transmodal_weight == 1.0
    assert all(node.receptor_weight_source == "coarse_literature_proxy_not_pet_map" for node in spec.node_metadata)
    assert default_node.receptor_weight > visual_node.receptor_weight > 0.0


def test_schaefer_grid_specs_cover_100_200_and_yeo_7_17() -> None:
    expected = {
        "schaefer_100_yeo_7": (100, 7),
        "schaefer_200_yeo_7": (200, 7),
        "schaefer_100_yeo_17": (100, 17),
        "schaefer_200_yeo_17": (200, 17),
    }

    for parcellation_id, (node_count, yeo_networks) in expected.items():
        spec = get_parcellation_spec(parcellation_id)

        assert spec.node_count == node_count
        assert spec.atlas_metadata["n_rois"] == node_count
        assert spec.atlas_metadata["yeo_networks"] == yeo_networks
        assert spec.atlas_metadata["fetch_function"] == "nilearn.datasets.fetch_atlas_schaefer_2018"


def test_unknown_parcellation_fails_clearly() -> None:
    with pytest.raises(ValueError, match="Unknown parcellation 'missing'. Available parcellations:"):
        get_parcellation_spec("missing")


def _test_root() -> Path:
    root = Path("codex_logs") / "parcellation_tests" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_parcellation_output_dir_includes_parcellation_name() -> None:
    root = _test_root()
    output = parcellation_output_dir(root / "stage_2", "schaefer_100_yeo_7")

    assert output == root / "stage_2" / "parcellations" / "schaefer_100_yeo_7"


def test_write_parcellation_metadata_does_not_overwrite_legacy_stage_2_targets() -> None:
    stage_2 = _test_root() / "stage_2"
    stage_2.mkdir()
    legacy_target = stage_2 / "empirical_sober_targets.yaml"
    legacy_target.write_text("legacy: keep\n", encoding="utf-8")

    output_dir = write_parcellation_metadata(get_parcellation_spec("schaefer_100_yeo_7"), stage_2)

    assert legacy_target.read_text(encoding="utf-8") == "legacy: keep\n"
    assert output_dir == stage_2 / "parcellations" / "schaefer_100_yeo_7"
    assert (output_dir / "node_metadata.json").exists()
    assert (output_dir / "atlas_metadata.json").exists()


def test_prepare_parcellation_outputs_dry_run_writes_ready_to_run_plan() -> None:
    output_dir = prepare_parcellation_outputs(
        stage_2_dir=_test_root() / "stage_2",
        parcellation_id="schaefer_100_yeo_7",
        dry_run=True,
    )

    plan = json.loads((output_dir / "dry_run_plan.json").read_text(encoding="utf-8"))
    node_metadata = json.loads((output_dir / "node_metadata.json").read_text(encoding="utf-8"))

    assert plan["parcellation_id"] == "schaefer_100_yeo_7"
    assert plan["status"] == "dry_run_metadata_only"
    assert "fetch_atlas_schaefer_2018" in plan["next_commands"][0]
    assert len(node_metadata["nodes"]) == 100
    assert not (output_dir / "empirical_run_summaries.json").exists()
