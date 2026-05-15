import importlib.util
import pathlib
import sys
from dataclasses import dataclass

SERVICE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, SERVICE_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@dataclass
class MockContainer:
    id: str = "container-1"
    name: str = "mock-container"
    status: str = "running"
    stopped: bool = False
    removed: bool = False
    started: bool = False
    restarted: bool = False

    def stop(self):
        self.stopped = True

    def remove(self):
        self.removed = True

    def start(self):
        self.started = True

    def restart(self):
        self.restarted = True

    def stats(self, stream=False):
        return {
            "cpu_stats": {"cpu_usage": {"total_usage": 300}, "system_cpu_usage": 1000},
            "precpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 500},
            "memory_stats": {"usage": 128, "limit": 512},
            "networks": {"eth0": {"rx_bytes": 10, "tx_bytes": 20}},
        }


class MockContainerCollection:
    def __init__(self):
        self.created = []
        self.by_id = {"container-1": MockContainer()}

    def run(self, **kwargs):
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


class MockDockerClient:
    def __init__(self):
        self.containers = MockContainerCollection()
