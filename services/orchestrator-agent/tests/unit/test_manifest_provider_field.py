"""Manifest ``provider`` / ``provider_options`` schema and engine plumbing.

The manifest is the source of truth for which backend runs an instance.
These tests cover the parsing, validation and bounded ``provider_options``
handling, plus the reconciliation path that forwards the options into the
provider ``InstanceSpec`` and records the assignment.
"""

from datetime import datetime

import pytest
from compute.base import (
    ComputeProvider,
    InstanceInfo,
    InstanceNotFoundError,
    InstancePowerState,
    InstanceSpec,
    ProviderCapabilities,
)
from compute.registry import ProviderRegistry
from manifest import schema
from manifest.engine import ManifestEngine
from manifest.schema import (
    BUILTIN_PROVIDERS,
    DEFAULT_PROVIDER,
    MAX_PROVIDER_OPTION_ENTRIES,
    MAX_PROVIDER_OPTION_VALUE_LEN,
    InfraFile,
    InfraInstance,
    validate_providers,
)
from manifest.store import ManifestStore


def _manifest(instance: dict, name: str = "demo") -> dict:
    return {
        "api_version": "v1",
        "kind": "InfraFile",
        "metadata": {"name": name},
        "spec": {"instances": [instance]},
    }


# ---------------------------------------------------------------------------
# Parsing / serialization
# ---------------------------------------------------------------------------
def test_provider_defaults_to_docker():
    infra = InfraFile.from_dict(_manifest({"name": "web", "image": "nginx:latest"}))
    assert infra.spec.instances[0].provider == DEFAULT_PROVIDER == "docker"


def test_explicit_provider_is_preserved():
    infra = InfraFile.from_dict(
        _manifest({"name": "web", "provider": "kubernetes", "image": "nginx:latest"})
    )
    assert infra.spec.instances[0].provider == "kubernetes"


def test_provider_round_trips_through_to_dict():
    payload = {
        "name": "web",
        "provider": "cloud-vm",
        "image": "nginx:latest",
        "provider_options": {"vm": "edge-1", "volume_mount_path": "/data"},
    }
    infra = InfraFile.from_dict(_manifest(payload))
    restored = infra.to_dict()["spec"]["instances"][0]
    assert restored["provider"] == "cloud-vm"
    assert restored["provider_options"] == {
        "vm": "edge-1",
        "volume_mount_path": "/data",
    }


def test_provider_options_default_is_not_shared():
    a = InfraInstance(name="a")
    b = InfraInstance(name="b")
    a.provider_options["namespace"] = "x"
    assert b.provider_options == {}


def test_provider_options_none_is_normalized():
    infra = InfraFile.from_dict(
        _manifest({"name": "web", "provider_options": None})
    )
    assert infra.spec.instances[0].provider_options == {}


# ---------------------------------------------------------------------------
# Provider-name validation
# ---------------------------------------------------------------------------
def test_validate_accepts_builtin_providers():
    for provider_name in BUILTIN_PROVIDERS:
        infra = InfraFile.from_dict(
            _manifest({"name": "web", "provider": provider_name})
        )
        infra.validate(providers=BUILTIN_PROVIDERS)


def test_validate_rejects_unregistered_provider():
    infra = InfraFile.from_dict(_manifest({"name": "web", "provider": "kubernetes"}))
    with pytest.raises(ValueError, match="unknown provider 'kubernetes'"):
        infra.validate(providers=["docker"])


def test_validate_without_allowlist_permits_custom_provider():
    infra = InfraFile.from_dict(_manifest({"name": "web", "provider": "fake"}))
    infra.validate()  # prints no registry knowledge -> accepted


@pytest.mark.parametrize("bad", ["Docker", "1docker", "bad_name", "with space", ""])
def test_validate_rejects_malformed_provider(bad):
    inst = InfraInstance(name="web", provider=bad)
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError):
        infra.validate()


def test_validate_providers_helper_returns_value():
    assert validate_providers("docker", {"docker", "kubernetes"}) == "docker"


def test_validate_providers_helper_rejects_unknown():
    with pytest.raises(ValueError, match="unknown provider"):
        validate_providers("cloud-vm", {"docker"})


def test_validate_providers_helper_rejects_malformed():
    with pytest.raises(ValueError, match="invalid provider"):
        validate_providers("Bad", None)


# ---------------------------------------------------------------------------
# provider_options bounds
# ---------------------------------------------------------------------------
def test_provider_options_nested_values_are_allowed():
    inst = InfraInstance(
        name="web",
        provider_options={
            "resources": {
                "requests": {"cpu": "250m", "memory": "128Mi"},
                "limits": {"cpu": "1"},
            },
            "command": ["sh", "-c", "echo hi"],
            "replicas": 3,
            "headless_service": True,
        },
    )
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    infra.validate()


def test_provider_options_rejects_too_many_entries():
    inst = InfraInstance(
        name="web",
        provider_options={
            f"k{i}": 1 for i in range(MAX_PROVIDER_OPTION_ENTRIES + 1)
        },
    )
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError, match="too many provider_options"):
        infra.validate()


def test_provider_options_rejects_oversized_value():
    inst = InfraInstance(
        name="web",
        provider_options={"namespace": "x" * (MAX_PROVIDER_OPTION_VALUE_LEN + 1)},
    )
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError, match="value too large"):
        infra.validate()


def test_provider_options_rejects_invalid_key():
    inst = InfraInstance(name="web", provider_options={"bad key!": 1})
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError, match="invalid provider_options key"):
        infra.validate()


def test_provider_options_rejects_invalid_nested_key():
    inst = InfraInstance(name="web", provider_options={"map": {"bad key!": 1}})
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError, match="invalid provider_options.map key"):
        infra.validate()


def test_provider_options_rejects_invalid_value_type():
    inst = InfraInstance(name="web", provider_options={"thing": object()})
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError, match="invalid provider_options.thing value"):
        infra.validate()


def test_provider_options_rejects_non_mapping():
    inst = InfraInstance(name="web")
    inst.provider_options = ["not", "a", "mapping"]
    infra = InfraFile(spec=schema.InfraFileSpec(instances=[inst]))
    with pytest.raises(ValueError, match="invalid provider_options"):
        infra.validate()


# ---------------------------------------------------------------------------
# Engine plumbing
# ---------------------------------------------------------------------------
class _CapturingProvider(ComputeProvider):
    name = "capture"

    def __init__(self):
        self.created_specs = []
        self.updated_specs = []
        self.listed = 0

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities()

    async def create(self, spec: InstanceSpec) -> InstanceInfo:
        self.created_specs.append(spec)
        return InstanceInfo(
            id=f"capture/{spec.name}",
            name=spec.name,
            provider=self.name,
            status=InstancePowerState.RUNNING,
            spec=spec,
            created_at=datetime.now(),
            host="capture.local",
        )

    async def get(self, instance_id: str) -> InstanceInfo:
        raise InstanceNotFoundError(instance_id)

    async def list(self):
        self.listed += 1
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
        self.updated_specs.append(spec)
        return True

    async def stats(self, instance_id: str):
        return None


@pytest.fixture
def capture_provider():
    saved = dict(ProviderRegistry._providers)
    saved_instances = dict(ProviderRegistry._instances)
    provider = _CapturingProvider()
    ProviderRegistry._providers["capture"] = _CapturingProvider
    ProviderRegistry._instances["capture"] = provider
    yield provider
    ProviderRegistry._providers = saved
    ProviderRegistry._instances = saved_instances


@pytest.mark.asyncio
async def test_reconcile_forwards_provider_options(capture_provider):
    infra = InfraFile.from_dict(
        _manifest(
            {
                "name": "web",
                "provider": "capture",
                "image": "nginx:latest",
                "cpu": 2,
                "memory_mb": 1024,
                "provider_options": {"namespace": "team-a", "replicas": 3},
            }
        )
    )
    engine = ManifestEngine()
    result = await engine.reconcile(infra)
    assert result.instances_created == 1
    assert result.errors == []
    spec = capture_provider.created_specs[0]
    assert spec.provider_options == {"namespace": "team-a", "replicas": 3}
    assert spec.cpu_cores == 2
    assert spec.memory_mb == 1024


@pytest.mark.asyncio
async def test_reconcile_records_provider_assignment(tmp_path):
    saved = dict(ProviderRegistry._providers)
    saved_instances = dict(ProviderRegistry._instances)
    provider = _CapturingProvider()
    ProviderRegistry._providers["capture"] = _CapturingProvider
    ProviderRegistry._instances["capture"] = provider
    store = ManifestStore(path=str(tmp_path / "assignments.json"))
    try:
        infra = InfraFile.from_dict(
            _manifest({"name": "web", "provider": "capture"})
        )
        engine = ManifestEngine()
        # Point the engine's store at the temp file via the config the store reads.
        from config import config

        original = config.MANIFEST_STORE_FILE
        config.MANIFEST_STORE_FILE = store.path
        try:
            await engine.reconcile(infra)
        finally:
            config.MANIFEST_STORE_FILE = original
        assert store.provider_for("web") == "capture"
    finally:
        ProviderRegistry._providers = saved
        ProviderRegistry._instances = saved_instances


@pytest.mark.asyncio
async def test_dry_run_does_not_create_or_record(capture_provider, tmp_path):
    from config import config

    original = config.MANIFEST_STORE_FILE
    config.MANIFEST_STORE_FILE = str(tmp_path / "dry.json")
    try:
        infra = InfraFile.from_dict(
            _manifest({"name": "web", "provider": "capture"})
        )
        engine = ManifestEngine(dry_run=True)
        result = await engine.reconcile(infra)
    finally:
        config.MANIFEST_STORE_FILE = original
    assert result.dry_run is True
    assert result.instances_created == 1
    assert capture_provider.created_specs == []
    assert not (tmp_path / "dry.json").exists()
