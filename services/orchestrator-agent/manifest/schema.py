"""Data models for the InfraFile declarative manifest format.

Example ``infra.yaml``::

    api_version: v1
    kind: InfraFile
    metadata:
      name: my-infra
      region: us-east-1
    spec:
      instances:
        - name: web-01
          provider: docker
          image: nginx:latest
          cpu: 1
          memory_mb: 512
          storage_gb: 10
          ports:
            "80/tcp": "8080"
          labels:
            app: web
          health_check:
            type: http
            target: http://localhost:80/health
      networks:
        - name: internal
          cidr: 10.0.0.0/24
      storage:
        - name: data-volume
          size_gb: 50
          driver: local
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from ipaddress import ip_network
from typing import Any, Dict, List, Optional

# Validation bounds for manifests. from_dict() stays lenient (parsing only);
# call validate() / validate_strict() before reconciling untrusted input
# (see deployment_apply in webhook_server.py).
MAX_INSTANCES = 50
MAX_NETWORKS = 50
MAX_STORAGE = 50
MAX_PORT_MAPPINGS = 16
MAX_ENV_ENTRIES = 64
MAX_LABEL_ENTRIES = 64
MAX_ENV_VALUE_LEN = 4096
MAX_USER_DATA_LEN = 65536
MAX_SSH_KEYS = 16
MAX_SSH_KEY_LEN = 8192
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")
IMAGE_PATTERN = re.compile(
    r"^[a-z0-9._/-]+(?::[A-Za-z0-9_.-]+)?(?:@[A-Za-z0-9_.-]+:[A-Fa-f0-9]+)?$"
)
ENV_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PORT_KEY_PATTERN = re.compile(r"^(\d{1,5})/(tcp|udp)$")
# Env vars that must never come from a manifest: they escape confinement
# (library preload) or redirect control-plane connections.
DENIED_ENV_VARS = frozenset(
    {
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "DOCKER_HOST",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    }
)


class HealthCheckType(str, Enum):
    PING = "ping"
    PORT = "port"
    PROCESS = "process"
    HTTP = "http"
    TCP = "tcp"


@dataclass
class HealthCheckSpec:
    type: HealthCheckType = HealthCheckType.HTTP
    target: str = "http://localhost:80/health"
    interval_seconds: int = 30
    timeout_seconds: int = 10
    retries: int = 3


@dataclass
class InfraInstance:
    name: str
    provider: str = "docker"
    image: str = "ubuntu:22.04"
    cpu: float = 1.0
    memory_mb: int = 512
    storage_gb: int = 10
    ports: Dict[str, str] = field(default_factory=dict)
    env: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    region: str = ""
    ssh_keys: List[str] = field(default_factory=list)
    user_data: str = ""
    network: str = ""
    health_check: Optional[HealthCheckSpec] = None
    auto_remediate: bool = True
    min_replicas: int = 1
    max_replicas: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InfraNetwork:
    name: str
    cidr: str = "10.0.0.0/24"
    gateway: str = ""
    dns: List[str] = field(default_factory=list)
    vlan_id: Optional[int] = None
    provider: str = "docker"
    region: str = ""


@dataclass
class InfraStorage:
    name: str
    size_gb: int = 10
    driver: str = "local"
    mount_point: str = "/data"
    provider: str = "docker"
    region: str = ""
    replication: int = 1


@dataclass
class InfraFileSpec:
    instances: List[InfraInstance] = field(default_factory=list)
    networks: List[InfraNetwork] = field(default_factory=list)
    storage: List[InfraStorage] = field(default_factory=list)


@dataclass
class InfraFileMetadata:
    name: str = "default"
    region: str = "default"
    project: str = "default"
    environment: str = "production"
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class InfraFile:
    """Top-level manifest representing desired infrastructure state."""

    api_version: str = "v1"
    kind: str = "InfraFile"
    metadata: InfraFileMetadata = field(default_factory=InfraFileMetadata)
    spec: InfraFileSpec = field(default_factory=InfraFileSpec)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InfraFile":
        """Parse a raw dictionary (from YAML/JSON) into typed models."""
        meta_data = data.get("metadata", {})
        spec_data = data.get("spec", {})

        metadata = InfraFileMetadata(
            name=meta_data.get("name", "default"),
            region=meta_data.get("region", "default"),
            project=meta_data.get("project", "default"),
            environment=meta_data.get("environment", "production"),
            labels=meta_data.get("labels", {}),
        )

        instances = []
        for inst in spec_data.get("instances", []):
            hc = inst.get("health_check")
            health_check = HealthCheckSpec(**hc) if hc else None
            instances.append(
                InfraInstance(
                    name=inst.get("name", ""),
                    provider=inst.get("provider", "docker"),
                    image=inst.get("image", "ubuntu:22.04"),
                    cpu=inst.get("cpu", 1.0),
                    memory_mb=inst.get("memory_mb", 512),
                    storage_gb=inst.get("storage_gb", 10),
                    ports=inst.get("ports", {}),
                    env=inst.get("env", {}),
                    labels=inst.get("labels", {}),
                    region=inst.get("region", ""),
                    ssh_keys=inst.get("ssh_keys", []),
                    user_data=inst.get("user_data", ""),
                    network=inst.get("network", ""),
                    health_check=health_check,
                    auto_remediate=inst.get("auto_remediate", True),
                    min_replicas=inst.get("min_replicas", 1),
                    max_replicas=inst.get("max_replicas", 1),
                    metadata=inst.get("metadata", {}),
                )
            )

        networks = [InfraNetwork(**n) for n in spec_data.get("networks", [])]
        storage = [InfraStorage(**s) for s in spec_data.get("storage", [])]

        return cls(
            api_version=data.get("api_version", "v1"),
            kind=data.get("kind", "InfraFile"),
            metadata=metadata,
            spec=InfraFileSpec(
                instances=instances,
                networks=networks,
                storage=storage,
            ),
        )

    def validate(self, strict: bool = False) -> None:
        """Validate manifest content; raise ValueError on violation.

        Lenient checks always apply (types, sizes, image/port/env shape).
        With ``strict=True`` (untrusted API input) host ports < 1025 are
        additionally rejected – binding privileged ports requires an
        explicit operator override outside the manifest.
        """
        if not NAME_PATTERN.fullmatch(self.metadata.name):
            raise ValueError(f"invalid metadata.name: {self.metadata.name!r}")
        if len(self.spec.instances) > MAX_INSTANCES:
            raise ValueError(
                f"too many instances: {len(self.spec.instances)} > {MAX_INSTANCES}"
            )
        if len(self.spec.networks) > MAX_NETWORKS:
            raise ValueError(
                f"too many networks: {len(self.spec.networks)} > {MAX_NETWORKS}"
            )
        if len(self.spec.storage) > MAX_STORAGE:
            raise ValueError(
                f"too many storage volumes: {len(self.spec.storage)} > {MAX_STORAGE}"
            )
        for inst in self.spec.instances:
            _validate_instance(inst, strict=strict)
        for network in self.spec.networks:
            _validate_network(network)
        for volume in self.spec.storage:
            _validate_storage(volume)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize back to a plain dictionary."""
        return {
            "api_version": self.api_version,
            "kind": self.kind,
            "metadata": {
                "name": self.metadata.name,
                "region": self.metadata.region,
                "project": self.metadata.project,
                "environment": self.metadata.environment,
                "labels": self.metadata.labels,
            },
            "spec": {
                "instances": [
                    {
                        "name": i.name,
                        "provider": i.provider,
                        "image": i.image,
                        "cpu": i.cpu,
                        "memory_mb": i.memory_mb,
                        "storage_gb": i.storage_gb,
                        "ports": i.ports,
                        "env": i.env,
                        "labels": i.labels,
                        "region": i.region,
                        "ssh_keys": i.ssh_keys,
                        "user_data": i.user_data,
                        "network": i.network,
                        "health_check": (
                            {
                                "type": (
                                    i.health_check.type.value
                                    if isinstance(i.health_check.type, HealthCheckType)
                                    else i.health_check.type
                                ),
                                "target": i.health_check.target,
                                "interval_seconds": i.health_check.interval_seconds,
                                "timeout_seconds": i.health_check.timeout_seconds,
                                "retries": i.health_check.retries,
                            }
                            if i.health_check
                            else None
                        ),
                        "auto_remediate": i.auto_remediate,
                        "min_replicas": i.min_replicas,
                        "max_replicas": i.max_replicas,
                        "metadata": i.metadata,
                    }
                    for i in self.spec.instances
                ],
                "networks": [
                    {
                        "name": n.name,
                        "cidr": n.cidr,
                        "gateway": n.gateway,
                        "dns": n.dns,
                        "vlan_id": n.vlan_id,
                        "provider": n.provider,
                        "region": n.region,
                    }
                    for n in self.spec.networks
                ],
                "storage": [
                    {
                        "name": s.name,
                        "size_gb": s.size_gb,
                        "driver": s.driver,
                        "mount_point": s.mount_point,
                        "provider": s.provider,
                        "region": s.region,
                        "replication": s.replication,
                    }
                    for s in self.spec.storage
                ],
            },
        }


def _validate_host_port(value: Any, strict: bool) -> None:
    try:
        host_port = int(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"invalid host port: {value!r}") from None
    if not 1 <= host_port <= 65535:
        raise ValueError(f"host port out of range: {value!r}")
    if strict and host_port < 1025:
        raise ValueError(
            f"privileged host port rejected in strict mode: {value!r} "
            "(use >= 1025 or an operator override)"
        )


def _validate_network(network: InfraNetwork) -> None:
    if not isinstance(network.name, str) or not NAME_PATTERN.fullmatch(network.name):
        raise ValueError(f"invalid network name: {network.name!r}")
    if not isinstance(network.cidr, str) or len(network.cidr) > 64:
        raise ValueError(f"invalid network CIDR: {network.cidr!r}")
    if network.cidr:
        try:
            ip_network(network.cidr, strict=False)
        except ValueError:
            raise ValueError(f"invalid network CIDR: {network.cidr!r}") from None


def _validate_storage(volume: InfraStorage) -> None:
    if not isinstance(volume.name, str) or not NAME_PATTERN.fullmatch(volume.name):
        raise ValueError(f"invalid storage name: {volume.name!r}")
    if not isinstance(volume.driver, str) or not NAME_PATTERN.fullmatch(volume.driver):
        raise ValueError(f"invalid storage driver: {volume.driver!r}")
    if (
        isinstance(volume.size_gb, bool)
        or not isinstance(volume.size_gb, (int, float))
        or not 0 < volume.size_gb <= 1_000_000
    ):
        raise ValueError(f"invalid storage size_gb: {volume.size_gb!r}")


def _validate_instance(inst: "InfraInstance", strict: bool) -> None:
    if not inst.name or not NAME_PATTERN.fullmatch(inst.name):
        raise ValueError(f"invalid instance name: {inst.name!r}")
    if not isinstance(inst.image, str) or len(inst.image) > 255:
        raise ValueError(f"invalid image: {inst.image!r}")
    if not IMAGE_PATTERN.fullmatch(inst.image):
        raise ValueError(f"invalid image reference: {inst.image!r}")
    for numeric, label in (
        (inst.cpu, "cpu"),
        (inst.memory_mb, "memory_mb"),
        (inst.storage_gb, "storage_gb"),
    ):
        if (
            isinstance(numeric, bool)
            or not isinstance(numeric, (int, float))
            or not (0 < numeric <= 1_000_000)
        ):
            raise ValueError(f"invalid {label}: {numeric!r}")
    if not isinstance(inst.ports, dict) or len(inst.ports) > MAX_PORT_MAPPINGS:
        raise ValueError(f"invalid ports mapping for {inst.name!r}")
    for container_port, host_port in inst.ports.items():
        match = (
            PORT_KEY_PATTERN.fullmatch(str(container_port))
            if isinstance(container_port, str)
            else None
        )
        if not match or not 1 <= int(match.group(1)) <= 65535:
            raise ValueError(f"invalid container port: {container_port!r}")
        _validate_host_port(host_port, strict)
    for mapping, limit, label in (
        (inst.env, MAX_ENV_ENTRIES, "env"),
        (inst.labels, MAX_LABEL_ENTRIES, "labels"),
    ):
        if not isinstance(mapping, dict) or len(mapping) > limit:
            raise ValueError(f"invalid {label} mapping for {inst.name!r}")
    for key, value in inst.env.items():
        if not isinstance(key, str) or not ENV_KEY_PATTERN.fullmatch(key):
            raise ValueError(f"invalid env key: {key!r}")
        if key in DENIED_ENV_VARS:
            raise ValueError(f"denied env var: {key!r}")
        if not isinstance(value, str) or len(value) > MAX_ENV_VALUE_LEN:
            raise ValueError(f"invalid env value for {key!r}")
    if not isinstance(inst.user_data, str) or len(inst.user_data) > MAX_USER_DATA_LEN:
        raise ValueError(f"user_data too large for {inst.name!r}")
    if not isinstance(inst.ssh_keys, list) or len(inst.ssh_keys) > MAX_SSH_KEYS:
        raise ValueError(f"invalid ssh_keys for {inst.name!r}")
    for ssh_key in inst.ssh_keys:
        if not isinstance(ssh_key, str) or len(ssh_key) > MAX_SSH_KEY_LEN:
            raise ValueError(f"invalid ssh_key for {inst.name!r}")
