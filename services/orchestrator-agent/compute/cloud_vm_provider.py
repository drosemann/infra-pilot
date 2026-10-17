"""Cloud-VM compute provider.

Manages Docker workloads on remote VMs over SSH.  It deliberately does not
talk to cloud APIs (EC2, Hetzner, ...): an operator registers VMs — SSH
endpoint plus total capacity — in a JSON inventory, and this provider
schedules containers onto them, exactly as the Docker provider manages
containers on the local daemon.

Why SSH instead of the Docker API
---------------------------------
Exposing a remote Docker TCP socket is a serious security boundary (root
equivalent over a cleartext port).  Reusing the system ``ssh`` client with
strict host-key verification, ``BatchMode``, and a control-master socket
keeps the transport authenticated and encrypted while allowing the same
``docker run`` semantics.

Architecture
------------
* :class:`~compute.vm_inventory.VMInventory` — persisted VM list with
  capacity accounting and least-loaded placement.
* :class:`~compute.ssh_runner.SSHRunner` — retrying SSH executor with
  host-key verification.
* :mod:`compute.vm_docker` — command builders and ``docker inspect``
  parsers.

Failure handling maps SSH and Docker failures onto the shared provider
error taxonomy; transient SSH failures are retried with backoff inside the
runner.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config import config

from .base import (
    ComputeProvider,
    InstanceAlreadyExistsError,
    InstanceInfo,
    InstanceNotFoundError,
    InstancePowerState,
    InstanceSpec,
    InstanceStats,
    ProviderAuthError,
    ProviderCapabilities,
    ProviderConfigError,
    ProviderConflictError,
    ProviderError,
    ProviderPermissionError,
    ProviderUnavailableError,
)
from .registry import provider
from .ssh_runner import (
    SSHAuthError,
    SSHCommandError,
    SSHConnectionError,
    SSHError,
    SSHHostKeyError,
    SSHRunner,
    classify_failure,
)
from .vm_docker import (
    build_disk_usage_command,
    build_inspect_command,
    build_inspect_ids_command,
    build_list_command,
    build_listening_ports_command,
    build_load_command,
    build_logs_command,
    build_remove_command,
    build_run_command,
    build_save_command,
    build_stats_command,
    instance_labels,
    parse_df_output,
    parse_inspect,
    parse_listening_ports,
    parse_stats,
    parse_version,
    sanitize_container_name,
)
from .vm_inventory import (
    InsufficientCapacityError,
    VMInventory,
    VMInventoryError,
    VMNotFoundError,
    VMRecord,
)

logger = logging.getLogger(__name__)


@provider
class CloudVMProvider(ComputeProvider):
    """Docker-on-remote-VM provider using SSH transport."""

    name = "cloud-vm"

    def __init__(
        self,
        inventory: Optional[VMInventory] = None,
        ssh_runner: Optional[SSHRunner] = None,
        inventory_file: Optional[str] = None,
        default_vm: Optional[str] = None,
        managed_by: Optional[str] = None,
        docker_bin: Optional[str] = None,
    ):
        self._managed_by = managed_by or config.K8S_MANAGED_BY or "infra-pilot"
        self._docker_bin = docker_bin or config.CLOUD_VM_DOCKER_BIN or "docker"
        self._default_vm = default_vm or ""
        self._inventory = inventory or VMInventory(
            path=inventory_file or config.CLOUD_VM_INVENTORY_FILE,
            default_user=config.CLOUD_VM_SSH_USER,
            default_port=config.CLOUD_VM_SSH_PORT,
            default_ssh_key=config.CLOUD_VM_SSH_KEY,
        )
        self._ssh = ssh_runner or SSHRunner(
            key_path=config.CLOUD_VM_SSH_KEY,
            known_hosts=config.CLOUD_VM_KNOWN_HOSTS,
            strict_host_key=config.CLOUD_VM_STRICT_HOST_KEY,
            user=config.CLOUD_VM_SSH_USER,
            port=config.CLOUD_VM_SSH_PORT,
            connect_timeout=config.CLOUD_VM_SSH_CONNECT_TIMEOUT,
            command_timeout=config.CLOUD_VM_COMMAND_TIMEOUT,
            retries=config.CLOUD_VM_SSH_RETRIES,
            backoff=config.CLOUD_VM_SSH_RETRY_BACKOFF,
            controlmaster=config.CLOUD_VM_CONTROLMASTER,
            control_path=config.CLOUD_VM_CONTROL_PATH,
            control_persist=config.CLOUD_VM_CONTROL_PERSIST,
        )

    # ------------------------------------------------------------------
    # Capabilities / introspection
    # ------------------------------------------------------------------
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_snapshots=False,
            supports_backups=False,
            supports_resize=True,
            supports_load_balancer=False,
            max_instances=0,
            regions=[],
            supports_exec=True,
            supports_stream=False,
            supports_logs=True,
            supports_env=True,
            supports_volumes=True,
            supports_namespaces=False,
            supports_ingress=False,
            supports_replicas=False,
            supports_autoscaling=False,
            supports_ssh=True,
            workload_kinds=["docker"],
            runtime="docker-over-ssh",
            notes="Remote Docker via SSH; VM capacity from the inventory",
        )

    @property
    def inventory(self) -> VMInventory:
        return self._inventory

    # ------------------------------------------------------------------
    # Error mapping
    # ------------------------------------------------------------------
    def _ssh_host(self, record: VMRecord) -> str:
        return record.host

    def _run_on(
        self,
        record: VMRecord,
        argv: List[str],
        timeout: Optional[int] = None,
        check: bool = False,
    ):
        command = self._ssh.quote_args(argv)
        return self._ssh.run(record.host, command, timeout=timeout, check=check)

    def _translate(self, exc: Exception, action: str, name: str = "") -> ProviderError:
        if isinstance(exc, ProviderError):
            return exc
        target = f" {name!r}" if name else ""
        if isinstance(exc, SSHAuthError):
            return ProviderAuthError(
                f"SSH authentication failed during {action}{target}: {exc}"
            )
        if isinstance(exc, SSHHostKeyError):
            return ProviderPermissionError(
                f"SSH host key verification failed during {action}{target}: {exc}"
            )
        if isinstance(exc, SSHConnectionError):
            return ProviderUnavailableError(
                f"could not reach VM during {action}{target}: {exc}"
            )
        if isinstance(exc, SSHCommandError):
            stderr = exc.stderr.lower()
            if "no such container" in stderr or "no such object" in stderr:
                return InstanceNotFoundError(
                    f"container for {action}{target} not found: {exc.stderr.strip()}"
                )
            if "permission denied" in stderr:
                return ProviderPermissionError(
                    f"permission denied during {action}{target}: {exc.stderr.strip()}"
                )
            return ProviderError(
                f"remote docker {action}{target} failed: {exc.stderr.strip()}"
            )
        if isinstance(exc, VMNotFoundError):
            return InstanceNotFoundError(str(exc))
        if isinstance(exc, InsufficientCapacityError):
            return ProviderUnavailableError(str(exc))
        if isinstance(exc, VMInventoryError):
            return ProviderConfigError(str(exc))
        if isinstance(exc, SSHError):
            return ProviderUnavailableError(
                f"SSH failure during {action}{target}: {exc}"
            )
        return ProviderError(f"cloud-vm {action}{target} failed: {exc}")

    def _raise_result(self, result: Any, action: str, name: str = "") -> None:
        """Classify a non-zero SSH/docker result and raise the right error.

        Host-key, auth, and transport failures would otherwise collapse into
        a generic provider error; classifying here keeps the HTTP layer able
        to distinguish "wrong credentials" from "command failed".
        """
        if getattr(result, "ok", False):
            return
        error = classify_failure(result.returncode, result.stderr or "")
        raise self._translate(error, action, name)

    # ------------------------------------------------------------------
    # Placement / inventory
    # ------------------------------------------------------------------
    def _pick_vm(self, spec: InstanceSpec, options: Dict[str, Any]) -> VMRecord:
        preferred = options.get("vm") or self._default_vm or None
        placement_labels = options.get("placement_labels")
        if not isinstance(placement_labels, dict):
            placement_labels = {}
        region = str(options.get("region") or spec.region or "")
        try:
            return self._inventory.place(
                cpu_cores=spec.cpu_cores,
                memory_mb=spec.memory_mb,
                labels=placement_labels,
                region=region,
                preferred=str(preferred) if preferred else None,
                storage_gb=float(spec.storage_gb or 0),
            )
        except InsufficientCapacityError as exc:
            raise ProviderUnavailableError(str(exc)) from exc

    def resolve_vm(self, identifier: str) -> VMRecord:
        try:
            return self._inventory.resolve(identifier)
        except VMNotFoundError as exc:
            raise InstanceNotFoundError(str(exc)) from exc

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create(self, spec: InstanceSpec) -> InstanceInfo:
        options = dict(spec.provider_options or {})
        record = self._pick_vm(spec, options)
        name = sanitize_container_name(spec.name)
        options.setdefault("vm", record.name)
        if options.get("manifest") is None and spec.metadata.get("manifest"):
            options["manifest"] = spec.metadata["manifest"]

        # Fail fast when the container already exists: Docker would report
        # a conflict only after pulling/starting, and the inventory must
        # not double-count either way.
        if self._inspect(record, name):
            raise InstanceAlreadyExistsError(
                f"container {name!r} already exists on {record.name}"
            )
        conflict = self._port_conflict(record, spec, name)
        if conflict:
            raise ProviderConflictError(
                f"host port {conflict} is already bound on {record.name}"
            )

        storage_gb = float(spec.storage_gb or 0)
        if storage_gb:
            options.setdefault("extra_labels", {})
            options["extra_labels"]["storage-gb"] = f"{storage_gb:g}"

        argv = build_run_command(name, spec, options, self._docker_bin)
        try:
            result = self._run_on(record, argv)
        except SSHError as exc:
            if self._adopt_after_failure(record, name, spec):
                logger.warning(
                    "SSH failed during create of %s but the container exists; "
                    "adopting it",
                    name,
                )
                self._reserve(record, spec, storage_gb)
                return await self.get(f"{record.name}/{name}")
            raise self._translate(exc, "create", spec.name)
        if not result.ok:
            stderr = (result.stderr or "").lower()
            if "already in use" in stderr or "conflict" in stderr:
                raise InstanceAlreadyExistsError(
                    f"container {name!r} already exists on {record.name}"
                )
            if isinstance(
                classify_failure(result.returncode, result.stderr or ""),
                SSHConnectionError,
            ):
                if self._adopt_after_failure(record, name, spec):
                    logger.warning(
                        "connection lost during create of %s but the container "
                        "exists; adopting it",
                        name,
                    )
                    self._reserve(record, spec, storage_gb)
                    return await self.get(f"{record.name}/{name}")
            self._raise_result(result, "create", spec.name)

        self._reserve(record, spec, storage_gb)
        container_id = (
            (result.stdout or "").strip().splitlines()[-1] if result.stdout else ""
        )
        logger.info(
            "Created container %s (%s) on VM %s", name, container_id[:12], record.name
        )
        return await self.get(f"{record.name}/{name}")

    def _reserve(self, record: VMRecord, spec: InstanceSpec, storage_gb: float) -> None:
        try:
            self._inventory.reserve(
                record.name,
                spec.cpu_cores,
                spec.memory_mb,
                instance_delta=1,
                storage_gb=storage_gb,
            )
        except VMInventoryError as exc:
            logger.warning(
                "Reservation failed after create for %s: %s",
                sanitize_container_name(spec.name),
                exc,
            )

    def _adopt_after_failure(
        self,
        record: VMRecord,
        name: str,
        spec: InstanceSpec,
    ) -> bool:
        """Verify the container exists after a lost SSH connection.

        A connection drop after ``docker run`` reached the daemon leaves a
        running container with no confirmed response.  Re-inspecting once
        lets us adopt that container (and its reservation) instead of
        reporting a failure the operator would have to debug by hand.
        """
        try:
            observed = self._inspect(record, name)
        except ProviderError:
            return False
        if not observed:
            return False
        labels = observed.get("labels", {}) or {}
        return (
            labels.get("infrapilot.io/instance") == name
            and labels.get("infrapilot.io/managed-by") == self._managed_by
        )

    def _port_conflict(
        self,
        record: VMRecord,
        spec: InstanceSpec,
        name: str,
    ) -> str:
        """Return a requested host port already bound on ``record``.

        ``docker run`` would fail after seconds with a daemon conflict;
        checking the listen table up front turns that into an immediate,
        precise error.  The check is skipped for the container's own name
        (handled by the existence check) and for ports Docker may allocate
        dynamically (``0`` or non-numeric).
        """
        wanted = set()
        for host_port in (spec.ports or {}).values():
            text = str(host_port).rsplit(":", 1)[-1]
            if text.isdigit() and int(text) > 0:
                wanted.add(int(text))
        if not wanted:
            return ""
        try:
            result = self._run_on(
                record, build_listening_ports_command(self._docker_bin)
            )
        except SSHError:
            return ""
        if not result.ok:
            # No ss(8)? Fall through and let Docker decide.
            return ""
        listening = parse_listening_ports(result.stdout or "")
        for port in sorted(wanted & listening):
            return str(port)
        return ""

    def _locate(self, instance_id: str) -> Tuple[VMRecord, str]:
        """Split ``vm/name`` (or bare ``name``) and resolve the VM."""
        if not instance_id:
            raise InstanceNotFoundError("empty instance id")
        if "/" in instance_id:
            vm_name, container_name = instance_id.split("/", 1)
            return self.resolve_vm(vm_name), sanitize_container_name(container_name)
        # Bare name: search the inventory for a container with that name.
        container_name = sanitize_container_name(instance_id)
        for record in self._inventory.list():
            raw = self._inspect(record, container_name)
            if raw:
                return record, container_name
        raise InstanceNotFoundError(instance_id)

    def _inspect(self, record: VMRecord, name: str) -> Dict[str, Any]:
        argv = build_inspect_command([name], self._docker_bin)
        try:
            result = self._run_on(record, argv)
        except SSHError as exc:
            raise self._translate(exc, "inspect", name)
        if not result.ok:
            return {}
        return parse_inspect(result.stdout)

    async def get(self, instance_id: str) -> InstanceInfo:
        record, name = self._locate(instance_id)
        observed = self._inspect(record, name)
        if not observed:
            raise InstanceNotFoundError(instance_id)
        return self._build_instance_info(record, name, observed)

    def _build_instance_info(
        self, record: VMRecord, name: str, observed: Dict[str, Any]
    ) -> InstanceInfo:
        labels = observed.get("labels", {}) or {}
        instance_name = labels.get("infrapilot.io/instance", name)
        created_at = _parse_timestamp(
            observed.get("created_at") or observed.get("started_at")
        )
        spec = InstanceSpec(
            name=instance_name,
            image=observed.get("image", ""),
            cpu_cores=observed.get("cpu_cores", 0.0),
            memory_mb=observed.get("memory_mb", 0),
            storage_gb=0,
            ports=observed.get("ports", {}),
            env_vars=observed.get("env", {}),
            labels=labels,
        )
        return InstanceInfo(
            id=f"{record.name}/{name}",
            name=instance_name,
            provider=self.name,
            status=_map_status(observed.get("status", "unknown")),
            spec=spec,
            created_at=created_at,
            host=record.host,
            private_ips=[record.host],
            public_ips=[record.host],
            metadata={
                "vm": record.name,
                "container": name,
                "container_id": observed.get("id", ""),
                "restarts": observed.get("restart_count", 0),
                "health": observed.get("health_status", ""),
                "runner": "ssh",
            },
        )

    async def list(self) -> List[InstanceInfo]:
        results: List[InstanceInfo] = []
        for record in self._inventory.list():
            argv = build_list_command(self._docker_bin, self._managed_by)
            try:
                result = self._run_on(record, argv)
            except SSHError:
                continue
            if not result.ok:
                continue
            container_ids = [
                line.strip()
                for line in (result.stdout or "").splitlines()
                if line.strip()
            ]
            for container_id in container_ids:
                observed = self._inspect(record, container_id)
                if observed:
                    results.append(
                        self._build_instance_info(
                            record, observed.get("name", container_id), observed
                        )
                    )
        return results

    async def start(self, instance_id: str) -> bool:
        return self._lifecycle(instance_id, ["start"])

    async def stop(self, instance_id: str) -> bool:
        return self._lifecycle(instance_id, ["stop"])

    async def restart(self, instance_id: str) -> bool:
        return self._lifecycle(instance_id, ["restart"])

    async def delete(self, instance_id: str) -> bool:
        record, name = self._locate(instance_id)
        observed = self._inspect(record, name)
        # ``-v`` drops anonymous volumes with the container so repeated
        # deploy/remove cycles do not leak them on the VM.
        argv = build_remove_command(name, volumes=True, docker_bin=self._docker_bin)
        try:
            result = self._run_on(record, argv, check=False)
        except SSHError as exc:
            raise self._translate(exc, "delete", name)
        if not result.ok and "no such container" not in (result.stderr or "").lower():
            self._raise_result(result, "delete", name)
        if observed:
            cpu = observed.get("cpu_cores", 0.0)
            memory = observed.get("memory_mb", 0)
            storage_gb = _storage_from_labels(observed.get("labels") or {})
            try:
                self._inventory.release(
                    record.name,
                    cpu,
                    memory,
                    instance_delta=1,
                    storage_gb=storage_gb,
                )
            except VMInventoryError as exc:
                logger.warning("Could not release capacity for %s: %s", name, exc)
        return True

    def _lifecycle(self, instance_id: str, action: List[str]) -> bool:
        record, name = self._locate(instance_id)
        argv = [self._docker_bin, *action, name]
        try:
            result = self._run_on(record, argv)
        except SSHError as exc:
            raise self._translate(exc, action[0], name)
        if not result.ok:
            self._raise_result(result, action[0], name)
        return True

    async def update(self, instance_id: str, spec: InstanceSpec) -> bool:
        record, name = self._locate(instance_id)
        observed = self._inspect(record, name)
        if not observed:
            raise InstanceNotFoundError(instance_id)
        # Image, published-port, or declared-env changes cannot be applied
        # to a running container; resources alone can (``docker update``).
        if observed.get("image") and observed.get("image") != spec.image:
            await self.delete(instance_id)
            await self.create(spec)
            return True
        if self._ports_differ(spec, observed) or self._env_differ(spec, observed):
            logger.info(
                "Recreating %s: ports/env of the running container differ "
                "from the manifest",
                name,
            )
            await self.delete(instance_id)
            await self.create(spec)
            return True
        argv = [
            self._docker_bin,
            "update",
            "--cpus",
            f"{float(spec.cpu_cores):g}",
            "--memory",
            f"{int(spec.memory_mb)}m",
            name,
        ]
        try:
            result = self._run_on(record, argv)
        except SSHError as exc:
            raise self._translate(exc, "update", name)
        if not result.ok:
            self._raise_result(result, "update", name)
        delta_cpu = float(spec.cpu_cores) - float(observed.get("cpu_cores", 0.0))
        delta_mem = int(spec.memory_mb) - int(observed.get("memory_mb", 0))
        try:
            if delta_cpu > 0 or delta_mem > 0:
                self._inventory.reserve(
                    record.name,
                    max(0.0, delta_cpu),
                    max(0, delta_mem),
                    instance_delta=0,
                )
            elif delta_cpu < 0 or delta_mem < 0:
                self._inventory.release(
                    record.name,
                    -min(0.0, delta_cpu),
                    -min(0, delta_mem),
                    instance_delta=0,
                )
        except VMInventoryError as exc:
            logger.warning("Capacity update failed for %s: %s", name, exc)
        return True

    @staticmethod
    def _ports_differ(spec: InstanceSpec, observed: Dict[str, Any]) -> bool:
        """True when declared ports are not what the container publishes.

        Only a non-empty declaration is compared: a manifest that omits
        ports lets Docker/legacy containers keep whatever they publish.
        """
        desired = {str(k): str(v) for k, v in (spec.ports or {}).items()}
        if not desired:
            return False
        actual = {str(k): str(v) for k, v in (observed.get("ports") or {}).items()}
        return desired != actual

    @staticmethod
    def _env_differ(spec: InstanceSpec, observed: Dict[str, Any]) -> bool:
        """True when any declared env var differs from the container's.

        Only declared keys are compared: the container carries image
        defaults (``PATH`` and friends) that a manifest never lists.
        """
        desired = spec.env_vars or {}
        if not desired:
            return False
        actual = observed.get("env") or {}
        return any(str(actual.get(k)) != str(v) for k, v in desired.items())

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------
    async def stats(self, instance_id: str) -> Optional[InstanceStats]:
        record, name = self._locate(instance_id)
        argv = build_stats_command(name, self._docker_bin)
        try:
            result = self._run_on(record, argv)
        except SSHError:
            return None
        if not result.ok:
            return None
        parsed = parse_stats(result.stdout)
        if not parsed:
            return None
        return InstanceStats(
            cpu_percent=parsed.get("cpu_percent", 0.0),
            memory_percent=parsed.get("memory_percent", 0.0),
            memory_used_bytes=int(parsed.get("memory_used_bytes", 0)),
            memory_total_bytes=0,
            network_rx_bytes=int(parsed.get("network_rx_bytes", 0)),
            network_tx_bytes=int(parsed.get("network_tx_bytes", 0)),
            disk_percent=parsed.get("disk_percent", 0.0),
            collected_at=datetime.now(timezone.utc),
        )

    async def health(self) -> Dict[str, Any]:
        vms = self._inventory.list()
        results: Dict[str, Any] = {}
        reachable = 0
        for record in vms:
            entry: Dict[str, Any] = {"enabled": record.enabled}
            try:
                argv = [self._docker_bin, "version", "--format", "{{.Server.Version}}"]
                result = self._run_on(
                    record, argv, timeout=config.CLOUD_VM_SSH_CONNECT_TIMEOUT
                )
                entry["status"] = "ok" if result.ok else "error"
                entry["docker_version"] = (result.stdout or "").strip()
                if result.ok:
                    reachable += 1
            except SSHError as exc:
                entry["status"] = "unreachable"
                entry["error"] = str(exc)
            results[record.name] = entry
        return {
            "status": "ok" if reachable or not vms else "degraded",
            "vms": results,
            "capacity": self._inventory.capacity(),
        }

    # ------------------------------------------------------------------
    # Exec / logs
    # ------------------------------------------------------------------
    async def execute_command(self, instance_id: str, command: str) -> Tuple[bool, str]:
        record, name = self._locate(instance_id)
        argv = [self._docker_bin, "exec", name, "sh", "-c", command]
        try:
            result = self._run_on(record, argv)
        except SSHError as exc:
            return False, str(self._translate(exc, "exec", name))
        if result.ok:
            return True, result.stdout
        error = classify_failure(result.returncode, result.stderr or "")
        return False, str(self._translate(error, "exec", name))

    async def logs(self, instance_id: str, tail: int = 200) -> str:
        record, name = self._locate(instance_id)
        argv = build_logs_command(name, tail, self._docker_bin)
        try:
            result = self._run_on(record, argv)
        except SSHError as exc:
            raise self._translate(exc, "logs", name)
        if not result.ok:
            self._raise_result(result, "logs", name)
        return result.stdout

    # ------------------------------------------------------------------
    # Drift
    # ------------------------------------------------------------------
    async def detect_drift(self, desired_instances: List[Any]) -> Any:
        """Compare live containers to desired ``InfraInstance`` objects."""
        from manifest.engine import DriftEntry, DriftReport, DriftSeverity

        current = {info.name: info for info in await self.list()}
        desired_names = set()
        entries: List[DriftEntry] = []
        for inst in desired_instances:
            name = getattr(inst, "name", "")
            desired_names.add(name)
            actual = current.get(name)
            if actual is None:
                entries.append(
                    DriftEntry(
                        instance_name=name,
                        field="exists",
                        expected=True,
                        actual=False,
                        severity=DriftSeverity.ERROR,
                        message=f"Container '{name}' is defined but does not exist",
                    )
                )
                continue
            if abs((actual.spec.cpu_cores or 0.0) - getattr(inst, "cpu", 0.0)) > 0.1:
                entries.append(
                    DriftEntry(
                        instance_name=name,
                        field="cpu_cores",
                        expected=inst.cpu,
                        actual=actual.spec.cpu_cores,
                    )
                )
            if actual.spec.memory_mb != getattr(inst, "memory_mb", 0):
                entries.append(
                    DriftEntry(
                        instance_name=name,
                        field="memory_mb",
                        expected=inst.memory_mb,
                        actual=actual.spec.memory_mb,
                    )
                )
            if actual.spec.image != getattr(inst, "image", ""):
                entries.append(
                    DriftEntry(
                        instance_name=name,
                        field="image",
                        expected=inst.image,
                        actual=actual.spec.image,
                    )
                )
        for name in set(current) - desired_names:
            entries.append(
                DriftEntry(
                    instance_name=name,
                    field="exists",
                    expected=False,
                    actual=True,
                    severity=DriftSeverity.WARNING,
                    message=f"Container '{name}' exists but is not in the manifest",
                )
            )
        return DriftReport(
            manifest_name="cloud-vm",
            total_instances=len(desired_instances),
            drifted_instances=len({e.instance_name for e in entries}),
            entries=entries,
        )

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------
    def _storage_from_observed(self, observed: Dict[str, Any]) -> float:
        return _storage_from_labels(observed.get("labels") or {})

    def _spec_from_observed(
        self,
        record: VMRecord,
        name: str,
        observed: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> InstanceSpec:
        """Rebuild the desired spec for a migration target.

        Environment and ports come from the running container, so the
        replica on the target VM starts with the same published surface
        (image-default env vars are carried through unchanged).
        """
        labels = observed.get("labels") or {}
        manifest = labels.get("infrapilot.io/manifest") or ""
        metadata: Dict[str, Any] = {}
        if manifest:
            metadata["manifest"] = manifest
        storage_gb = _storage_from_labels(labels)
        spec = InstanceSpec(
            name=labels.get("infrapilot.io/instance") or name,
            image=observed.get("image", ""),
            cpu_cores=float(observed.get("cpu_cores") or 0.0),
            memory_mb=int(observed.get("memory_mb") or 0),
            storage_gb=int(storage_gb) if storage_gb else 0,
            ports={
                str(k): str(v)
                for k, v in (observed.get("ports") or {}).items()
                if str(v)
            },
            env_vars=dict(observed.get("env") or {}),
            labels=dict(labels),
            metadata=metadata,
            provider_options=options or {},
        )
        return spec

    def _migration_options(
        self,
        target: VMRecord,
        observed: Dict[str, Any],
        source_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Provider options for the target run, preserving custom labels."""
        labels = observed.get("labels") or {}
        options = dict(source_options or {})
        options["vm"] = target.name
        manifest = labels.get("infrapilot.io/manifest") or ""
        if manifest:
            options["manifest"] = manifest
        base = instance_labels("x", vm_name=target.name, manifest=manifest)
        extra = {
            key.split("/", 1)[1]: value
            for key, value in labels.items()
            if key.startswith("infrapilot.io/") and key not in base
        }
        if extra:
            existing = dict(options.get("extra_labels") or {})
            existing.update(extra)
            options["extra_labels"] = existing
        return options

    def _pick_migration_target(
        self,
        source: VMRecord,
        cpu_cores: float,
        memory_mb: int,
        storage_gb: float,
    ) -> VMRecord:
        """Least-loaded enabled VM other than ``source`` that fits."""
        candidates = [
            record
            for record in self._inventory.list(enabled_only=True)
            if record.name != source.name
            and record.can_fit(cpu_cores, memory_mb, storage_gb)
        ]
        if not candidates:
            raise ProviderUnavailableError(
                f"no VM other than {source.name!r} fits "
                f"{cpu_cores} cpu / {memory_mb} MiB"
                + (f" / {storage_gb} GB disk" if storage_gb else "")
            )
        candidates.sort(key=lambda r: (r.utilization(), r.name))
        return candidates[0]

    async def migrate(
        self,
        instance_id: str,
        target_vm: str = "",
        stop_source: bool = True,
    ) -> InstanceInfo:
        """Move a container to another VM: stop, stream image, run, clean up.

        The image is streamed host-to-host (``ssh src docker save | ssh dst
        docker load``) without buffering the tarball on this machine.  The
        source container is stopped first to keep writes consistent, and if
        the target run fails it is started again so a failed migration
        leaves the workload where it was.

        Returns the :class:`InstanceInfo` on the target; idempotent when
        the container already lives on ``target_vm``.
        """
        record, name = self._locate(instance_id)
        observed = self._inspect(record, name)
        if not observed:
            raise InstanceNotFoundError(instance_id)
        storage_gb = self._storage_from_observed(observed)
        cpu_cores = float(observed.get("cpu_cores") or 0.0)
        memory_mb = int(observed.get("memory_mb") or 0)

        if target_vm:
            target = self.resolve_vm(target_vm)
        else:
            target = self._pick_migration_target(
                record, cpu_cores, memory_mb, storage_gb
            )
        if target.name == record.name:
            logger.info("Container %s already runs on %s", name, target.name)
            return await self.get(instance_id)

        image = observed.get("image") or ""
        if not image:
            raise ProviderConfigError(
                f"cannot migrate {name!r}: the running container reports no image"
            )

        options = self._migration_options(target, observed)
        spec = self._spec_from_observed(record, name, observed, options)
        conflict = self._port_conflict(target, spec, name)
        if conflict:
            raise ProviderConflictError(
                f"host port {conflict} is already bound on target {target.name}"
            )

        was_running = bool(observed.get("running"))
        stopped = False
        if was_running and stop_source:
            result = self._run_on(record, [self._docker_bin, "stop", name])
            if not result.ok:
                self._raise_result(result, "stop", name)
            stopped = True

        try:
            producer = self._ssh.build_command(
                record.host,
                self._ssh.quote_args(build_save_command(image, self._docker_bin)),
            )
            consumer = self._ssh.build_command(
                target.host,
                self._ssh.quote_args(build_load_command(self._docker_bin)),
            )
            self._ssh.stream_pipe(
                producer,
                consumer,
                context=f"image migration of {name}",
            )
        except SSHError as exc:
            self._resume_after_failed_migration(record, name, stopped)
            raise self._translate(exc, "migrate", name) from exc

        argv = build_run_command(name, spec, options, self._docker_bin)
        try:
            result = self._run_on(target, argv)
        except SSHError as exc:
            self._resume_after_failed_migration(record, name, stopped)
            raise self._translate(exc, "migrate", name) from exc
        if not result.ok:
            self._resume_after_failed_migration(record, name, stopped)
            stderr = (result.stderr or "").lower()
            if "already in use" in stderr or "conflict" in stderr:
                raise InstanceAlreadyExistsError(
                    f"container {name!r} already exists on {target.name}"
                )
            self._raise_result(result, "migrate", name)

        remove = self._run_on(
            record,
            build_remove_command(name, volumes=True, docker_bin=self._docker_bin),
        )
        if not remove.ok:
            # The target is live; the leftover source copy must stay
            # accounted for until an operator removes it.
            logger.error(
                "Migration of %s to %s succeeded but removing the source "
                "container failed: %s",
                name,
                target.name,
                (remove.stderr or "").strip(),
            )
        else:
            try:
                self._inventory.release(
                    record.name,
                    cpu_cores,
                    memory_mb,
                    instance_delta=1,
                    storage_gb=storage_gb,
                )
            except VMInventoryError as exc:
                logger.warning("Could not release capacity on %s: %s", record.name, exc)
        try:
            self._inventory.reserve(
                target.name,
                cpu_cores,
                memory_mb,
                instance_delta=1,
                storage_gb=storage_gb,
            )
        except VMInventoryError as exc:
            logger.warning(
                "Reservation failed on %s after migration: %s", target.name, exc
            )
        logger.info(
            "Migrated container %s from %s to %s", name, record.name, target.name
        )
        return await self.get(f"{target.name}/{name}")

    def _resume_after_failed_migration(
        self, record: VMRecord, name: str, stopped: bool
    ) -> None:
        if not stopped:
            return
        try:
            result = self._run_on(record, [self._docker_bin, "start", name])
        except SSHError as exc:
            logger.error(
                "Could not restart %s on %s after failed migration: %s",
                name,
                record.name,
                exc,
            )
            return
        if not result.ok:
            logger.error(
                "Could not restart %s on %s after failed migration: %s",
                name,
                record.name,
                (result.stderr or "").strip(),
            )

    # ------------------------------------------------------------------
    # Capacity operations (sync / drain / verify)
    # ------------------------------------------------------------------
    def _inspect_many(self, record: VMRecord, ids: List[str]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        try:
            result = self._run_on(
                record, build_inspect_ids_command(ids, self._docker_bin)
            )
        except SSHError:
            return []
        if not result.ok:
            return []
        try:
            raw = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            return []
        if isinstance(raw, dict):
            raw = [raw]
        return [parse_inspect(item) for item in raw if isinstance(item, dict)]

    async def sync_vm(self, vm_name: str) -> Dict[str, Any]:
        """Recompute reserved capacity on ``vm_name`` from live containers.

        The containers actually running are the source of truth: a crash
        between ``docker run`` and the inventory write, a manual
        ``docker rm``, or an interrupted migration all leave accounting
        behind.  This repairs it in place.
        """
        record = self.resolve_vm(vm_name)
        before = {
            "reserved_cpu": record.reserved_cpu,
            "reserved_memory_mb": record.reserved_memory_mb,
            "reserved_disk_gb": record.reserved_disk_gb,
            "instance_count": record.instance_count,
        }
        try:
            result = self._run_on(
                record, build_list_command(self._docker_bin, self._managed_by)
            )
        except SSHError as exc:
            raise self._translate(exc, "sync", vm_name) from exc
        if not result.ok:
            self._raise_result(result, "sync", vm_name)
        ids = [
            line.strip() for line in (result.stdout or "").splitlines() if line.strip()
        ]
        observed = self._inspect_many(record, ids)
        managed = [
            item
            for item in observed
            if (item.get("labels") or {}).get("infrapilot.io/managed-by")
            == self._managed_by
        ]
        reserved_cpu = round(sum(float(i.get("cpu_cores") or 0.0) for i in managed), 3)
        reserved_memory = int(sum(int(i.get("memory_mb") or 0) for i in managed))
        reserved_disk = round(sum(self._storage_from_observed(i) for i in managed), 3)
        after = self._inventory.set_usage(
            vm_name,
            reserved_cpu,
            reserved_memory,
            len(managed),
            storage_gb=reserved_disk,
        )
        corrected = before != {
            "reserved_cpu": after.reserved_cpu,
            "reserved_memory_mb": after.reserved_memory_mb,
            "reserved_disk_gb": after.reserved_disk_gb,
            "instance_count": after.instance_count,
        }
        if corrected:
            logger.warning(
                "Inventory for %s corrected: %s -> %s",
                vm_name,
                before,
                {
                    "reserved_cpu": after.reserved_cpu,
                    "reserved_memory_mb": after.reserved_memory_mb,
                    "reserved_disk_gb": after.reserved_disk_gb,
                    "instance_count": after.instance_count,
                },
            )
        return {
            "vm": vm_name,
            "containers": len(managed),
            "observed_ids": ids,
            "before": before,
            "after": {
                "reserved_cpu": after.reserved_cpu,
                "reserved_memory_mb": after.reserved_memory_mb,
                "reserved_disk_gb": after.reserved_disk_gb,
                "instance_count": after.instance_count,
            },
            "corrected": corrected,
        }

    async def sync_all(self) -> Dict[str, Any]:
        """Run :meth:`sync_vm` on every enabled VM; unreachable ones report."""
        results: Dict[str, Any] = {}
        failures = 0
        for record in self._inventory.list(enabled_only=True):
            try:
                results[record.name] = await self.sync_vm(record.name)
                results[record.name]["status"] = "ok"
            except ProviderError as exc:
                failures += 1
                results[record.name] = {"status": "error", "error": str(exc)}
        return {
            "vms": results,
            "synced": len(results) - failures,
            "failed": failures,
        }

    async def verify_vm(self, vm_name: str) -> Dict[str, Any]:
        """Probe SSH, the Docker daemon and disk usage on one VM."""
        record = self.resolve_vm(vm_name)
        entry: Dict[str, Any] = {"vm": vm_name, "enabled": record.enabled}
        entry["ssh"] = self._ssh.ping(
            record.host, timeout=config.CLOUD_VM_SSH_CONNECT_TIMEOUT
        )
        if not entry["ssh"]:
            entry["status"] = "unreachable"
            return entry
        try:
            version = self._run_on(
                record,
                [self._docker_bin, "version", "--format", "{{json .}}"],
                timeout=config.CLOUD_VM_SSH_CONNECT_TIMEOUT,
            )
        except SSHError as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)
            return entry
        if not version.ok:
            entry["status"] = "error"
            entry["error"] = (version.stderr or "").strip()
            return entry
        entry["docker"] = parse_version(version.stdout or "") or {
            "version": (version.stdout or "").strip()
        }
        try:
            disk = self._run_on(record, build_disk_usage_command("/"))
        except SSHError:
            disk = None
        if disk is not None and disk.ok:
            entry["disk"] = parse_df_output(disk.stdout or "")
        record = self._inventory.find(vm_name) or record
        entry["capacity"] = record.to_dict()
        entry["status"] = "ok"
        return entry

    def enable_vm(self, vm_name: str) -> Dict[str, Any]:
        """Re-enable placement on a VM (used after maintenance)."""
        record = self._inventory.set_enabled(vm_name, True)
        return record.to_dict()

    def disable_vm(self, vm_name: str) -> Dict[str, Any]:
        """Disable placement and close the multiplexed SSH connection."""
        record = self._inventory.set_enabled(vm_name, False)
        self._ssh.close_control_master(record.host)
        return record.to_dict()

    async def drain_vm(
        self,
        vm_name: str,
        target_vm: str = "",
    ) -> Dict[str, Any]:
        """Migrate every instance off ``vm_name``, then disable it.

        Stops accepting new placements first (so a drain is not raced by a
        concurrent deploy).  Any failed migration leaves the VM enabled and
        is reported so the operator can retry instead of losing workload.
        """
        record = self.resolve_vm(vm_name)
        self._inventory.set_enabled(vm_name, False)
        instances = [
            info for info in await self.list() if info.metadata.get("vm") == vm_name
        ]
        migrated: List[str] = []
        failed: List[Dict[str, str]] = []
        for info in instances:
            try:
                await self.migrate(info.id, target_vm=target_vm)
                migrated.append(info.id)
            except ProviderError as exc:
                failed.append({"instance": info.id, "error": str(exc)})
        if failed:
            self._inventory.set_enabled(vm_name, True)
            logger.warning(
                "Drain of %s incomplete (%d failed); keeping it enabled",
                vm_name,
                len(failed),
            )
        else:
            self._ssh.close_control_master(record.host)
        return {
            "vm": vm_name,
            "instances": [info.id for info in instances],
            "migrated": migrated,
            "failed": failed,
            "disabled": not failed,
        }

    # ------------------------------------------------------------------
    # Diagnosis
    # ------------------------------------------------------------------
    async def diagnose(self, instance_id: str) -> Dict[str, Any]:
        """Classify why an instance is unhealthy, with recent logs."""
        record, name = self._locate(instance_id)
        observed = self._inspect(record, name)
        if not observed:
            raise InstanceNotFoundError(instance_id)
        restarts = int(observed.get("restart_count") or 0)
        health = str(observed.get("health_status") or "")
        running = bool(observed.get("running"))
        exit_code = observed.get("exit_code")
        category, hint = "healthy", "container is running normally"
        if not running:
            category = "stopped"
            hint = (
                f"container exited with code {exit_code}"
                if exit_code not in (None, 0)
                else "container is not running; check the restart policy and logs"
            )
        elif health == "unhealthy":
            category = "unhealthy"
            hint = "the container healthcheck is failing; see recent logs"
        elif restarts > 3:
            category = "flapping"
            hint = f"container restarted {restarts} times; it is likely crashing"
        recent_logs = ""
        try:
            recent_logs = (await self.logs(instance_id, tail=100))[-4000:]
        except ProviderError as exc:
            recent_logs = f"(logs unavailable: {exc})"
        return {
            "instance_id": instance_id,
            "vm": record.name,
            "container": name,
            "status": observed.get("status"),
            "running": running,
            "health": health,
            "restarts": restarts,
            "exit_code": exit_code,
            "image": observed.get("image"),
            "ports": observed.get("ports"),
            "diagnosis": {"category": category, "hint": hint},
            "recent_logs": recent_logs,
        }

    # ------------------------------------------------------------------
    # VM administration (used by operator tooling / API)
    # ------------------------------------------------------------------
    def add_vm(
        self,
        name: str,
        host: str,
        cpu_cores: float,
        memory_mb: int,
        user: str = "",
        port: int = 0,
        ssh_key: str = "",
        region: str = "",
        labels: Optional[Dict[str, str]] = None,
        disk_gb: float = 0.0,
    ) -> VMRecord:
        record = VMRecord(
            name=name,
            host=host,
            cpu_cores=float(cpu_cores),
            memory_mb=int(memory_mb),
            disk_gb=float(disk_gb or 0.0),
            user=user or config.CLOUD_VM_SSH_USER,
            port=port or config.CLOUD_VM_SSH_PORT,
            ssh_key=ssh_key or config.CLOUD_VM_SSH_KEY,
            region=region,
            labels=dict(labels or {}),
        )
        return self._inventory.add(record)

    def update_vm(self, name: str, **changes: Any) -> VMRecord:
        """Update registration fields (endpoint, credentials, capacity)."""
        return self._inventory.update(name, **changes)

    def remove_vm(self, name: str, force: bool = False) -> bool:
        return self._inventory.remove(name, force=force)

    def list_vms(self) -> List[Dict[str, Any]]:
        return [record.to_dict() for record in self._inventory.list()]


def _storage_from_labels(labels: Dict[str, str]) -> float:
    """Read the ``storage-gb`` label written at create time."""
    try:
        return float(labels.get("infrapilot.io/storage-gb") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _map_status(status: str) -> InstancePowerState:
    mapping = {
        "running": InstancePowerState.RUNNING,
        "exited": InstancePowerState.STOPPED,
        "created": InstancePowerState.STOPPED,
        "dead": InstancePowerState.STOPPED,
        "paused": InstancePowerState.PAUSED,
        "restarting": InstancePowerState.RUNNING,
        "removing": InstancePowerState.STOPPED,
    }
    return mapping.get(status, InstancePowerState.UNKNOWN)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        text = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
    return datetime.now(timezone.utc)
