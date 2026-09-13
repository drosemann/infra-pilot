import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

SERVICE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


@pytest.fixture(autouse=True)
def no_database(monkeypatch):
    """Stub database access so unit tests are hermetic and fast.

    ``vps_manager`` falls back to JSON-file persistence when the database
    is unreachable; stubbing the connection helpers exercises exactly that
    production resilience path without real connection timeouts.
    """

    async def no_pool():
        raise RuntimeError("database disabled in unit tests")

    def no_sync_connection():
        raise RuntimeError("database disabled in unit tests")

    monkeypatch.setattr("db.get_pool", no_pool)
    monkeypatch.setattr("db.get_sync_connection", no_sync_connection)


@dataclass
class MockImage:
    """Minimal mock for Docker image used in VPSManager.migrate_vps tests."""

    id: str = "image-1"

    def save(self, *args, **kwargs):
        """Return iterable chunks like docker-py Image.save()."""
        return [b"chunk"]


@dataclass
class MockContainer:
    id: str = "container-1"
    name: str = "mock-container"
    status: str = "running"
    stopped: bool = False
    removed: bool = False
    started: bool = False
    restarted: bool = False
    updated: bool = False
    last_exec: object = None

    def stop(self):
        self.stopped = True
        self.status = "stopped"

    def remove(self):
        self.removed = True

    def start(self):
        self.started = True
        self.status = "running"

    def restart(self):
        self.restarted = True
        self.status = "running"

    def update(self, **kwargs):
        self.updated = True
        self.update_kwargs = kwargs

    def commit(self, repository="", **kwargs):
        return MockImage(id=f"{repository}-img-1")

    def exec_run(self, cmd, **kwargs):
        self.last_exec = cmd

        # Simulate successful exec for health checks / benchmarks
        class _Result:
            exit_code = 0
            output = b"200"

        # For pgrep / ping / curl / port checks return success by default
        # cmd is list-form to avoid shell injection; store for assertion
        return _Result()

    def stats(self, stream=False):
        return {
            "cpu_stats": {"cpu_usage": {"total_usage": 300}, "system_cpu_usage": 1000},
            "precpu_stats": {
                "cpu_usage": {"total_usage": 100},
                "system_cpu_usage": 500,
            },
            "memory_stats": {"usage": 128, "limit": 512},
            "networks": {"eth0": {"rx_bytes": 10, "tx_bytes": 20}},
        }


class MockContainerCollection:
    """Collects containers.run calls for assertions; get/list mirror docker-py."""

    def __init__(self):
        self.created: list = []
        self.by_id: dict = {"container-1": MockContainer()}

    def run(self, **kwargs):
        # Simulate Docker's storage_opt validation: raise if driver mocked to reject (used in quota fallback tests)
        if kwargs.get("storage_opt") and kwargs.get("_fail_storage_opt"):
            raise RuntimeError("storage_opt is not supported for this driver")
        container = MockContainer(id=f"container-{len(self.created) + 1}")
        self.created.append((container, kwargs))
        self.by_id[container.id] = container
        return container

    def get(self, container_id):
        if container_id not in self.by_id:
            raise KeyError(container_id)
        return self.by_id[container_id]

    def list(self):
        return list(self.by_id.values())


class _MockImages:
    """Image collection mock exposing get().save() like docker-py."""

    def get(self, image_id: str):  # pylint: disable=unused-argument
        class _Img:
            def save(self, *args, **kwargs):
                # Must accept bound self; return chunk iterable for migrate_vps
                return [b"chunk"]

        return _Img()

    # Backward-compat alias for earlier inline mock shape
    __getitem__ = get


class MockDockerClient:
    """Deterministic Docker mock covering containers/images/info for unit tests."""

    def __init__(self):
        self.containers = MockContainerCollection()
        self.images = _MockImages()

    def info(self) -> dict:
        """Return minimal daemon info; overlay2 supports storage_opt in prod."""
        return {"Driver": "overlay2"}
