"""File-backed inventory of cloud VMs managed over SSH.

``CloudVMProvider`` does not call cloud APIs: an operator (or a bootstrap
script) registers VMs — their SSH endpoint and total resources — and the
provider schedules Docker workloads onto them.  The inventory is persisted
as JSON and guarded by an advisory file lock so concurrent deploy/remove
requests do not lose updates.

Resource accounting is two-sided:

* ``cpu_cores``/``memory_mb``/``disk_gb`` are the VM's total capacity, and
* ``reserved_cpu``/``reserved_memory_mb``/``reserved_disk_gb`` are the
  amounts handed out to InfraFile instances (disk only when the VM
  declares a total, so operators with unknown disk sizes are unaffected).

Placement picks the least-loaded VM that still fits the request.  Live
usage from ``docker stats`` can be layered on by callers that want
utilization-aware placement; reserved capacity alone is enough to avoid
double-booking.  :meth:`VMInventory.set_usage` rewrites the reserved side
from observed containers, which repairs accounting after a crash or a
manual ``docker rm``.

The JSON file is written atomically with a ``.bak`` copy of the previous
state; reads go through :func:`read_json_recovering`, which quarantines a
corrupt file and restores the backup so one bad disk write cannot take the
inventory away.
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .file_lock import (
    file_lock,
    read_json_recovering,
    update_json_locked,
    write_json_atomic,
)

logger = logging.getLogger(__name__)


class VMInventoryError(Exception):
    """Base class for inventory failures."""


class VMNotFoundError(VMInventoryError):
    """The requested VM is not registered."""


class VMAlreadyExistsError(VMInventoryError):
    """A VM with the same name is already registered."""


class InsufficientCapacityError(VMInventoryError):
    """No registered VM can hold the requested workload."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VMRecord:
    """A single remote VM in the inventory."""

    name: str
    host: str
    port: int = 22
    user: str = "root"
    ssh_key: str = ""
    cpu_cores: float = 0.0
    memory_mb: int = 0
    disk_gb: float = 0.0
    region: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    reserved_cpu: float = 0.0
    reserved_memory_mb: int = 0
    reserved_disk_gb: float = 0.0
    instance_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    @property
    def free_cpu(self) -> float:
        return max(0.0, self.cpu_cores - self.reserved_cpu)

    @property
    def free_memory_mb(self) -> int:
        return max(0, int(self.memory_mb - self.reserved_memory_mb))

    @property
    def free_disk_gb(self) -> float:
        if not self.disk_gb:
            return 0.0
        return max(0.0, self.disk_gb - self.reserved_disk_gb)

    def utilization(self) -> float:
        """Return a 0..1 load figure combining CPU, memory and disk."""
        ratios = []
        if self.cpu_cores:
            ratios.append(self.reserved_cpu / self.cpu_cores)
        if self.memory_mb:
            ratios.append(self.reserved_memory_mb / self.memory_mb)
        if self.disk_gb:
            ratios.append(self.reserved_disk_gb / self.disk_gb)
        if not ratios:
            return 0.0
        return sum(ratios) / len(ratios)

    def can_fit(
        self,
        cpu_cores: float,
        memory_mb: int,
        storage_gb: float = 0.0,
    ) -> bool:
        if not self.enabled:
            return False
        if self.cpu_cores and cpu_cores > self.free_cpu:
            return False
        if self.memory_mb and memory_mb > self.free_memory_mb:
            return False
        if storage_gb and self.disk_gb and storage_gb > self.free_disk_gb:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["free_cpu"] = self.free_cpu
        data["free_memory_mb"] = self.free_memory_mb
        data["free_disk_gb"] = self.free_disk_gb
        data["utilization"] = round(self.utilization(), 4)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VMRecord":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class VMInventory:
    """Persisted collection of :class:`VMRecord` objects."""

    def __init__(
        self,
        path: str,
        default_user: str = "root",
        default_port: int = 22,
        default_ssh_key: str = "",
        lock_timeout: float = 10.0,
    ):
        self.path = path
        self.default_user = default_user
        self.default_port = default_port
        self.default_ssh_key = default_ssh_key
        self.lock_timeout = lock_timeout

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _read(self) -> Dict[str, Dict[str, Any]]:
        raw = read_json_recovering(self.path, default=None)
        if raw is None:
            return {}
        if isinstance(raw, dict) and "vms" in raw and isinstance(raw["vms"], dict):
            raw = raw["vms"]
        if isinstance(raw, list):
            records: Dict[str, Dict[str, Any]] = {}
            for item in raw:
                if isinstance(item, dict) and item.get("name"):
                    records[item["name"]] = item
            return records
        if not isinstance(raw, dict):
            logger.warning("Ignoring malformed inventory at %s", self.path)
            return {}
        return raw

    def _write(self, records: Dict[str, Dict[str, Any]]) -> None:
        payload = {
            "version": 1,
            "updated_at": _utcnow(),
            "vms": records,
        }
        write_json_atomic(self.path, payload, mode=0o600, backup=True)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def get(self, name: str) -> VMRecord:
        records = self._read()
        record = records.get(name)
        if record is None:
            raise VMNotFoundError(name)
        return VMRecord.from_dict(record)

    def find(self, name: str) -> Optional[VMRecord]:
        try:
            return self.get(name)
        except VMNotFoundError:
            return None

    def resolve(self, identifier: str) -> VMRecord:
        """Look up a VM by name, or by host/``user@host`` string."""
        records = self._read()
        if identifier in records:
            return VMRecord.from_dict(records[identifier])
        for record in records.values():
            if record.get("host") == identifier:
                return VMRecord.from_dict(record)
            if f"{record.get('user')}@{record.get('host')}" == identifier:
                return VMRecord.from_dict(record)
        raise VMNotFoundError(identifier)

    def list(
        self,
        enabled_only: bool = False,
        region: str = "",
        labels: Optional[Dict[str, str]] = None,
    ) -> List[VMRecord]:
        """Return registered VMs, optionally filtered.

        ``region`` keeps only VMs of that region (empty string disables the
        filter); ``labels`` requires an exact match for every given key.
        """
        records = [VMRecord.from_dict(v) for v in self._read().values()]
        records.sort(key=lambda r: r.name)
        if enabled_only:
            records = [r for r in records if r.enabled]
        if region:
            records = [r for r in records if r.region == region]
        if labels:
            records = [
                r
                for r in records
                if all(r.labels.get(k) == v for k, v in labels.items())
            ]
        return records

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def add(self, record: VMRecord) -> VMRecord:
        if not record.name:
            raise VMInventoryError("VM name is required")
        if not record.host:
            raise VMInventoryError("VM host is required")
        record.user = record.user or self.default_user
        record.port = record.port or self.default_port
        record.ssh_key = record.ssh_key or self.default_ssh_key
        now = _utcnow()
        record.created_at = record.created_at or now
        record.updated_at = now

        def _mutate(current: Dict[str, Any]) -> Dict[str, Any]:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            if (
                record.name in records
                and records[record.name].get("host") == record.host
            ):
                raise VMAlreadyExistsError(record.name)
            # A different VM may already use this endpoint; keep names unique.
            for other_name, other in records.items():
                if other_name != record.name and other.get("host") == record.host:
                    raise VMAlreadyExistsError(
                        f"host {record.host} already registered as {other_name}"
                    )
            records[record.name] = asdict(record)
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return record

    def remove(self, name: str, force: bool = False) -> bool:
        removed = {"value": False}

        def _mutate(current: Dict[str, Any]) -> Any:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            record = records.get(name)
            if record is None:
                return current
            if not force and record.get("instance_count", 0) > 0:
                raise VMInventoryError(
                    f"VM {name!r} still hosts {record['instance_count']} instance(s); "
                    "use force=true to remove"
                )
            records.pop(name)
            removed["value"] = True
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return removed["value"]

    def set_enabled(self, name: str, enabled: bool) -> VMRecord:
        def _mutate(current: Dict[str, Any]) -> Any:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            record = records.get(name)
            if record is None:
                raise VMNotFoundError(name)
            record["enabled"] = enabled
            record["updated_at"] = _utcnow()
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return self.get(name)

    def reserve(
        self,
        name: str,
        cpu_cores: float,
        memory_mb: int,
        instance_delta: int = 1,
        storage_gb: float = 0.0,
    ) -> VMRecord:
        """Reserve capacity for a new instance on ``name``.

        Raises :class:`InsufficientCapacityError` when the VM cannot fit the
        request, re-checking under the lock so concurrent placements cannot
        oversubscribe.  ``storage_gb`` is only enforced on VMs that declare
        a ``disk_gb`` total.
        """

        def _mutate(current: Dict[str, Any]) -> Any:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            record = records.get(name)
            if record is None:
                raise VMNotFoundError(name)
            candidate = VMRecord.from_dict(record)
            if not candidate.can_fit(cpu_cores, memory_mb, storage_gb):
                raise InsufficientCapacityError(
                    f"VM {name!r} cannot fit {cpu_cores} cpu / {memory_mb} MiB"
                    + (f" / {storage_gb} GB disk" if storage_gb else "")
                )
            record["reserved_cpu"] = candidate.reserved_cpu + cpu_cores
            record["reserved_memory_mb"] = candidate.reserved_memory_mb + memory_mb
            if storage_gb:
                record["reserved_disk_gb"] = round(
                    candidate.reserved_disk_gb + storage_gb, 3
                )
            record["instance_count"] = candidate.instance_count + instance_delta
            record["updated_at"] = _utcnow()
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return self.get(name)

    def release(
        self,
        name: str,
        cpu_cores: float,
        memory_mb: int,
        instance_delta: int = 1,
        storage_gb: float = 0.0,
    ) -> VMRecord:
        """Release previously reserved capacity (never below zero)."""

        def _mutate(current: Dict[str, Any]) -> Any:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            record = records.get(name)
            if record is None:
                raise VMNotFoundError(name)
            record["reserved_cpu"] = max(
                0.0, float(record.get("reserved_cpu", 0.0)) - cpu_cores
            )
            record["reserved_memory_mb"] = max(
                0, int(record.get("reserved_memory_mb", 0)) - memory_mb
            )
            record["reserved_disk_gb"] = max(
                0.0, round(float(record.get("reserved_disk_gb", 0.0)) - storage_gb, 3)
            )
            record["instance_count"] = max(
                0, int(record.get("instance_count", 0)) - instance_delta
            )
            record["updated_at"] = _utcnow()
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return self.get(name)

    def set_usage(
        self,
        name: str,
        cpu_cores: float,
        memory_mb: int,
        instance_count: int,
        storage_gb: float = 0.0,
    ) -> VMRecord:
        """Replace reserved figures with observed ones (absolute set).

        Used by ``CloudVMProvider.sync_vm`` to repair accounting after a
        crash, a manual ``docker rm``, or a partially applied migration:
        the containers actually running on the VM are the source of truth.
        """

        def _mutate(current: Dict[str, Any]) -> Any:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            record = records.get(name)
            if record is None:
                raise VMNotFoundError(name)
            record["reserved_cpu"] = max(0.0, round(cpu_cores, 3))
            record["reserved_memory_mb"] = max(0, int(memory_mb))
            record["reserved_disk_gb"] = max(0.0, round(storage_gb, 3))
            record["instance_count"] = max(0, int(instance_count))
            record["updated_at"] = _utcnow()
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return self.get(name)

    def update(self, name: str, **changes: Any) -> VMRecord:
        """Update mutable registration fields of ``name``.

        Allowed keys: ``host``, ``port``, ``user``, ``ssh_key``, ``region``,
        ``labels``, ``metadata``, ``cpu_cores``, ``memory_mb``, ``disk_gb``.
        Unknown keys raise :class:`VMInventoryError` so a typo cannot be
        silently dropped.
        """
        allowed = {
            "host",
            "port",
            "user",
            "ssh_key",
            "region",
            "labels",
            "metadata",
            "cpu_cores",
            "memory_mb",
            "disk_gb",
        }
        unknown = sorted(set(changes) - allowed)
        if unknown:
            raise VMInventoryError(f"cannot update fields: {', '.join(unknown)}")
        if not changes:
            return self.get(name)

        def _mutate(current: Dict[str, Any]) -> Any:
            records = current.get("vms", current) if isinstance(current, dict) else {}
            record = records.get(name)
            if record is None:
                raise VMNotFoundError(name)
            for key, value in changes.items():
                if value is None:
                    continue
                record[key] = value
            record["updated_at"] = _utcnow()
            return {"version": 1, "updated_at": _utcnow(), "vms": records}

        update_json_locked(
            self.path, _mutate, default={"vms": {}}, timeout=self.lock_timeout
        )
        return self.get(name)

    # ------------------------------------------------------------------
    # Placement
    # ------------------------------------------------------------------
    def place(
        self,
        cpu_cores: float,
        memory_mb: int,
        labels: Optional[Dict[str, str]] = None,
        region: str = "",
        preferred: Optional[str] = None,
        live_usage: Optional[Dict[str, Dict[str, float]]] = None,
        storage_gb: float = 0.0,
    ) -> VMRecord:
        """Return the least-loaded VM that fits the request.

        ``labels`` must all match a VM's labels (scheduling constraints).
        ``region`` filters by region when non-empty.  ``preferred`` pins to
        a named VM when it fits.  ``live_usage`` maps VM name to observed
        ``{"cpu": .., "memory": ..}`` figures, weighted with reserved
        capacity so a busy-but-empty VM is not chosen over a quieter one.
        ``storage_gb`` additionally constrains VMs that declare a disk.
        """
        constraints = labels or {}
        candidates: List[VMRecord] = []
        for record in self.list(enabled_only=True):
            if region and record.region and record.region != region:
                continue
            if any(record.labels.get(k) != v for k, v in constraints.items()):
                continue
            if not record.can_fit(cpu_cores, memory_mb, storage_gb):
                continue
            candidates.append(record)
        if not candidates:
            raise InsufficientCapacityError(
                f"no VM fits {cpu_cores} cpu / {memory_mb} MiB "
                f"(region={region!r}, labels={constraints})"
            )
        if preferred:
            for record in candidates:
                if record.name == preferred:
                    return record
            logger.warning(
                "Preferred VM %s does not fit; falling back to least-loaded", preferred
            )

        def score(record: VMRecord) -> tuple:
            live = (live_usage or {}).get(record.name, {})
            live_cpu = float(live.get("cpu", 0.0)) / 100.0
            live_mem = float(live.get("memory", 0.0)) / 100.0
            projected_cpu = record.reserved_cpu + cpu_cores
            projected_mem = record.reserved_memory_mb + memory_mb
            cpu_ratio = projected_cpu / record.cpu_cores if record.cpu_cores else 0.0
            mem_ratio = projected_mem / record.memory_mb if record.memory_mb else 0.0
            return (cpu_ratio + live_cpu + mem_ratio + live_mem, record.name)

        candidates.sort(key=score)
        return candidates[0]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def capacity(self) -> Dict[str, Any]:
        """Aggregate capacity/usage across all registered VMs."""
        records = self.list()
        total_cpu = sum(r.cpu_cores for r in records)
        total_mem = sum(r.memory_mb for r in records)
        total_disk = sum(r.disk_gb for r in records)
        used_cpu = sum(r.reserved_cpu for r in records)
        used_mem = sum(r.reserved_memory_mb for r in records)
        used_disk = sum(r.reserved_disk_gb for r in records)
        return {
            "vms": len(records),
            "enabled_vms": sum(1 for r in records if r.enabled),
            "total_cpu": total_cpu,
            "total_memory_mb": total_mem,
            "total_disk_gb": total_disk,
            "reserved_cpu": used_cpu,
            "reserved_memory_mb": used_mem,
            "reserved_disk_gb": used_disk,
            "free_cpu": max(0.0, total_cpu - used_cpu),
            "free_memory_mb": max(0, total_mem - used_mem),
            "free_disk_gb": max(0.0, total_disk - used_disk),
            "instances": sum(r.instance_count for r in records),
        }

    def with_lock(self, target: Optional[str] = None):
        """Expose the underlying lock for callers doing multi-step updates."""
        return file_lock(target or self.path, timeout=self.lock_timeout)
