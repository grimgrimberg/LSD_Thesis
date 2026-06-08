import numpy as np

from lsd_thesis.metrics import safe_correlation_matrix


def test_safe_correlation_matrix():
    """Test the basic correlation matrix metric."""
    time_series = np.random.randn(100, 10) # 100 timepoints, 10 regions
    fc_matrix = safe_correlation_matrix(time_series)

    assert fc_matrix.shape == (10, 10)
    assert np.allclose(np.diag(fc_matrix), 1.0)
