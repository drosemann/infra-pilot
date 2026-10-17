"""Cloud-VM provider tests with a fake SSH transport.

The provider shells out to the remote ``docker`` CLI over SSH, so these
tests substitute the transport with an in-memory docker simulator.  They
cover the command builders/parsers, inventory accounting and locking,
placement, SSH failure classification and retry, the provider error
taxonomy, lifecycle, monitoring, exec, drift, and VM administration.
"""

import json
import shlex
import subprocess
import threading

import pytest
from compute.base import (
    InstanceAlreadyExistsError,
    InstanceNotFoundError,
    InstancePowerState,
    InstanceSpec,
    ProviderAuthError,
    ProviderPermissionError,
    ProviderUnavailableError,
)
from compute.cloud_vm_provider import CloudVMProvider
from compute.file_lock import (
    SKIP_WRITE,
    file_lock,
    read_json,
    update_json_locked,
    write_json_atomic,
)
from compute.ssh_runner import (
    SSHAuthError,
    SSHCommandError,
    SSHConnectionError,
    SSHHostKeyError,
    SSHRunner,
    classify_failure,
)
from compute.vm_docker import (
    build_logs_command,
    build_run_command,
    build_stats_command,
    label_filter,
    parse_inspect,
    parse_stats,
    sanitize_container_name,
)
from compute.vm_inventory import (
    InsufficientCapacityError,
    VMAlreadyExistsError,
    VMInventory,
    VMInventoryError,
    VMNotFoundError,
    VMRecord,
)


# ---------------------------------------------------------------------------
# Fake SSH + docker transport
# ---------------------------------------------------------------------------
def _completed(rc, stdout="", stderr=""):
    return subprocess.CompletedProcess([], rc, stdout, stderr)


class FakeSSH:
    """Parse the ssh argv, simulate ``docker`` on the far side."""

    def __init__(self):
        self.containers = {}
        self.commands = []
        self.hosts = []
        self.transient_failures = 0
        self.host_key_fail = False
        self.auth_fail = False
        self.version_fail = False
        self.exec_fail = False
        self.exec_output = "exec-output\n"
        self.log_output = "log line one\n"

    # -- entry point ------------------------------------------------------
    def __call__(self, argv, timeout):
        try:
            dash = argv.index("--")
        except ValueError:
            dash = len(argv) - 1
        target = argv[dash - 1]
        host = target.split("@", 1)[-1]
        remote = argv[dash + 1] if dash + 1 < len(argv) else ""
        tokens = shlex.split(remote)
        self.hosts.append(host)
        self.commands.append(tokens)

        if self.host_key_fail:
            return _completed(255, "", "Host key verification failed.")
        if self.auth_fail:
            return _completed(255, "", "Permission denied (publickey).")
        if self.transient_failures > 0:
            self.transient_failures -= 1
            return _completed(
                255, "", "kex_exchange_identification: Connection closed by remote host"
            )
        return self._docker(tokens)

    # -- docker simulation ------------------------------------------------
    def _docker(self, tokens):
        if not tokens:
            return _completed(127, "", "command not found")
        sub = tokens[1] if len(tokens) > 1 else ""
        if sub == "run":
            return self._run(tokens)
        if sub == "ps":
            return _completed(0, "\n".join(self.containers) + ("\n" if self.containers else ""))
        if sub == "inspect":
            return self._inspect(tokens[2:])
        if sub in ("start", "stop", "restart"):
            return self._lifecycle(sub, tokens[2])
        if sub == "rm":
            return self._rm(tokens[-1])
        if sub == "update":
            return self._update(tokens)
        if sub == "stats":
            return self._stats(tokens[-1])
        if sub == "logs":
            return _completed(0, self.log_output, "")
        if sub == "exec":
            return self._exec(tokens)
        if sub == "version":
            if self.version_fail:
                return _completed(1, "", "Cannot connect to the Docker daemon")
            return _completed(0, "24.0.7\n", "")
        return _completed(0, "", "")

    def _run(self, tokens):
        name = None
        image = None
        cpus = 0.0
        memory_mb = 0
        labels = {}
        env = []
        ports = {}
        i = 2
        while i < len(tokens):
            token = tokens[i]
            if token == "-d":
                i += 1
            elif token == "--name":
                name = tokens[i + 1]
                i += 2
            elif token in ("--restart", "--memory-swap", "--shm-size", "--network",
                           "--hostname", "--entrypoint", "--user", "--pull",
                           "--cap-add"):
                i += 2
            elif token == "--cpus":
                cpus = float(tokens[i + 1])
                i += 2
            elif token == "--memory":
                memory_mb = int(tokens[i + 1].rstrip("m"))
                i += 2
            elif token == "-p":
                host_port, container = tokens[i + 1].split(":", 1)
                if "/" in container:
                    cport, proto = container.split("/", 1)
                else:
                    cport, proto = container, "tcp"
                ports[f"{cport}/{proto}"] = [{"HostPort": host_port}]
                i += 2
            elif token == "-e":
                env.append(tokens[i + 1])
                i += 2
            elif token == "--label":
                key, value = tokens[i + 1].split("=", 1)
                labels[key] = value
                i += 2
            elif token == "-v":
                i += 2
            elif token == "--privileged":
                i += 1
            elif token.startswith("-"):
                i += 1
            else:
                image = token
                i += 1
                break

        if name in self.containers:
            return _completed(
                1,
                "",
                f'Conflict. The container name "/{name}" is already in use by '
                "container abc.",
            )
        self.containers[name] = {
            "Name": f"/{name}",
            "Id": f"id-{name}-deadbeef",
            "Config": {"Image": image, "Labels": labels, "Env": env},
            "HostConfig": {
                "NanoCpus": int(cpus * 1_000_000_000),
                "Memory": memory_mb * 1024 * 1024,
            },
            "State": {
                "Status": "running",
                "Running": True,
                "StartedAt": "2026-01-01T00:00:00.000000000Z",
            },
            "NetworkSettings": {"Ports": ports},
            "Created": "2026-01-01T00:00:00.000000000Z",
            "RestartCount": 0,
        }
        return _completed(0, f"id-{name}-deadbeef\n", "")

    def _inspect(self, names):
        result = []
        for name in names:
            record = self.containers.get(name)
            if record is None:
                return _completed(1, "", f"Error: No such object: {name}")
            result.append(record)
        return _completed(0, json.dumps(result), "")

    def _lifecycle(self, action, name):
        record = self.containers.get(name)
        if record is None:
            return _completed(1, "", f"Error response from daemon: No such container: {name}")
        if action == "stop":
            record["State"]["Status"] = "exited"
            record["State"]["Running"] = False
        else:
            record["State"]["Status"] = "running"
            record["State"]["Running"] = True
        return _completed(0, name + "\n", "")

    def _rm(self, name):
        if name not in self.containers:
            return _completed(
                1, "", f"Error response from daemon: No such container: {name}"
            )
        del self.containers[name]
        return _completed(0, name + "\n", "")

    def _update(self, tokens):
        name = tokens[-1]
        record = self.containers.get(name)
        if record is None:
            return _completed(1, "", f"Error response from daemon: No such container: {name}")
        i = 2
        while i < len(tokens) - 1:
            if tokens[i] == "--cpus":
                record["HostConfig"]["NanoCpus"] = int(float(tokens[i + 1]) * 1e9)
                i += 2
            elif tokens[i] == "--memory":
                record["HostConfig"]["Memory"] = int(tokens[i + 1].rstrip("m")) * 1024 * 1024
                i += 2
            else:
                i += 1
        return _completed(0, name + "\n", "")

    def _stats(self, name):
        return _completed(
            0,
            json.dumps(
                {
                    "CPUPerc": "12.50%",
                    "MemPerc": "20.00%",
                    "MemUsage": "100MiB / 512MiB",
                    "NetIO": "1.5kB / 2.5kB",
                    "Name": name,
                }
            )
            + "\n",
            "",
        )

    def _exec(self, tokens):
        if self.exec_fail:
            return _completed(1, "", "exec failed")
        return _completed(0, self.exec_output, "")


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------
def make_inventory(tmp_path, vms):
    inventory = VMInventory(path=str(tmp_path / "vms.json"))
    for vm in vms:
        inventory.add(VMRecord(**vm))
    return inventory


def make_provider(tmp_path, vms, default_vm="vm1"):
    fake = FakeSSH()
    sleeps = []
    runner = SSHRunner(
        transport=fake,
        sleep=sleeps.append,
        retries=3,
        backoff=0.01,
        controlmaster=False,
    )
    inventory = make_inventory(tmp_path, vms)
    provider = CloudVMProvider(
        inventory=inventory,
        ssh_runner=runner,
        default_vm=default_vm,
        docker_bin="docker",
    )
    return provider, inventory, fake, sleeps


DEFAULT_VM = {
    "name": "vm1",
    "host": "10.0.0.1",
    "cpu_cores": 4.0,
    "memory_mb": 4096,
    "region": "eu",
}


def _spec(name="web", **kwargs):
    base = dict(
        name=name,
        image="nginx:1.27",
        cpu_cores=0.5,
        memory_mb=512,
        storage_gb=0,
        ports={"80/tcp": "8080"},
    )
    base.update(kwargs)
    return InstanceSpec(**base)


# ---------------------------------------------------------------------------
# vm_docker builders / parsers
# ---------------------------------------------------------------------------
def test_build_run_command_full():
    spec = _spec(ports={"80/tcp": "8080"}, env_vars={"A": "1"})
    argv = build_run_command(
        "web",
        spec,
        {"vm": "vm1", "manifest": "stack", "volumes": ["/data:/data"]},
    )
    assert argv[:3] == ["docker", "run", "-d"]
    assert "--name" in argv and "web" in argv
    assert "--cpus" in argv and "0.5" in argv
    assert "--memory" in argv and "512m" in argv
    assert "-p" in argv and "8080:80" in argv
    assert "-e" in argv and "A=1" in argv
    assert "-v" in argv and "/data:/data" in argv
    assert "infrapilot.io/instance=web" in argv
    assert argv[-1] == "nginx:1.27"


def test_sanitize_container_name_leading_digit():
    assert sanitize_container_name("123 app") == "123-app"
    assert sanitize_container_name("") == "app"


def test_label_filter_variants():
    assert label_filter("web") == "infrapilot.io/instance=web"
    assert label_filter() == "infrapilot.io/managed-by=infra-pilot"


def test_parse_inspect_accepts_list_and_string():
    record = {
        "Name": "/web",
        "Id": "abc",
        "Config": {"Image": "nginx", "Labels": {"x": "y"}, "Env": ["A=1"]},
        "HostConfig": {"NanoCpus": 500_000_000, "Memory": 512 * 1024 * 1024},
        "State": {"Status": "running", "Running": True, "StartedAt": ""},
        "NetworkSettings": {"Ports": {"80/tcp": [{"HostPort": "8080"}]}},
        "RestartCount": 1,
    }
    parsed = parse_inspect(json.dumps([record]))
    assert parsed["name"] == "web"
    assert parsed["cpu_cores"] == 0.5
    assert parsed["memory_mb"] == 512
    assert parsed["ports"] == {"80/tcp": "8080"}
    assert parse_inspect("not json") == {}
    assert parse_inspect([]) == {}


def test_parse_stats_and_commands():
    line = json.dumps(
        {
            "CPUPerc": "12.50%",
            "MemPerc": "20.00%",
            "MemUsage": "100MiB / 512MiB",
            "NetIO": "1.5kB / 2.5kB",
        }
    )
    stats = parse_stats(line)
    assert stats["cpu_percent"] == 12.5
    assert stats["memory_used_bytes"] == 100 * 1024 * 1024
    assert stats["network_rx_bytes"] == 1500
    assert stats["network_tx_bytes"] == 2500
    assert build_stats_command("web")[1] == "stats"
    assert build_logs_command("web", 50)[1:3] == ["logs", "--tail"]
    assert build_logs_command("web", 50)[3] == "50"


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
class TestInventory:
    def test_add_get_list(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        record = inventory.get("vm1")
        assert record.host == "10.0.0.1"
        assert [r.name for r in inventory.list()] == ["vm1"]

    def test_add_duplicate_name_and_host(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        with pytest.raises(VMAlreadyExistsError):
            inventory.add(VMRecord(name="vm1", host="10.0.0.1"))
        with pytest.raises(VMAlreadyExistsError):
            inventory.add(VMRecord(name="vm-other", host="10.0.0.1"))

    def test_get_missing_raises(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        with pytest.raises(VMNotFoundError):
            inventory.get("nope")

    def test_resolve_by_host_and_user(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        assert inventory.resolve("vm1").name == "vm1"
        assert inventory.resolve("10.0.0.1").name == "vm1"
        assert inventory.resolve("root@10.0.0.1").name == "vm1"

    def test_reserve_and_release_floor(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        inventory.reserve("vm1", 2.0, 1024)
        record = inventory.get("vm1")
        assert record.reserved_cpu == 2.0
        assert record.instance_count == 1
        inventory.release("vm1", 8.0, 8192)
        record = inventory.get("vm1")
        assert record.reserved_cpu == 0.0
        assert record.instance_count == 0

    def test_reserve_rejects_oversubscription(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        with pytest.raises(InsufficientCapacityError):
            inventory.reserve("vm1", 8.0, 512)

    def test_remove_requires_force_when_busy(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        inventory.reserve("vm1", 1.0, 256)
        with pytest.raises(VMInventoryError):
            inventory.remove("vm1")
        assert inventory.remove("vm1", force=True) is True

    def test_set_enabled_filters_placement(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        inventory.set_enabled("vm1", False)
        assert inventory.list(enabled_only=True) == []
        with pytest.raises(InsufficientCapacityError):
            inventory.place(1.0, 256)

    def test_capacity_aggregate(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])
        inventory.reserve("vm1", 1.0, 512)
        capacity = inventory.capacity()
        assert capacity["vms"] == 1
        assert capacity["reserved_cpu"] == 1.0
        assert capacity["free_memory_mb"] == 4096 - 512
        assert capacity["instances"] == 1

    def test_placement_prefers_least_loaded(self, tmp_path):
        inventory = make_inventory(
            tmp_path,
            [
                DEFAULT_VM,
                {"name": "vm2", "host": "10.0.0.2", "cpu_cores": 4.0, "memory_mb": 4096},
            ],
        )
        inventory.reserve("vm1", 3.0, 3072)
        chosen = inventory.place(1.0, 512)
        assert chosen.name == "vm2"

    def test_placement_honors_labels_and_region(self, tmp_path):
        inventory = make_inventory(
            tmp_path,
            [
                {"name": "vm1", "host": "10.0.0.1", "cpu_cores": 4.0,
                 "memory_mb": 4096, "labels": {"tier": "edge"}, "region": "eu"},
                {"name": "vm2", "host": "10.0.0.2", "cpu_cores": 4.0,
                 "memory_mb": 4096, "labels": {"tier": "core"}, "region": "us"},
            ],
        )
        chosen = inventory.place(1.0, 512, labels={"tier": "core"}, region="us")
        assert chosen.name == "vm2"
        with pytest.raises(InsufficientCapacityError):
            inventory.place(1.0, 512, region="ap")

    def test_placement_preferred_when_fits(self, tmp_path):
        inventory = make_inventory(
            tmp_path,
            [
                DEFAULT_VM,
                {"name": "vm2", "host": "10.0.0.2", "cpu_cores": 4.0, "memory_mb": 4096},
            ],
        )
        inventory.reserve("vm2", 3.0, 3072)
        assert inventory.place(1.0, 512, preferred="vm2").name == "vm2"

    def test_concurrent_reserve_is_serialized(self, tmp_path):
        inventory = make_inventory(tmp_path, [DEFAULT_VM])

        def worker():
            inventory.reserve("vm1", 2.0, 1024)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        record = inventory.get("vm1")
        assert record.reserved_cpu == 4.0
        assert record.instance_count == 2


def test_vm_record_roundtrip_ignores_unknown():
    record = VMRecord(name="vm1", host="h", cpu_cores=2.0, memory_mb=1024)
    payload = record.to_dict()
    payload["unknown_field"] = "ignored"
    restored = VMRecord.from_dict(payload)
    assert restored.name == "vm1"
    assert restored.free_cpu == 2.0
    assert "utilization" in payload


# ---------------------------------------------------------------------------
# file_lock helpers
# ---------------------------------------------------------------------------
def test_update_json_locked_accumulates(tmp_path):
    path = str(tmp_path / "state.json")

    def bump(current):
        current = dict(current or {})
        current["count"] = current.get("count", 0) + 1
        return current

    update_json_locked(path, bump, default={})
    update_json_locked(path, bump, default={})
    assert read_json(path)["count"] == 2


def test_update_json_locked_skip_write(tmp_path):
    path = str(tmp_path / "state.json")
    write_json_atomic(path, {"count": 5})
    update_json_locked(path, lambda _current: SKIP_WRITE, default={})
    assert read_json(path)["count"] == 5


def test_read_json_default_for_missing(tmp_path):
    assert read_json(str(tmp_path / "absent.json"), default={"x": 1}) == {"x": 1}


def test_file_lock_context(tmp_path):
    with file_lock(str(tmp_path / "target")):
        pass


# ---------------------------------------------------------------------------
# SSH classification / retries
# ---------------------------------------------------------------------------
def test_classify_failure_variants():
    assert isinstance(classify_failure(255, "Host key verification failed."), SSHHostKeyError)
    assert isinstance(classify_failure(255, "Permission denied (publickey)."), SSHAuthError)
    assert isinstance(classify_failure(255, "kex_exchange_identification: closed"), SSHConnectionError)
    assert isinstance(classify_failure(1, "No such container: web"), SSHCommandError)


def test_runner_retries_transient_failures():
    fake = FakeSSH()
    fake.transient_failures = 2
    sleeps = []
    runner = SSHRunner(transport=fake, sleep=sleeps.append, retries=3, backoff=0.01)
    result = runner.run("10.0.0.1", "docker version")
    assert result.ok
    assert len(fake.commands) == 3
    assert len(sleeps) == 2


def test_runner_check_raises_typed_error():
    fake = FakeSSH()
    fake.host_key_fail = True
    runner = SSHRunner(transport=fake, sleep=lambda _s: None, retries=1)
    with pytest.raises(SSHHostKeyError):
        runner.check("10.0.0.1", "true")


# ---------------------------------------------------------------------------
# Provider lifecycle
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_and_get(tmp_path):
    provider, inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    info = await provider.create(_spec())
    assert info.id == "vm1/web"
    assert info.provider == "cloud-vm"
    assert info.status is InstancePowerState.RUNNING
    assert info.host == "10.0.0.1"
    assert info.metadata["vm"] == "vm1"
    assert info.metadata["container"] == "web"
    assert inventory.get("vm1").instance_count == 1
    fetched = await provider.get("vm1/web")
    assert fetched.name == "web"


@pytest.mark.asyncio
async def test_create_duplicate_raises(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    with pytest.raises(InstanceAlreadyExistsError):
        await provider.create(_spec())


@pytest.mark.asyncio
async def test_create_maps_host_key_failure(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    fake.host_key_fail = True
    with pytest.raises(ProviderPermissionError):
        await provider.create(_spec())


@pytest.mark.asyncio
async def test_create_maps_auth_failure(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    fake.auth_fail = True
    with pytest.raises(ProviderAuthError):
        await provider.create(_spec())


@pytest.mark.asyncio
async def test_create_retries_transient_transport(tmp_path):
    provider, _inventory, fake, sleeps = make_provider(tmp_path, [DEFAULT_VM])
    fake.transient_failures = 2
    info = await provider.create(_spec())
    assert info.name == "web"
    assert sleeps


@pytest.mark.asyncio
async def test_create_without_capacity_raises_unavailable(tmp_path):
    provider, _inventory, _fake, _ = make_provider(
        tmp_path, [{"name": "vm1", "host": "10.0.0.1", "cpu_cores": 1.0, "memory_mb": 256}]
    )
    with pytest.raises(ProviderUnavailableError):
        await provider.create(_spec(cpu_cores=2.0, memory_mb=1024))


@pytest.mark.asyncio
async def test_get_missing_raises(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    with pytest.raises(InstanceNotFoundError):
        await provider.get("vm1/ghost")


@pytest.mark.asyncio
async def test_list_returns_containers(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec(name="web"))
    await provider.create(_spec(name="api", ports={}))
    names = {info.name for info in await provider.list()}
    assert names == {"web", "api"}


@pytest.mark.asyncio
async def test_lifecycle_and_delete(tmp_path):
    provider, inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    await provider.stop("vm1/web")
    assert (await provider.get("vm1/web")).status is InstancePowerState.STOPPED
    await provider.start("vm1/web")
    assert (await provider.get("vm1/web")).status is InstancePowerState.RUNNING
    await provider.restart("vm1/web")
    assert await provider.delete("vm1/web") is True
    assert inventory.get("vm1").instance_count == 0
    # Idempotent: a second delete tolerates the missing container.
    assert await provider.delete("vm1/web") is True


@pytest.mark.asyncio
async def test_update_image_recreates(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    await provider.update("vm1/web", _spec(image="nginx:1.28"))
    assert fake.containers["web"]["Config"]["Image"] == "nginx:1.28"


@pytest.mark.asyncio
async def test_update_resources_in_place(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    await provider.update("vm1/web", _spec(cpu_cores=1.0, memory_mb=1024))
    host = fake.containers["web"]["HostConfig"]
    assert host["NanoCpus"] == 1_000_000_000
    assert host["Memory"] == 1024 * 1024 * 1024


# ---------------------------------------------------------------------------
# Monitoring / exec / drift
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_stats_and_logs(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    stats = await provider.stats("vm1/web")
    assert stats.cpu_percent == 12.5
    assert stats.memory_used_bytes == 100 * 1024 * 1024
    assert await provider.logs("vm1/web") == "log line one\n"


@pytest.mark.asyncio
async def test_execute_command(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    ok, output = await provider.execute_command("vm1/web", "echo hi")
    assert ok is True
    assert output == fake.exec_output


@pytest.mark.asyncio
async def test_execute_command_failure(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec())
    fake.exec_fail = True
    ok, message = await provider.execute_command("vm1/web", "false")
    assert ok is False
    assert "exec" in message.lower()


@pytest.mark.asyncio
async def test_health_ok_and_degraded(tmp_path):
    provider, _inventory, fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    health = await provider.health()
    assert health["status"] == "ok"
    assert health["vms"]["vm1"]["status"] == "ok"
    fake.version_fail = True
    degraded = await provider.health()
    assert degraded["status"] == "degraded"
    assert degraded["vms"]["vm1"]["status"] == "error"


@pytest.mark.asyncio
async def test_detect_drift(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    await provider.create(_spec(name="web"))
    await provider.create(_spec(name="stray"))

    class Desired:
        name = "web"
        image = "nginx:2.0"
        cpu = 0.5
        memory_mb = 512

    report = await provider.detect_drift([Desired()])
    fields = {(entry.instance_name, entry.field) for entry in report.entries}
    assert ("web", "image") in fields
    assert ("stray", "exists") in fields


@pytest.mark.asyncio
async def test_detect_drift_missing_instance(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])

    class Desired:
        name = "ghost"
        image = "nginx"
        cpu = 1.0
        memory_mb = 256

    report = await provider.detect_drift([Desired()])
    assert any(entry.field == "exists" and entry.expected is True for entry in report.entries)


# ---------------------------------------------------------------------------
# VM administration
# ---------------------------------------------------------------------------
def test_add_remove_list_vms(tmp_path):
    provider, _inventory, _fake, _ = make_provider(tmp_path, [DEFAULT_VM])
    provider.add_vm("vm2", "10.0.0.2", 2.0, 2048, labels={"tier": "edge"})
    names = {vm["name"] for vm in provider.list_vms()}
    assert names == {"vm1", "vm2"}
    assert provider.remove_vm("vm2") is True
    assert {vm["name"] for vm in provider.list_vms()} == {"vm1"}
