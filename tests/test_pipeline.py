from unittest.mock import patch


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
