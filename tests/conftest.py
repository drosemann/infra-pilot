import pytest
import os

@pytest.fixture(autouse=True, scope="session")
def _set_test_env():
    # Ensure environment has a predictable default for local runs
    os.environ.setdefault("TEST_ENV", os.environ.get("TEST_ENV", "local"))
    os.environ.setdefault("PROVIDER_MOCK_API_URL", os.environ.get("PROVIDER_MOCK_API_URL", "http://localhost:8080/mock"))
    yield
