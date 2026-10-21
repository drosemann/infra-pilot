"""Reconciliation engine — the heart of GitOps.

Read a desired ``InfraFile`` manifest, query the current state from
the compute providers, compute a diff, and apply changes to converge.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import docker
import yaml
from compute.base import ComputeProvider, InstanceInfo, InstanceSpec, ProviderError
from compute.registry import ProviderRegistry
from manifest.schema import InfraFile, InfraInstance, InfraNetwork, InfraStorage
from manifest.store import ManifestStore

logger = logging.getLogger(__name__)


class DriftSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DriftEntry:
    """A single drift item — a difference between desired and actual state."""

    instance_name: str
    field: str
    expected: Any
    actual: Any
    severity: DriftSeverity = DriftSeverity.WARNING
    message: str = ""


@dataclass
class DriftReport:
    """Complete drift analysis for a manifest."""

    manifest_name: str
    total_instances: int
    drifted_instances: int
    entries: List[DriftEntry] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReconcileResult:
    """Outcome of a reconciliation run."""

    manifest_name: str
    instances_created: int = 0
    instances_updated: int = 0
    instances_deleted: int = 0
    instances_unchanged: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dry_run: bool = False


def _resolve_single_ref(service: Any, raw: str) -> Tuple[str, str]:
    """Resolve one ``ref:secrets://`` value; returns (resolved, error).

    ``error`` is empty on success and carries a sanitized reason otherwise
    (paths/refs are safe to surface; backend values never are).
    """
    from secrets_service import parse_secret_ref

    try:
        ref_path, ref_key = parse_secret_ref(raw)
        stored = service.get(ref_path, ref_key)
    except ValueError as exc:
        return "", str(exc)
    except Exception as exc:
        return "", f"secrets backend error: {type(exc).__name__}"
    if isinstance(stored, str):
        return stored, ""
    if isinstance(stored, (int, float, bool)):
        return str(stored), ""
    return "", f"no stored entry at {raw[len('ref:secrets://'):]}"


class ManifestEngine:
    """Reads an InfraFile manifest and reconciles infrastructure state."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._docker = None

    def _docker_client(self):
        """Lazily connect to the Docker daemon.

        Returns ``None`` when the daemon is unreachable so that the
        provider-based drift/reconcile logic still works without it;
        docker-only concerns (networks, volumes) are then skipped.
        """
        if self._docker is None:
            try:
                client = docker.from_env()
                client.ping()
                self._docker = client
            except Exception as exc:
                logger.warning("Docker daemon unavailable: %s", exc)
        return self._docker

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    @staticmethod
    def load_yaml(path: str) -> InfraFile:
        """Load an InfraFile from a YAML file on disk."""
        with open(path) as f:
            raw = yaml.safe_load(f)
        return InfraFile.from_dict(raw)

    @staticmethod
    def load_dict(data: Dict[str, Any]) -> InfraFile:
        """Load an InfraFile from an in-memory dictionary."""
        return InfraFile.from_dict(data)

    # ------------------------------------------------------------------
    # Drift detection
    # ------------------------------------------------------------------
    async def detect_drift(
        self, desired: InfraFile, current_instances: Dict[str, InstanceInfo]
    ) -> DriftReport:
        """Compare desired instances against current state."""
        desired.validate()
        entries: List[DriftEntry] = []
        desired_names: Set[str] = {i.name for i in desired.spec.instances}
        current_names: Set[str] = set(current_instances.keys())

        for inst in desired.spec.instances:
            actual = current_instances.get(inst.name)
            if actual is None:
                entries.append(
                    DriftEntry(
                        instance_name=inst.name,
                        field="exists",
                        expected=True,
                        actual=False,
                        severity=DriftSeverity.ERROR,
                        message=f"Instance '{inst.name}' is defined but does not exist",
                    )
                )
                continue

            # Check provider
            if actual.provider != inst.provider:
                entries.append(
                    DriftEntry(
                        instance_name=inst.name,
                        field="provider",
                        expected=inst.provider,
                        actual=actual.provider,
                        severity=DriftSeverity.WARNING,
                    )
                )

            # Check CPU
            if abs(actual.spec.cpu_cores - inst.cpu) > 0.1:
                entries.append(
                    DriftEntry(
                        instance_name=inst.name,
                        field="cpu_cores",
                        expected=inst.cpu,
                        actual=actual.spec.cpu_cores,
                        severity=DriftSeverity.WARNING,
                    )
                )

            # Check memory
            if actual.spec.memory_mb != inst.memory_mb:
                entries.append(
                    DriftEntry(
                        instance_name=inst.name,
                        field="memory_mb",
                        expected=inst.memory_mb,
                        actual=actual.spec.memory_mb,
                        severity=DriftSeverity.WARNING,
                    )
                )

            # Check image
            if actual.spec.image != inst.image:
                entries.append(
                    DriftEntry(
                        instance_name=inst.name,
                        field="image",
                        expected=inst.image,
                        actual=actual.spec.image,
                        severity=DriftSeverity.WARNING,
                    )
                )

        # Check networks
        docker_client = self._docker_client()
        if docker_client is not None:
            existing_networks = {n.name for n in docker_client.networks.list()}
            for net in desired.spec.networks:
                if net.name not in existing_networks:
                    entries.append(
                        DriftEntry(
                            instance_name=net.name,
                            field="network_exists",
                            expected=True,
                            actual=False,
                            severity=DriftSeverity.ERROR,
                            message=f"Network '{net.name}' is defined but does not exist",
                        )
                    )

        # Check storage volumes
        if docker_client is not None:
            existing_volumes = {v.name for v in docker_client.volumes.list()}
            for vol in desired.spec.storage:
                if vol.name not in existing_volumes:
                    entries.append(
                        DriftEntry(
                            instance_name=vol.name,
                            field="volume_exists",
                            expected=True,
                            actual=False,
                            severity=DriftSeverity.ERROR,
                            message=f"Volume '{vol.name}' is defined but does not exist",
                        )
                    )
                else:
                    # Check size
                    vol_info = docker_client.volumes.get(vol.name)
                    labels = getattr(vol_info, "labels", {}) or {}
                    desired_size = labels.get("size_gb")
                    if desired_size and str(vol.size_gb) != desired_size:
                        entries.append(
                            DriftEntry(
                                instance_name=vol.name,
                                field="volume_size_gb",
                                expected=vol.size_gb,
                                actual=int(desired_size),
                                severity=DriftSeverity.WARNING,
                            )
                        )

        # Instances that exist but are not in the manifest
        for name in current_names - desired_names:
            entries.append(
                DriftEntry(
                    instance_name=name,
                    field="exists",
                    expected=False,
                    actual=True,
                    severity=DriftSeverity.WARNING,
                    message=f"Instance '{name}' exists but is not in the manifest",
                )
            )

        return DriftReport(
            manifest_name=desired.metadata.name,
            total_instances=len(desired.spec.instances),
            drifted_instances=len({e.instance_name for e in entries}),
            entries=entries,
        )

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------
    async def reconcile(self, desired: InfraFile) -> ReconcileResult:
        """Converge actual infrastructure toward the desired manifest."""
        desired.validate()
        # Resolve ``ref:secrets://<path>#<key>`` env values before any
        # instance is created. Dry runs never touch the secrets backend;
        # real reconciles fail closed when a reference cannot be resolved.
        env_map: Dict[str, Dict[str, str]] = {}
        if not self.dry_run:
            env_map = self._resolve_secret_refs(desired)
        result = ReconcileResult(
            manifest_name=desired.metadata.name,
            dry_run=self.dry_run,
        )

        # Index current instances by name across all providers
        current: Dict[str, InstanceInfo] = {}
        provider_map: Dict[str, ComputeProvider] = {}

        for inst in desired.spec.instances:
            prov = ProviderRegistry.get(inst.provider)
            if prov is None:
                result.errors.append(
                    f"Provider '{inst.provider}' not found for {inst.name}"
                )
                continue
            provider_map[inst.provider] = prov
            try:
                all_instances = await prov.list()
                for info in all_instances:
                    current[info.name] = info
            except Exception as exc:
                logger.warning(
                    "Failed to list instances from %s: %s", inst.provider, exc
                )

        desired_names: Set[str] = {i.name for i in desired.spec.instances}

        for inst in desired.spec.instances:
            prov = provider_map.get(inst.provider)
            if prov is None:
                continue

            spec = InstanceSpec(
                name=inst.name,
                image=inst.image,
                cpu_cores=inst.cpu,
                memory_mb=inst.memory_mb,
                storage_gb=inst.storage_gb,
                ports=inst.ports,
                env_vars=env_map.get(inst.name, inst.env),
                labels=inst.labels,
                region=inst.region or desired.metadata.region,
                metadata=inst.metadata,
                provider_options=inst.provider_options,
            )

            try:
                existing = current.get(inst.name)

                if existing is None:
                    # Create
                    if not self.dry_run:
                        await prov.create(spec)
                    result.instances_created += 1
                    logger.info(
                        "Would create%s instance: %s",
                        " (dry-run)" if self.dry_run else "",
                        inst.name,
                    )
                else:
                    # Update if drifted
                    needs_update = (
                        abs(existing.spec.cpu_cores - inst.cpu) > 0.1
                        or existing.spec.memory_mb != inst.memory_mb
                        or existing.spec.image != inst.image
                    )
                    if needs_update:
                        if not self.dry_run:
                            await prov.update(existing.id, spec)
                        result.instances_updated += 1
                        logger.info(
                            "Would update%s instance: %s",
                            " (dry-run)" if self.dry_run else "",
                            inst.name,
                        )
                    else:
                        result.instances_unchanged += 1
            except Exception as exc:
                msg = f"Failed to reconcile {inst.name}: {exc}"
                result.errors.append(msg)
                logger.error(msg)

        # Reconcile networks
        docker_client = self._docker_client()
        if docker_client is not None:
            for net in desired.spec.networks:
                try:
                    existing = docker_client.networks.list(names=[net.name])
                    if not existing:
                        if not self.dry_run:
                            ipam = (
                                docker.types.IPAMConfig(
                                    driver="default",
                                    config=[{"subnet": net.cidr}],
                                )
                                if net.cidr
                                else None
                            )
                            docker_client.networks.create(
                                net.name,
                                driver="bridge",
                                ipam=ipam,
                                labels={
                                    "region": net.region,
                                    "manifest": desired.metadata.name,
                                },
                            )
                            logger.info("Created network: %s", net.name)
                    # else: network exists — could validate subnet but Docker doesn't easily expose IPAM config
                except Exception as exc:
                    msg = f"Failed to reconcile network {net.name}: {exc}"
                    result.errors.append(msg)
                    logger.error(msg)

        # Reconcile storage volumes
        if docker_client is not None:
            for vol in desired.spec.storage:
                try:
                    existing = docker_client.volumes.list()
                    found = any(v.name == vol.name for v in existing)
                    if not found:
                        if not self.dry_run:
                            docker_client.volumes.create(
                                vol.name,
                                driver=vol.driver,
                                labels={
                                    "size_gb": str(vol.size_gb),
                                    "region": vol.region,
                                    "manifest": desired.metadata.name,
                                },
                            )
                            logger.info("Created volume: %s", vol.name)
                except Exception as exc:
                    msg = f"Failed to reconcile volume {vol.name}: {exc}"
                    result.errors.append(msg)
                    logger.error(msg)

        result.completed_at = datetime.now(timezone.utc)
        if not result.dry_run:
            self._record_assignments(desired, result)
        return result

    def _resolve_secret_refs(self, desired: InfraFile) -> Dict[str, Dict[str, str]]:
        """Resolve ``ref:secrets://<path>#<key>`` env values (fail closed).

        Only called for real reconciles; dry runs keep the raw references.
        Raises ``ValueError`` listing every unresolved reference (no backend
        configured, malformed ref, missing entry, or backend error) instead
        of creating half-res instances. Resolved values are never logged.
        """
        from secrets_service import resolve_secrets_service

        refs: List[Tuple[str, str, str]] = []
        for inst in desired.spec.instances:
            for env_key, env_value in inst.env.items():
                if isinstance(env_value, str) and env_value.startswith("ref:secrets://"):
                    refs.append((inst.name, env_key, env_value))
        if not refs:
            return {}

        service = resolve_secrets_service()
        if service is None:
            listing = ", ".join(f"{name}.{env_key}" for name, env_key, _ in refs)
            raise ValueError(
                "no secrets backend configured (set SECRETS_BACKEND) "
                f"for secret refs: {listing}"
            )
        env_map: Dict[str, Dict[str, str]] = {}
        failures: List[str] = []
        for name, env_key, raw in refs:
            resolved, error = _resolve_single_ref(service, raw)
            if error:
                failures.append(f"{name}.{env_key} ({error})")
            else:
                env_map.setdefault(name, {})[env_key] = resolved
        if failures:
            raise ValueError("unresolved secret refs: " + ", ".join(failures))
        logger.info(
            "Resolved %d secret env refs across %d instance(s) for %s",
            sum(len(v) for v in env_map.values()),
            len(env_map),
            desired.metadata.name,
        )
        return env_map

    def _record_assignments(
        self, desired: InfraFile, result: ReconcileResult
    ) -> None:
        """Persist instance -> provider decisions for later inspection.

        Best-effort: a read-only filesystem or a locked store must never
        fail a reconciliation that already succeeded.
        """
        assignments = {i.name: i.provider for i in desired.spec.instances}
        if not assignments:
            return
        try:
            store = ManifestStore()
            store.record_manifest(
                desired.metadata.name,
                assignments,
                error="; ".join(result.errors),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Could not persist provider assignments for %s: %s",
                desired.metadata.name,
                exc,
            )
