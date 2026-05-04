import pytest


@pytest.mark.smoke
def test_basic_smoke():
    # Lightweight sanity check for test environment; no network I/O
    assert True
