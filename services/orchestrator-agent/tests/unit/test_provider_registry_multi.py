"""Multi-provider registry behaviour: discovery, selection, capabilities.

These tests pin the contract the rest of the service (manifest engine,
deployment API, webhook server) relies on now that more than one backend
is shipped: providers self-register, are listed deterministically, resolve
by name with an explicit default fallback, and expose a capability matrix.
"""

from datetime import datetime

import pytest
from compute.base import (
    ComputeProvider,
    InstanceAlreadyExistsError,
    InstanceInfo,
    InstanceNotFoundError,
    InstancePowerState,
    InstanceSpec,
    ProviderAuthError,
    ProviderCapabilities,
    ProviderConflictError,
    ProviderConfigError,
    ProviderError,
    ProviderNotSupportedError,
    ProviderPermissionError,
    ProviderUnavailableError,
)
from compute.registry import ProviderRegistry, provider

# Import for the side effect of self-registration at collection time, so the
# sandbox fixture snapshots a registry that already contains the built-ins.
import compute.cloud_vm_provider  # noqa: E402,F401
import compute.docker_provider  # noqa: E402,F401
import compute.kubernetes_provider  # noqa: E402,F401


class _StubProvider(ComputeProvider):
    """Minimal concrete provider used to probe registry behaviour."""

    name = "stub"

    def __init__(self, boom: bool = False):
        if boom:
            raise RuntimeError("cannot initialize")
        self.created = 0

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_exec=True,
            supports_stream=True,
            runtime="stub",
            workload_kinds=["container"],
        )

    async def create(self, spec: InstanceSpec) -> InstanceInfo:
        self.created += 1
        return InstanceInfo(
            id=f"stub/{spec.name}",
            name=spec.name,
            provider=self.name,
            status=InstancePowerState.RUNNING,
            spec=spec,
            created_at=datetime.now(),
            host="stub.local",
        )

    async def get(self, instance_id: str) -> InstanceInfo:
        raise InstanceNotFoundError(instance_id)

    async def list(self):
        return []

    async def start(self, instance_id: str) -> bool:
        return True

    async def stop(self, instance_id: str) -> bool:
        return True

    async def restart(self, instance_id: str) -> bool:
        return True

    async def delete(self, instance_id: str) -> bool:
        return True

    async def update(self, instance_id: str, spec: InstanceSpec) -> bool:
        return True

    async def stats(self, instance_id: str):
        return None


class _BrokenProvider(ComputeProvider):
    name = "broken"

    def __init__(self):
        raise RuntimeError("no backend available")

    @property
    def capabilities(self) -> ProviderCapabilities:  # pragma: no cover
        raise AssertionError("should never be reached")

    async def create(self, spec):  # pragma: no cover
        raise NotImplementedError

    async def get(self, instance_id):  # pragma: no cover
        raise NotImplementedError

    async def list(self):  # pragma: no cover
        return []

    async def start(self, instance_id):  # pragma: no cover
        return True

    async def stop(self, instance_id):  # pragma: no cover
        return True

    async def restart(self, instance_id):  # pragma: no cover
        return True

    async def delete(self, instance_id):  # pragma: no cover
        return True

    async def update(self, instance_id, spec):  # pragma: no cover
        return True

    async def stats(self, instance_id):  # pragma: no cover
        return None


@pytest.fixture
def registry_sandbox():
    """Snapshot the global registry and (re-)register the built-ins.

    Other test modules call ``ProviderRegistry.clear()`` in their own
    fixtures, so import-time registration cannot be relied upon here.
    """
    import compute.cloud_vm_provider as cloud_vm_module
    import compute.docker_provider as docker_module
    import compute.kubernetes_provider as kubernetes_module

    saved_providers = dict(ProviderRegistry._providers)
    saved_instances = dict(ProviderRegistry._instances)
    ProviderRegistry._instances.clear()
    ProviderRegistry.register(docker_module.DockerProvider)
    ProviderRegistry.register(kubernetes_module.KubernetesProvider)
    ProviderRegistry.register(cloud_vm_module.CloudVMProvider)
    yield
    ProviderRegistry._providers = saved_providers
    ProviderRegistry._instances = saved_instances


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def test_builtin_providers_register_on_import(registry_sandbox):
    names = ProviderRegistry.names()
    assert names == sorted(names)
    for expected in ("docker", "kubernetes", "cloud-vm"):
        assert ProviderRegistry.is_registered(expected)


def test_is_registered_rejects_unknown(registry_sandbox):
    assert ProviderRegistry.is_registered("does-not-exist") is False


def test_register_decorator_returns_class(registry_sandbox):
    @provider
    class _Decorated(ComputeProvider):
        name = "decorated"

        @property
        def capabilities(self):  # pragma: no cover
            return ProviderCapabilities()

        async def create(self, spec):  # pragma: no cover
            raise NotImplementedError

        async def get(self, instance_id):  # pragma: no cover
            raise NotImplementedError

        async def list(self):  # pragma: no cover
            return []

        async def start(self, instance_id):  # pragma: no cover
            return True

        async def stop(self, instance_id):  # pragma: no cover
            return True

        async def restart(self, instance_id):  # pragma: no cover
            return True

        async def delete(self, instance_id):  # pragma: no cover
            return True

        async def update(self, instance_id, spec):  # pragma: no cover
            return True

        async def stats(self, instance_id):  # pragma: no cover
            return None

    assert _Decorated is not None
    assert ProviderRegistry.is_registered("decorated")


def test_list_providers_maps_name_to_path(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    mapping = ProviderRegistry.list_providers()
    assert mapping["stub"].endswith("._StubProvider")


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------
def test_get_returns_cached_singleton(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    first = ProviderRegistry.get("stub")
    second = ProviderRegistry.get("stub")
    assert first is second


def test_get_unknown_returns_none(registry_sandbox):
    assert ProviderRegistry.get("nope") is None


def test_get_returns_none_when_init_fails(registry_sandbox):
    ProviderRegistry.register(_BrokenProvider)
    assert ProviderRegistry.get("broken") is None


def test_clear_instances_drops_cache(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    first = ProviderRegistry.get("stub")
    ProviderRegistry.clear_instances()
    second = ProviderRegistry.get("stub")
    assert first is not second


def test_get_or_default_uses_named_provider(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    assert ProviderRegistry.get_or_default("stub", default="stub") is not None


def test_get_or_default_falls_back_when_missing(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    chosen = ProviderRegistry.get_or_default("missing", default="stub")
    assert chosen is not None
    assert chosen.name == "stub"


def test_get_or_default_uses_default_when_name_none(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    chosen = ProviderRegistry.get_or_default(None, default="stub")
    assert chosen is not None


def test_get_or_default_returns_none_without_default(registry_sandbox):
    ProviderRegistry._providers.pop("stub", None)
    assert ProviderRegistry.get_or_default("missing", default="missing") is None


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------
def test_list_capabilities_reports_each_provider(registry_sandbox):
    ProviderRegistry.register(_StubProvider)
    caps = ProviderRegistry.list_capabilities()
    assert set(caps) == set(ProviderRegistry.names())
    assert caps["stub"]["supports_stream"] is True
    assert caps["stub"]["workload_kinds"] == ["container"]


def test_list_capabilities_marks_failed_providers(registry_sandbox):
    ProviderRegistry.register(_BrokenProvider)
    caps = ProviderRegistry.list_capabilities()
    assert caps["broken"] == {"error": "provider failed to initialize"}


def test_kubernetes_capability_matrix(registry_sandbox):
    caps = ProviderRegistry.list_capabilities()["kubernetes"]
    assert caps["supports_replicas"] is True
    assert caps["supports_ingress"] is True
    assert caps["supports_exec"] is True
    assert caps["supports_stream"] is True
    assert caps["supports_ssh"] is False
    assert set(caps["workload_kinds"]) == {"deployment", "statefulset"}


def test_cloud_vm_capability_matrix(registry_sandbox):
    caps = ProviderRegistry.list_capabilities()["cloud-vm"]
    assert "error" not in caps
    assert caps["runtime"] == "docker-over-ssh"
    assert caps["supports_ssh"] is True
    assert caps["supports_replicas"] is False
    assert caps["supports_stream"] is False


# ---------------------------------------------------------------------------
# Error taxonomy shared by every provider
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "error_cls",
    [
        InstanceNotFoundError,
        InstanceAlreadyExistsError,
        ProviderAuthError,
        ProviderPermissionError,
        ProviderConflictError,
        ProviderUnavailableError,
        ProviderConfigError,
        ProviderNotSupportedError,
    ],
)
def test_error_taxonomy_subclasses_provider_error(error_cls):
    assert issubclass(error_cls, ProviderError)
    assert isinstance(error_cls("boom"), ProviderError)
