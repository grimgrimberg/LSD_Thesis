"""Tests for error paths and edge cases found during audit."""

import nibabel as nib
import numpy as np
import pytest
from pydantic import ValidationError

from lsd_thesis.core import SimulationSettings
from lsd_thesis.data import ds003059


def test_burn_in_equal_to_steps_raises_validation_error() -> None:
    with pytest.raises(ValidationError, match="burn_in"):
        SimulationSettings(dt=0.05, steps=200, burn_in=200, seed=1)


def test_burn_in_greater_than_steps_raises_validation_error() -> None:
    with pytest.raises(ValidationError, match="burn_in"):
        SimulationSettings(dt=0.05, steps=100, burn_in=300, seed=1)


def test_burn_in_zero_is_valid() -> None:
    settings = SimulationSettings(dt=0.05, steps=200, burn_in=0, seed=1)
    assert settings.burn_in == 0


def test_burn_in_less_than_steps_is_valid() -> None:
    settings = SimulationSettings(dt=0.05, steps=200, burn_in=100, seed=1)
    assert settings.burn_in == 100


def test_extract_module_time_series_retries_transient_oserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    source_image = nib.Nifti1Image(np.zeros((2, 2, 2, 2), dtype=np.int16), affine=np.eye(4))

    class FlakyMasker:
        def __init__(self, *, labels_img: object, standardize: str) -> None:
            assert labels_img is not None
            assert standardize == "zscore_sample"

        def fit_transform(self, run_path: str) -> np.ndarray:
            calls["count"] += 1
            if calls["count"] == 1:
                raise OSError(22, "Invalid argument")
            return np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=float)

    monkeypatch.setattr(ds003059.nib, "load", lambda _: source_image)
    monkeypatch.setattr(ds003059, "NiftiLabelsMasker", FlakyMasker)

    result = ds003059.extract_module_time_series("dummy.nii.gz", labels_img=object())

    assert result.shape == (2, 2)
    assert calls["count"] == 2


def test_extract_module_time_series_falls_back_after_three_oserrors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    source_image = nib.Nifti1Image(
        np.asarray(
            [
                [[[1.0, 2.0, 3.0]]],
                [[[4.0, 5.0, 6.0]]],
            ],
            dtype=float,
        ),
        affine=np.eye(4),
    )
    labels_image = nib.Nifti1Image(
        np.asarray(
            [
                [[1]],
                [[2]],
            ],
            dtype=np.int16,
        ),
        affine=np.eye(4),
    )

    class BrokenMasker:
        def __init__(self, *, labels_img: object, standardize: str) -> None:
            assert labels_img is labels_image
            assert standardize == "zscore_sample"

        def fit_transform(self, run_path: str) -> np.ndarray:
            calls["count"] += 1
            raise OSError(22, "Invalid argument")

    monkeypatch.setattr(ds003059.nib, "load", lambda _: source_image)
    monkeypatch.setattr(ds003059, "_build_macro_module_labels_image", lambda: labels_image)
    monkeypatch.setattr(ds003059, "NiftiLabelsMasker", BrokenMasker)

    result = ds003059.extract_module_time_series("dummy.nii.gz")

    assert result.shape == (3, 2)
    assert np.allclose(result, np.asarray([[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]]))
    assert calls["count"] == 3


def test_extract_module_time_series_retries_transient_file_not_found_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    source_image = nib.Nifti1Image(np.zeros((2, 2, 2, 2), dtype=np.int16), affine=np.eye(4))

    class FlakyMasker:
        def __init__(self, *, labels_img: object, standardize: str) -> None:
            assert labels_img is not None
            assert standardize == "zscore_sample"

        def fit_transform(self, run_path: str) -> np.ndarray:
            calls["count"] += 1
            if calls["count"] == 1:
                raise ValueError(f"File not found: '{run_path}'")
            return np.asarray([[5.0, 6.0], [7.0, 8.0]], dtype=float)

    monkeypatch.setattr(ds003059.nib, "load", lambda _: source_image)
    monkeypatch.setattr(ds003059, "NiftiLabelsMasker", FlakyMasker)

    result = ds003059.extract_module_time_series("dummy.nii.gz", labels_img=object())

    assert result.shape == (2, 2)
    assert calls["count"] == 2


def test_extract_module_time_series_passes_loaded_image_to_masker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_image = nib.Nifti1Image(np.zeros((2, 2, 2, 2), dtype=np.int16), affine=np.eye(4))

    class InspectingMasker:
        def __init__(self, *, labels_img: object, standardize: str) -> None:
            assert labels_img is not None
            assert standardize == "zscore_sample"

        def fit_transform(self, run_input: object) -> np.ndarray:
            assert isinstance(run_input, nib.Nifti1Image)
            return np.asarray([[1.0, 2.0]], dtype=float)

    monkeypatch.setattr(ds003059.nib, "load", lambda _: source_image)
    monkeypatch.setattr(ds003059, "NiftiLabelsMasker", InspectingMasker)

    result = ds003059.extract_module_time_series("dummy.nii.gz", labels_img=object())

    assert result.shape == (1, 2)


def test_extract_module_time_series_falls_back_to_manual_label_average(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_image = nib.Nifti1Image(
        np.asarray(
            [
                [[[1.0, 2.0, 3.0]]],
                [[[4.0, 5.0, 6.0]]],
            ],
            dtype=float,
        ),
        affine=np.eye(4),
    )
    labels_image = nib.Nifti1Image(
        np.asarray(
            [
                [[1]],
                [[2]],
            ],
            dtype=np.int16,
        ),
        affine=np.eye(4),
    )

    class BrokenMasker:
        def __init__(self, *, labels_img: object, standardize: str) -> None:
            assert labels_img is labels_image
            assert standardize == "zscore_sample"

        def fit_transform(self, run_input: object) -> np.ndarray:
            raise OSError(22, "Invalid argument")

    monkeypatch.setattr(ds003059.nib, "load", lambda _: source_image)
    monkeypatch.setattr(ds003059, "NiftiLabelsMasker", BrokenMasker)

    result = ds003059.extract_module_time_series("dummy.nii.gz", labels_img=labels_image)

    assert result.shape == (3, 2)
    assert np.allclose(result, np.asarray([[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]]))
