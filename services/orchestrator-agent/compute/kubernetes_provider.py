"""Kubernetes compute provider.

Implements the :class:`~compute.base.ComputeProvider` interface against a
Kubernetes cluster using the official ``kubernetes`` Python client.  The
client is imported lazily so the service runs — and tests pass — without
the optional dependency installed; every cluster call then raises
:class:`ProviderUnavailableError` instead of an ``ImportError``.

Design notes
------------

* **Ownership by labels.** Every object created carries
  ``app.kubernetes.io/managed-by=<managed_by>`` and
  ``<prefix>/instance=<name>``.  Listing and deletion only ever touch
  objects with that label, so the provider coexists with other tooling.
* **One instance = one workload.** Deployments by default, StatefulSets
  when ``provider_options.workload: statefulset``.  A Service, optional
  Ingress, ConfigMap (env), Secret (secret env), and PVC are created
  alongside.
* **Namespaces.** Shared namespace by default (``K8S_NAMESPACE``);
  per-app namespaces when ``K8S_NAMESPACE_PER_APP`` is on, unless the
  manifest pins ``provider_options.namespace``.
* **Error taxonomy.** HTTP 401/403/404/409/5xx map onto the shared
  provider errors so callers and the HTTP layer behave consistently.
* **Drift.** :meth:`detect_drift` compares live workloads against
  ``InfraInstance`` desired state and returns the same ``DriftReport``
  shape the manifest engine uses.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from config import config

from .base import (
    ComputeProvider,
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
from .k8s_builders import (
    DEFAULT_MANAGED_BY,
    DEFAULT_PREFIX,
    build_config_map,
    build_hpa,
    build_ingress,
    build_network_policy,
    build_pdb,
    build_pvc,
    build_secret,
    build_service,
    build_service_account,
    build_workload,
    instance_selector,
    managed_selector,
    map_pod_conditions,
    map_pod_health,
    parse_hpa,
    parse_workload,
    sanitize_name,
    status_from_health,
    summarize_events,
    validate_k8s_options,
)
from .registry import provider

logger = logging.getLogger(__name__)

# Lazy optional dependency.  ``_K8S_AVAILABLE`` gates all cluster access.
try:  # pragma: no cover - exercised via the skip path in tests
    from kubernetes import client as k8s_client
    from kubernetes import config as k8s_config
    from kubernetes.client.rest import ApiException as K8sApiException  # noqa: F401

    _K8S_AVAILABLE = True
except ImportError:  # pragma: no cover - environment dependent
    k8s_client = None
    k8s_config = None

    class K8sApiException(Exception):  # type: ignore[no-redef]
        """Stand-in so except clauses are valid without the client."""

        status = None
        reason = ""

    _K8S_AVAILABLE = False


DRIFT_REPLICAS_ANNOTATION = "infrapilot.io/desired-replicas"
KEEP_PVC_ANNOTATION = "infrapilot.io/keep-pvc"
RESTART_ANNOTATION = "kubectl.kubernetes.io/restartedAt"


@dataclass
class KubernetesClients:
    """Bundle of API clients so tests can inject fakes.

    ``policy``/``autoscaling``/``discovery``/``authorization`` are optional
    extras; newer features (PDB, HPA, RBAC self-checks) skip cleanly when
    they are ``None`` or lack the method the provider needs.
    """

    core: Any
    apps: Any
    networking: Any = None
    custom: Any = None
    version: Any = None
    policy: Any = None
    autoscaling: Any = None
    discovery: Any = None
    authorization: Any = None


def _to_dict(obj: Any) -> Dict[str, Any]:
    """Return a plain dict for either a model object or an existing dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:  # pragma: no cover - defensive
            return {}
    return {}


def _as_list(obj: Any) -> List[Any]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        items = obj.get("items")
        return list(items) if isinstance(items, list) else []
    items = getattr(obj, "items", None)
    if items is None:
        return []
    if callable(items):
        try:
            return list(items())
        except Exception:  # pragma: no cover - defensive
            return []
    return list(items)


def _client_supports(clients: KubernetesClients, attr: str, *methods: str) -> bool:
    """Return whether an optional client exposes the given methods.

    Capability checks never call the API server; they only inspect the
    injected client object, so ``capabilities`` and deletion paths stay
    side-effect free on clusters that lack an API group.
    """
    obj = getattr(clients, attr, None)
    if obj is None:
        return False
    if not methods:
        return True
    return all(callable(getattr(obj, m, None)) for m in methods)


@provider
class KubernetesProvider(ComputeProvider):
    """Manage workloads as instances on a Kubernetes cluster."""

    name = "kubernetes"

    def __init__(
        self,
        kubeconfig: Optional[str] = None,
        context: Optional[str] = None,
        namespace: Optional[str] = None,
        in_cluster: Optional[bool] = None,
        app_label_prefix: Optional[str] = None,
        managed_by: Optional[str] = None,
        clients: Optional[KubernetesClients] = None,
        client_loader: Optional[Any] = None,
        wait_enabled: Optional[bool] = None,
        namespace_per_app: Optional[bool] = None,
    ):
        self._kubeconfig = (
            kubeconfig if kubeconfig is not None else (config.KUBECONFIG or None)
        )
        self._context = context if context is not None else (config.K8S_CONTEXT or None)
        self._namespace = namespace or config.K8S_NAMESPACE or "default"
        self._in_cluster = (
            in_cluster if in_cluster is not None else config.K8S_IN_CLUSTER
        )
        self._prefix = app_label_prefix or config.K8S_APP_LABEL_PREFIX or DEFAULT_PREFIX
        self._managed_by = managed_by or config.K8S_MANAGED_BY or DEFAULT_MANAGED_BY
        self._clients = clients
        self._client_loader = client_loader
        self._wait_enabled = (
            wait_enabled if wait_enabled is not None else config.K8S_WAIT_ENABLED
        )
        self._namespace_per_app = (
            namespace_per_app
            if namespace_per_app is not None
            else config.K8S_NAMESPACE_PER_APP
        )

    # ------------------------------------------------------------------
    # Capabilities / client bootstrap
    # ------------------------------------------------------------------
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_snapshots=False,
            supports_backups=False,
            supports_resize=True,
            supports_firewall=True,
            supports_load_balancer=True,
            max_instances=0,
            regions=[self._namespace],
            supports_exec=True,
            supports_stream=True,
            supports_logs=True,
            supports_env=True,
            supports_volumes=True,
            supports_namespaces=True,
            supports_ingress=True,
            supports_replicas=True,
            supports_autoscaling=True,
            supports_ssh=False,
            workload_kinds=["deployment", "statefulset"],
            runtime="kubernetes",
            notes="Workloads, Services, Ingress, ConfigMap/Secret, PVC",
        )

    def _clients_ready(self) -> KubernetesClients:
        if self._clients is not None:
            return self._clients
        if not _K8S_AVAILABLE:
            raise ProviderUnavailableError(
                "the 'kubernetes' Python client is not installed; install "
                "services/orchestrator-agent/requirements-optional.txt to "
                "enable the kubernetes provider"
            )
        loader = self._client_loader or self._load_clients
        self._clients = loader()
        return self._clients

    def _load_clients(self) -> KubernetesClients:  # pragma: no cover - needs cluster
        loaded = False
        try:
            if self._in_cluster:
                k8s_config.load_incluster_config()
                loaded = True
            elif self._kubeconfig:
                k8s_config.load_kube_config(
                    config_file=self._kubeconfig, context=self._context
                )
                loaded = True
            else:
                try:
                    k8s_config.load_incluster_config()
                    loaded = True
                except Exception:
                    k8s_config.load_kube_config(context=self._context)
                    loaded = True
        except Exception as exc:
            raise ProviderConfigError(
                f"could not load Kubernetes configuration: {exc}"
            ) from exc
        if not loaded:  # pragma: no cover - defensive
            raise ProviderConfigError("no Kubernetes configuration available")
        return KubernetesClients(
            core=k8s_client.CoreV1Api(),
            apps=k8s_client.AppsV1Api(),
            networking=k8s_client.NetworkingV1Api(),
            custom=k8s_client.CustomObjectsApi(),
            version=k8s_client.VersionApi(),
            policy=k8s_client.PolicyV1Api(),
            autoscaling=k8s_client.AutoscalingV2Api(),
            discovery=k8s_client.DiscoveryApi(),
            authorization=k8s_client.AuthorizationV1Api(),
        )

    # ------------------------------------------------------------------
    # Error translation
    # ------------------------------------------------------------------
    def _translate(self, exc: Exception, action: str, name: str = "") -> ProviderError:
        if isinstance(exc, ProviderError):
            return exc
        status = getattr(exc, "status", None)
        reason = getattr(exc, "reason", "") or str(exc)
        target = f" {name!r}" if name else ""
        if status == 401:
            return ProviderAuthError(
                f"Kubernetes authentication failed during {action}{target}: {reason}"
            )
        if status == 403:
            return ProviderPermissionError(
                f"Kubernetes RBAC denied {action}{target}: {reason}"
            )
        if status == 404:
            return InstanceNotFoundError(
                f"Kubernetes resource for {action}{target} not found: {reason}"
            )
        if status == 409:
            return ProviderConflictError(
                f"Kubernetes conflict during {action}{target}: {reason}"
            )
        if status in (429, 500, 502, 503, 504):
            return ProviderUnavailableError(
                f"Kubernetes unavailable during {action}{target}: {reason}"
            )
        return ProviderError(f"Kubernetes {action}{target} failed: {reason}")

    # ------------------------------------------------------------------
    # Namespace helpers
    # ------------------------------------------------------------------
    def _target_namespace(
        self, instance_name: str, options: Optional[Dict[str, Any]] = None
    ) -> str:
        options = options or {}
        explicit = options.get("namespace")
        if isinstance(explicit, str) and explicit:
            return sanitize_name(explicit)
        if self._namespace_per_app:
            return sanitize_name(instance_name)
        return self._namespace

    def _ensure_namespace(self, namespace: str) -> None:
        if namespace == self._namespace or namespace == "default":
            return
        clients = self._clients_ready()
        try:
            clients.core.read_namespace(namespace)
            return
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status not in (404, None):
                raise self._translate(exc, "read namespace", namespace)
        try:
            clients.core.create_namespace(
                body={
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {
                        "name": namespace,
                        "labels": {
                            "app.kubernetes.io/managed-by": self._managed_by,
                        },
                    },
                }
            )
            logger.info("Created namespace %s", namespace)
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status == 409:
                return
            raise self._translate(exc, "create namespace", namespace)

    # ------------------------------------------------------------------
    # Instance id helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _instance_id(namespace: str, name: str) -> str:
        return f"{namespace}/{name}"

    def _parse_instance_id(self, instance_id: str) -> Tuple[str, str]:
        if not instance_id:
            raise InstanceNotFoundError("empty instance id")
        if "/" in instance_id:
            namespace, name = instance_id.split("/", 1)
            return namespace, name
        return self._namespace, instance_id

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def _validate_options(self, options: Dict[str, Any], action: str) -> None:
        """Fail fast on bad ``provider_options`` before touching the cluster."""
        errors = validate_k8s_options(options)
        if errors:
            raise ProviderConfigError(
                f"invalid provider_options during {action}: " + "; ".join(errors)
            )

    async def create(self, spec: InstanceSpec) -> InstanceInfo:
        clients = self._clients_ready()
        options = dict(spec.provider_options or {})
        self._validate_options(options, "create")
        namespace = self._target_namespace(spec.name, options)
        manifest = str(options.get("manifest", "") or spec.metadata.get("manifest", ""))
        name = sanitize_name(spec.name)
        self._ensure_namespace(namespace)

        desired_replicas = options.get("replicas", 1)
        try:
            desired_replicas = int(desired_replicas)
        except (TypeError, ValueError):
            desired_replicas = 1

        configmap = build_config_map(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        secret = build_secret(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        pvc = build_pvc(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        workload = build_workload(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        workload["metadata"].setdefault("annotations", {})[
            DRIFT_REPLICAS_ANNOTATION
        ] = str(desired_replicas)
        if options.get("keep_pvc"):
            workload["metadata"]["annotations"][KEEP_PVC_ANNOTATION] = "true"

        # The pod spec references the ServiceAccount, so create it first.
        self._apply_service_account(clients, namespace, name, options, manifest)

        self._apply_object(
            "configmap",
            lambda: clients.core.create_namespaced_config_map(namespace, configmap),
            configmap,
            namespace,
            name,
        )
        self._apply_object(
            "secret",
            lambda: clients.core.create_namespaced_secret(namespace, secret),
            secret,
            namespace,
            name,
        )
        self._apply_object(
            "pvc",
            lambda: clients.core.create_namespaced_persistent_volume_claim(
                namespace, pvc
            ),
            pvc,
            namespace,
            name,
        )

        try:
            if workload["kind"] == "StatefulSet":
                clients.apps.create_namespaced_stateful_set(namespace, workload)
            else:
                clients.apps.create_namespaced_deployment(namespace, workload)
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status == 409:
                raise ProviderConflictError(
                    f"instance {spec.name!r} already exists in {namespace}"
                ) from exc
            raise self._translate(exc, "create workload", spec.name)

        service = build_service(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        if service is not None and clients.core is not None:
            self._apply_object(
                "service",
                lambda: clients.core.create_namespaced_service(namespace, service),
                service,
                namespace,
                name,
            )

        ingress = build_ingress(
            spec.name,
            spec,
            options,
            self._prefix,
            self._managed_by,
            manifest,
            default_class=config.K8S_INGRESS_CLASS,
            host_suffix=config.K8S_INGRESS_HOST_SUFFIX,
        )
        if ingress is not None and clients.networking is not None:
            self._apply_object(
                "ingress",
                lambda: clients.networking.create_namespaced_ingress(namespace, ingress),
                ingress,
                namespace,
                name,
            )

        self._apply_policy_objects(
            clients, namespace, name, options, manifest, workload["kind"]
        )

        if self._wait_enabled:
            self._wait_for_ready(
                clients, namespace, name, desired_replicas, workload["kind"]
            )

        return await self.get(self._instance_id(namespace, name))

    def _apply_object(
        self,
        kind: str,
        create: Any,
        body: Optional[Dict[str, Any]],
        namespace: str,
        name: str,
    ) -> None:
        """Create an auxiliary object, tolerating "already exists"."""
        if body is None:
            return
        try:
            create()
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status == 409:
                logger.debug("Kubernetes %s for %s already exists", kind, name)
                return
            if status == 403:
                raise self._translate(exc, f"create {kind}", name)
            # 404 on the API path usually means the networking API group is
            # absent; failing the whole create for a missing Ingress/Service
            # capability would be worse than logging it.
            logger.warning("Could not create kubernetes %s for %s: %s", kind, name, exc)

    def _apply_service_account(
        self,
        clients: KubernetesClients,
        namespace: str,
        name: str,
        options: Dict[str, Any],
        manifest: str,
    ) -> None:
        body = build_service_account(
            name, options, self._prefix, self._managed_by, manifest
        )
        if body is None:
            return
        if not _client_supports(clients, "core", "create_namespaced_service_account"):
            logger.warning(
                "Skipping ServiceAccount for %s: core client cannot create them",
                name,
            )
            return
        self._apply_object(
            "serviceaccount",
            lambda: clients.core.create_namespaced_service_account(namespace, body),
            body,
            namespace,
            name,
        )

    def _apply_policy_objects(
        self,
        clients: KubernetesClients,
        namespace: str,
        name: str,
        options: Dict[str, Any],
        manifest: str,
        workload_kind: str,
    ) -> None:
        """Create HPA / PDB / NetworkPolicy alongside a new workload."""
        hpa = build_hpa(
            name,
            options,
            self._prefix,
            self._managed_by,
            manifest,
            target_kind=workload_kind,
        )
        if hpa is not None:
            if _client_supports(
                clients,
                "autoscaling",
                "create_namespaced_horizontal_pod_autoscaler",
            ):
                self._apply_object(
                    "hpa",
                    lambda: clients.autoscaling.create_namespaced_horizontal_pod_autoscaler(
                        namespace, hpa
                    ),
                    hpa,
                    namespace,
                    name,
                )
            else:
                logger.warning(
                    "Skipping HPA for %s: autoscaling API client unavailable", name
                )

        pdb = build_pdb(name, options, self._prefix, self._managed_by, manifest)
        if pdb is not None:
            if _client_supports(
                clients, "policy", "create_namespaced_pod_disruption_budget"
            ):
                self._apply_object(
                    "pdb",
                    lambda: clients.policy.create_namespaced_pod_disruption_budget(
                        namespace, pdb
                    ),
                    pdb,
                    namespace,
                    name,
                )
            else:
                logger.warning(
                    "Skipping PodDisruptionBudget for %s: policy API client "
                    "unavailable",
                    name,
                )

        netpol = build_network_policy(
            name, options, self._prefix, self._managed_by, manifest
        )
        if netpol is not None:
            if _client_supports(
                clients, "networking", "create_namespaced_network_policy"
            ):
                self._apply_object(
                    "networkpolicy",
                    lambda: clients.networking.create_namespaced_network_policy(
                        namespace, netpol
                    ),
                    netpol,
                    namespace,
                    name,
                )
            else:
                logger.warning(
                    "Skipping NetworkPolicy for %s: networking API client cannot "
                    "create policies",
                    name,
                )

    def _patch_aux(
        self,
        kind: str,
        namespace: str,
        name: str,
        patch: Any,
        create: Any,
        body: Optional[Dict[str, Any]],
    ) -> None:
        """Patch an auxiliary object, creating it when it does not exist."""
        try:
            patch()
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status == 404:
                self._apply_object(kind, create, body, namespace, name)
            elif status == 403:
                raise self._translate(exc, f"patch {kind}", name)
            else:
                logger.warning("Could not patch %s for %s: %s", kind, name, exc)

    def _patch_service_account(
        self,
        clients: KubernetesClients,
        namespace: str,
        name: str,
        options: Dict[str, Any],
        manifest: str,
    ) -> None:
        body = build_service_account(
            name, options, self._prefix, self._managed_by, manifest
        )
        if body is None:
            return
        if not _client_supports(
            clients, "core", "patch_namespaced_service_account"
        ):
            logger.warning(
                "Skipping ServiceAccount update for %s: core client cannot patch "
                "them",
                name,
            )
            return
        sa_name = (body.get("metadata", {}) or {}).get("name", name)
        self._patch_aux(
            "serviceaccount",
            namespace,
            name,
            lambda: clients.core.patch_namespaced_service_account(
                sa_name, namespace, body
            ),
            lambda: clients.core.create_namespaced_service_account(namespace, body),
            body,
        )

    def _patch_policy_objects(
        self,
        clients: KubernetesClients,
        namespace: str,
        name: str,
        options: Dict[str, Any],
        manifest: str,
        workload_kind: str,
    ) -> None:
        hpa = build_hpa(
            name,
            options,
            self._prefix,
            self._managed_by,
            manifest,
            target_kind=workload_kind,
        )
        if hpa is not None:
            if _client_supports(
                clients, "autoscaling", "patch_namespaced_horizontal_pod_autoscaler"
            ):
                self._patch_aux(
                    "hpa",
                    namespace,
                    name,
                    lambda: clients.autoscaling.patch_namespaced_horizontal_pod_autoscaler(
                        name, namespace, hpa
                    ),
                    lambda: clients.autoscaling.create_namespaced_horizontal_pod_autoscaler(
                        namespace, hpa
                    ),
                    hpa,
                )
            else:
                logger.warning(
                    "Skipping HPA update for %s: autoscaling API client unavailable",
                    name,
                )

        pdb = build_pdb(name, options, self._prefix, self._managed_by, manifest)
        if pdb is not None:
            if _client_supports(
                clients, "policy", "patch_namespaced_pod_disruption_budget"
            ):
                self._patch_aux(
                    "pdb",
                    namespace,
                    name,
                    lambda: clients.policy.patch_namespaced_pod_disruption_budget(
                        name, namespace, pdb
                    ),
                    lambda: clients.policy.create_namespaced_pod_disruption_budget(
                        namespace, pdb
                    ),
                    pdb,
                )
            else:
                logger.warning(
                    "Skipping PodDisruptionBudget update for %s: policy API client "
                    "unavailable",
                    name,
                )

        netpol = build_network_policy(
            name, options, self._prefix, self._managed_by, manifest
        )
        if netpol is not None:
            if _client_supports(
                clients, "networking", "patch_namespaced_network_policy"
            ):
                self._patch_aux(
                    "networkpolicy",
                    namespace,
                    name,
                    lambda: clients.networking.patch_namespaced_network_policy(
                        name, namespace, netpol
                    ),
                    lambda: clients.networking.create_namespaced_network_policy(
                        namespace, netpol
                    ),
                    netpol,
                )
            else:
                logger.warning(
                    "Skipping NetworkPolicy update for %s: networking API client "
                    "cannot patch policies",
                    name,
                )

    _FATAL_POD_CATEGORIES = frozenset(
        {"image-pull", "crashloop", "config", "unschedulable", "failed"}
    )

    def _fatal_pod_condition(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> Optional[Dict[str, str]]:
        """First pod condition that will not resolve without intervention."""
        for pod in self._pods_for(clients, namespace, name):
            conditions = map_pod_conditions(pod)
            if conditions.get("category") in self._FATAL_POD_CATEGORIES:
                return conditions
        return None

    def _wait_for_ready(
        self,
        clients: KubernetesClients,
        namespace: str,
        name: str,
        replicas: int,
        kind: str = "Deployment",
    ) -> bool:  # pragma: no cover - sleeps against a live cluster
        import time

        if replicas == 0:
            return True
        deadline = time.monotonic() + config.K8S_WAIT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            try:
                if str(kind).lower() == "statefulset":
                    raw = _to_dict(
                        clients.apps.read_namespaced_stateful_set_status(name, namespace)
                    )
                else:
                    raw = _to_dict(
                        clients.apps.read_namespaced_deployment_status(name, namespace)
                    )
            except Exception:
                break
            status = raw.get("status", {}) or {}
            ready = int(status.get("readyReplicas") or 0)
            updated = status.get("updatedReplicas")
            if ready >= replicas and (updated is None or int(updated) >= replicas):
                return True
            fatal = self._fatal_pod_condition(clients, namespace, name)
            if fatal:
                logger.warning(
                    "Stopping wait for %s/%s: %s (%s)",
                    namespace,
                    name,
                    fatal.get("reason", ""),
                    fatal.get("message", ""),
                )
                return False
            time.sleep(2)
        logger.warning("Timed out waiting for %s/%s to become ready", namespace, name)
        return False

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def _read_workload(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> Dict[str, Any]:
        errors: List[Exception] = []
        for kind, reader in (
            ("Deployment", clients.apps.read_namespaced_deployment),
            ("StatefulSet", clients.apps.read_namespaced_stateful_set),
        ):
            try:
                raw = _to_dict(reader(name, namespace))
                if raw:
                    raw.setdefault("kind", kind)
                    return raw
            except Exception as exc:
                status = getattr(exc, "status", None)
                if status == 401:
                    raise self._translate(exc, "read workload", name)
                if status == 403:
                    raise self._translate(exc, "read workload", name)
                errors.append(exc)
        raise InstanceNotFoundError(
            f"no deployment or statefulset {name!r} in namespace {namespace!r}"
        )

    def _list_workloads(
        self, clients: KubernetesClients, namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        selector = managed_selector(self._prefix, self._managed_by)
        results: List[Dict[str, Any]] = []
        for kind, namespaced, all_ns in (
            ("Deployment", "list_namespaced_deployment", "list_deployment_for_all_namespaces"),
            ("StatefulSet", "list_namespaced_stateful_set", "list_stateful_set_for_all_namespaces"),
        ):
            use_all = namespace is None and self._namespace_per_app
            try:
                if use_all:
                    response = getattr(clients.apps, all_ns)(label_selector=selector)
                else:
                    ns = namespace or self._namespace
                    response = getattr(clients.apps, namespaced)(
                        ns, label_selector=selector
                    )
            except Exception as exc:
                status = getattr(exc, "status", None)
                if status == 403 and use_all:
                    # Fall back to the configured namespace without all-ns perms.
                    try:
                        response = getattr(clients.apps, namespaced)(
                            namespace or self._namespace, label_selector=selector
                        )
                    except Exception as inner:
                        logger.warning("Could not list %s: %s", kind, inner)
                        continue
                else:
                    logger.warning("Could not list %s: %s", kind, exc)
                    continue
            for item in _as_list(response):
                raw = _to_dict(item)
                raw.setdefault("kind", kind)
                results.append(raw)
        return results

    def _pods_for(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> List[Dict[str, Any]]:
        try:
            response = clients.core.list_namespaced_pod(
                namespace, label_selector=instance_selector(name, self._prefix)
            )
        except Exception as exc:
            logger.debug("Could not list pods for %s/%s: %s", namespace, name, exc)
            return []
        return [_to_dict(item) for item in _as_list(response)]

    def _health_for(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> Dict[str, Any]:
        pods = self._pods_for(clients, namespace, name)
        if not pods:
            return {"ready": False, "phase": "Unknown", "restarts": 0, "reason": "no pods", "pods": 0}
        aggregated = {"ready": True, "phase": "Running", "restarts": 0, "reason": "", "pods": len(pods)}
        for pod in pods:
            health = map_pod_health(pod)
            aggregated["restarts"] += health["restarts"]
            if not health["ready"]:
                aggregated["ready"] = False
                aggregated["phase"] = health["phase"]
                aggregated["reason"] = health["reason"] or aggregated["reason"]
        return aggregated

    async def get(self, instance_id: str) -> InstanceInfo:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        raw = self._read_workload(clients, namespace, name)
        observed = parse_workload(raw)
        health = self._health_for(clients, namespace, name)
        return self._build_instance_info(namespace, name, observed, health)

    def _build_instance_info(
        self,
        namespace: str,
        name: str,
        observed: Dict[str, Any],
        health: Dict[str, Any],
    ) -> InstanceInfo:
        replicas = int(observed.get("replicas") or 0)
        ready_replicas = int(observed.get("ready_replicas") or 0)
        state_str = status_from_health(health.get("ready", False), replicas, ready_replicas)
        labels = observed.get("labels", {}) or {}
        spec_name = labels.get(f"{self._prefix}/instance", name)
        created_at = _parse_timestamp(observed.get("created_at"))
        spec = InstanceSpec(
            name=spec_name,
            image=observed.get("image", ""),
            cpu_cores=observed.get("cpu_cores", 0.0),
            memory_mb=observed.get("memory_mb", 0),
            storage_gb=0,
            ports=observed.get("ports", {}),
            env_vars=observed.get("env", {}),
            labels=labels,
        )
        return InstanceInfo(
            id=self._instance_id(namespace, name),
            name=spec_name,
            provider=self.name,
            status=_map_power_state(state_str),
            spec=spec,
            created_at=created_at,
            host=f"{name}.{namespace}.svc.cluster.local",
            private_ips=[],
            metadata={
                "namespace": namespace,
                "replicas": replicas,
                "ready_replicas": ready_replicas,
                "restarts": health.get("restarts", 0),
                "health": health,
                "workload": observed.get("workload", "deployment"),
                "annotations": observed.get("annotations", {}),
            },
        )

    async def list(self) -> List[InstanceInfo]:
        clients = self._clients_ready()
        results: List[InstanceInfo] = []
        for raw in self._list_workloads(clients):
            metadata = raw.get("metadata", {}) or {}
            namespace = metadata.get("namespace", self._namespace)
            name = metadata.get("name", "")
            observed = parse_workload(raw)
            health = self._health_for(clients, namespace, name)
            results.append(self._build_instance_info(namespace, name, observed, health))
        return results

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _desired_replicas(self, raw: Dict[str, Any]) -> int:
        annotations = (raw.get("metadata", {}) or {}).get("annotations", {}) or {}
        raw_annotation = annotations.get(DRIFT_REPLICAS_ANNOTATION)
        if raw_annotation is not None:
            try:
                return max(1, int(raw_annotation))
            except (TypeError, ValueError):
                pass
        spec = raw.get("spec", {}) or {}
        return max(1, int(spec.get("replicas") or 1))

    def _scale(self, instance_id: str, replicas: int) -> bool:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        raw = self._read_workload(clients, namespace, name)
        scale_body = {"spec": {"replicas": replicas}}
        try:
            if raw.get("kind") == "StatefulSet":
                clients.apps.patch_namespaced_stateful_set(name, namespace, scale_body)
            else:
                clients.apps.patch_namespaced_deployment(name, namespace, scale_body)
        except Exception as exc:
            raise self._translate(exc, "scale workload", name)
        return True

    async def start(self, instance_id: str) -> bool:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        raw = self._read_workload(clients, namespace, name)
        return self._scale(instance_id, self._desired_replicas(raw))

    async def stop(self, instance_id: str) -> bool:
        return self._scale(instance_id, 0)

    async def restart(self, instance_id: str) -> bool:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        raw = self._read_workload(clients, namespace, name)
        stamp = datetime.now(timezone.utc).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {"annotations": {RESTART_ANNOTATION: stamp}}
                }
            }
        }
        try:
            if raw.get("kind") == "StatefulSet":
                clients.apps.patch_namespaced_stateful_set(name, namespace, body)
            else:
                clients.apps.patch_namespaced_deployment(name, namespace, body)
        except Exception as exc:
            raise self._translate(exc, "restart workload", name)
        return True

    async def delete(self, instance_id: str) -> bool:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        raw = self._read_workload(clients, namespace, name)
        annotations = (raw.get("metadata", {}) or {}).get("annotations", {}) or {}
        keep_pvc = str(annotations.get(KEEP_PVC_ANNOTATION, "")).lower() in (
            "1",
            "true",
            "yes",
        )
        workload_kind = raw.get("kind", "Deployment")
        template_spec = (
            (raw.get("spec", {}) or {}).get("template", {}) or {}
        ).get("spec", {}) or {}
        options = {
            "service_account_name": str(
                template_spec.get("serviceAccountName") or ""
            ),
        }

        if workload_kind == "StatefulSet":
            try:
                clients.apps.delete_namespaced_stateful_set(name, namespace)
            except Exception as exc:
                raise self._translate(exc, "delete statefulset", name)
        else:
            try:
                clients.apps.delete_namespaced_deployment(name, namespace)
            except Exception as exc:
                raise self._translate(exc, "delete deployment", name)

        self._delete_aux(clients, namespace, name, keep_pvc, options)
        return True

    def _delete_aux(
        self,
        clients: KubernetesClients,
        namespace: str,
        name: str,
        keep_pvc: bool,
        options: Dict[str, Any],
    ) -> None:
        def _ignore_404(call: Any, label: str) -> None:
            try:
                call()
            except Exception as exc:
                status = getattr(exc, "status", None)
                if status not in (404, None):
                    logger.warning("Could not delete %s %s/%s: %s", label, namespace, name, exc)

        if clients.networking is not None:
            _ignore_404(
                lambda: clients.networking.delete_namespaced_ingress(name, namespace),
                "ingress",
            )
        if _client_supports(
            clients, "networking", "delete_namespaced_network_policy"
        ):
            _ignore_404(
                lambda: clients.networking.delete_namespaced_network_policy(
                    name, namespace
                ),
                "networkpolicy",
            )
        if _client_supports(
            clients, "autoscaling", "delete_namespaced_horizontal_pod_autoscaler"
        ):
            _ignore_404(
                lambda: clients.autoscaling.delete_namespaced_horizontal_pod_autoscaler(
                    name, namespace
                ),
                "hpa",
            )
        if _client_supports(
            clients, "policy", "delete_namespaced_pod_disruption_budget"
        ):
            _ignore_404(
                lambda: clients.policy.delete_namespaced_pod_disruption_budget(
                    name, namespace
                ),
                "pdb",
            )
        _ignore_404(
            lambda: clients.core.delete_namespaced_service(name, namespace), "service"
        )
        sa_name = str(options.get("service_account_name") or "")
        if sa_name and sa_name != "default":
            self._delete_managed_service_account(
                clients, namespace, sa_name, name
            )
        _ignore_404(
            lambda: clients.core.delete_namespaced_config_map(
                f"{name}-config", namespace
            ),
            "configmap",
        )
        _ignore_404(
            lambda: clients.core.delete_namespaced_secret(f"{name}-secret", namespace),
            "secret",
        )
        if not keep_pvc:
            _ignore_404(
                lambda: clients.core.delete_namespaced_persistent_volume_claim(
                    f"{name}-data", namespace
                ),
                "pvc",
            )
            if clients.apps is not None:
                # StatefulSet PVCs are named data-<name>-0..N.
                for ordinal in range(0, int(options.get("max_pvc_ordinals", 16))):
                    claim = f"data-{name}-{ordinal}"
                    _ignore_404(
                        lambda claim=claim: clients.core.delete_namespaced_persistent_volume_claim(
                            claim, namespace
                        ),
                        "pvc",
                    )

    def _delete_managed_service_account(
        self,
        clients: KubernetesClients,
        namespace: str,
        sa_name: str,
        instance_name: str,
    ) -> None:
        """Delete a ServiceAccount only when this provider created it.

        Operators can point a workload at a pre-existing account via
        ``provider_options.service_account``; that account must survive
        instance deletion, so the labels decide ownership here.
        """
        if not _client_supports(clients, "core", "read_namespaced_service_account"):
            return
        try:
            raw = _to_dict(clients.core.read_namespaced_service_account(sa_name, namespace))
        except Exception:
            return
        labels = (raw.get("metadata", {}) or {}).get("labels", {}) or {}
        if labels.get("app.kubernetes.io/managed-by") != self._managed_by:
            return
        if labels.get(f"{self._prefix}/instance") != sanitize_name(instance_name):
            return
        try:
            clients.core.delete_namespaced_service_account(sa_name, namespace)
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status not in (404, None):
                logger.warning(
                    "Could not delete serviceaccount %s/%s: %s",
                    namespace,
                    sa_name,
                    exc,
                )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    async def update(self, instance_id: str, spec: InstanceSpec) -> bool:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        raw = self._read_workload(clients, namespace, name)
        options = dict(spec.provider_options or {})
        self._validate_options(options, "update")
        manifest = str(options.get("manifest", "") or spec.metadata.get("manifest", ""))

        # Refresh ConfigMap / Secret env.
        configmap = build_config_map(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        if configmap is not None:
            try:
                clients.core.patch_namespaced_config_map(
                    f"{name}-config", namespace, configmap
                )
            except Exception as exc:
                logger.warning("Could not patch configmap for %s: %s", name, exc)

        # Patch the container image / resources / env via a replace-safe merge.
        workload = build_workload(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        container = workload["spec"]["template"]["spec"]["containers"][0]
        patch: Dict[str, Any] = {
            "spec": {
                "template": {
                    "spec": {"containers": [container]},
                }
            }
        }
        replicas = options.get("replicas")
        if replicas is not None:
            try:
                patch["spec"]["replicas"] = max(0, int(replicas))
            except (TypeError, ValueError):
                pass
        try:
            if raw.get("kind") == "StatefulSet":
                clients.apps.patch_namespaced_stateful_set(name, namespace, patch)
            else:
                clients.apps.patch_namespaced_deployment(name, namespace, patch)
        except Exception as exc:
            raise self._translate(exc, "update workload", name)

        service = build_service(
            spec.name, spec, options, self._prefix, self._managed_by, manifest
        )
        if service is not None:
            try:
                clients.core.patch_namespaced_service(name, namespace, service)
            except Exception as exc:
                logger.warning("Could not patch service for %s: %s", name, exc)

        self._patch_service_account(clients, namespace, name, options, manifest)
        self._patch_policy_objects(
            clients,
            namespace,
            name,
            options,
            manifest,
            raw.get("kind", "Deployment"),
        )
        return True

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------
    async def stats(self, instance_id: str) -> Optional[InstanceStats]:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        if clients.custom is None:
            return None
        try:
            response = clients.custom.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
                label_selector=instance_selector(name, self._prefix),
            )
        except Exception as exc:
            logger.debug("Pod metrics unavailable for %s: %s", name, exc)
            return None
        items = _as_list(response)
        cpu_cores = 0.0
        memory_bytes = 0
        for item in items:
            raw = _to_dict(item)
            for container in (raw.get("containers", []) or []):
                usage = container.get("usage", {}) or {}
                cpu_cores += _parse_cpu_quantity(usage.get("cpu"))
                memory_bytes += _parse_memory_bytes(usage.get("memory"))
        if not items:
            return None
        return InstanceStats(
            cpu_percent=round(cpu_cores * 100.0, 3),
            memory_percent=0.0,
            memory_used_bytes=memory_bytes,
            memory_total_bytes=0,
            network_rx_bytes=0,
            network_tx_bytes=0,
            disk_percent=0.0,
            collected_at=datetime.now(timezone.utc),
        )

    async def health(self) -> Dict[str, Any]:
        try:
            clients = self._clients_ready()
        except ProviderError as exc:
            return {"status": "unavailable", "error": str(exc)}
        try:
            code = clients.version.get_code()
            version = _to_dict(code).get("gitVersion", "")
            return {"status": "ok", "version": version, "namespace": self._namespace}
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}

    async def self_check(self) -> Dict[str, Any]:
        """Probe configuration, API access, and RBAC without side effects.

        Complements :meth:`health` (reachability only) with operator-
        facing checks: usable client, target namespace, required API
        groups, and create permission for workloads in the namespace.
        """
        checks: List[Dict[str, Any]] = []
        try:
            clients = self._clients_ready()
            checks.append(
                {"check": "client", "ok": True, "detail": "configuration loaded"}
            )
        except ProviderError as exc:
            return {
                "status": "unavailable",
                "checks": [{"check": "client", "ok": False, "detail": str(exc)}],
                "hint": (
                    "install services/orchestrator-agent/requirements-"
                    "optional.txt and set KUBECONFIG or K8S_IN_CLUSTER"
                ),
            }

        try:
            if clients.version is None:
                raise AttributeError("version client not configured")
            version = _to_dict(clients.version.get_code()).get("gitVersion", "")
            checks.append(
                {"check": "apiserver", "ok": True, "detail": version or "reachable"}
            )
        except Exception as exc:
            checks.append({"check": "apiserver", "ok": False, "detail": str(exc)})

        try:
            clients.core.read_namespace(self._namespace)
            checks.append(
                {
                    "check": "namespace",
                    "ok": True,
                    "detail": f"namespace {self._namespace!r} exists",
                }
            )
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status == 404:
                checks.append(
                    {
                        "check": "namespace",
                        "ok": True,
                        "detail": (
                            f"namespace {self._namespace!r} will be created on "
                            "first use"
                        ),
                    }
                )
            else:
                checks.append({"check": "namespace", "ok": False, "detail": str(exc)})

        required_groups = (
            "apps",
            "networking.k8s.io",
            "policy",
            "autoscaling",
        )
        if _client_supports(clients, "discovery", "get_api_versions"):
            try:
                payload = _to_dict(clients.discovery.get_api_versions())
                served = {
                    str(group.get("name", ""))
                    for group in (payload.get("groups") or [])
                    if isinstance(group, dict)
                }
                missing = [g for g in required_groups if g not in served]
                checks.append(
                    {
                        "check": "api_groups",
                        "ok": not missing,
                        "detail": (
                            "missing groups: " + ", ".join(missing)
                            if missing
                            else "all required API groups served"
                        ),
                    }
                )
            except Exception as exc:
                checks.append({"check": "api_groups", "ok": False, "detail": str(exc)})
        else:
            checks.append(
                {
                    "check": "api_groups",
                    "ok": True,
                    "detail": "discovery client unavailable; skipped",
                }
            )

        if _client_supports(
            clients, "authorization", "create_self_subject_access_review"
        ):
            review = {
                "apiVersion": "authorization.k8s.io/v1",
                "kind": "SelfSubjectAccessReview",
                "spec": {
                    "resourceAttributes": {
                        "namespace": self._namespace,
                        "verb": "create",
                        "group": "apps",
                        "resource": "deployments",
                    }
                },
            }
            try:
                response = _to_dict(
                    clients.authorization.create_self_subject_access_review(review)
                )
                allowed = bool(
                    (response.get("status", {}) or {}).get("allowed", False)
                )
                checks.append(
                    {
                        "check": "rbac_create_workloads",
                        "ok": allowed,
                        "detail": (
                            "allowed" if allowed else "RBAC denied workload creation"
                        ),
                    }
                )
            except Exception as exc:
                checks.append(
                    {"check": "rbac_create_workloads", "ok": False, "detail": str(exc)}
                )
        else:
            checks.append(
                {
                    "check": "rbac_create_workloads",
                    "ok": True,
                    "detail": "authorization client unavailable; skipped",
                }
            )

        ok = all(entry["ok"] for entry in checks)
        result: Dict[str, Any] = {
            "status": "ok" if ok else "degraded",
            "namespace": self._namespace,
            "checks": checks,
        }
        if not ok:
            failing = next(entry for entry in checks if not entry["ok"])
            result["hint"] = f"{failing['check']} failed: {failing['detail']}"
        return result

    # ------------------------------------------------------------------
    # Scaling / rollout
    # ------------------------------------------------------------------
    async def scale(self, instance_id: str, replicas: int) -> bool:
        """Set the workload replica count explicitly (0 acts like stop)."""
        try:
            target = max(0, int(replicas))
        except (TypeError, ValueError) as exc:
            raise ProviderConfigError(
                f"replicas must be an integer, got {replicas!r}"
            ) from exc
        return self._scale(instance_id, target)

    async def rollout_status(
        self, instance_id: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Poll until a workload finishes rolling out or fails.

        Returns one of ``complete``, ``failed`` (a pod condition that
        will not self-heal, e.g. ImagePullBackOff), ``missing``, or
        ``timeout``.  Used by the webhook apply path and by operators
        watching a rollout; sleeps between polls like ``_wait_for_ready``.
        """
        import asyncio
        import time

        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        limit = float(
            timeout if timeout is not None else config.K8S_WAIT_TIMEOUT_SECONDS
        )
        deadline = time.monotonic() + limit
        counts: Dict[str, int] = {"desired": 0, "ready": 0, "updated": 0}
        while True:
            try:
                raw = self._read_workload(clients, namespace, name)
            except InstanceNotFoundError:
                return {
                    "status": "missing",
                    "instance": instance_id,
                    "message": "workload no longer exists",
                }
            status = raw.get("status", {}) or {}
            desired = self._desired_replicas(raw)
            updated_raw = status.get("updatedReplicas")
            counts = {
                "desired": desired,
                "ready": int(status.get("readyReplicas") or 0),
                "updated": (
                    int(updated_raw) if updated_raw is not None else desired
                ),
            }
            if counts["ready"] >= desired and counts["updated"] >= desired:
                return {
                    "status": "complete",
                    "instance": instance_id,
                    "message": f"{counts['ready']}/{desired} replicas ready",
                    **counts,
                }
            fatal = self._fatal_pod_condition(clients, namespace, name)
            if fatal:
                return {
                    "status": "failed",
                    "instance": instance_id,
                    "reason": fatal.get("reason", ""),
                    "message": fatal.get("message", ""),
                    **counts,
                }
            if time.monotonic() >= deadline:
                return {
                    "status": "timeout",
                    "instance": instance_id,
                    "message": f"rollout did not finish within {limit:.0f}s",
                    **counts,
                }
            await asyncio.sleep(2)

    # ------------------------------------------------------------------
    # Diagnosis / housekeeping
    # ------------------------------------------------------------------
    _DIAGNOSIS_HINTS = {
        "image-pull": (
            "Check the image name/tag and imagePullSecrets; the node could "
            "not fetch the image."
        ),
        "crashloop": (
            "Inspect logs (provider logs endpoint); the main container keeps "
            "exiting."
        ),
        "config": (
            "A startup command or probe is failing; review ConfigMap/Secret "
            "values and the health check path."
        ),
        "unschedulable": (
            "No node fits the request; check capacity, node selectors, "
            "affinity and taints."
        ),
        "failed": "The pod terminated with an error; inspect events and logs.",
        "not-ready": (
            "Readiness probe is failing; verify the service listens on the "
            "declared port."
        ),
        "starting": "Pod is still initializing; wait or raise probe timeouts.",
        "pending": (
            "Pod is queued for scheduling; watch events for capacity or "
            "volume issues."
        ),
    }

    def _read_hpa(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Normalized HPA state, or ``None`` when absent/unsupported."""
        if not _client_supports(
            clients,
            "autoscaling",
            "read_namespaced_horizontal_pod_autoscaler",
        ):
            return None
        try:
            raw = _to_dict(
                clients.autoscaling.read_namespaced_horizontal_pod_autoscaler(
                    name, namespace
                )
            )
        except Exception:
            return None
        return parse_hpa(raw) or None

    async def diagnose(self, instance_id: str) -> Dict[str, Any]:
        """Explain why an instance is unhealthy with an actionable hint."""
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        try:
            raw = self._read_workload(clients, namespace, name)
        except InstanceNotFoundError:
            return {
                "instance": instance_id,
                "status": "missing",
                "hint": (
                    "The workload was deleted or never created; re-apply the "
                    "manifest."
                ),
                "pods": [],
                "events": [],
            }

        observed = parse_workload(raw)
        pods = self._pods_for(clients, namespace, name)
        pod_reports: List[Dict[str, Any]] = []
        for pod in pods:
            meta = pod.get("metadata", {}) or {}
            conditions = map_pod_conditions(pod)
            health = map_pod_health(pod)
            pod_reports.append(
                {
                    "name": meta.get("name", ""),
                    "category": conditions.get("category", "unknown"),
                    "reason": conditions.get("reason", ""),
                    "message": conditions.get("message", ""),
                    "restarts": health.get("restarts", 0),
                    "ready": health.get("ready", False),
                }
            )

        categories = [entry["category"] for entry in pod_reports]
        if not pod_reports:
            status = "no-pods"
            hint = (
                "No pods match this instance; the workload may be scaled to "
                "zero or still creating its ReplicaSet."
            )
        else:
            fatal = next(
                (c for c in categories if c in self._FATAL_POD_CATEGORIES), ""
            )
            unhealthy = next((c for c in categories if c != "running"), "")
            category = fatal or unhealthy
            if category:
                status = "degraded"
                hint = self._DIAGNOSIS_HINTS.get(
                    category, "Pods are not fully running; inspect events."
                )
            else:
                status = "healthy"
                hint = ""

        event_names = [name] + [
            entry["name"]
            for entry in pod_reports
            if entry["category"] != "running" and entry["name"]
        ]
        events = self._recent_events(clients, namespace, event_names[:4])
        return {
            "instance": instance_id,
            "status": status,
            "workload": observed.get("workload", "deployment"),
            "replicas": {
                "desired": observed.get("replicas", 0),
                "ready": observed.get("ready_replicas", 0),
            },
            "pods": pod_reports,
            "events": events,
            "autoscaling": self._read_hpa(clients, namespace, name),
            "hint": hint,
        }

    def _recent_events(
        self,
        clients: KubernetesClients,
        namespace: str,
        object_names: List[str],
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Deduplicated events for the workload and its problem pods."""
        if not _client_supports(clients, "core", "list_namespaced_event"):
            return []
        collected: List[Any] = []
        for object_name in object_names:
            try:
                response = clients.core.list_namespaced_event(
                    namespace, field_selector=f"involvedObject.name={object_name}"
                )
            except Exception as exc:
                logger.debug("Could not list events for %s: %s", object_name, exc)
                continue
            collected.extend(_as_list(response))
        return summarize_events(collected, limit=limit)

    async def garbage_collection(
        self,
        manifest_name: str = "",
        keep: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> List[str]:
        """Delete managed workloads no longer listed in the manifest.

        Only objects carrying the provider's managed-by label (and the
        manifest label when ``manifest_name`` is set) are considered, so
        coexisting tooling is untouched.  Returns the instance ids that
        were (or, with ``dry_run``, would be) deleted.
        """
        clients = self._clients_ready()
        keep_names = {sanitize_name(entry) for entry in (keep or [])}
        removed: List[str] = []
        for raw in self._list_workloads(clients):
            metadata = raw.get("metadata", {}) or {}
            labels = metadata.get("labels", {}) or {}
            if manifest_name and labels.get(f"{self._prefix}/manifest") != manifest_name:
                continue
            name = metadata.get("name", "")
            namespace = metadata.get("namespace", self._namespace)
            if not name or sanitize_name(name) in keep_names:
                continue
            instance_id = self._instance_id(namespace, name)
            if dry_run:
                removed.append(instance_id)
                continue
            try:
                await self.delete(instance_id)
            except ProviderError as exc:
                logger.warning("Garbage collection skipped %s: %s", instance_id, exc)
                continue
            removed.append(instance_id)
            logger.info("Garbage collected %s", instance_id)
        return removed

    # ------------------------------------------------------------------
    # Exec / logs
    # ------------------------------------------------------------------
    def _running_pod(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> Optional[str]:
        pods = self._pods_for(clients, namespace, name)
        running = [
            p
            for p in pods
            if (p.get("status", {}) or {}).get("phase") == "Running"
        ]
        chosen = running or pods
        if not chosen:
            return None
        return (chosen[0].get("metadata", {}) or {}).get("name")

    async def execute_command(self, instance_id: str, command: str) -> Tuple[bool, str]:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        pod = self._running_pod(clients, namespace, name)
        if pod is None:
            raise InstanceNotFoundError(
                f"no running pod for {name!r} in namespace {namespace!r}"
            )
        exec_command = ["/bin/sh", "-c", command]
        try:
            output = clients.core.connect_get_namespaced_pod_exec(
                pod,
                namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=True,
            )
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            # ApiException.status 400 (exec) distinguishes "command failed"
            # from transport errors; surface output to the caller.
            status = getattr(exc, "status", None)
            if status in (400, 500):
                return False, str(exc)
            raise self._translate(exc, "exec", name)
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return True, str(output or "")

    async def stream_command(
        self, instance_id: str, command: str
    ) -> AsyncIterator[str]:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        pod = self._running_pod(clients, namespace, name)
        if pod is None:
            raise InstanceNotFoundError(
                f"no running pod for {name!r} in namespace {namespace!r}"
            )
        exec_command = ["/bin/sh", "-c", command]
        try:
            resp = clients.core.connect_get_namespaced_pod_exec(
                pod,
                namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
            )
        except Exception as exc:
            raise self._translate(exc, "stream exec", name)
        if resp is None:
            raise ProviderUnavailableError("kubernetes exec stream unavailable")
        if hasattr(resp, "read_stdout"):
            while resp.is_open():
                resp.update(timeout=1)
                chunk = resp.read_stdout()
                if chunk:
                    yield chunk
            return
        # Fallback: a preloaded string result.
        if isinstance(resp, bytes):
            resp = resp.decode("utf-8", errors="replace")
        yield str(resp)

    async def logs(self, instance_id: str, tail: int = 200) -> str:
        clients = self._clients_ready()
        namespace, name = self._parse_instance_id(instance_id)
        pod = self._running_pod(clients, namespace, name)
        if pod is None:
            raise InstanceNotFoundError(
                f"no running pod for {name!r} in namespace {namespace!r}"
            )
        try:
            output = clients.core.read_namespaced_pod_log(
                pod, namespace, tail_lines=tail
            )
        except Exception as exc:
            raise self._translate(exc, "read logs", name)
        return output if isinstance(output, str) else str(output)

    # ------------------------------------------------------------------
    # Drift
    # ------------------------------------------------------------------
    def _configmap_env(
        self, clients: KubernetesClients, namespace: str, name: str
    ) -> Dict[str, str]:
        """Declared env values as stored in the instance ConfigMap.

        Most env vars reach the container through ``envFrom``, so the
        pod spec alone cannot show drift; the ConfigMap is the source of
        truth.  Unreadable ConfigMaps yield an empty mapping (the env
        check then falls back to container env only).
        """
        reader = getattr(clients.core, "read_namespaced_config_map", None)
        if not callable(reader):
            return {}
        try:
            raw = _to_dict(reader(f"{name}-config", namespace))
        except Exception:
            return {}
        data = raw.get("data") or {}
        return {str(key): str(value) for key, value in data.items()}

    async def detect_drift(self, desired_instances: List[Any]) -> Any:
        """Compare live workloads to desired ``InfraInstance`` objects.

        Returns the manifest engine's ``DriftReport`` so drift from the
        Kubernetes provider can be merged with the generic detector.  The
        import is local to avoid a hard dependency cycle with the engine.
        """
        from manifest.engine import DriftEntry, DriftReport, DriftSeverity

        clients = self._clients_ready()
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
                        message=f"Workload '{name}' is defined but does not exist",
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
            options = getattr(inst, "provider_options", {}) or {}
            desired_replicas = options.get("replicas")
            if desired_replicas is not None:
                try:
                    desired_replicas = int(desired_replicas)
                except (TypeError, ValueError):
                    desired_replicas = None
            if desired_replicas is not None:
                actual_replicas = actual.metadata.get("replicas")
                if actual_replicas != desired_replicas:
                    entries.append(
                        DriftEntry(
                            instance_name=name,
                            field="replicas",
                            expected=desired_replicas,
                            actual=actual_replicas,
                            severity=DriftSeverity.WARNING,
                        )
                    )
            desired_ports = getattr(inst, "ports", None) or {}
            if desired_ports:
                actual_ports = actual.spec.ports or {}
                if {str(p) for p in desired_ports} != set(actual_ports):
                    entries.append(
                        DriftEntry(
                            instance_name=name,
                            field="ports",
                            expected=sorted(str(p) for p in desired_ports),
                            actual=sorted(actual_ports),
                            severity=DriftSeverity.WARNING,
                            message=(
                                f"Declared ports differ for '{name}' (desired "
                                f"{sorted(desired_ports)}, observed "
                                f"{sorted(actual_ports)})"
                            ),
                        )
                    )
            desired_env = getattr(inst, "env", None) or {}
            if desired_env:
                ns = actual.id.split("/", 1)[0]
                observed_env = dict(actual.spec.env_vars or {})
                for key, value in self._configmap_env(clients, ns, name).items():
                    if key in desired_env and key not in observed_env:
                        observed_env[key] = value
                mismatched = {
                    key: observed_env.get(key)
                    for key in desired_env
                    if observed_env.get(key) != desired_env[key]
                }
                if mismatched:
                    entries.append(
                        DriftEntry(
                            instance_name=name,
                            field="env",
                            expected={
                                key: desired_env[key] for key in mismatched
                            },
                            actual=mismatched,
                            severity=DriftSeverity.WARNING,
                            message=(
                                f"Environment values differ for '{name}' "
                                f"({', '.join(sorted(mismatched))})"
                            ),
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
                    message=f"Workload '{name}' exists but is not in the manifest",
                )
            )
        return DriftReport(
            manifest_name="kubernetes",
            total_instances=len(desired_instances),
            drifted_instances=len({e.instance_name for e in entries}),
            entries=entries,
        )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
_CPU_SUFFIXES = (("n", 1e-9), ("u", 1e-6), ("m", 1e-3))
_MEMORY_SUFFIXES = (
    ("Ki", 1024),
    ("Mi", 1024 ** 2),
    ("Gi", 1024 ** 3),
    ("Ti", 1024 ** 4),
    ("K", 1000),
    ("M", 1000 ** 2),
    ("G", 1000 ** 3),
)


def _parse_cpu_quantity(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip()
    for suffix, factor in _CPU_SUFFIXES:
        if text.endswith(suffix):
            try:
                return float(text[: -len(suffix)]) * factor
            except ValueError:
                return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _parse_memory_bytes(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    for suffix, factor in _MEMORY_SUFFIXES:
        if text.endswith(suffix):
            try:
                return int(float(text[: -len(suffix)]) * factor)
            except ValueError:
                return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


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


def _map_power_state(state: str) -> InstancePowerState:
    mapping = {
        "running": InstancePowerState.RUNNING,
        "stopped": InstancePowerState.STOPPED,
        "paused": InstancePowerState.PAUSED,
        "unknown": InstancePowerState.UNKNOWN,
    }
    return mapping.get(state, InstancePowerState.UNKNOWN)
