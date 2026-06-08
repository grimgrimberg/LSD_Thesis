
def test_dynamic_mechanism_imports():
    """Ensure the refactored dynamic_mechanism sub-package imports correctly."""
    import lsd_thesis.dynamic_mechanism.connectivity
    import lsd_thesis.dynamic_mechanism.core
    import lsd_thesis.dynamic_mechanism.hierarchy
    import lsd_thesis.dynamic_mechanism.priors
    import lsd_thesis.dynamic_mechanism.repertoire
    import lsd_thesis.dynamic_mechanism.stats
    import lsd_thesis.dynamic_mechanism.transitions

    assert hasattr(lsd_thesis.dynamic_mechanism.core, "__name__")
