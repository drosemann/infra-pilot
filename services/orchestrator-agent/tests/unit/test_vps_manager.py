import asyncio
import importlib
import json
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


def make_config(config_type, **overrides):
    values = dict(
        cpu_limit=1.5,
        memory_limit=512,
        storage_limit=20,
        image="ubuntu:22.04",
        ports={"22/tcp": "2222"},
        env_vars={"TOKEN": "redacted"},
    )
    values.update(overrides)
    return config_type(**values)


def test_create_vps_uses_configured_docker_runtime(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    config = make_config(config_type)

    container_id = asyncio.run(manager.create_vps("user-1", config))

    assert container_id == "container-1"
    assert manager.vps_instances[container_id]["user_id"] == "user-1"
    _, kwargs = mock_client.containers.created[0]
    assert kwargs["cpu_quota"] == 150000
    assert kwargs["mem_limit"] == "512m"
    assert kwargs["restart_policy"] == {"Name": "unless-stopped"}


def test_create_vps_never_spawns_privileged_containers(monkeypatch, tmp_path):
    """Regression: container spawns must not carry --privileged/--cap-add=ALL."""
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    config = make_config(config_type)

    asyncio.run(manager.create_vps("user-1", config))

    _, kwargs = mock_client.containers.created[0]
    assert kwargs.get("privileged") in (None, False)
    assert not kwargs.get("cap_add")


def test_create_vps_failure_returns_none(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)

    def boom(**kwargs):
        raise RuntimeError("docker daemon down")

    mock_client.containers.run = boom

    result = asyncio.run(manager.create_vps("user-1", make_config(config_type)))
    assert result is None


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


def test_start_stop_restart_lifecycle(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    container_id = asyncio.run(manager.create_vps("user-1", make_config(config_type)))

    assert asyncio.run(manager.stop_vps(container_id)) is True
    assert manager.vps_instances[container_id]["status"] == "stopped"

    assert asyncio.run(manager.start_vps(container_id)) is True
    assert manager.vps_instances[container_id]["status"] == "running"

    assert asyncio.run(manager.restart_vps(container_id)) is True
    assert manager.vps_instances[container_id]["status"] == "running"


def test_delete_vps_removes_instance(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    container_id = asyncio.run(manager.create_vps("user-1", make_config(config_type)))

    assert asyncio.run(manager.delete_vps(container_id)) is True
    assert container_id not in manager.vps_instances


def test_update_vps_config_changes_limits(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    container_id = asyncio.run(manager.create_vps("user-1", make_config(config_type)))

    updated = make_config(
        config_type, cpu_limit=2.0, memory_limit=1024, storage_limit=50
    )
    assert asyncio.run(manager.update_vps_config(container_id, updated)) is True

    stored = manager.vps_instances[container_id]["config"]
    assert stored["cpu_limit"] == 2.0
    assert stored["memory_limit"] == 1024
    assert stored["storage_limit"] == 50
    container = mock_client.containers.by_id[container_id]
    assert container.updated is True
    assert container.update_kwargs == {
        "cpu_period": 100000,
        "cpu_quota": 200000,
        "mem_limit": "1024m",
    }


def test_list_user_instances_scopes_to_user(monkeypatch, tmp_path):
    manager, config_type, _mock_client = build_manager(monkeypatch, tmp_path)
    asyncio.run(manager.create_vps("user-1", make_config(config_type)))
    asyncio.run(manager.create_vps("user-2", make_config(config_type)))

    instances = asyncio.run(manager.list_user_instances("user-1"))

    assert len(instances) == 1
    assert instances[0]["container_id"] == "container-1"
    assert instances[0]["info"]["user_id"] == "user-1"
    assert instances[0]["stats"] == {
        "status": "running",
        "cpu_usage": 40.0,
        "memory_usage": 25.0,
        "network": {"rx_bytes": 10, "tx_bytes": 20},
    }


def test_create_backup_commits_container_image(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    container_id = asyncio.run(manager.create_vps("user-1", make_config(config_type)))

    image_id = asyncio.run(manager.create_backup(container_id, retention_type="daily"))

    backups = manager.vps_instances[container_id].get("backups", [])
    assert backups == [
        {
            "image_id": image_id,
            "created_at": backups[0]["created_at"],
            "name": "mock-container_backup_" + backups[0]["created_at"],
            "retention_type": "daily",
        }
    ]
    assert image_id == backups[0]["name"] + "-img-1"


def test_list_backups_falls_back_to_in_memory(monkeypatch, tmp_path):
    manager, config_type, _mock_client = build_manager(monkeypatch, tmp_path)
    container_id = asyncio.run(manager.create_vps("user-1", make_config(config_type)))
    asyncio.run(manager.create_backup(container_id, retention_type="weekly"))

    backups = asyncio.run(manager.list_backups(container_id))

    assert backups == [
        {
            "image_id": backups[0]["image_id"],
            "created_at": backups[0]["created_at"],
            "name": "mock-container_backup_" + backups[0]["created_at"],
            "retention_type": "weekly",
        }
    ]
    assert backups[0]["image_id"] == backups[0]["name"] + "-img-1"


def test_container_name_validation_rejects_injection(monkeypatch, tmp_path):
    manager, _config_type, _mock_client = build_manager(monkeypatch, tmp_path)

    assert manager.is_safe_name("web-app-01") is True
    assert manager.is_safe_name("web.app_01") is True

    assert manager.is_safe_name("foo; rm -rf /") is False
    assert manager.is_safe_name("foo$(whoami)") is False
    assert manager.is_safe_name("foo`id`") is False
    assert manager.is_safe_name("foo && docker rm -f $(docker ps -q)") is False
    assert manager.is_safe_name("..") is False
    assert manager.is_safe_name("") is False
    assert manager.is_safe_name("a" * 129) is False


def test_generate_random_port_is_in_ephemeral_range(monkeypatch, tmp_path):
    manager, _config_type, _mock_client = build_manager(monkeypatch, tmp_path)

    for _ in range(100):
        port = manager.generate_random_port()
        assert 1025 <= port <= 65535


def test_instances_persist_to_json_fallback(monkeypatch, tmp_path):
    manager, config_type, _mock_client = build_manager(monkeypatch, tmp_path)
    asyncio.run(manager.create_vps("user-1", make_config(config_type)))

    persisted = (tmp_path / "vps_instances.json").read_text(encoding="utf-8")
    assert '"container_id": "container-1"' in persisted
    assert '"user_id": "user-1"' in persisted
    assert '"TOKEN"' not in persisted


def test_high_volume_developer_workflow_handles_fifty_application_vms(
    monkeypatch, tmp_path
):
    """Exercise provisioning, daily operations, and persistence at team scale."""
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    applications = (
        "nginx:alpine",
        "node:22-alpine",
        "python:3.13-slim",
        "postgres:17-alpine",
        "redis:7-alpine",
    )

    async def developer_workflow():
        creations = []
        for developer in range(10):
            for application in applications:
                creations.append(
                    manager.create_vps(
                        f"developer-{developer}",
                        make_config(
                            config_type,
                            image=application,
                            ports={"8080/tcp": str(30000 + len(creations))},
                            env_vars={"APP_ENV": "staging"},
                        ),
                    )
                )

        container_ids = await asyncio.gather(*creations)
        assert all(container_ids)
        assert len(set(container_ids)) == 50

        # Typical self-service activity: inspect a team inventory, restart an
        # application, resize another one, and take a deployment backup.
        inventory = await manager.list_user_instances("developer-4")
        assert len(inventory) == 5
        assert all(item["stats"]["status"] == "running" for item in inventory)

        assert await manager.restart_vps(container_ids[0]) is True
        assert await manager.update_vps_config(
            container_ids[1],
            make_config(config_type, cpu_limit=2.0, memory_limit=1024),
        )
        assert await manager.create_backup(container_ids[2], "weekly")

    asyncio.run(developer_workflow())

    assert len(mock_client.containers.created) == 50
    persisted = json.loads(
        (tmp_path / "vps_instances.json").read_text(encoding="utf-8")
    )
    assert len(persisted) == 50
    assert {entry["user_id"] for entry in persisted.values()} == {
        f"developer-{developer}" for developer in range(10)
    }


def test_failed_resize_restores_a_running_developer_workload(monkeypatch, tmp_path):
    manager, config_type, mock_client = build_manager(monkeypatch, tmp_path)
    container_id = asyncio.run(manager.create_vps("user-1", make_config(config_type)))
    container = mock_client.containers.by_id[container_id]

    def update_fails(**_kwargs):
        raise RuntimeError("Docker rejected resource update")

    container.update = update_fails

    assert (
        asyncio.run(manager.update_vps_config(container_id, make_config(config_type)))
        is False
    )
    assert container.status == "running"
    assert container.started is True
    assert manager.vps_instances[container_id]["config"]["memory_limit"] == 512
