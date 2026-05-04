import pytest
from infra.naming import resolver


@pytest.mark.unit
def test_unknown_token_fallback():
    # Unknown tokens should fall back to their original value
    assert resolver.resolve_provider("UNKNOWN_TOKEN") == "UNKNOWN_TOKEN"
