import asyncio

import importlib
import sys

import docker

from conftest import MockDockerClient


def build_manager(monkeypatch, tmp_path):
    mock_client = MockDockerClient()
    monkeypatch.setattr(docker, "from_env", lambda: mock_client)
    monkeypatch.chdir(tmp_path)
    if "vps_manager" in sys.modules:
        module = importlib.reload(sys.modules["vps_manager"])
    else:
        module = importlib.import_module("vps_manager")
    return module.VPSManager(), module.VPSConfig, mock_client


def test_create_vps_uses_configured_docker_runtime(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    config = config_type(
        cpu_limit=1.5,
        memory_limit=512,
        storage_limit=20,
        image="ubuntu:22.04",
        ports={"22/tcp": "2222"},
        env_vars={"TOKEN": "redacted"},
    )

    container_id = asyncio.run(manager.create_vps("user-1", config))

    assert container_id == "container-1"
    assert manager.vps_instances[container_id]["user_id"] == "user-1"
    _, kwargs = mock_client.containers.created[0]
    assert kwargs["cpu_quota"] == 150000
    assert kwargs["mem_limit"] == "512m"
    assert kwargs["restart_policy"] == {"Name": "unless-stopped"}


def test_runtime_errors_return_false_without_raising(monkeypatch, tmp_path):
    manager, _config_type, _mock_client = build_manager(monkeypatch, tmp_path)

    assert asyncio.run(manager.stop_vps("missing")) is False


def test_stats_are_normalized_from_docker_payload(monkeypatch, tmp_path):
    manager, _config_type, _mock_client = build_manager(monkeypatch, tmp_path)

    stats = asyncio.run(manager.get_vps_stats("container-1"))

    assert stats == {
        "status": "running",
        "cpu_usage": 40.0,
        "memory_usage": 25.0,
        "network": {"rx_bytes": 10, "tx_bytes": 20},
    }
