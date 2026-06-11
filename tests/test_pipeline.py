from unittest.mock import patch

import pytest


def test_pipeline_instantiation():
    from scripts.run_pipeline import SurrogatePipeline
    pipeline = SurrogatePipeline(model_family="bistable")

    assert pipeline.model_family == "bistable"
    assert "stage1" in pipeline.stages
    assert "stage4" in pipeline.stages

@patch("scripts.run_pipeline.SurrogatePipeline._run_stage1")
def test_pipeline_run_stage1(mock_run_stage1):
    from scripts.run_pipeline import SurrogatePipeline
    pipeline = SurrogatePipeline(model_family="bistable")
    pipeline.run_stage("stage1")

    mock_run_stage1.assert_called_once()

def test_dashboard_runner():
    from scripts.run_pipeline import DashboardRunner
    assert hasattr(DashboardRunner, "launch")


def test_documented_pipeline_commands_remain_parser_choices():
    from scripts.run_pipeline import build_parser

    parser = build_parser()

    for command in (
        "run-everything",
        "run-everything-serve",
        "generate-empirical-targets",
        "stage-2b-target-validation",
        "validate-subject-split",
        "run-stage-5",
        "run-rgg-fit",
        "run-literature-fit",
    ):
        assert parser.parse_args([command]).command == command


def test_resolve_command_for_run_everything():
    from scripts.run_pipeline import PIPELINE_STAGES, resolve_command

    assert resolve_command("run-everything") == (PIPELINE_STAGES, False)
    assert resolve_command("run-everything-serve") == (PIPELINE_STAGES, True)


def test_pipeline_rejects_unwired_model_family():
    from scripts.run_pipeline import SurrogatePipeline

    with pytest.raises(ValueError, match="bistable baseline"):
        SurrogatePipeline(model_family="receptor_gradient_neural_mass")
