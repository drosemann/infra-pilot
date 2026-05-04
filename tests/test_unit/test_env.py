import pytest
import os

from infra.naming import resolver


@pytest.mark.unit
@pytest.mark.parametrize("env_value", ["local", "ci", "on-prem"])
def test_current_env_respects_variable(env_value, monkeypatch):
    monkeypatch.setenv("TEST_ENV", env_value)
    assert resolver.current_env() == env_value
