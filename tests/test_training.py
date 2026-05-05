import numpy as np

from lsd_thesis.training import slice_windows


def test_slice_windows_builds_overlapping_fixed_length_windows() -> None:
    time_series = np.arange(30, dtype=float).reshape(10, 3)

    windows = slice_windows(time_series, window_length=4, stride=3)

    assert windows.shape == (3, 4, 3)
    assert np.array_equal(windows[0], time_series[0:4])
    assert np.array_equal(windows[1], time_series[3:7])
    assert np.array_equal(windows[2], time_series[6:10])
