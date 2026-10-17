"""Pure builders that translate provider-neutral specs into Kubernetes objects.

The builders return plain dictionaries matching the Kubernetes JSON schema
(camelCase keys), which the official client accepts directly as request
bodies.  Keeping them dependency-free means the translation logic can be
unit-tested without installing the ``kubernetes`` package, and the
provider only concerns itself with API calls, error mapping, and drift.

The label scheme is how the provider later finds its own objects:

* ``app.kubernetes.io/managed-by=<K8S_MANAGED_BY>`` (default ``infra-pilot``)
* ``<prefix>/instance=<name>``
* ``<prefix>/manifest=<manifest>`` where known

Only these labelled objects are ever listed or deleted, so the provider
never touches workloads it does not own.
"""

import re
from typing import Any, Dict, List, Optional

from compute.base import InstanceSpec

# Kubernetes name rules (RFC 1123 subdomain, 253 chars).
_DNS_1123 = re.compile(r"[^a-z0-9-]+")
_DNS_1123_START = re.compile(r"^[^a-z0-9]+")
_DNS_1123_END = re.compile(r"[^a-z0-9]+$")

DEFAULT_PREFIX = "infrapilot.io"
DEFAULT_MANAGED_BY = "infra-pilot"

WORKLOAD_DEPLOYMENT = "deployment"
WORKLOAD_STATEFULSET = "statefulset"

VALID_IMAGE_PULL_POLICIES = frozenset({"Always", "IfNotPresent", "Never"})
VALID_SERVICE_TYPES = frozenset({"ClusterIP", "NodePort", "LoadBalancer"})
VALID_WORKLOADS = frozenset({WORKLOAD_DEPLOYMENT, WORKLOAD_STATEFULSET})


def sanitize_name(name: str, max_len: int = 63) -> str:
    """Coerce ``name`` into a valid RFC 1123 label/subdomain."""
    candidate = _DNS_1123.sub("-", (name or "").lower())
    candidate = _DNS_1123_START.sub("", candidate)
    candidate = _DNS_1123_END.sub("", candidate)
    if not candidate:
        candidate = "app"
    if len(candidate) > max_len:
        candidate = candidate[:max_len].rstrip("-")
    return candidate or "app"


def managed_labels(
    instance_name: str,
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
    extra: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Return the identifying label set for an instance's objects."""
    labels = {
        "app.kubernetes.io/managed-by": managed_by,
        "app.kubernetes.io/name": sanitize_name(instance_name),
        f"{prefix}/instance": sanitize_name(instance_name),
    }
    if manifest:
        labels[f"{prefix}/manifest"] = sanitize_name(manifest)
    if extra:
        for key, value in extra.items():
            labels[str(key)] = str(value)
    return labels


def managed_selector(
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> str:
    """Return a label selector matching all objects this provider owns."""
    parts = [f"app.kubernetes.io/managed-by={managed_by}"]
    if manifest:
        parts.append(f"{prefix}/manifest={sanitize_name(manifest)}")
    return ",".join(parts)


def instance_selector(instance_name: str, prefix: str = DEFAULT_PREFIX) -> str:
    return f"{prefix}/instance={sanitize_name(instance_name)}"


# ----------------------------------------------------------------------
# Resource translation
# ----------------------------------------------------------------------
def _cpu_to_quantity(cpu_cores: float) -> str:
    value = float(cpu_cores)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def memory_to_quantity(memory_mb: int) -> str:
    return f"{int(memory_mb)}Mi"


def storage_to_quantity(size: Any, storage_gb: Any, default: str = "10Gi") -> str:
    if isinstance(size, str) and size:
        return size
    try:
        gb = int(storage_gb)
        if gb > 0:
            return f"{gb}Gi"
    except (TypeError, ValueError):
        pass
    return default


def build_resources(spec: InstanceSpec, options: Dict[str, Any]) -> Dict[str, Any]:
    """Build the container ``resources`` block from requests/limits options.

    ``provider_options.resources.limits`` / ``.requests`` override the
    manifest's cpu/memory.  Requests default to the manifest values and
    limits default to the requests so a scheduler has a real signal.
    """
    overrides = options.get("resources") if isinstance(options, dict) else None
    overrides = overrides if isinstance(overrides, dict) else {}
    request_cpu = overrides.get("requests", {}).get(
        "cpu", _cpu_to_quantity(spec.cpu_cores)
    )
    request_mem = overrides.get("requests", {}).get(
        "memory", memory_to_quantity(spec.memory_mb)
    )
    limit_cpu = overrides.get("limits", {}).get("cpu", request_cpu)
    limit_mem = overrides.get("limits", {}).get("memory", request_mem)
    resources: Dict[str, Any] = {
        "requests": {"cpu": request_cpu, "memory": request_mem},
        "limits": {"cpu": limit_cpu, "memory": limit_mem},
    }
    return resources


# ----------------------------------------------------------------------
# Ports / services
# ----------------------------------------------------------------------
def _split_port_key(key: str) -> tuple:
    text = str(key)
    if "/" in text:
        port, protocol = text.split("/", 1)
    else:
        port, protocol = text, "tcp"
    try:
        number = int(port)
    except (TypeError, ValueError):
        number = 0
    protocol = protocol.upper()
    if protocol not in ("TCP", "UDP", "SCTP"):
        protocol = "TCP"
    return number, protocol


def build_container_ports(spec: InstanceSpec) -> List[Dict[str, Any]]:
    ports = []
    for key in sorted(spec.ports):
        number, protocol = _split_port_key(key)
        if number <= 0:
            continue
        ports.append(
            {
                "name": f"port-{number}-{protocol.lower()}",
                "containerPort": number,
                "protocol": protocol,
            }
        )
    return ports


def build_service(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    """Build a Service when the instance exposes ports (or asks for one)."""
    ports = build_container_ports(spec)
    service_type = str(options.get("service_type", "ClusterIP"))
    if service_type not in VALID_SERVICE_TYPES:
        service_type = "ClusterIP"
    # Allow an explicit Service even without declared ports (e.g. headless).
    headless = bool(options.get("headless_service"))
    explicit = bool(options.get("service")) or headless
    if not ports and not explicit:
        return None

    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    service_ports = []
    for entry in ports:
        service_port: Dict[str, Any] = {
            "name": entry["name"],
            "port": entry["containerPort"],
            "targetPort": entry["containerPort"],
            "protocol": entry["protocol"],
        }
        node_port = options.get("node_ports", {}).get(str(entry["containerPort"]))
        if node_port and service_type == "NodePort":
            try:
                service_port["nodePort"] = int(node_port)
            except (TypeError, ValueError):
                pass
        service_ports.append(service_port)

    service: Dict[str, Any] = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": sanitize_name(instance_name),
            "labels": labels,
        },
        "spec": {
            "selector": managed_labels(instance_name, prefix, managed_by, manifest),
            "type": service_type,
            "ports": service_ports,
        },
    }
    if headless:
        service["spec"]["clusterIP"] = "None"
        service["spec"]["type"] = "ClusterIP"
    if options.get("session_affinity"):
        service["spec"]["sessionAffinity"] = str(options["session_affinity"])
    return service


def build_ingress(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
    default_class: str = "",
    host_suffix: str = "",
) -> Optional[Dict[str, Any]]:
    """Build an Ingress when ``provider_options.ingress`` is set."""
    ingress_opt = options.get("ingress")
    if not ingress_opt:
        return None
    if isinstance(ingress_opt, dict):
        host = ingress_opt.get("host", "")
        path = ingress_opt.get("path", "/")
        path_type = ingress_opt.get("path_type", "Prefix")
        tls_secret = ingress_opt.get("tls_secret", "")
    else:
        host = str(options.get("ingress_host", "") or "")
        path = str(options.get("ingress_path", "/"))
        path_type = "Prefix"
        tls_secret = str(options.get("ingress_tls_secret", "") or "")
    if not host and host_suffix:
        host = f"{sanitize_name(instance_name)}.{host_suffix}"

    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    service_name = sanitize_name(instance_name)
    # First declared container port becomes the backend port.
    ports = build_container_ports(spec)
    backend_port = ports[0]["containerPort"] if ports else int(options.get("port", 80))
    backend: Dict[str, Any] = {
        "service": {"name": service_name, "port": {"number": backend_port}}
    }
    ingress: Dict[str, Any] = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {"name": sanitize_name(instance_name), "labels": labels},
        "spec": {
            "rules": [
                {
                    "host": host or None,
                    "http": {
                        "paths": [
                            {
                                "path": path,
                                "pathType": path_type,
                                "backend": backend,
                            }
                        ]
                    },
                }
            ]
        },
    }
    if not host:
        # No host means a catch-all rule; ``host: null`` is invalid JSON-ish.
        ingress["spec"]["rules"][0].pop("host", None)
    ingress_class = options.get("ingress_class") or default_class
    if ingress_class:
        ingress["spec"]["ingressClassName"] = str(ingress_class)
    if tls_secret:
        ingress["spec"]["tls"] = [
            {"hosts": [host] if host else [], "secretName": str(tls_secret)}
        ]
    annotations = options.get("ingress_annotations")
    if isinstance(annotations, dict) and annotations:
        ingress["metadata"]["annotations"] = {
            str(k): str(v) for k, v in annotations.items()
        }
    return ingress


# ----------------------------------------------------------------------
# Config / secrets
# ----------------------------------------------------------------------
def build_config_map(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    data = {}
    data.update(spec.env_vars or {})
    config_env = options.get("config_env")
    if isinstance(config_env, dict):
        data.update({str(k): str(v) for k, v in config_env.items()})
    if not data:
        return None
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": f"{sanitize_name(instance_name)}-config",
            "labels": labels,
        },
        "data": data,
    }


def build_secret(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    secret_env = options.get("secret_env")
    if not isinstance(secret_env, dict) or not secret_env:
        return None
    import base64

    data = {
        str(k): base64.b64encode(str(v).encode("utf-8")).decode("ascii")
        for k, v in secret_env.items()
    }
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "metadata": {
            "name": f"{sanitize_name(instance_name)}-secret",
            "labels": labels,
        },
        "data": data,
    }


def build_pvc(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    """Build a standalone PVC for a Deployment that needs persistent storage.

    StatefulSets declare storage via ``volumeClaimTemplates`` instead, so
    the caller uses that path and skips this builder.
    """
    if not spec.storage_gb or options.get("persistent_storage") is False:
        return None
    if (
        str(options.get("workload", WORKLOAD_DEPLOYMENT)).lower()
        == WORKLOAD_STATEFULSET
    ):
        return None
    storage_class = options.get("storage_class", "")
    size = storage_to_quantity(options.get("storage_size"), spec.storage_gb)
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    spec_block: Dict[str, Any] = {
        "accessModes": [str(options.get("access_mode", "ReadWriteOnce"))],
        "resources": {"requests": {"storage": size}},
    }
    if storage_class:
        spec_block["storageClassName"] = str(storage_class)
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": f"{sanitize_name(instance_name)}-data", "labels": labels},
        "spec": spec_block,
    }


# ----------------------------------------------------------------------
# Workloads
# ----------------------------------------------------------------------
def build_container(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
) -> Dict[str, Any]:
    container: Dict[str, Any] = {
        "name": sanitize_name(instance_name),
        "image": spec.image,
        "resources": build_resources(spec, options),
    }
    policy = str(options.get("image_pull_policy", ""))
    if policy in VALID_IMAGE_PULL_POLICIES:
        container["imagePullPolicy"] = policy
    ports = build_container_ports(spec)
    if ports:
        container["ports"] = ports
    if spec.env_vars:
        container["envFrom"] = [
            {"configMapRef": {"name": f"{sanitize_name(instance_name)}-config"}}
        ]
    if options.get("secret_env"):
        container.setdefault("envFrom", []).append(
            {"secretRef": {"name": f"{sanitize_name(instance_name)}-secret"}}
        )
    explicit_env = options.get("env")
    if isinstance(explicit_env, dict) and explicit_env:
        container["env"] = [
            {"name": str(k), "value": str(v)} for k, v in explicit_env.items()
        ]
    if options.get("command"):
        container["command"] = [str(c) for c in options["command"]]
    if options.get("args"):
        container["args"] = [str(a) for a in options["args"]]
    probes = build_probes(spec, options)
    container.update(probes)
    security_context = build_container_security_context(options)
    if security_context:
        container["securityContext"] = security_context
    if spec.storage_gb:
        mount_path = str(options.get("volume_mount_path", "/data"))
        workload = str(options.get("workload", WORKLOAD_DEPLOYMENT)).lower()
        if workload == WORKLOAD_STATEFULSET:
            claim_name = "data"
        else:
            claim_name = f"{sanitize_name(instance_name)}-data"
        container["volumeMounts"] = [{"name": claim_name, "mountPath": mount_path}]
    return container


def _pod_spec(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    workload: str,
) -> Dict[str, Any]:
    init_containers, sidecars = build_sidecars(instance_name, spec, options)
    pod_spec: Dict[str, Any] = {
        "containers": [build_container(instance_name, spec, options), *sidecars],
    }
    if init_containers:
        pod_spec["initContainers"] = init_containers
    pod_security_context = build_pod_security_context(options)
    if pod_security_context:
        pod_spec["securityContext"] = pod_security_context
    if options.get("service_account"):
        pod_spec["serviceAccountName"] = str(options["service_account"])
    if isinstance(options.get("node_selector"), dict):
        pod_spec["nodeSelector"] = {
            str(k): str(v) for k, v in options["node_selector"].items()
        }
    if isinstance(options.get("tolerations"), list):
        pod_spec["tolerations"] = options["tolerations"]
    if isinstance(options.get("affinity"), dict):
        pod_spec["affinity"] = options["affinity"]
    if options.get("host_network"):
        pod_spec["hostNetwork"] = True
    if options.get("restart_policy"):
        pod_spec["restartPolicy"] = str(options["restart_policy"])
    if options.get("termination_grace_period_seconds") is not None:
        pod_spec["terminationGracePeriodSeconds"] = int(
            options["termination_grace_period_seconds"]
        )
    if workload != WORKLOAD_STATEFULSET and spec.storage_gb:
        pod_spec["volumes"] = [
            {
                "name": f"{sanitize_name(instance_name)}-data",
                "persistentVolumeClaim": {
                    "claimName": f"{sanitize_name(instance_name)}-data"
                },
            }
        ]
    # Pull secrets referenced by name (already present in the namespace).
    pull_secrets = options.get("image_pull_secrets")
    if isinstance(pull_secrets, list) and pull_secrets:
        pod_spec["imagePullSecrets"] = [{"name": str(s)} for s in pull_secrets]
    return pod_spec


def build_workload(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Dict[str, Any]:
    """Build a Deployment or StatefulSet body from an :class:`InstanceSpec`."""
    workload = str(options.get("workload", WORKLOAD_DEPLOYMENT)).lower()
    if workload not in VALID_WORKLOADS:
        workload = WORKLOAD_DEPLOYMENT
    replicas = options.get("replicas")
    try:
        replicas = int(replicas) if replicas is not None else 1
    except (TypeError, ValueError):
        replicas = 1
    if replicas < 0:
        replicas = 0
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    pod_labels = dict(labels)
    if isinstance(options.get("labels"), dict):
        for k, v in options["labels"].items():
            labels[str(k)] = str(v)
            pod_labels[str(k)] = str(v)
    pod_spec = _pod_spec(instance_name, spec, options, workload)
    metadata: Dict[str, Any] = {"name": sanitize_name(instance_name), "labels": labels}
    pod_template_meta: Dict[str, Any] = {"labels": pod_labels}
    annotations = options.get("annotations")
    if isinstance(annotations, dict) and annotations:
        metadata["annotations"] = {str(k): str(v) for k, v in annotations.items()}
    pod_annotations = options.get("pod_annotations")
    if isinstance(pod_annotations, dict) and pod_annotations:
        pod_template_meta["annotations"] = {
            str(k): str(v) for k, v in pod_annotations.items()
        }
    if options.get("hostname") or options.get("subdomain"):
        if options.get("hostname"):
            pod_spec["hostname"] = str(options["hostname"])
        if options.get("subdomain"):
            pod_spec["subdomain"] = str(options["subdomain"])

    template = {"metadata": pod_template_meta, "spec": pod_spec}

    if workload == WORKLOAD_STATEFULSET:
        body: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": metadata,
            "spec": {
                "serviceName": str(
                    options.get("service_name") or sanitize_name(instance_name)
                ),
                "replicas": replicas,
                "selector": {
                    "matchLabels": managed_labels(
                        instance_name, prefix, managed_by, manifest
                    )
                },
                "template": template,
            },
        }
        if spec.storage_gb:
            size = storage_to_quantity(options.get("storage_size"), spec.storage_gb)
            claim_spec: Dict[str, Any] = {
                "accessModes": [str(options.get("access_mode", "ReadWriteOnce"))],
                "resources": {"requests": {"storage": size}},
            }
            storage_class = options.get("storage_class", "")
            if storage_class:
                claim_spec["storageClassName"] = str(storage_class)
            body["spec"]["volumeClaimTemplates"] = [
                {
                    "metadata": {
                        "name": "data",
                        "labels": managed_labels(
                            instance_name, prefix, managed_by, manifest
                        ),
                    },
                    "spec": claim_spec,
                }
            ]
        return body

    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": metadata,
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": managed_labels(
                    instance_name, prefix, managed_by, manifest
                )
            },
            "template": template,
        },
    }


# ----------------------------------------------------------------------
# Probes (health_check / options["probes"])
# ----------------------------------------------------------------------
def _probe_from_dict(
    probe_opt: Any,
    default_port: int = 0,
) -> Optional[Dict[str, Any]]:
    """Translate one probe definition into a Kubernetes probe body.

    Accepted shapes::

        {"path": "/healthz", "port": 8080}          # httpGet
        {"type": "tcp", "port": 8080}                # tcpSocket
        {"type": "exec", "cmd": ["curl", "-f", ...]} # exec
        {"type": "http", "path": "/", "port": 80}
        {"cmd": "wget -q -O- ..."}                   # exec from a string

    Timing keys map to the Kubernetes field names when given in snake_case
    (``initial_delay``, ``period``, ``timeout``, ``success``,
    ``failure``) or already in camelCase.
    """
    if isinstance(probe_opt, bool):
        if not probe_opt:
            return None
        probe_opt = {}
    if not isinstance(probe_opt, dict):
        return None
    probe_type = str(probe_opt.get("type", "")).lower()
    path = probe_opt.get("path")
    port = probe_opt.get("port", default_port)
    cmd = probe_opt.get("cmd") or probe_opt.get("command")
    if not probe_type:
        if cmd:
            probe_type = "exec"
        elif path:
            probe_type = "http"
        else:
            probe_type = "tcp"
    try:
        port_number = int(port) if port is not None else 0
    except (TypeError, ValueError):
        port_number = 0

    body: Dict[str, Any] = {}
    if probe_type in ("http", "httpget", "http_get"):
        if port_number <= 0:
            return None
        body["httpGet"] = {
            "path": str(path or "/"),
            "port": port_number,
            "scheme": str(probe_opt.get("scheme", "HTTP")).upper(),
        }
    elif probe_type in ("tcp", "tcpsocket", "tcp_socket"):
        if port_number <= 0:
            return None
        body["tcpSocket"] = {"port": port_number}
    elif probe_type in ("exec", "command"):
        if isinstance(cmd, str):
            argv = ["/bin/sh", "-c", cmd]
        elif isinstance(cmd, (list, tuple)) and cmd:
            argv = [str(part) for part in cmd]
        else:
            return None
        body["exec"] = {"command": argv}
    else:
        return None

    timing = (
        ("initial_delay_seconds", "initial_delay", "initialDelaySeconds"),
        ("period_seconds", "period", "periodSeconds"),
        ("timeout_seconds", "timeout", "timeoutSeconds"),
        ("success_threshold", "success", "successThreshold"),
        ("failure_threshold", "failure", "failureThreshold"),
    )
    for field, snake, camel in timing:
        value = probe_opt.get(snake, probe_opt.get(camel))
        if value is None:
            continue
        try:
            body[field] = int(value)
        except (TypeError, ValueError):
            continue
    return body


def build_probes(
    spec: InstanceSpec,
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """Build ``livenessProbe``/``readinessProbe``/``startupProbe`` entries.

    The manifest's ``health_check`` block (forwarded as
    ``spec.health_check``) becomes a readiness + liveness probe on the
    declared port; ``provider_options.probes`` overrides each probe
    individually with ``liveness``/``readiness``/``startup`` keys.
    Returns an empty dict when nothing asks for probes.
    """
    probes: Dict[str, Any] = {}
    declared = options.get("probes")
    declared = declared if isinstance(declared, dict) else {}

    default_port = 0
    ports = build_container_ports(spec)
    if ports:
        default_port = ports[0]["containerPort"]

    health = spec.health_check or options.get("health_check")
    if isinstance(health, dict) and health:
        shared = _probe_from_dict(health, default_port)
        if shared:
            probes["readinessProbe"] = dict(shared)
            probes["livenessProbe"] = dict(shared)
            # A generous startup window keeps slow boots from being killed
            # by the liveness probe before they bind their port.
            startup_source = health.get("startup") or health.get("startup_probe")
            startup = (
                _probe_from_dict(startup_source, default_port)
                if startup_source
                else None
            )
            if startup:
                probes["startupProbe"] = startup

    for key, field in (
        ("liveness", "livenessProbe"),
        ("readiness", "readinessProbe"),
        ("startup", "startupProbe"),
    ):
        if key not in declared:
            continue
        override = _probe_from_dict(declared[key], default_port)
        if override is None and declared[key] is False:
            probes.pop(field, None)
        elif override:
            probes[field] = override
    return probes


# ----------------------------------------------------------------------
# Security context
# ----------------------------------------------------------------------
def build_container_security_context(
    options: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Container ``securityContext`` from ``hardened`` preset + overrides.

    ``provider_options.hardened: true`` applies the restrictive baseline
    (no privilege escalation, read-only root FS, non-root, drop ALL
    capabilities); explicit ``security_context`` keys win over it.
    Returns ``None`` when nothing is requested so unaffected workloads
    keep the cluster default.
    """
    context: Dict[str, Any] = {}
    if options.get("hardened"):
        context.update(
            {
                "allowPrivilegeEscalation": False,
                "readOnlyRootFilesystem": True,
                "runAsNonRoot": True,
                "capabilities": {"drop": ["ALL"]},
            }
        )
    if options.get("privileged"):
        context["privileged"] = True

    mapping = {
        "run_as_user": "runAsUser",
        "run_as_group": "runAsGroup",
        "fs_group": "fsGroup",
        "read_only_root_filesystem": "readOnlyRootFilesystem",
        "allow_privilege_escalation": "allowPrivilegeEscalation",
        "run_as_non_root": "runAsNonRoot",
        "privileged": "privileged",
    }
    for key, field in mapping.items():
        if key in options and options[key] is not None:
            value = options[key]
            if field in (
                "runAsUser",
                "runAsGroup",
                "fsGroup",
            ):
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    continue
            elif isinstance(value, str):
                value = value.lower() in ("1", "true", "yes", "on")
            context[field] = value
    capabilities = options.get("capabilities")
    if isinstance(capabilities, dict):
        block: Dict[str, Any] = {}
        if isinstance(capabilities.get("add"), list):
            block["add"] = [str(c) for c in capabilities["add"]]
        if isinstance(capabilities.get("drop"), list):
            block["drop"] = [str(c) for c in capabilities["drop"]]
        if block:
            context["capabilities"] = block
    explicit = options.get("security_context")
    if isinstance(explicit, dict):
        for key, value in explicit.items():
            context[str(key)] = value
    return context or None


def build_pod_security_context(options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Pod-level ``securityContext`` (fsGroup, seccomp, runAs* defaults)."""
    source = options.get("pod_security_context")
    context: Dict[str, Any] = {}
    if isinstance(source, dict):
        context.update(source)
    for key, field in (
        ("fs_group", "fsGroup"),
        ("fs_group_change_policy", "fsGroupChangePolicy"),
        ("run_as_user", "runAsUser"),
        ("run_as_group", "runAsGroup"),
        ("run_as_non_root", "runAsNonRoot"),
        ("supplemental_groups", "supplementalGroups"),
    ):
        if key in options and options[key] is not None:
            value = options[key]
            if field in ("runAsUser", "runAsGroup", "fsGroup"):
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    continue
            elif field == "supplementalGroups":
                try:
                    value = [int(v) for v in value]
                except (TypeError, ValueError):
                    continue
            elif isinstance(value, str):
                value = value.lower() in ("1", "true", "yes", "on")
            context[field] = value
    seccomp = options.get("seccomp_profile")
    if isinstance(seccomp, dict):
        context["seccompProfile"] = seccomp
    elif seccomp:
        context["seccompProfile"] = {"type": str(seccomp)}
    return context or None


# ----------------------------------------------------------------------
# Sidecar / init containers
# ----------------------------------------------------------------------
def _aux_container(entry: Any, main_name: str) -> Optional[Dict[str, Any]]:
    """Build one sidecar/init container dict from a manifest entry."""
    if not isinstance(entry, dict) or not entry.get("image"):
        return None
    name = sanitize_name(str(entry.get("name") or f"{main_name}-aux"))
    if name == main_name:
        name = f"{main_name}-aux"
    container: Dict[str, Any] = {"name": name, "image": str(entry["image"])}
    for key in ("command", "args"):
        value = entry.get(key)
        if isinstance(value, (list, tuple)) and value:
            container[key] = [str(v) for v in value]
    env = entry.get("env")
    if isinstance(env, dict) and env:
        container["env"] = [{"name": str(k), "value": str(v)} for k, v in env.items()]
    ports = entry.get("ports")
    if isinstance(ports, dict):
        built: List[Dict[str, Any]] = []
        for key in ports:
            number, protocol = _split_port_key(str(key))
            if number <= 0:
                continue
            built.append(
                {
                    "name": f"port-{number}-{protocol.lower()}",
                    "containerPort": number,
                    "protocol": protocol,
                }
            )
        if built:
            container["ports"] = built
    mounts = entry.get("volume_mounts") or entry.get("volumeMounts")
    if isinstance(mounts, list):
        container["volumeMounts"] = mounts
    resources = entry.get("resources")
    if isinstance(resources, dict):
        container["resources"] = resources
    if entry.get("privileged"):
        container["securityContext"] = {"privileged": True}
    return container


def build_sidecars(
    instance_name: str,
    spec: InstanceSpec,
    options: Dict[str, Any],
) -> tuple:
    """Return ``(init_containers, sidecars)`` from provider options.

    Entries missing an image or duplicating another container name are
    skipped; :func:`validate_k8s_options` reports them as errors first in
    the normal flow.
    """
    main_name = sanitize_name(instance_name)
    init_entries = options.get("init_containers")
    side_entries = options.get("sidecars")
    init_containers: List[Dict[str, Any]] = []
    sidecars: List[Dict[str, Any]] = []
    seen = {main_name}
    if isinstance(init_entries, list):
        for entry in init_entries:
            built = _aux_container(entry, main_name)
            if built and built["name"] not in seen:
                init_containers.append(built)
                seen.add(built["name"])
    if isinstance(side_entries, list):
        for entry in side_entries:
            built = _aux_container(entry, main_name)
            if built and built["name"] not in seen:
                sidecars.append(built)
                seen.add(built["name"])
    return init_containers, sidecars


# ----------------------------------------------------------------------
# Autoscaling / availability / network policy
# ----------------------------------------------------------------------
def build_hpa(
    instance_name: str,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
    target_kind: str = WORKLOAD_DEPLOYMENT,
) -> Optional[Dict[str, Any]]:
    """Build an autoscaling/v2 HorizontalPodAutoscaler.

    Driven by ``provider_options.autoscale``::

        autoscale:
          min_replicas: 2
          max_replicas: 6
          cpu_percent: 70        # target average utilization
          memory_percent: 80     # optional second metric

    Returns ``None`` when autoscaling is not requested or the bounds are
    invalid (reported by :func:`validate_k8s_options` first).
    """
    autoscale = options.get("autoscale")
    if not isinstance(autoscale, dict) or not autoscale:
        return None
    try:
        min_replicas = int(
            autoscale.get("min_replicas", autoscale.get("minReplicas", 1))
        )
        max_replicas = int(
            autoscale.get("max_replicas", autoscale.get("maxReplicas", 0))
        )
    except (TypeError, ValueError):
        return None
    if min_replicas < 1 or max_replicas < min_replicas:
        return None

    metrics: List[Dict[str, Any]] = []
    cpu_percent = autoscale.get("cpu_percent", autoscale.get("cpuPercent"))
    memory_percent = autoscale.get("memory_percent", autoscale.get("memoryPercent"))
    for source, resource_name in ((cpu_percent, "cpu"), (memory_percent, "memory")):
        if source is None:
            continue
        try:
            utilization = int(source)
        except (TypeError, ValueError):
            continue
        if not 1 <= utilization <= 100:
            continue
        metrics.append(
            {
                "type": "Resource",
                "resource": {
                    "name": resource_name,
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": utilization,
                    },
                },
            }
        )
    if not metrics:
        return None

    kind = (
        "StatefulSet"
        if str(target_kind).lower() == WORKLOAD_STATEFULSET
        else "Deployment"
    )
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    return {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {"name": sanitize_name(instance_name), "labels": labels},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": kind,
                "name": sanitize_name(instance_name),
            },
            "minReplicas": min_replicas,
            "maxReplicas": max_replicas,
            "metrics": metrics,
        },
    }


def build_pdb(
    instance_name: str,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    """Build a policy/v1 PodDisruptionBudget from ``provider_options.pdb``.

    ``{"min_available": 1}`` or ``{"max_unavailable": 1}`` (ints or
    percentage strings); exactly one key is honored.
    """
    pdb_opt = options.get("pdb")
    if not isinstance(pdb_opt, dict) or not pdb_opt:
        return None
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    spec_block: Dict[str, Any] = {
        "selector": {
            "matchLabels": managed_labels(instance_name, prefix, managed_by, manifest)
        }
    }
    if pdb_opt.get("min_available") is not None:
        spec_block["minAvailable"] = _pdb_value(pdb_opt["min_available"])
    elif pdb_opt.get("max_unavailable") is not None:
        spec_block["maxUnavailable"] = _pdb_value(pdb_opt["max_unavailable"])
    else:
        return None
    return {
        "apiVersion": "policy/v1",
        "kind": "PodDisruptionBudget",
        "metadata": {"name": sanitize_name(instance_name), "labels": labels},
        "spec": spec_block,
    }


def _pdb_value(value: Any) -> Any:
    if isinstance(value, str) and value.endswith("%"):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_network_policy(
    instance_name: str,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    """Build a networking.k8s.io/v1 NetworkPolicy.

    ``provider_options.network_policy`` may be:

    * ``true`` — ingress allowed only from pods of the same manifest
      (same instance when no manifest is set);
    * a dict with ``ingress``/``egress`` where each is ``false`` (deny
      all), ``true`` (allow all — an empty rule), or a list of raw
      Kubernetes rule objects.

    DNS egress is preserved when egress is restricted unless raw rules
    are supplied, so a locked-down pod can still resolve names.
    """
    np_opt = options.get("network_policy")
    if not np_opt:
        return None
    if isinstance(np_opt, bool):
        np_opt = {"ingress": True}
    if not isinstance(np_opt, dict):
        return None

    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    peer_labels = (
        {f"{prefix}/manifest": sanitize_name(manifest)}
        if manifest
        else {f"{prefix}/instance": sanitize_name(instance_name)}
    )
    spec_block: Dict[str, Any] = {
        "podSelector": {
            "matchLabels": {f"{prefix}/instance": sanitize_name(instance_name)}
        },
        "policyTypes": [],
    }

    if "ingress" in np_opt:
        spec_block["policyTypes"].append("Ingress")
        ingress = np_opt["ingress"]
        if ingress is False:
            pass  # policy type without rules denies all ingress
        elif ingress is True:
            spec_block["ingress"] = [
                {"from": [{"podSelector": {"matchLabels": peer_labels}}]}
            ]
        elif isinstance(ingress, list):
            spec_block["ingress"] = ingress

    if "egress" in np_opt:
        spec_block["policyTypes"].append("Egress")
        egress = np_opt["egress"]
        if egress is False:
            spec_block["egress"] = [
                {
                    "to": [
                        {
                            "namespaceSelector": {
                                "matchLabels": {
                                    "kubernetes.io/metadata.name": "kube-system"
                                }
                            }
                        }
                    ],
                    "ports": [
                        {"protocol": "UDP", "port": 53},
                        {"protocol": "TCP", "port": 53},
                    ],
                }
            ]
        elif egress is True:
            spec_block["egress"] = [{}]
        elif isinstance(egress, list):
            spec_block["egress"] = egress

    if not spec_block["policyTypes"]:
        return None
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": sanitize_name(instance_name), "labels": labels},
        "spec": spec_block,
    }


def build_service_account(
    instance_name: str,
    options: Dict[str, Any],
    prefix: str = DEFAULT_PREFIX,
    managed_by: str = DEFAULT_MANAGED_BY,
    manifest: str = "",
) -> Optional[Dict[str, Any]]:
    """Build a ServiceAccount when ``create_service_account`` is set.

    Without the flag an operator-managed account is referenced by
    ``provider_options.service_account`` instead (already wired into the
    pod spec) and is never created or deleted here.
    """
    if not options.get("create_service_account"):
        return None
    name = str(options.get("service_account") or sanitize_name(instance_name))
    labels = managed_labels(instance_name, prefix, managed_by, manifest)
    body: Dict[str, Any] = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": sanitize_name(name), "labels": labels},
    }
    if options.get("automount_service_account_token") is not None:
        body["automountServiceAccountToken"] = bool(
            options["automount_service_account_token"]
        )
    return body


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------
VALID_ACCESS_MODES = frozenset(
    {"ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany", "ReadWriteOncePod"}
)
VALID_PATH_TYPES = frozenset({"Prefix", "Exact", "ImplementationSpecific"})
VALID_RESTART_POLICIES = frozenset({"Always", "OnFailure", "Never"})


def validate_k8s_options(options: Dict[str, Any]) -> List[str]:
    """Return human-readable problems in ``provider_options``.

    The provider raises ``ProviderConfigError`` with these messages before
    touching the cluster, so a bad manifest fails fast instead of leaving
    half-applied objects.  An empty list means the options are acceptable.
    """
    if not isinstance(options, dict):
        return ["provider_options must be a mapping"]
    errors: List[str] = []

    workload = options.get("workload")
    if workload is not None and str(workload).lower() not in VALID_WORKLOADS:
        errors.append(
            f"workload must be one of {sorted(VALID_WORKLOADS)}, got {workload!r}"
        )

    if options.get("replicas") is not None:
        try:
            replicas = int(options["replicas"])
            if replicas < 0:
                errors.append("replicas must be >= 0")
        except (TypeError, ValueError):
            errors.append("replicas must be an integer")

    service_type = options.get("service_type")
    if service_type is not None and service_type not in VALID_SERVICE_TYPES:
        errors.append(
            f"service_type must be one of {sorted(VALID_SERVICE_TYPES)}, "
            f"got {service_type!r}"
        )
    node_ports = options.get("node_ports")
    if isinstance(node_ports, dict):
        for container_port, node_port in node_ports.items():
            try:
                number = int(node_port)
            except (TypeError, ValueError):
                errors.append(f"node_ports[{container_port!r}] must be an integer")
                continue
            if not 30000 <= number <= 32767:
                errors.append(
                    f"node_ports[{container_port!r}] must be in 30000-32767, "
                    f"got {number}"
                )
    elif node_ports is not None:
        errors.append("node_ports must be a mapping of container port to node port")

    pull_policy = options.get("image_pull_policy")
    if pull_policy is not None and pull_policy not in VALID_IMAGE_PULL_POLICIES:
        errors.append(
            f"image_pull_policy must be one of {sorted(VALID_IMAGE_PULL_POLICIES)}, "
            f"got {pull_policy!r}"
        )

    restart_policy = options.get("restart_policy")
    if restart_policy is not None and restart_policy not in VALID_RESTART_POLICIES:
        errors.append(
            f"restart_policy must be one of {sorted(VALID_RESTART_POLICIES)}, "
            f"got {restart_policy!r}"
        )

    errors.extend(_validate_resources(options))
    errors.extend(_validate_ingress(options))
    errors.extend(_validate_autoscale(options))
    errors.extend(_validate_pdb(options))
    errors.extend(_validate_storage(options))
    errors.extend(_validate_probes(options))
    errors.extend(_validate_aux_containers(options))
    errors.extend(_validate_network_policy(options))
    errors.extend(_validate_misc(options))
    return errors


def _validate_resources(options: Dict[str, Any]) -> List[str]:
    resources = options.get("resources")
    if resources is None:
        return []
    if not isinstance(resources, dict):
        return ["resources must be a mapping with requests/limits"]
    errors: List[str] = []
    requests = resources.get("requests")
    limits = resources.get("limits")
    for label, block in (("requests", requests), ("limits", limits)):
        if block is not None and not isinstance(block, dict):
            errors.append(f"resources.{label} must be a mapping")
    if not isinstance(requests, dict) or not isinstance(limits, dict):
        return errors
    for metric, parser in (
        ("cpu", parse_quantity_cpu),
        ("memory", parse_quantity_memory),
    ):
        request = requests.get(metric)
        limit = limits.get(metric)
        if request is None or limit is None:
            continue
        try:
            if parser(request) > parser(limit):
                errors.append(
                    f"resources.{metric}: request {request!r} exceeds limit {limit!r}"
                )
        except (TypeError, ValueError):
            errors.append(f"resources.{metric} values must be quantities")
    return errors


def _validate_ingress(options: Dict[str, Any]) -> List[str]:
    ingress = options.get("ingress")
    if not ingress:
        return []
    errors: List[str] = []
    if isinstance(ingress, dict):
        path = ingress.get("path", "/")
        if not str(path).startswith("/"):
            errors.append(f"ingress.path must start with '/', got {path!r}")
        path_type = ingress.get("path_type", "Prefix")
        if path_type not in VALID_PATH_TYPES:
            errors.append(
                f"ingress.path_type must be one of {sorted(VALID_PATH_TYPES)}, "
                f"got {path_type!r}"
            )
    elif not isinstance(ingress, str):
        errors.append("ingress must be a hostname string or a mapping")
    return errors


def _validate_autoscale(options: Dict[str, Any]) -> List[str]:
    autoscale = options.get("autoscale")
    if not autoscale:
        return []
    errors: List[str] = []
    if not isinstance(autoscale, dict):
        return ["autoscale must be a mapping"]
    try:
        min_replicas = int(
            autoscale.get("min_replicas", autoscale.get("minReplicas", 1))
        )
        max_replicas = int(
            autoscale.get("max_replicas", autoscale.get("maxReplicas", 0))
        )
    except (TypeError, ValueError):
        return ["autoscale min_replicas/max_replicas must be integers"]
    if min_replicas < 1:
        errors.append("autoscale.min_replicas must be >= 1")
    if max_replicas < min_replicas:
        errors.append(
            f"autoscale.max_replicas ({max_replicas}) must be >= "
            f"min_replicas ({min_replicas})"
        )
    for key in ("cpu_percent", "memory_percent", "cpuPercent", "memoryPercent"):
        if autoscale.get(key) is None:
            continue
        try:
            value = int(autoscale[key])
        except (TypeError, ValueError):
            errors.append(f"autoscale.{key} must be an integer percentage")
            continue
        if not 1 <= value <= 100:
            errors.append(f"autoscale.{key} must be between 1 and 100")
    return errors


def _validate_pdb(options: Dict[str, Any]) -> List[str]:
    pdb_opt = options.get("pdb")
    if not pdb_opt:
        return []
    if not isinstance(pdb_opt, dict):
        return ["pdb must be a mapping"]
    has_min = pdb_opt.get("min_available") is not None
    has_max = pdb_opt.get("max_unavailable") is not None
    if has_min == has_max:
        return ["pdb requires exactly one of min_available or max_unavailable"]
    for key in ("min_available", "max_unavailable"):
        value = pdb_opt.get(key)
        if value is None:
            continue
        if isinstance(value, str) and value.endswith("%"):
            try:
                percent = int(value[:-1])
            except ValueError:
                return [f"pdb.{key} must be an integer or a percentage like '50%'"]
            if not 0 <= percent <= 100:
                return [f"pdb.{key} percentage must be 0-100"]
        else:
            try:
                if int(value) < 0:
                    return [f"pdb.{key} must be >= 0"]
            except (TypeError, ValueError):
                return [f"pdb.{key} must be an integer or a percentage like '50%'"]
    return []


def _validate_storage(options: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    access_mode = options.get("access_mode")
    if access_mode is not None and access_mode not in VALID_ACCESS_MODES:
        errors.append(
            f"access_mode must be one of {sorted(VALID_ACCESS_MODES)}, "
            f"got {access_mode!r}"
        )
    mount_path = options.get("volume_mount_path")
    if mount_path is not None and not str(mount_path).startswith("/"):
        errors.append(f"volume_mount_path must be absolute, got {mount_path!r}")
    storage_size = options.get("storage_size")
    if storage_size is not None and not isinstance(storage_size, str):
        errors.append("storage_size must be a quantity string like '10Gi'")
    return errors


def _validate_probes(options: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    probes = options.get("probes")
    sources: List[tuple] = []
    if isinstance(probes, dict):
        sources = [(f"probes.{key}", value) for key, value in probes.items()]
    health = options.get("health_check")
    if isinstance(health, dict):
        sources.append(("health_check", health))
    for label, source in sources:
        if not isinstance(source, dict) or source is False:
            continue
        for time_key in ("initial_delay", "period", "timeout", "success", "failure"):
            if source.get(time_key) is None:
                continue
            try:
                if int(source[time_key]) < 0:
                    errors.append(f"{label}.{time_key} must be >= 0")
            except (TypeError, ValueError):
                errors.append(f"{label}.{time_key} must be an integer")
        port = source.get("port")
        if port is not None:
            try:
                if int(port) <= 0:
                    errors.append(f"{label}.port must be > 0")
            except (TypeError, ValueError):
                errors.append(f"{label}.port must be an integer")
        if not source.get("cmd") and not source.get("command") and port is None:
            if source.get("path") or source.get("type") in ("http", "tcp"):
                errors.append(f"{label} needs a port")
    return errors


def _validate_aux_containers(options: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    seen: set = set()
    for key, label in (
        ("init_containers", "init_containers"),
        ("sidecars", "sidecars"),
    ):
        entries = options.get(key)
        if entries is None:
            continue
        if not isinstance(entries, list):
            errors.append(f"{label} must be a list of container mappings")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"{label}[{index}] must be a mapping")
                continue
            if not entry.get("image"):
                errors.append(f"{label}[{index}] requires an image")
            name = entry.get("name")
            if name:
                cleaned = sanitize_name(str(name))
                if cleaned in seen:
                    errors.append(f"duplicate container name {cleaned!r}")
                seen.add(cleaned)
    return errors


def _validate_network_policy(options: Dict[str, Any]) -> List[str]:
    np_opt = options.get("network_policy")
    if not np_opt or isinstance(np_opt, bool):
        return []
    if not isinstance(np_opt, dict):
        return ["network_policy must be a boolean or a mapping"]
    errors: List[str] = []
    for key in ("ingress", "egress"):
        if key not in np_opt:
            continue
        value = np_opt[key]
        if not isinstance(value, (bool, list)):
            errors.append(f"network_policy.{key} must be a boolean or a list of rules")
    unknown = set(np_opt) - {"ingress", "egress"}
    if unknown:
        errors.append(f"network_policy has unknown keys: {', '.join(sorted(unknown))}")
    return errors


def _validate_misc(options: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    grace = options.get("termination_grace_period_seconds")
    if grace is not None:
        try:
            if int(grace) < 0:
                errors.append("termination_grace_period_seconds must be >= 0")
        except (TypeError, ValueError):
            errors.append("termination_grace_period_seconds must be an integer")
    namespace = options.get("namespace")
    if namespace is not None and not re.fullmatch(
        r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", str(namespace)
    ):
        errors.append(f"namespace {namespace!r} is not a valid DNS label")
    for key in (
        "node_selector",
        "affinity",
        "annotations",
        "pod_annotations",
        "ingress_annotations",
        "labels",
    ):
        value = options.get(key)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{key} must be a mapping")
    for key in ("tolerations", "image_pull_secrets"):
        value = options.get(key)
        if value is not None and not isinstance(value, list):
            errors.append(f"{key} must be a list")
    pull_secrets = options.get("image_pull_secrets")
    if isinstance(pull_secrets, list):
        for entry in pull_secrets:
            if not isinstance(entry, str) or not entry:
                errors.append("image_pull_secrets entries must be non-empty strings")
                break
    service_account = options.get("service_account")
    if service_account is not None and not re.fullmatch(
        r"[a-z0-9]([-a-z0-9.]*[a-z0-9])?", str(service_account)
    ):
        errors.append(f"service_account {service_account!r} is not a valid DNS name")
    ingress = options.get("ingress")
    if isinstance(ingress, dict) and ingress.get("host") is not None:
        host = str(ingress["host"])
        if " " in host:
            errors.append(f"ingress.host {host!r} must not contain spaces")
    return errors


# ----------------------------------------------------------------------
# Drift / observed state parsing
# ----------------------------------------------------------------------
def parse_quantity_cpu(value: Any) -> float:
    """Parse a Kubernetes CPU quantity (``500m``, ``1``, ``1.5``) to cores."""
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        if text.endswith("m"):
            return float(text[:-1]) / 1000.0
        if text.endswith("n"):
            return float(text[:-1]) / 1_000_000_000.0
        return float(text)
    except ValueError:
        return 0.0


def parse_quantity_memory(value: Any) -> int:
    """Parse a Kubernetes memory quantity to MiB."""
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    units = {
        "Ki": 1 / 1024.0,
        "Mi": 1.0,
        "Gi": 1024.0,
        "Ti": 1024.0 * 1024.0,
        "K": 1000.0 / (1024.0 * 1024.0),
        "M": 1_000_000.0 / (1024.0 * 1024.0),
        "G": 1_000_000_000.0 / (1024.0 * 1024.0),
    }
    for suffix, factor in sorted(units.items(), key=lambda kv: -len(kv[0])):
        if text.endswith(suffix):
            try:
                return int(float(text[: -len(suffix)]) * factor)
            except ValueError:
                return 0
    try:
        return int(float(text) / (1024.0 * 1024.0))
    except ValueError:
        return 0


def parse_workload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract normalized observed state from a Deployment/StatefulSet body."""
    spec = raw.get("spec", {}) or {}
    status = raw.get("status", {}) or {}
    metadata = raw.get("metadata", {}) or {}
    template_spec = (spec.get("template", {}) or {}).get("spec", {}) or {}
    containers = template_spec.get("containers", []) or [{}]
    container = containers[0] if containers else {}
    resources = container.get("resources", {}) or {}
    limits = resources.get("limits", {}) or {}
    requests = resources.get("requests", {}) or {}

    port_entries = container.get("ports", []) or []
    ports: Dict[str, str] = {}
    for entry in port_entries:
        number = entry.get("containerPort")
        protocol = str(entry.get("protocol", "TCP")).lower()
        if number:
            ports[f"{number}/{protocol}"] = str(number)

    env: Dict[str, str] = {}
    for entry in container.get("env", []) or []:
        if entry.get("name") is not None and entry.get("value") is not None:
            env[str(entry["name"])] = str(entry["value"])

    replicas = spec.get("replicas", 0)
    return {
        "name": metadata.get("name", ""),
        "labels": metadata.get("labels", {}) or {},
        "annotations": metadata.get("annotations", {}) or {},
        "image": container.get("image", ""),
        "replicas": replicas if replicas is not None else 0,
        "ready_replicas": status.get("readyReplicas", 0) or 0,
        "available_replicas": status.get("availableReplicas", 0) or 0,
        "updated_replicas": status.get("updatedReplicas", 0) or 0,
        "cpu_cores": parse_quantity_cpu(limits.get("cpu") or requests.get("cpu")),
        "memory_mb": parse_quantity_memory(
            limits.get("memory") or requests.get("memory")
        ),
        "ports": ports,
        "env": env,
        "created_at": metadata.get("creationTimestamp", ""),
        "kind": raw.get("kind", "Deployment"),
        "workload": (
            WORKLOAD_STATEFULSET
            if str(raw.get("kind", "")).lower() == "statefulset"
            else WORKLOAD_DEPLOYMENT
        ),
        "selector": (spec.get("selector", {}) or {}).get("matchLabels", {}) or {},
    }


def map_pod_health(pod: Dict[str, Any]) -> Dict[str, Any]:
    """Map a pod's phase/container statuses to the shared health model.

    Returns ``{"ready": bool, "phase": str, "restarts": int, "reason": str}``
    which the provider folds into ``InstanceInfo.status`` and health.
    """
    status = pod.get("status", {}) or {}
    phase = str(status.get("phase", "Unknown"))
    ready = False
    restarts = 0
    reason = ""
    container_statuses = status.get("containerStatuses", []) or []
    if container_statuses:
        ready = all(bool(cs.get("ready")) for cs in container_statuses)
        restarts = sum(int(cs.get("restartCount", 0)) for cs in container_statuses)
        for cs in container_statuses:
            state = cs.get("state", {}) or {}
            if "waiting" in state:
                reason = str(state["waiting"].get("reason", "")) or reason
            elif "terminated" in state:
                reason = str(state["terminated"].get("reason", "")) or reason
    else:
        ready = phase == "Running"
    return {
        "ready": ready,
        "phase": phase,
        "restarts": restarts,
        "reason": reason,
    }


def map_pod_conditions(pod: Dict[str, Any]) -> Dict[str, str]:
    """Classify a pod for diagnosis (distinct from :func:`map_pod_health`).

    Returns ``{"category": ..., "reason": ..., "message": ...}`` where
    category is one of ``running``, ``not-ready``, ``starting``,
    ``unschedulable``, ``image-pull``, ``crashloop``, ``config``,
    ``failed``, ``succeeded``, ``pending``, ``unknown``.  The provider
    uses it to turn raw pod state into an actionable hint instead of
    "pod is not ready".
    """
    status = pod.get("status", {}) or {}
    phase = str(status.get("phase", "Unknown"))
    conditions = status.get("conditions", []) or []
    container_statuses = status.get("containerStatuses", []) or []
    init_statuses = status.get("initContainerStatuses", []) or []

    for cs in init_statuses + container_statuses:
        state = cs.get("state", {}) or {}
        waiting = state.get("waiting")
        if isinstance(waiting, dict):
            reason = str(waiting.get("reason", ""))
            message = str(waiting.get("message", "")) or reason
            if reason in ("ImagePullBackOff", "ErrImagePull", "InvalidImageName"):
                return {
                    "category": "image-pull",
                    "reason": reason,
                    "message": message,
                }
            if reason == "ErrImageNeverPull":
                return {
                    "category": "image-pull",
                    "reason": reason,
                    "message": message or "image must be pulled before it can run",
                }
            if reason == "CrashLoopBackOff":
                return {"category": "crashloop", "reason": reason, "message": message}
            if reason in (
                "CreateContainerConfigError",
                "CreateContainerError",
                "SetupFailure",
            ):
                return {"category": "config", "reason": reason, "message": message}
            if reason in ("ContainerCreating", "PodInitializing"):
                return {"category": "starting", "reason": reason, "message": message}
            if reason:
                return {"category": "starting", "reason": reason, "message": message}
        terminated = state.get("terminated")
        if isinstance(terminated, dict) and phase in ("Failed", "Succeeded"):
            reason = str(terminated.get("reason", "")) or phase
            message = str(terminated.get("message", "")) or (
                f"exit code {terminated.get('exitCode')}"
            )
            category = "failed" if phase == "Failed" else "succeeded"
            return {"category": category, "reason": reason, "message": message}

    for condition in conditions:
        if (
            str(condition.get("type")) == "PodScheduled"
            and condition.get("status") == "False"
        ):
            return {
                "category": "unschedulable",
                "reason": str(condition.get("reason") or "Unschedulable"),
                "message": str(condition.get("message") or "pod cannot be scheduled"),
            }

    if phase == "Failed":
        return {
            "category": "failed",
            "reason": "Failed",
            "message": "pod phase is Failed",
        }
    if phase == "Succeeded":
        return {
            "category": "succeeded",
            "reason": "Succeeded",
            "message": "pod completed successfully",
        }
    if phase == "Pending":
        return {"category": "pending", "reason": "Pending", "message": "pod is pending"}
    if phase == "Running":
        ready = (
            all(bool(cs.get("ready")) for cs in container_statuses)
            if container_statuses
            else False
        )
        if ready:
            return {"category": "running", "reason": "Ready", "message": "pod is ready"}
        restarts = sum(int(cs.get("restartCount", 0)) for cs in container_statuses)
        if restarts:
            return {
                "category": "crashloop",
                "reason": "Restarting",
                "message": f"container restarted {restarts} time(s) and is not ready",
            }
        return {
            "category": "not-ready",
            "reason": "NotReady",
            "message": "pod runs but is not ready",
        }
    return {"category": "unknown", "reason": phase, "message": f"phase {phase}"}


def summarize_events(
    items: Optional[List[Dict[str, Any]]],
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Flatten and dedupe Kubernetes events for a diagnosis response.

    Repeated events (same reason+message) collapse into one entry with a
    count; warnings sort before normal events, then newest first.  The
    raw involved-object payload is reduced to strings so the result is
    JSON-serializable as-is.
    """
    if not items:
        return []
    grouped: Dict[tuple, Dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        involved = item.get("involvedObject") or {}
        reason = str(item.get("reason") or "Unknown")
        message = str(item.get("message") or "")
        last = (
            item.get("lastTimestamp")
            or item.get("eventTime")
            or item.get("firstTimestamp")
            or ""
        )
        key = (str(involved.get("name") or ""), reason, message)
        entry = grouped.get(key)
        if entry is None:
            grouped[key] = {
                "object": str(involved.get("name") or ""),
                "kind": str(involved.get("kind") or ""),
                "type": str(item.get("type") or "Normal"),
                "reason": reason,
                "message": message,
                "count": int(item.get("count") or 1),
                "last_timestamp": str(last),
            }
        else:
            entry["count"] += int(item.get("count") or 1)
            if str(last) > entry["last_timestamp"]:
                entry["last_timestamp"] = str(last)
            if str(item.get("type") or "") == "Warning":
                entry["type"] = "Warning"
    ordered = sorted(
        grouped.values(),
        key=lambda e: (e["type"] != "Warning", e["last_timestamp"]),
        reverse=True,
    )
    return ordered[:limit]


def parse_hpa(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract normalized observed state from an autoscaling/v2 HPA body."""
    if not isinstance(raw, dict):
        return {}
    spec = raw.get("spec", {}) or {}
    status = raw.get("status", {}) or {}
    current_cpu: Optional[int] = None
    current_memory: Optional[int] = None
    for metric in status.get("currentMetrics") or []:
        resource = (metric.get("resource") or {}) if isinstance(metric, dict) else {}
        if resource.get("name") != "cpu" and resource.get("name") != "memory":
            continue
        target = resource.get("current") or {}
        value = target.get("averageUtilization")
        if value is None:
            continue
        if resource.get("name") == "cpu":
            current_cpu = int(value)
        else:
            current_memory = int(value)
    return {
        "name": (raw.get("metadata") or {}).get("name", ""),
        "min_replicas": spec.get("minReplicas", 0) or 0,
        "max_replicas": spec.get("maxReplicas", 0) or 0,
        "desired_replicas": status.get("desiredReplicas", 0) or 0,
        "current_replicas": status.get("currentReplicas", 0) or 0,
        "current_cpu": current_cpu,
        "current_memory": current_memory,
    }


def status_from_health(ready: bool, replicas: int, ready_replicas: int) -> str:
    """Collapse replica/health signals into a power-state string."""
    if replicas == 0:
        return "stopped"
    if ready and ready_replicas >= replicas:
        return "running"
    if ready_replicas > 0:
        return "running"
    return "unknown"
