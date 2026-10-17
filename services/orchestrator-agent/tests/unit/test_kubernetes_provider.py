"""Kubernetes provider tests using an in-memory fake cluster.

The provider talks to the cluster through the bundled ``KubernetesClients``
seam, so these tests inject lightweight fakes instead of the real (and
optional) ``kubernetes`` client.  They cover object construction, CRUD and
lifecycle, error-taxonomy mapping, exec/stream/logs, metrics, drift, and
the missing-optional-dependency path.
"""

import json
from datetime import datetime

import pytest
from compute.base import (
    InstanceNotFoundError,
    InstancePowerState,
    InstanceSpec,
    ProviderAuthError,
    ProviderConflictError,
    ProviderPermissionError,
    ProviderUnavailableError,
)
from compute.k8s_builders import (
    build_config_map,
    build_container_ports,
    build_ingress,
    build_pvc,
    build_resources,
    build_secret,
    build_service,
    build_workload,
    instance_selector,
    managed_labels,
    managed_selector,
    map_pod_health,
    parse_workload,
    sanitize_name,
    status_from_health,
)
from compute.kubernetes_provider import (
    DRIFT_REPLICAS_ANNOTATION,
    KubernetesClients,
    KubernetesProvider,
    _parse_cpu_quantity,
    _parse_memory_bytes,
)

import compute.kubernetes_provider as kp


# ---------------------------------------------------------------------------
# Fake Kubernetes API
# ---------------------------------------------------------------------------
class FakeApiError(Exception):
    def __init__(self, status, reason=""):
        super().__init__(f"{status} {reason}")
        self.status = status
        self.reason = reason


class FakeExecChannel:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self._open = True

    def is_open(self):
        return self._open

    def update(self, timeout=None):
        if not self._chunks:
            self._open = False

    def read_stdout(self):
        if self._chunks:
            return self._chunks.pop(0)
        self._open = False
        return ""


def _merge(base, patch):
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return patch
    result = dict(base)
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _select(labels, selector):
    labels = labels or {}
    for clause in (selector or "").split(","):
        if not clause:
            continue
        if "=" not in clause:
            return False
        key, value = clause.split("=", 1)
        if labels.get(key) != value:
            return False
    return True


class FakeCluster:
    """One object exposing every client API the provider calls."""

    def __init__(self, ready=True, with_metrics=True):
        self.namespaces = set()
        self.deployments = {}
        self.statefulsets = {}
        self.services = {}
        self.configmaps = {}
        self.secrets = {}
        self.pvcs = {}
        self.ingresses = {}
        self.pods = []
        self.exec_commands = []
        self.exec_output = "exec-output\n"
        self.stream_chunks = ["chunk-1", "chunk-2"]
        self.log_output = "log line one\n"
        self.pod_ready = ready
        self.restarts = 0
        self.with_metrics = with_metrics
        self.metrics = [
            {"containers": [{"usage": {"cpu": "250m", "memory": "64Mi"}}]}
        ]
        self.fail = {}

    # -- internal helpers -------------------------------------------------
    def _fail_if(self, op):
        if op in self.fail:
            raise self.fail[op]

    def _sync_pods(self, namespace, body):
        labels = ((body.get("spec", {}) or {}).get("template", {}) or {}).get(
            "metadata", {}
        ).get("labels", {})
        instance = labels.get("infrapilot.io/instance", body["metadata"]["name"])
        replicas = int((body.get("spec", {}) or {}).get("replicas") or 0)
        self.pods = [
            p
            for p in self.pods
            if not (
                p["metadata"]["namespace"] == namespace
                and p["metadata"]["labels"].get("infrapilot.io/instance") == instance
            )
        ]
        for index in range(replicas):
            self.pods.append(self._pod(namespace, instance, labels, index))

    def _pod(self, namespace, instance, labels, index):
        ready = self.pod_ready
        container_status = {
            "ready": ready,
            "restartCount": self.restarts,
            "state": {} if ready else {"waiting": {"reason": "CrashLoopBackOff"}},
        }
        return {
            "metadata": {
                "name": f"{instance}-{index:05d}-abcde",
                "namespace": namespace,
                "labels": dict(labels),
            },
            "status": {
                "phase": "Running" if ready else "Pending",
                "containerStatuses": [container_status],
            },
        }

    def _with_status(self, body):
        spec = body.get("spec", {}) or {}
        replicas = int(spec.get("replicas") or 0)
        ready = replicas if self.pod_ready else 0
        result = dict(body)
        result["status"] = {
            "replicas": replicas,
            "readyReplicas": ready,
            "availableReplicas": ready,
            "updatedReplicas": replicas,
        }
        return result

    # -- core -------------------------------------------------------------
    def read_namespace(self, name):
        self._fail_if("read_namespace")
        if name not in self.namespaces:
            raise FakeApiError(404, "not found")
        return {"metadata": {"name": name}}

    def create_namespace(self, body):
        self._fail_if("create_namespace")
        name = body["metadata"]["name"]
        if name in self.namespaces:
            raise FakeApiError(409, "already exists")
        self.namespaces.add(name)
        return body

    def create_namespaced_config_map(self, namespace, body):
        self._fail_if("create_namespaced_config_map")
        self.configmaps[(namespace, body["metadata"]["name"])] = body
        return body

    def patch_namespaced_config_map(self, name, namespace, body):
        self._fail_if("patch_namespaced_config_map")
        self.configmaps[(namespace, name)] = body
        return body

    def delete_namespaced_config_map(self, name, namespace):
        if (namespace, name) not in self.configmaps:
            raise FakeApiError(404, "not found")
        del self.configmaps[(namespace, name)]

    def create_namespaced_secret(self, namespace, body):
        self._fail_if("create_namespaced_secret")
        self.secrets[(namespace, body["metadata"]["name"])] = body
        return body

    def delete_namespaced_secret(self, name, namespace):
        if (namespace, name) not in self.secrets:
            raise FakeApiError(404, "not found")
        del self.secrets[(namespace, name)]

    def create_namespaced_persistent_volume_claim(self, namespace, body):
        self._fail_if("create_namespaced_persistent_volume_claim")
        self.pvcs[(namespace, body["metadata"]["name"])] = body
        return body

    def delete_namespaced_persistent_volume_claim(self, name, namespace):
        if (namespace, name) not in self.pvcs:
            raise FakeApiError(404, "not found")
        del self.pvcs[(namespace, name)]

    def create_namespaced_service(self, namespace, body):
        self._fail_if("create_namespaced_service")
        self.services[(namespace, body["metadata"]["name"])] = body
        return body

    def patch_namespaced_service(self, name, namespace, body):
        self._fail_if("patch_namespaced_service")
        self.services[(namespace, name)] = body
        return body

    def delete_namespaced_service(self, name, namespace):
        if (namespace, name) not in self.services:
            raise FakeApiError(404, "not found")
        del self.services[(namespace, name)]

    def list_namespaced_pod(self, namespace, label_selector=""):
        return {
            "items": [
                p
                for p in self.pods
                if p["metadata"]["namespace"] == namespace
                and _select(p["metadata"]["labels"], label_selector)
            ]
        }

    def connect_get_namespaced_pod_exec(
        self,
        name,
        namespace,
        command=None,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=True,
    ):
        self._fail_if("exec")
        self.exec_commands.append(command)
        if _preload_content:
            return self.exec_output
        return FakeExecChannel(self.stream_chunks)

    def read_namespaced_pod_log(self, name, namespace, tail_lines=200):
        self._fail_if("logs")
        return self.log_output

    # -- apps -------------------------------------------------------------
    def _create_workload(self, store, body, op, app_op):
        self._fail_if(op)
        namespace = body["metadata"].get("namespace") or app_op
        name = body["metadata"]["name"]
        if (namespace, name) in store:
            raise FakeApiError(409, "already exists")
        stored = json.loads(json.dumps(body))
        stored["metadata"].setdefault("namespace", namespace)
        store[(namespace, name)] = stored
        self._sync_pods(namespace, stored)
        return stored

    def create_namespaced_deployment(self, namespace, body):
        return self._create_workload(
            self.deployments, body, "create_namespaced_deployment", namespace
        )

    def create_namespaced_stateful_set(self, namespace, body):
        return self._create_workload(
            self.statefulsets, body, "create_namespaced_stateful_set", namespace
        )

    def read_namespaced_deployment(self, name, namespace):
        self._fail_if("read_namespaced_deployment")
        if (namespace, name) not in self.deployments:
            raise FakeApiError(404, "not found")
        body = dict(self.deployments[(namespace, name)])
        body.setdefault("kind", "Deployment")
        return self._with_status(body)

    def read_namespaced_deployment_status(self, name, namespace):
        return self.read_namespaced_deployment(name, namespace)

    def read_namespaced_stateful_set(self, name, namespace):
        self._fail_if("read_namespaced_stateful_set")
        if (namespace, name) not in self.statefulsets:
            raise FakeApiError(404, "not found")
        body = dict(self.statefulsets[(namespace, name)])
        body.setdefault("kind", "StatefulSet")
        return self._with_status(body)

    def list_namespaced_deployment(self, namespace, label_selector=""):
        return self._list(self.deployments, namespace, label_selector)

    def list_namespaced_stateful_set(self, namespace, label_selector=""):
        return self._list(self.statefulsets, namespace, label_selector)

    def list_deployment_for_all_namespaces(self, label_selector=""):
        return self._list(self.deployments, None, label_selector)

    def list_stateful_set_for_all_namespaces(self, label_selector=""):
        return self._list(self.statefulsets, None, label_selector)

    def _list(self, store, namespace, label_selector):
        items = []
        for (ns, name), body in store.items():
            if namespace is not None and ns != namespace:
                continue
            if not _select(body["metadata"].get("labels", {}), label_selector):
                continue
            full = dict(body)
            full.setdefault("kind", "StatefulSet" if store is self.statefulsets else "Deployment")
            items.append(self._with_status(full))
        return {"items": items}

    def _patch_workload(self, store, name, namespace, body, op):
        self._fail_if(op)
        if (namespace, name) not in store:
            raise FakeApiError(404, "not found")
        merged = _merge(store[(namespace, name)], body)
        store[(namespace, name)] = merged
        self._sync_pods(namespace, merged)
        return merged

    def patch_namespaced_deployment(self, name, namespace, body):
        return self._patch_workload(
            self.deployments, name, namespace, body, "patch_namespaced_deployment"
        )

    def patch_namespaced_stateful_set(self, name, namespace, body):
        return self._patch_workload(
            self.statefulsets, name, namespace, body, "patch_namespaced_stateful_set"
        )

    def delete_namespaced_deployment(self, name, namespace):
        self._fail_if("delete_namespaced_deployment")
        if (namespace, name) not in self.deployments:
            raise FakeApiError(404, "not found")
        del self.deployments[(namespace, name)]

    def delete_namespaced_stateful_set(self, name, namespace):
        self._fail_if("delete_namespaced_stateful_set")
        if (namespace, name) not in self.statefulsets:
            raise FakeApiError(404, "not found")
        del self.statefulsets[(namespace, name)]

    # -- networking / custom / version ------------------------------------
    def create_namespaced_ingress(self, namespace, body):
        self._fail_if("create_namespaced_ingress")
        self.ingresses[(namespace, body["metadata"]["name"])] = body
        return body

    def delete_namespaced_ingress(self, name, namespace):
        if (namespace, name) not in self.ingresses:
            raise FakeApiError(404, "not found")
        del self.ingresses[(namespace, name)]

    def list_namespaced_custom_object(
        self, group, version, namespace, plural, label_selector=""
    ):
        self._fail_if("metrics")
        return {"items": self.metrics}

    def get_code(self):
        self._fail_if("version")
        return {"gitVersion": "v1.29.1"}


@pytest.fixture
def cluster():
    return FakeCluster()


@pytest.fixture
def provider(cluster):
    clients = KubernetesClients(
        core=cluster, apps=cluster, networking=cluster, custom=cluster, version=cluster
    )
    return KubernetesProvider(
        namespace="default",
        namespace_per_app=False,
        wait_enabled=False,
        clients=clients,
    )


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
# Builders (dependency-free translation)
# ---------------------------------------------------------------------------
def test_sanitize_name_falls_back_to_app():
    assert sanitize_name("") == "app"
    assert sanitize_name("My App!") == "my-app"
    assert sanitize_name("-bad-") == "bad"


def test_managed_labels_and_selectors():
    labels = managed_labels("web", manifest="stack")
    assert labels["app.kubernetes.io/managed-by"] == "infra-pilot"
    assert labels["infrapilot.io/instance"] == "web"
    assert labels["infrapilot.io/manifest"] == "stack"
    assert instance_selector("web") == "infrapilot.io/instance=web"
    assert managed_selector() == "app.kubernetes.io/managed-by=infra-pilot"
    assert "infrapilot.io/manifest=stack" in managed_selector(manifest="stack")


def test_build_container_ports_and_resources():
    spec = _spec(ports={"80/tcp": "8080", "53/udp": "5353"})
    ports = build_container_ports(spec)
    assert {p["containerPort"] for p in ports} == {80, 53}
    resources = build_resources(spec, {})
    assert resources["requests"]["cpu"] == "0.5"
    assert resources["requests"]["memory"] == "512Mi"
    assert resources["limits"] == resources["requests"]


def test_build_resources_honors_overrides():
    spec = _spec()
    resources = build_resources(
        spec,
        {"resources": {"limits": {"cpu": "2", "memory": "1Gi"}}},
    )
    assert resources["limits"]["cpu"] == "2"
    assert resources["limits"]["memory"] == "1Gi"
    assert resources["requests"]["cpu"] == "0.5"


def test_build_service_nodeport_maps_node_ports():
    spec = _spec()
    service = build_service("web", spec, {"service_type": "NodePort", "node_ports": {"80": 30080}})
    assert service["spec"]["type"] == "NodePort"
    assert service["spec"]["ports"][0]["nodePort"] == 30080


def test_build_service_is_none_without_ports():
    spec = _spec(ports={})
    assert build_service("web", spec, {}) is None
    assert build_service("web", spec, {"headless_service": True}) is not None


def test_build_ingress_with_tls_and_annotations():
    spec = _spec()
    ingress = build_ingress(
        "web",
        spec,
        {
            "ingress": {
                "host": "app.example.com",
                "path": "/x",
                "tls_secret": "tls-secret",
            },
            "ingress_annotations": {"nginx.ingress.kubernetes.io/rewrite-target": "/"},
        },
    )
    assert ingress["spec"]["rules"][0]["host"] == "app.example.com"
    assert ingress["spec"]["tls"][0]["secretName"] == "tls-secret"
    assert "annotations" in ingress["metadata"]


def test_build_config_map_and_secret():
    spec = _spec(env_vars={"LOG_LEVEL": "info"})
    configmap = build_config_map("web", spec, {"config_env": {"EXTRA": "1"}})
    assert configmap["data"] == {"LOG_LEVEL": "info", "EXTRA": "1"}
    secret = build_secret("web", spec, {"secret_env": {"TOKEN": "abc"}})
    import base64

    assert base64.b64decode(secret["data"]["TOKEN"]).decode() == "abc"


def test_build_pvc_skips_statefulset():
    spec = _spec(storage_gb=5)
    assert build_pvc("web", spec, {}) is not None
    assert build_pvc("web", spec, {"workload": "statefulset"}) is None


def test_build_workload_statefulset_has_volume_claim_templates():
    spec = _spec(storage_gb=5)
    body = build_workload("web", spec, {"workload": "statefulset"})
    assert body["kind"] == "StatefulSet"
    assert body["spec"]["volumeClaimTemplates"][0]["metadata"]["name"] == "data"


def test_build_workload_deployment_defaults():
    body = build_workload("web", _spec(), {})
    assert body["kind"] == "Deployment"
    assert body["spec"]["replicas"] == 1
    assert body["spec"]["selector"]["matchLabels"]["infrapilot.io/instance"] == "web"


def test_parse_workload_extracts_observed_state():
    body = build_workload("web", _spec(env_vars={"A": "b"}), {})
    body["metadata"]["creationTimestamp"] = "2026-01-01T00:00:00Z"
    body["status"] = {"readyReplicas": 1}
    observed = parse_workload(body)
    assert observed["image"] == "nginx:1.27"
    assert observed["cpu_cores"] == 0.5
    assert observed["memory_mb"] == 512
    assert observed["ports"] == {"80/tcp": "80"}
    assert observed["ready_replicas"] == 1


def test_quantity_parsers():
    assert _parse_cpu_quantity("500m") == 0.5
    assert _parse_cpu_quantity("2") == 2.0
    assert _parse_cpu_quantity("100n") == pytest.approx(1e-7)
    assert _parse_memory_bytes("64Mi") == 64 * 1024 * 1024
    assert _parse_memory_bytes("1Gi") == 1024 ** 3
    assert _parse_memory_bytes(None) == 0


def test_pod_health_and_status_helpers():
    healthy = {
        "status": {
            "phase": "Running",
            "containerStatuses": [{"ready": True, "restartCount": 2, "state": {}}],
        }
    }
    health = map_pod_health(healthy)
    assert health == {"ready": True, "phase": "Running", "restarts": 2, "reason": ""}
    assert status_from_health(True, 1, 1) == "running"
    assert status_from_health(True, 0, 0) == "stopped"
    assert status_from_health(False, 1, 0) == "unknown"


# ---------------------------------------------------------------------------
# CRUD / lifecycle
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_deployment(provider, cluster):
    info = await provider.create(_spec())
    assert info.id == "default/web"
    assert info.provider == "kubernetes"
    assert info.status is InstancePowerState.RUNNING
    assert info.spec.image == "nginx:1.27"
    assert info.metadata["namespace"] == "default"
    assert ("default", "web") in cluster.deployments
    assert ("default", "web") in cluster.services


@pytest.mark.asyncio
async def test_create_statefulset(provider, cluster):
    info = await provider.create(
        _spec(storage_gb=5, provider_options={"workload": "statefulset"})
    )
    assert ("default", "web") in cluster.statefulsets
    assert info.metadata["workload"] == "statefulset"


@pytest.mark.asyncio
async def test_create_in_per_app_namespace_creates_namespace(cluster):
    provider = KubernetesProvider(
        namespace="default",
        namespace_per_app=True,
        wait_enabled=False,
        clients=KubernetesClients(core=cluster, apps=cluster, networking=cluster),
    )
    info = await provider.create(_spec(name="team-web"))
    assert info.metadata["namespace"] == "team-web"
    assert "team-web" in cluster.namespaces


@pytest.mark.asyncio
async def test_create_with_explicit_namespace_option(provider, cluster):
    info = await provider.create(_spec(provider_options={"namespace": "team-a"}))
    assert info.metadata["namespace"] == "team-a"
    assert ("team-a", "web") in cluster.deployments


@pytest.mark.asyncio
async def test_create_with_ingress(provider, cluster):
    await provider.create(
        _spec(provider_options={"ingress": {"host": "app.example.com"}})
    )
    assert ("default", "web") in cluster.ingresses


@pytest.mark.asyncio
async def test_create_env_creates_configmap_and_envfrom(provider, cluster):
    info = await provider.create(_spec(env_vars={"LOG_LEVEL": "debug"}))
    assert ("default", "web-config") in cluster.configmaps
    deployment = cluster.deployments[("default", "web")]
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["envFrom"][0]["configMapRef"]["name"] == "web-config"
    assert cluster.configmaps[("default", "web-config")]["data"] == {
        "LOG_LEVEL": "debug"
    }
    assert info.spec.image == "nginx:1.27"


@pytest.mark.asyncio
async def test_get_missing_raises(provider):
    with pytest.raises(InstanceNotFoundError):
        await provider.get("default/absent")


@pytest.mark.asyncio
async def test_list_returns_created_workloads(provider):
    await provider.create(_spec(name="web"))
    await provider.create(_spec(name="api", ports={}))
    names = {info.name for info in await provider.list()}
    assert names == {"web", "api"}


@pytest.mark.asyncio
async def test_stop_and_start_toggle_replicas(provider, cluster):
    await provider.create(_spec())
    await provider.stop("default/web")
    assert cluster.deployments[("default", "web")]["spec"]["replicas"] == 0
    info = await provider.get("default/web")
    assert info.status is InstancePowerState.STOPPED
    await provider.start("default/web")
    assert cluster.deployments[("default", "web")]["spec"]["replicas"] == 1


@pytest.mark.asyncio
async def test_restart_sets_annotation(provider, cluster):
    await provider.create(_spec())
    await provider.restart("default/web")
    annotations = cluster.deployments[("default", "web")]["spec"]["template"]["metadata"]["annotations"]
    assert "kubectl.kubernetes.io/restartedAt" in annotations


@pytest.mark.asyncio
async def test_delete_removes_workload_and_aux(provider, cluster):
    await provider.create(_spec(env_vars={"A": "1"}))
    assert await provider.delete("default/web") is True
    assert ("default", "web") not in cluster.deployments
    assert ("default", "web") not in cluster.services
    assert ("default", "web-config") not in cluster.configmaps


@pytest.mark.asyncio
async def test_delete_keeps_pvc_when_annotated(provider, cluster):
    await provider.create(
        _spec(storage_gb=5, provider_options={"keep_pvc": True})
    )
    assert ("default", "web-data") in cluster.pvcs
    await provider.delete("default/web")
    assert ("default", "web-data") in cluster.pvcs


@pytest.mark.asyncio
async def test_update_changes_image(provider, cluster):
    await provider.create(_spec())
    await provider.update("default/web", _spec(image="nginx:1.28"))
    deployment = cluster.deployments[("default", "web")]
    assert deployment["spec"]["template"]["spec"]["containers"][0]["image"] == "nginx:1.28"


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_conflict_maps_to_conflict_error(provider, cluster):
    cluster.fail["create_namespaced_deployment"] = FakeApiError(409, "exists")
    with pytest.raises(ProviderConflictError):
        await provider.create(_spec())


@pytest.mark.asyncio
async def test_read_forbidden_maps_to_permission_error(provider, cluster):
    cluster.fail["read_namespaced_deployment"] = FakeApiError(403, "forbidden")
    with pytest.raises(ProviderPermissionError):
        await provider.get("default/web")


@pytest.mark.asyncio
async def test_read_unauthorized_maps_to_auth_error(provider, cluster):
    cluster.fail["read_namespaced_deployment"] = FakeApiError(401, "unauthorized")
    with pytest.raises(ProviderAuthError):
        await provider.get("default/web")


@pytest.mark.asyncio
async def test_scale_forbidden_maps_to_permission_error(provider, cluster):
    await provider.create(_spec())
    cluster.fail["patch_namespaced_deployment"] = FakeApiError(403, "forbidden")
    with pytest.raises(ProviderPermissionError):
        await provider.stop("default/web")


@pytest.mark.asyncio
async def test_missing_kubernetes_client_raises_unavailable(monkeypatch):
    monkeypatch.setattr(kp, "_K8S_AVAILABLE", False)
    provider = KubernetesProvider(namespace="default", wait_enabled=False)
    with pytest.raises(ProviderUnavailableError):
        await provider.create(_spec())


@pytest.mark.asyncio
async def test_health_unavailable_without_client(monkeypatch):
    monkeypatch.setattr(kp, "_K8S_AVAILABLE", False)
    provider = KubernetesProvider(namespace="default", wait_enabled=False)
    health = await provider.health()
    assert health["status"] == "unavailable"


# ---------------------------------------------------------------------------
# Monitoring / exec / logs
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_reports_cluster_version(provider):
    health = await provider.health()
    assert health == {"status": "ok", "version": "v1.29.1", "namespace": "default"}


@pytest.mark.asyncio
async def test_health_unreachable(provider, cluster):
    cluster.fail["version"] = FakeApiError(500, "boom")
    health = await provider.health()
    assert health["status"] == "unreachable"


@pytest.mark.asyncio
async def test_stats_sums_pod_usage(provider):
    await provider.create(_spec())
    stats = await provider.stats("default/web")
    assert stats is not None
    assert stats.cpu_percent == 25.0
    assert stats.memory_used_bytes == 64 * 1024 * 1024


@pytest.mark.asyncio
async def test_stats_none_without_metrics_api(cluster):
    clients = KubernetesClients(core=cluster, apps=cluster, custom=None)
    provider = KubernetesProvider(namespace="default", wait_enabled=False, clients=clients)
    await provider.create(_spec())
    assert await provider.stats("default/web") is None


@pytest.mark.asyncio
async def test_execute_command(provider, cluster):
    await provider.create(_spec())
    ok, output = await provider.execute_command("default/web", "echo hi")
    assert ok is True
    assert output == "exec-output\n"
    assert cluster.exec_commands[-1] == ["/bin/sh", "-c", "echo hi"]


@pytest.mark.asyncio
async def test_stream_command_yields_chunks(provider):
    await provider.create(_spec())
    chunks = [chunk async for chunk in provider.stream_command("default/web", "ls")]
    assert chunks == ["chunk-1", "chunk-2"]


@pytest.mark.asyncio
async def test_logs(provider):
    await provider.create(_spec())
    assert await provider.logs("default/web") == "log line one\n"


@pytest.mark.asyncio
async def test_execute_command_without_pods_raises(provider, cluster):
    await provider.create(_spec())
    cluster.pods = []
    with pytest.raises(InstanceNotFoundError):
        await provider.execute_command("default/web", "echo hi")


# ---------------------------------------------------------------------------
# Drift
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_detect_drift_no_drift(provider):
    from manifest.schema import InfraInstance

    await provider.create(_spec(name="web"))
    desired = [
        InfraInstance(
            name="web", provider="kubernetes", image="nginx:1.27", cpu=0.5, memory_mb=512
        )
    ]
    report = await provider.detect_drift(desired)
    assert report.entries == []
    assert report.drifted_instances == 0


@pytest.mark.asyncio
async def test_detect_drift_missing_instance(provider):
    from manifest.schema import InfraInstance

    desired = [InfraInstance(name="ghost", provider="kubernetes", image="nginx:1.27")]
    report = await provider.detect_drift(desired)
    assert any(entry.field == "exists" and entry.expected is True for entry in report.entries)


@pytest.mark.asyncio
async def test_detect_drift_image_and_replica_mismatch(provider):
    from manifest.schema import InfraInstance

    await provider.create(_spec(name="web"))
    desired = [
        InfraInstance(
            name="web",
            provider="kubernetes",
            image="nginx:2.0",
            cpu=0.5,
            memory_mb=512,
            provider_options={"replicas": 3},
        )
    ]
    report = await provider.detect_drift(desired)
    fields = {entry.field for entry in report.entries}
    assert "image" in fields
    assert "replicas" in fields


@pytest.mark.asyncio
async def test_detect_drift_extra_workload(provider):
    from manifest.schema import InfraInstance

    await provider.create(_spec(name="stray"))
    report = await provider.detect_drift([])
    assert any(
        entry.instance_name == "stray" and entry.expected is False
        for entry in report.entries
    )


def test_optional_kubernetes_client_available():
    kubernetes = pytest.importorskip("kubernetes")
    assert kp._K8S_AVAILABLE is True
    assert hasattr(kubernetes, "client")
