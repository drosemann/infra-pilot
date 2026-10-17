"""Docker-over-SSH command builders and inspect parsers for the VM provider.

The cloud-VM provider does not use the Docker SDK against remote hosts (that
would require exposing the daemon TCP socket).  Instead it shells out to the
remote ``docker`` CLI over SSH and parses the JSON these commands emit.
Keeping the command construction and parsing here makes both unit-testable
without an SSH connection.

Container identity is expressed with labels so the provider only lists and
removes containers it created:

* ``infrapilot.io/managed-by=<managed_by>``
* ``infrapilot.io/instance=<name>``
* ``infrapilot.io/vm=<vm name>``
"""

import json
import re
import shlex
from typing import Any, Dict, List, Optional

from compute.base import InstanceSpec

DEFAULT_PREFIX = "infrapilot.io"
DEFAULT_MANAGED_BY = "infra-pilot"

_NAME_SAFE = re.compile(r"[^a-zA-Z0-9_.-]+")
_PORT_KEY = re.compile(r"^(\d{1,5})/(tcp|udp)$")


def sanitize_container_name(name: str, max_len: int = 63) -> str:
    candidate = _NAME_SAFE.sub("-", (name or "").strip())
    candidate = candidate.strip("-._")
    if not candidate:
        candidate = "app"
    if (
        candidate[0]
        not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ):
        candidate = f"app-{candidate}"
    if len(candidate) > max_len:
        candidate = candidate[:max_len].rstrip("-._")
    return candidate


def instance_labels(
    instance_name: str,
    vm_name: str = "",
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
    extra: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    labels = {
        f"{DEFAULT_PREFIX}/managed-by": managed_by,
        f"{DEFAULT_PREFIX}/instance": sanitize_container_name(instance_name),
    }
    if vm_name:
        labels[f"{DEFAULT_PREFIX}/vm"] = sanitize_container_name(vm_name)
    if manifest:
        labels[f"{DEFAULT_PREFIX}/manifest"] = sanitize_container_name(manifest)
    if extra:
        for key, value in extra.items():
            labels[f"{DEFAULT_PREFIX}/{key}"] = str(value)
    return labels


def label_filter(instance_name: str = "", managed_by: str = DEFAULT_MANAGED_BY) -> str:
    if instance_name:
        return f"{DEFAULT_PREFIX}/instance={sanitize_container_name(instance_name)}"
    return f"{DEFAULT_PREFIX}/managed-by={managed_by}"


# ----------------------------------------------------------------------
# Command builders
# ----------------------------------------------------------------------
def build_run_command(
    name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    docker_bin: str = "docker",
) -> List[str]:
    """Build ``docker run -d`` for an instance spec.

    Returns the argument list *after* the remote ``docker`` binary, so a
    caller serializes it with ``SSHRunner.quote_args``.
    """
    command: List[str] = [
        docker_bin,
        "run",
        "-d",
        "--name",
        sanitize_container_name(name),
        "--restart",
        str(options.get("restart_policy", "unless-stopped")),
    ]
    if spec.cpu_cores:
        command += ["--cpus", f"{float(spec.cpu_cores):g}"]
    if spec.memory_mb:
        command += ["--memory", f"{int(spec.memory_mb)}m"]
    if options.get("memory_swap_mb"):
        command += ["--memory-swap", f"{int(options['memory_swap_mb'])}m"]
    if options.get("shm_size_mb"):
        command += ["--shm-size", f"{int(options['shm_size_mb'])}m"]

    for container_port, host_port in sorted((spec.ports or {}).items()):
        match = _PORT_KEY.fullmatch(str(container_port))
        if not match:
            continue
        protocol = match.group(2)
        suffix = "" if protocol == "tcp" else f"/{protocol}"
        command += ["-p", f"{host_port}:{match.group(1)}{suffix}"]

    for key, value in sorted((spec.env_vars or {}).items()):
        command += ["-e", f"{key}={value}"]

    for key, value in instance_labels(
        name,
        vm_name=str(options.get("vm", "")),
        manifest=str(options.get("manifest", "")),
    ).items():
        command += ["--label", f"{key}={value}"]

    for key, value in sorted((options.get("extra_labels") or {}).items()):
        command += ["--label", f"{key}={value}"]

    if options.get("network"):
        command += ["--network", str(options["network"])]
    if options.get("hostname"):
        command += ["--hostname", str(options["hostname"])]
    if options.get("privileged"):
        command += ["--privileged"]
    if options.get("entrypoint"):
        command += ["--entrypoint", str(options["entrypoint"])]
    if options.get("user"):
        command += ["--user", str(options["user"])]
    if isinstance(options.get("volumes"), list):
        for volume in options["volumes"]:
            command += ["-v", str(volume)]
    if isinstance(options.get("cap_add"), list):
        for cap in options["cap_add"]:
            command += ["--cap-add", str(cap)]
    if options.get("pull_policy"):
        command += ["--pull", str(options["pull_policy"])]

    command += build_health_args(spec, options)

    command.append(spec.image)
    for arg in options.get("command", []) or []:
        command.append(str(arg))
    return command


def build_health_args(
    spec: InstanceSpec,
    options: Dict[str, Any],
) -> List[str]:
    """Build ``docker run`` healthcheck flags for a spec.

    Reads ``spec.health_check`` (forwarded from the manifest's
    ``health_check`` block) or ``options["health_check"]``.  Recognized
    keys: ``cmd`` (string or argv list), ``interval``, ``timeout``,
    ``retries``, ``start_period``; when only ``port``/``path`` are given a
    ``wget`` probe against localhost is synthesized.

    Every flag is emitted as a single ``--flag=value`` token so both the
    Docker CLI and the unit-test transport parse it without ambiguity.
    """
    health = spec.health_check or options.get("health_check") or {}
    if not isinstance(health, dict) or not health:
        return []

    cmd = health.get("cmd") or health.get("command") or ""
    if not cmd:
        port = health.get("port") or ""
        path = str(health.get("path") or "/")
        if port:
            if not path.startswith("/"):
                path = "/" + path
            cmd = (
                f"wget -q -O- http://127.0.0.1:{int(port)}{path} >/dev/null "
                "|| exit 1"
            )
    if not cmd:
        return []
    if isinstance(cmd, (list, tuple)):
        cmd = " ".join(shlex.quote(str(part)) for part in cmd)

    args = [f"--health-cmd={cmd}"]
    if health.get("interval"):
        args.append(f"--health-interval={health['interval']}")
    if health.get("timeout"):
        args.append(f"--health-timeout={health['timeout']}")
    if health.get("retries") is not None:
        args.append(f"--health-retries={int(health['retries'])}")
    if health.get("start_period"):
        args.append(f"--health-start-period={health['start_period']}")
    return args


def build_inspect_command(names: List[str], docker_bin: str = "docker") -> List[str]:
    return [docker_bin, "inspect", *names]


def build_list_command(
    docker_bin: str = "docker", managed_by: str = DEFAULT_MANAGED_BY
) -> List[str]:
    return [
        docker_bin,
        "ps",
        "-aq",
        "--filter",
        f"label={DEFAULT_PREFIX}/managed-by={managed_by}",
    ]


def build_stats_command(name: str, docker_bin: str = "docker") -> List[str]:
    return [
        docker_bin,
        "stats",
        "--no-stream",
        "--format",
        "{{json .}}",
        sanitize_container_name(name),
    ]


def build_logs_command(
    name: str, tail: int = 200, docker_bin: str = "docker"
) -> List[str]:
    return [
        docker_bin,
        "logs",
        "--tail",
        str(int(tail)),
        sanitize_container_name(name),
    ]


def build_save_command(image: str, docker_bin: str = "docker") -> List[str]:
    """``docker image save`` writes a tarball to stdout (migration source)."""
    return [docker_bin, "image", "save", image]


def build_load_command(docker_bin: str = "docker") -> List[str]:
    """``docker image load`` reads a tarball from stdin (migration target)."""
    return [docker_bin, "image", "load"]


def build_remove_command(
    name: str,
    volumes: bool = False,
    docker_bin: str = "docker",
) -> List[str]:
    command = [docker_bin, "rm", "-f"]
    if volumes:
        command.append("-v")
    command.append(sanitize_container_name(name))
    return command


def build_rename_command(
    old_name: str,
    new_name: str,
    docker_bin: str = "docker",
) -> List[str]:
    return [
        docker_bin,
        "rename",
        sanitize_container_name(old_name),
        sanitize_container_name(new_name),
    ]


def build_ps_json_command(
    docker_bin: str = "docker",
    managed_by: str = DEFAULT_MANAGED_BY,
    instance_name: str = "",
    all_containers: bool = True,
) -> List[str]:
    """``docker ps`` one JSON object per line, filtered to our labels.

    Used by ``CloudVMProvider.sync_vm`` to enumerate managed containers
    without a full ``docker inspect`` of every container on the host.
    """
    command = [docker_bin, "ps"]
    if all_containers:
        command.append("-a")
    command += [
        "--format",
        "{{json .}}",
        "--filter",
        label_filter(instance_name, managed_by),
    ]
    return command


def build_inspect_ids_command(
    ids: List[str],
    docker_bin: str = "docker",
) -> List[str]:
    """Inspect many containers in one round trip (sync/verify paths)."""
    if not ids:
        return [docker_bin, "version", "--format", "{{json .}}"]
    return [docker_bin, "inspect", *ids]


def build_disk_usage_command(path: str = "/", shell_bin: str = "df") -> List[str]:
    """POSIX ``df`` in 1024-byte blocks plus header, for VM disk figures."""
    return [shell_bin, "-Pk", path]


def build_listening_ports_command(shell_bin: str = "ss") -> List[str]:
    """TCP listen sockets without headers (port pre-check before docker run)."""
    return [shell_bin, "-ltnH"]


def build_top_command(name: str, docker_bin: str = "docker") -> List[str]:
    return [docker_bin, "top", sanitize_container_name(name)]


# ----------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------
def parse_ps_lines(raw: Any) -> List[Dict[str, Any]]:
    """Parse ``docker ps --format '{{json .}}'`` output (one JSON per line).

    Returns dicts with ``id``, ``names``, ``image``, ``state``, ``status``,
    ``labels`` (decoded) and ``ports`` (raw publish string) — enough for
    sync/accounting without inspecting each container.
    """
    if isinstance(raw, (list, tuple)):
        lines = [str(line) for line in raw]
    else:
        lines = str(raw or "").splitlines()
    containers: List[Dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        containers.append(
            {
                "id": str(data.get("ID") or data.get("Id") or ""),
                "names": str(data.get("Names") or data.get("Name") or ""),
                "image": str(data.get("Image") or ""),
                "state": str(data.get("State") or ""),
                "status": str(data.get("Status") or ""),
                "labels": parse_label_string(data.get("Labels")),
                "ports": str(data.get("Ports") or ""),
            }
        )
    return containers


def parse_label_string(raw: Any) -> Dict[str, str]:
    """Decode Docker's ``a=b,c=d`` label formatting."""
    labels: Dict[str, str] = {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    for part in str(raw or "").split(","):
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            labels[key.strip()] = value.strip()
        elif part:
            labels[part] = ""
    return labels


def parse_df_output(raw: str) -> Dict[str, Any]:
    """Parse ``df -Pk <path>`` into byte figures and a 0..100 load.

    The last non-header line wins (the mounted filesystem that holds
    ``/var/lib/docker`` is what the operator cares about).
    """
    lines = [line for line in str(raw or "").splitlines() if line.strip()]
    if not lines:
        return {}
    fields = lines[-1].split()
    if len(fields) < 5 or fields[0].lower() == "filesystem":
        return {}
    try:
        block_size = int(fields[1])
        total_blocks = int(fields[2])
        used_blocks = int(fields[3])
        available_blocks = int(fields[4])
    except ValueError:
        return {}
    percent_text = fields[5].rstrip("%") if len(fields) > 5 else ""
    try:
        used_percent = float(percent_text)
    except ValueError:
        used_percent = 0.0
    return {
        "total_bytes": block_size * total_blocks,
        "used_bytes": block_size * used_blocks,
        "available_bytes": block_size * available_blocks,
        "used_percent": used_percent,
    }


def parse_listening_ports(raw: str) -> set:
    """Extract bound TCP ports from ``ss -ltnH`` output.

    IPv4, IPv6 and wildcard binds all reduce to the port number so the
    provider can pre-check a requested host port before ``docker run``.
    """
    ports = set()
    for line in str(raw or "").splitlines():
        tokens = line.split()
        if len(tokens) < 4:
            continue
        local = tokens[-2]
        port_text = local.rsplit(":", 1)[-1]
        if port_text.isdigit():
            ports.add(int(port_text))
    return ports


def parse_version(raw: Any) -> Dict[str, str]:
    """Parse ``docker version --format '{{json .}}'`` (or plain text)."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            text = (raw or "").strip()
            return {"version": text.splitlines()[0]} if text else {}
    if not isinstance(raw, dict):
        return {}
    client = raw.get("Client") or {}
    server = raw.get("Server") or {}
    return {
        "version": str(client.get("Version") or raw.get("Version") or ""),
        "server_version": str(server.get("Version") or ""),
        "api_version": str(client.get("ApiVersion") or ""),
    }


def describe_ports(ports: Dict[str, str]) -> str:
    """Human-readable ``80/tcp->8080`` summary for logs and errors."""
    parts = []
    for container_port, host_port in sorted((ports or {}).items()):
        parts.append(f"{container_port}->{host_port}" if host_port else container_port)
    return ", ".join(parts)


def _split_env(entries: Optional[List[str]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for entry in entries or []:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        result[key] = value
    return result


def parse_inspect(raw: Any) -> Dict[str, Any]:
    """Normalize ``docker inspect`` output for one container.

    Accepts the parsed list form or a single dict, returning the same
    observed-state shape the Kubernetes parser produces so drift detection
    reads uniformly.
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if isinstance(raw, list):
        raw = raw[0] if raw else {}
    if not isinstance(raw, dict):
        return {}
    if not raw:
        return {}

    config = raw.get("Config", {}) or {}
    host_config = raw.get("HostConfig", {}) or {}
    state = raw.get("State", {}) or {}
    network = raw.get("NetworkSettings", {}) or {}
    labels = config.get("Labels", {}) or {}

    nano_cpus = host_config.get("NanoCpus") or 0
    if nano_cpus:
        cpu_cores = float(nano_cpus) / 1_000_000_000.0
    else:
        cpu_cores = float(host_config.get("CpuShares") or 0) / 1024.0
    memory_mb = int((host_config.get("Memory") or 0) / (1024 * 1024))

    ports: Dict[str, str] = {}
    port_bindings = network.get("Ports", {}) or {}
    for container_port, bindings in port_bindings.items():
        if bindings:
            host_port = bindings[0].get("HostPort")
            if host_port:
                ports[str(container_port)] = str(host_port)
        else:
            ports[str(container_port)] = ""

    health = state.get("Health", {}) or {}
    return {
        "name": str(raw.get("Name", "")).lstrip("/"),
        "id": raw.get("Id", ""),
        "image": config.get("Image", ""),
        "labels": labels,
        "cpu_cores": cpu_cores,
        "memory_mb": memory_mb,
        "ports": ports,
        "env": _split_env(config.get("Env")),
        "status": str(state.get("Status", "unknown")),
        "running": bool(state.get("Running")),
        "started_at": state.get("StartedAt", ""),
        "created_at": raw.get("Created", ""),
        "health_status": str(health.get("Status", "")),
        "restart_count": int(raw.get("RestartCount") or 0),
        "exit_code": state.get("ExitCode"),
        "error": state.get("Error", ""),
    }


def parse_stats(raw: str) -> Dict[str, float]:
    """Parse one JSON line from ``docker stats --format '{{json .}}'``."""
    text = (raw or "").strip()
    if not text:
        return {}
    line = text.splitlines()[0]
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return {
        "cpu_percent": _to_percent(data.get("CPUPerc")),
        "memory_percent": _to_percent(data.get("MemPerc")),
        "memory_used_bytes": _to_bytes(_segment(data.get("MemUsage", ""), 0)),
        "network_rx_bytes": _to_bytes(_segment(data.get("NetIO", ""), 0)),
        "network_tx_bytes": _to_bytes(_segment(data.get("NetIO", ""), 1)),
        "disk_percent": 0.0,
    }


def _to_percent(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().rstrip("%")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _segment(value: Any, index: int) -> str:
    parts = [p.strip() for p in str(value).split("/")]
    return parts[index] if len(parts) > index else ""


def _to_bytes(value: Any) -> int:
    text = str(value).strip()
    if not text:
        return 0
    units = {
        "B": 1,
        "kB": 1000,
        "MB": 1000**2,
        "GB": 1000**3,
        "KiB": 1024,
        "MiB": 1024**2,
        "GiB": 1024**3,
    }
    for suffix, factor in sorted(units.items(), key=lambda kv: -len(kv[0])):
        if text.endswith(suffix):
            try:
                return int(float(text[: -len(suffix)]) * factor)
            except ValueError:
                return 0
    try:
        return int(float(text))
    except ValueError:
        return 0
