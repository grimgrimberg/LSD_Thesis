from lsd_thesis.core import MODULE_NAMES


def test_macro_module_names_are_exposed() -> None:
    assert MODULE_NAMES == (
        "visual",
        "auditory",
        "salience",
        "default_mode",
        "executive_frontoparietal",
        "limbic_affective",
        "thalamic_gateway",
        "sensorimotor",
    )
