"""Abstract base class for all compute providers.

Providers translate generic operations (create, start, stop, etc.)
into hypervisor-specific API calls.  New providers register themselves
via ``ProviderRegistry`` and are selected by the ``provider`` field
in a server's manifest.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple


class InstancePowerState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    UNKNOWN = "unknown"


class ProviderError(Exception):
    """Generic provider-level failure."""


class InstanceNotFoundError(ProviderError):
    """Requested instance does not exist."""


class InstanceAlreadyExistsError(ProviderError):
    """An instance with the requested name already exists."""


class ProviderAuthError(ProviderError):
    """Authentication against the provider backend failed.

    Mapped from Docker/Kubernetes/SSH authentication and authorization
    failures so callers can distinguish "credentials bad" from
    "the backend is broken".
    """


class ProviderPermissionError(ProviderError):
    """Authenticated, but not allowed to perform the operation.

    Kubernetes RBAC denials, Docker permission errors, and SSH forced
    commands that reject the request all surface as this type.
    """


class ProviderConflictError(ProviderError):
    """Optimistic-concurrency conflict or resource already owned.

    Kubernetes ``409 Conflict`` and Docker "name already in use" errors
    map here; callers may retry after re-reading state.
    """


class ProviderUnavailableError(ProviderError):
    """The provider backend could not be reached or is not configured.

    Used for missing credentials, an unreachable daemon/cluster, or an
    optional dependency (e.g. the ``kubernetes`` client) not installed.
    """


class ProviderConfigError(ProviderError):
    """The provider configuration is invalid (bad path, bad option)."""


class ProviderNotSupportedError(ProviderError):
    """The requested operation is not supported by this provider."""


@dataclass
class InstanceSpec:
    """Desired state of a compute instance."""

    name: str
    image: str
    cpu_cores: float
    memory_mb: int
    storage_gb: int
    ports: Dict[str, str] = field(default_factory=dict)
    env_vars: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    region: str = ""
    ssh_keys: List[str] = field(default_factory=list)
    user_data: str = ""
    network_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Provider-specific knobs from the manifest (``provider_options``).
    # Keys are interpreted by each provider; unknown keys are ignored so
    # a manifest stays portable across backends.
    provider_options: Dict[str, Any] = field(default_factory=dict)
    # Forwarded from the InfraFile ``health_check`` block: Docker turns it
    # into a container HEALTHCHECK, Kubernetes into probes.
    health_check: Optional[Dict[str, Any]] = None


@dataclass
class InstanceInfo:
    """Reported state of an existing instance."""

    id: str
    name: str
    provider: str
    status: InstancePowerState
    spec: InstanceSpec
    created_at: datetime
    host: str
    private_ips: List[str] = field(default_factory=list)
    public_ips: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstanceStats:
    """Live resource usage snapshot."""

    cpu_percent: float
    memory_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
    network_rx_bytes: int
    network_tx_bytes: int
    disk_percent: float
    collected_at: datetime


@dataclass
class ProviderCapabilities:
    """What a provider can do.

    The first block is the original capability surface (kept for
    backward compatibility).  The second block describes the multi-backend
    matrix used by the Kubernetes and cloud-VM providers.
    """

    supports_snapshots: bool = False
    supports_backups: bool = False
    supports_live_migration: bool = False
    supports_resize: bool = False
    supports_firewall: bool = False
    supports_load_balancer: bool = False
    max_instances: int = 0
    regions: List[str] = field(default_factory=list)

    # Extended capability descriptors.
    supports_exec: bool = False
    supports_stream: bool = False
    supports_logs: bool = False
    supports_env: bool = True
    supports_volumes: bool = False
    supports_namespaces: bool = False
    supports_ingress: bool = False
    supports_replicas: bool = False
    supports_autoscaling: bool = False
    supports_ssh: bool = False
    workload_kinds: List[str] = field(default_factory=list)
    runtime: str = ""
    notes: str = ""

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable view for the provider API."""
        return {
            "supports_snapshots": self.supports_snapshots,
            "supports_backups": self.supports_backups,
            "supports_live_migration": self.supports_live_migration,
            "supports_resize": self.supports_resize,
            "supports_firewall": self.supports_firewall,
            "supports_load_balancer": self.supports_load_balancer,
            "max_instances": self.max_instances,
            "regions": list(self.regions),
            "supports_exec": self.supports_exec,
            "supports_stream": self.supports_stream,
            "supports_logs": self.supports_logs,
            "supports_env": self.supports_env,
            "supports_volumes": self.supports_volumes,
            "supports_namespaces": self.supports_namespaces,
            "supports_ingress": self.supports_ingress,
            "supports_replicas": self.supports_replicas,
            "supports_autoscaling": self.supports_autoscaling,
            "supports_ssh": self.supports_ssh,
            "workload_kinds": list(self.workload_kinds),
            "runtime": self.runtime,
            "notes": self.notes,
        }


class ComputeProvider(ABC):
    """Every provider must implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short unique identifier, e.g. ``docker``, ``proxmox``, ``aws``."""

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Declare what this provider supports."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @abstractmethod
    async def create(self, spec: InstanceSpec) -> InstanceInfo:
        """Provision a new instance."""

    @abstractmethod
    async def get(self, instance_id: str) -> InstanceInfo:
        """Return current info (raise InstanceNotFoundError if missing)."""

    @abstractmethod
    async def list(self) -> List[InstanceInfo]:
        """Return all instances managed by this provider."""

    @abstractmethod
    async def start(self, instance_id: str) -> bool:
        """Power on an instance."""

    @abstractmethod
    async def stop(self, instance_id: str) -> bool:
        """Power off an instance."""

    @abstractmethod
    async def restart(self, instance_id: str) -> bool:
        """Reboot an instance."""

    @abstractmethod
    async def delete(self, instance_id: str) -> bool:
        """Destroy an instance."""

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @abstractmethod
    async def update(self, instance_id: str, spec: InstanceSpec) -> bool:
        """Apply new resource limits / config."""

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------
    @abstractmethod
    async def stats(self, instance_id: str) -> Optional[InstanceStats]:
        """Return live resource usage or None."""

    # ------------------------------------------------------------------
    # Snapshots / Backups
    # ------------------------------------------------------------------
    async def create_snapshot(
        self, instance_id: str, name: Optional[str] = None
    ) -> Optional[str]:
        raise NotImplementedError

    async def list_snapshots(self, instance_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def restore_snapshot(self, instance_id: str, snapshot_id: str) -> bool:
        raise NotImplementedError

    async def create_backup(
        self, instance_id: str, retention_type: str = "daily"
    ) -> Optional[str]:
        raise NotImplementedError

    async def list_backups(self, instance_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------
    async def get_public_ip(self, instance_id: str) -> Optional[str]:
        info = await self.get(instance_id)
        return info.public_ips[0] if info.public_ips else None

    async def execute_command(self, instance_id: str, command: str) -> Tuple[bool, str]:
        raise NotImplementedError

    async def stream_command(
        self, instance_id: str, command: str
    ) -> AsyncIterator[str]:
        """Yield output chunks for a command, streaming when supported.

        The default implementation buffers ``execute_command`` so providers
        without native streaming still satisfy the interface.  Providers
        that advertise ``supports_stream`` override this with a real
        streaming implementation (e.g. Kubernetes pod exec).
        """
        ok, output = await self.execute_command(instance_id, command)
        if output:
            yield output
        if not ok:
            raise ProviderError(f"command failed on {instance_id}")

    async def logs(self, instance_id: str, tail: int = 200) -> str:
        """Return recent logs for an instance."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    async def health(self) -> Dict[str, Any]:
        """Return provider-level health (connection, resource usage)."""
        return {"status": "unknown"}
