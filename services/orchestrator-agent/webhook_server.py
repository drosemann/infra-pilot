"""aiohttp webhook server for GitOps, health and metrics endpoints.

Extracted from main.py so the webhook surface can be tested and
extended without importing the Discord bot entry point.
"""

import dataclasses
import hashlib
import hmac
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import compute.docker_provider  # noqa: F401  (self-registers the built-in provider)
import psutil
import rbac_store
from aiohttp import web
from compute.registry import ProviderRegistry
from manifest.engine import ManifestEngine
from manifest.schema import InfraFile
from rbac import Organization, Permission, RBACEngine, Role

logger = logging.getLogger(__name__)
# The federation API token holder acts as platform administrator for the
# RBAC management API. Tenant users are represented by memberships inside
# the engine and never authenticate over the wire.
rbac_engine = RBACEngine()
LOCAL_DEVELOPMENT_ENVIRONMENTS = frozenset({"dev", "development", "local"})

# Security-rejection counters for /metrics and alerting. Auth failures today
# are only log lines; without counters brute-force or token-misconfig stays
# invisible until someone reads logs. Outcomes: federation_401/503,
# webhook_401/503, rbac_403.
_auth_failure_counters: dict = {
    "federation_401": 0,
    "federation_503": 0,
    "webhook_401": 0,
    "webhook_503": 0,
    "rbac_403": 0,
}


def _count_auth_failure(outcome: str) -> None:
    """Increment a security-rejection counter (unknown outcomes ignored)."""
    if outcome in _auth_failure_counters:
        _auth_failure_counters[outcome] += 1


def reset_auth_failure_counters() -> None:
    """Reset counters (tests; not used in production paths)."""
    for key in _auth_failure_counters:
        _auth_failure_counters[key] = 0


def _serialize_rbac(obj: Any) -> Any:
    """Serialize RBAC dataclasses and enums into JSON-safe primitives."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return sorted(_serialize_rbac(v) for v in obj)
    if isinstance(obj, dict):
        return {k: _serialize_rbac(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_rbac(v) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return {k: _serialize_rbac(v) for k, v in dataclasses.asdict(obj).items()}
    return obj


async def rbac_roles_list(request: web.Request) -> web.Response:
    """List all roles with their permissions."""
    return web.json_response(
        {"roles": [_serialize_rbac(r) for r in rbac_engine.list_roles()]}
    )


async def rbac_role_create(request: web.Request) -> web.Response:
    """Create a custom role from {name, permissions, description?}."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    name = body.get("name")
    permission_names = body.get("permissions")
    if not isinstance(name, str) or not name or not isinstance(permission_names, list):
        return web.json_response(
            {"error": "name and permissions list are required"}, status=400
        )
    try:
        permissions = {Permission(p) for p in permission_names}
    except ValueError:
        valid = ", ".join(sorted(p.value for p in Permission))
        return web.json_response(
            {"error": "unknown permission; valid values: " + valid}, status=400
        )
    role = Role(
        name=name, permissions=permissions, description=str(body.get("description", ""))
    )
    created = rbac_engine.create_role(role)
    await rbac_store.persist_role(created)
    return web.json_response(_serialize_rbac(created), status=201)


async def rbac_org_create(request: web.Request) -> web.Response:
    """Create an organization and auto-assign the owner role."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    name = body.get("name")
    owner_user_id = body.get("owner_user_id")
    if (
        not isinstance(name, str)
        or not name
        or not isinstance(owner_user_id, str)
        or not owner_user_id
    ):
        return web.json_response(
            {"error": "name and owner_user_id are required"}, status=400
        )
    org = Organization(
        id=str(body.get("id") or f"org-{uuid.uuid4().hex[:12]}"),
        name=name,
        owner_user_id=owner_user_id,
    )
    created = rbac_engine.create_org(org)
    await rbac_store.persist_org(created)
    owner_membership = next(
        (m for m in rbac_engine.list_members(org.id) if m.user_id == owner_user_id),
        None,
    )
    if owner_membership:
        await rbac_store.persist_membership(owner_membership)
    return web.json_response(_serialize_rbac(created), status=201)


async def rbac_orgs_for_user(request: web.Request) -> web.Response:
    """List organizations the given user is a member of (?user_id=...)."""
    user_id = request.query.get("user_id", "")
    if not user_id:
        return web.json_response(
            {"error": "user_id query parameter is required"}, status=400
        )
    orgs = rbac_engine.list_orgs_for_user(user_id)
    return web.json_response({"orgs": [_serialize_rbac(o) for o in orgs]})


async def rbac_role_assign(request: web.Request) -> web.Response:
    """Assign a role to a user within an organization (optionally scoped to a project)."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    user_id = body.get("user_id")
    org_id = body.get("org_id")
    role_name = body.get("role_name")
    if not all(isinstance(v, str) and v for v in (user_id, org_id, role_name)):
        return web.json_response(
            {"error": "user_id, org_id and role_name are required"}, status=400
        )
    if rbac_engine.get_role(role_name) is None:
        return web.json_response({"error": f"unknown role: {role_name}"}, status=400)
    if rbac_engine.get_org(org_id) is None:
        return web.json_response({"error": f"unknown org: {org_id}"}, status=404)
    membership = rbac_engine.assign_role(
        user_id=user_id,
        org_id=org_id,
        role_name=role_name,
        project_id=str(body.get("project_id", "")),
        granted_by=str(body.get("granted_by", "api")),
    )
    await rbac_store.persist_membership(membership)
    return web.json_response(_serialize_rbac(membership), status=201)


async def rbac_org_permissions(request: web.Request) -> web.Response:
    """Return the resolved permission list for a user within an org (?user_id=...)."""
    user_id = request.query.get("user_id", "")
    org_id = request.match_info["org_id"]
    if not user_id:
        return web.json_response(
            {"error": "user_id query parameter is required"}, status=400
        )
    if rbac_engine.get_org(org_id) is None:
        return web.json_response({"error": f"unknown org: {org_id}"}, status=404)
    resolved = [
        p for p in Permission if rbac_engine.has_permission(user_id, p, org_id=org_id)
    ]
    return web.json_response(
        {
            "user_id": user_id,
            "org_id": org_id,
            "permissions": sorted(p.value for p in resolved),
        }
    )


async def rbac_org_members(request: web.Request) -> web.Response:
    """List memberships of an organization (optionally ?project_id=...)."""
    org_id = request.match_info["org_id"]
    if rbac_engine.get_org(org_id) is None:
        return web.json_response({"error": f"unknown org: {org_id}"}, status=404)
    members = rbac_engine.list_members(org_id, request.query.get("project_id", ""))
    return web.json_response({"members": [_serialize_rbac(m) for m in members]})


_SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")


def _require_actor_permission(
    request: web.Request, org_id: str, permission: Permission
) -> Optional[web.Response]:
    """Check actor_user_id has permission; return error response or None if allowed.

    Trust model: every ``/api/`` route already requires the shared
    ``FEDERATION_API_TOKEN`` bearer (see ``verify_federation_token``), so the
    federation token holder is platform admin by design. ``actor_user_id`` is
    asserted by that trusted caller (query ``?actor_user_id=...`` or header
    ``X-Actor-User-Id``) for per-user scoping and audit – it is NOT an
    independent authentication proof. Do not expose ``/api/`` without the
    federation token and expect per-user isolation.
    """
    # Actor can be supplied via query or header. (Membership revocation also
    # accepts it in the JSON body – handled by that caller, not here, because
    # request.json() may only be consumed once.)
    actor_user_id = (
        request.query.get("actor_user_id")
        or request.headers.get("X-Actor-User-Id")
        or request.headers.get("X-User-Id")
    )
    if not actor_user_id:
        return web.json_response(
            {
                "error": "actor_user_id required (query ?actor_user_id=... or header X-Actor-User-Id)"
            },
            status=401,
        )
    if not _SAFE_ID_PATTERN.fullmatch(actor_user_id):
        return web.json_response({"error": "invalid actor_user_id format"}, status=400)
    if not rbac_engine.has_permission(actor_user_id, permission, org_id=org_id):
        logger.warning(
            "RBAC deny: actor %s lacks %s in org %s",
            actor_user_id,
            permission.value,
            org_id,
        )
        _count_auth_failure("rbac_403")
        return web.json_response(
            {"error": f"{permission.value} permission required"}, status=403
        )
    return None


async def rbac_org_delete(request: web.Request) -> web.Response:
    """Delete an organization and its persisted state (requires org:delete).

    Trust model: see ``_require_actor_permission`` – the federation token
    holder asserts ``actor_user_id``; this check scopes/audits the operation
    but does not authenticate the actor independently.
    """
    org_id = request.match_info["org_id"]
    if rbac_engine.get_org(org_id) is None:
        return web.json_response({"error": f"unknown org: {org_id}"}, status=404)
    # Principal-bound authorization
    err = _require_actor_permission(request, org_id, Permission.ORG_DELETE)
    if err:
        return err
    # Persist first – if DB fails, do not mutate in-memory state (atomic)
    before = rbac_store.rbac_persist_failures
    await rbac_store.delete_org(org_id)
    if rbac_store.rbac_persist_failures > before:
        logger.error(
            "Failed to persist org delete %s; in-memory state unchanged", org_id
        )
        return web.json_response(
            {"error": "persistence failed, org not deleted"}, status=500
        )
    rbac_engine.delete_org(org_id)
    return web.json_response({"deleted": org_id})


async def rbac_role_delete(request: web.Request) -> web.Response:
    """Delete a custom role (built-ins cannot be deleted, requires actor with org:manage).

    Trust model: see ``_require_actor_permission`` – the federation token
    holder asserts ``actor_user_id``; this check scopes/audits the operation
    but does not authenticate the actor independently.
    """
    role_name = request.match_info["role_name"]
    role = rbac_engine.get_role(role_name)
    if role is None:
        return web.json_response({"error": f"unknown role: {role_name}"}, status=404)
    if role.is_builtin:
        return web.json_response({"error": "cannot delete built-in role"}, status=400)
    # Role is global – require actor who can manage orgs; use first org of actor or require actor_user_id with any org
    actor_user_id = (
        request.query.get("actor_user_id")
        or request.headers.get("X-Actor-User-Id")
        or request.headers.get("X-User-Id")
    )
    if not actor_user_id:
        return web.json_response(
            {"error": "actor_user_id required for role deletion"}, status=401
        )
    if not _SAFE_ID_PATTERN.fullmatch(actor_user_id):
        return web.json_response({"error": "invalid actor_user_id format"}, status=400)
    # Check that actor has at least org:manage in any org they belong to
    actor_orgs = rbac_engine.list_orgs_for_user(actor_user_id)
    if not any(
        rbac_engine.has_permission(actor_user_id, Permission.ORG_MANAGE, org_id=o.id)
        for o in actor_orgs
    ):
        # Also allow owner/admin who may not yet have org? Fallback to global check via first org
        logger.warning(
            "RBAC deny: actor %s lacks org:manage for role delete", actor_user_id
        )
        _count_auth_failure("rbac_403")
        return web.json_response(
            {"error": "org:manage permission required"}, status=403
        )
    # Persist first – if DB fails, do not mutate in-memory state (atomic,
    # same ordering as rbac_org_delete / rbac_membership_delete). The
    # built-in guard above ensures we never delete a built-in DB row.
    before = rbac_store.rbac_persist_failures
    await rbac_store.delete_role(role_name)
    if rbac_store.rbac_persist_failures > before:
        logger.error(
            "Failed to persist role delete %s; in-memory state unchanged", role_name
        )
        return web.json_response(
            {"error": "persistence failed, role not deleted"}, status=500
        )
    if not rbac_engine.delete_role(role_name):
        # Defensive: is_builtin was checked above, so this means the role
        # vanished between the lookup and now – DB row is already gone.
        logger.warning("Role %s missing from engine after persisted delete", role_name)
    return web.json_response({"deleted": role_name})


async def rbac_membership_delete(request: web.Request) -> web.Response:
    """Revoke a membership (role assignment, requires member:remove).

    Trust model: see ``_require_actor_permission`` – the federation token
    holder asserts ``actor_user_id``; this check scopes/audits the operation
    but does not authenticate the actor independently.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    user_id = body.get("user_id")
    org_id = body.get("org_id")
    project_id = str(body.get("project_id", ""))
    actor_user_id = (
        body.get("actor_user_id")
        or request.query.get("actor_user_id")
        or request.headers.get("X-Actor-User-Id")
    )
    if not all(isinstance(v, str) and v for v in (user_id, org_id)):
        return web.json_response(
            {"error": "user_id and org_id are required"}, status=400
        )
    if not actor_user_id:
        return web.json_response(
            {"error": "actor_user_id required for revocation"}, status=401
        )
    if not _SAFE_ID_PATTERN.fullmatch(actor_user_id) or not _SAFE_ID_PATTERN.fullmatch(
        user_id
    ):
        return web.json_response({"error": "invalid user_id format"}, status=400)
    if not rbac_engine.has_permission(
        actor_user_id, Permission.MEMBER_REMOVE, org_id=org_id
    ):
        logger.info(
            "RBAC deny: actor %s lacks member:remove in org %s", actor_user_id, org_id
        )
        return web.json_response(
            {"error": "member:remove permission required"}, status=403
        )
    # Persist first for atomicity
    before = rbac_store.rbac_persist_failures
    await rbac_store.delete_membership(user_id, org_id, project_id)
    if rbac_store.rbac_persist_failures > before:
        logger.error("Failed to persist membership delete %s@%s", user_id, org_id)
        return web.json_response(
            {"error": "persistence failed, membership not revoked"}, status=500
        )
    removed = rbac_engine.remove_membership(user_id, org_id, project_id)
    if not removed:
        return web.json_response({"error": "membership not found"}, status=404)
    return web.json_response(
        {"revoked": {"user_id": user_id, "org_id": org_id, "project_id": project_id}}
    )


async def deployment_apply(request: web.Request) -> web.Response:
    """Reconcile a manifest on demand (POST /api/v1/deployments).

    Body: ``{"manifest": {...InfraFile...}, "dry_run": bool,
    "user_id": str, "org_id": str}``.  When ``user_id`` and ``org_id``
    are supplied the caller (already authenticated via the federation token
    middleware) is evaluated as that user – requires ``manifest:deploy``.
    Without them the federation token holder acts as platform admin; this
    path is audited and should be used only by trusted internal callers
    (e.g. management-panel forward).

    Trust model: ``FEDERATION_API_TOKEN`` is a shared platform-admin
    credential. ``user_id``/``org_id`` and ``as_platform_admin`` are asserted
    by that trusted caller for scoping/audit – they are NOT independently
    authenticated. Anyone holding the federation token can deploy as any user
    or as platform admin. Keep the token server-side only.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    manifest_data = body.get("manifest")
    if not isinstance(manifest_data, dict) or not manifest_data:
        return web.json_response({"error": "manifest object is required"}, status=400)
    dry_run = bool(body.get("dry_run", False))
    user_id = body.get("user_id")
    org_id = body.get("org_id")
    if user_id is not None or org_id is not None:
        # Strict validation: both must be present and match allow-list
        if not isinstance(user_id, str) or not isinstance(org_id, str):
            return web.json_response(
                {"error": "user_id and org_id must be strings"}, status=400
            )
        if not user_id or not org_id:
            return web.json_response(
                {
                    "error": "org_id is required when user_id is provided (and vice versa)"
                },
                status=400,
            )
        if not _SAFE_ID_PATTERN.fullmatch(user_id) or not _SAFE_ID_PATTERN.fullmatch(
            org_id
        ):
            return web.json_response(
                {"error": "invalid user_id or org_id format"}, status=400
            )
        if not rbac_engine.has_permission(
            user_id, Permission.MANIFEST_DEPLOY, org_id=org_id
        ):
            logger.warning(
                "RBAC deny: user %s lacks manifest:deploy in org %s from %s",
                user_id,
                org_id,
                request.remote,
            )
            _count_auth_failure("rbac_403")
            return web.json_response(
                {"error": "manifest:deploy permission required"}, status=403
            )
        logger.info(
            "deployment_apply as user %s@%s (federated) from %s dry_run=%s",
            user_id,
            org_id,
            request.remote,
            dry_run,
        )
    else:
        # Platform-admin path now requires explicit flag on the federation API.
        # The GitOps webhook (/webhook/gitops) is authenticated via HMAC and is allowed
        # to reconcile without a user context; it should not be forced to set the flag.
        is_gitops = request.path == "/webhook/gitops"
        if not is_gitops and not body.get("as_platform_admin"):
            return web.json_response(
                {
                    "error": "user_id and org_id required, or set as_platform_admin=true for explicit platform operation",
                    "hint": "forward from management-panel should set as_platform_admin=true",
                },
                status=400,
            )
        logger.warning(
            "deployment_apply as platform admin (as_platform_admin=%s, gitops=%s) from %s dry_run=%s – audited",
            body.get("as_platform_admin"),
            is_gitops,
            request.remote,
            dry_run,
        )
    try:
        desired = InfraFile.from_dict(manifest_data)
    except Exception as exc:
        return web.json_response({"error": f"invalid manifest: {exc}"}, status=400)
    result = await ManifestEngine(dry_run=dry_run).reconcile(desired)
    status = 200 if not result.errors else 207
    return web.json_response(_serialize_rbac(result), status=status)


async def deployment_providers(request: web.Request) -> web.Response:
    """List registered compute providers (GET /api/v1/providers)."""
    return web.json_response({"providers": ProviderRegistry.list_providers()})


WEBHOOK_REPLAY_WINDOW_SECONDS = int(os.getenv("WEBHOOK_REPLAY_WINDOW_SECONDS", "300"))

# Identities seen within the replay window, used to reject replayed
# requests. Bounded by evicting entries older than the window.
_seen_deliveries: set[str] = set()
_seen_signatures: set[str] = set()
_last_prune = time.monotonic()


def _is_recently_seen(seen: set[str], identity: str) -> bool:
    """Return True if the identity has not been seen recently."""
    global _last_prune
    now = time.monotonic()
    if now - _last_prune > WEBHOOK_REPLAY_WINDOW_SECONDS:
        seen.clear()
        _last_prune = now
    if identity in seen:
        return False
    seen.add(identity)
    return True


def _delivery_is_fresh(delivery_id: str) -> bool:
    """Return True if the delivery ID has not been seen recently."""
    return _is_recently_seen(_seen_deliveries, delivery_id)


def _timestamp_is_fresh(timestamp: str) -> bool:
    """Check an epoch-seconds header against the replay window.

    Rejects malformed or out-of-window values so replayed requests
    carrying an old timestamp fail closed.
    """
    try:
        sent = int(timestamp)
    except (TypeError, ValueError):
        return False
    now = time.time()
    return abs(now - sent) <= WEBHOOK_REPLAY_WINDOW_SECONDS


async def verify_github_signature(
    request: web.Request, handler: Callable[[web.Request], object]
) -> web.Response:
    """Verify GitHub webhook HMAC-SHA256 signature (X-Hub-Signature-256).

    Fails closed: without a configured GITHUB_WEBHOOK_SECRET the route
    refuses all traffic instead of accepting unsigned requests. Each
    X-GitHub-Delivery ID is accepted only once, which blocks replay of
    a captured signed request.
    """
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").strip()
    if not secret:
        _count_auth_failure("webhook_503")
        return web.json_response({"error": "webhook auth not configured"}, status=503)
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if not delivery_id or not _delivery_is_fresh(delivery_id):
        logger.warning(
            "Rejected webhook with missing or replayed delivery ID from %s",
            request.remote,
        )
        _count_auth_failure("webhook_401")
        return web.json_response({"error": "invalid webhook delivery"}, status=401)
    body = await request.read()
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        logger.warning(
            "Rejected webhook with invalid signature from %s", request.remote
        )
        _count_auth_failure("webhook_401")
        return web.json_response({"error": "invalid webhook signature"}, status=401)
    return await handler(request)


async def verify_gitops_token(
    request: web.Request, handler: Callable[[web.Request], object]
) -> web.Response:
    """Verify GitOps webhook signature.

    Fails closed: without a configured GITOPS_WEBHOOK_TOKEN the route
    refuses all traffic instead of accepting unauthenticated requests.
    The ``X-Signature-256`` header must carry
    ``sha256=<hex HMAC-SHA256(GITOPS_WEBHOOK_TOKEN, "{X-Timestamp}\\n{body}")>``
    so the signature covers both the timestamp and the exact manifest
    content. ``X-Timestamp`` must be within the replay window and each
    signature is accepted only once, which blocks replay of a captured
    request inside that window.
    """
    token = os.getenv("GITOPS_WEBHOOK_TOKEN", "").strip()
    if not token:
        _count_auth_failure("webhook_503")
        return web.json_response({"error": "webhook auth not configured"}, status=503)
    timestamp = request.headers.get("X-Timestamp", "")
    if not _timestamp_is_fresh(timestamp):
        logger.warning(
            "Rejected webhook with missing or stale timestamp from %s",
            request.remote,
        )
        _count_auth_failure("webhook_401")
        return web.json_response({"error": "stale webhook"}, status=401)
    signature = request.headers.get("X-Signature-256", "")
    if not signature.startswith("sha256="):
        logger.warning(
            "Rejected webhook with missing signature from %s", request.remote
        )
        _count_auth_failure("webhook_401")
        return web.json_response({"error": "invalid webhook signature"}, status=401)
    body = await request.read()
    expected = hmac.new(
        token.encode(), f"{timestamp}\n".encode() + body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature[7:], expected):
        logger.warning(
            "Rejected webhook with invalid signature from %s", request.remote
        )
        _count_auth_failure("webhook_401")
        return web.json_response({"error": "invalid webhook signature"}, status=401)
    if not _is_recently_seen(_seen_signatures, signature):
        logger.warning("Rejected replayed webhook signature from %s", request.remote)
        _count_auth_failure("webhook_401")
        return web.json_response({"error": "replayed webhook"}, status=401)
    return await handler(request)


async def start_webhook_server(bot_instance=None):
    """Start the aiohttp webhook server for GitOps and health endpoints.

    Args:
        bot_instance: Optional for backwards compatibility; no longer used.
    """
    await rbac_store.load_rbac_state(rbac_engine)
    app = await build_webhook_app(bot_instance)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("GITOPS_WEBHOOK_PORT", "8500"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Webhook server listening on port %d", port)


async def build_webhook_app(bot_instance=None) -> web.Application:
    """Build the aiohttp application with all webhook and API routes.

    Extracted from start_webhook_server so the route table can be tested
    with aiohttp's TestClient without binding a real port.
    """
    app = web.Application()

    async def verify_federation_token(request: web.Request) -> Optional[web.Response]:
        """Check Bearer token on federation API routes (fail-closed).

        In all environments a missing ``FEDERATION_API_TOKEN`` fails closed
        (503) unless ``ALLOW_INSECURE_FEDERATION=true`` is explicitly set – an
        opt-in for local development. This prevents the previous implicit
        dev bypass from accidentally reaching production.

        The federation token is a shared platform-admin credential: any
        holder can assert any ``user_id``/``actor_user_id`` or set
        ``as_platform_admin=true``. Per-user / per-actor checks below are
        scoping and audit, not independent authentication.
        """
        api_token = os.getenv("FEDERATION_API_TOKEN", "").strip()
        if not api_token:
            allow_insecure = (
                os.getenv("ALLOW_INSECURE_FEDERATION", "").strip().lower() == "true"
            )
            if allow_insecure:
                node_environment = os.getenv("NODE_ENV", "").strip()
                environment = (
                    node_environment or os.getenv("ENVIRONMENT", "").strip()
                ).lower()
                if environment not in LOCAL_DEVELOPMENT_ENVIRONMENTS:
                    logger.error(
                        "ALLOW_INSECURE_FEDERATION=true is rejected outside local development "
                        "(resolved environment: %r)",
                        environment,
                    )
                    _count_auth_failure("federation_503")
                    return web.json_response(
                        {
                            "error": "auth not configured",
                            "message": "FEDERATION_API_TOKEN is required outside explicit local development",
                        },
                        status=503,
                    )
                logger.warning(
                    "FEDERATION_API_TOKEN is not set but ALLOW_INSECURE_FEDERATION=true; "
                    "/api/ routes are unauthenticated in %s environment. "
                    "Do not use this outside local development.",
                    environment,
                )
                return None
            _count_auth_failure("federation_503")
            return web.json_response(
                {
                    "error": "auth not configured",
                    "message": "FEDERATION_API_TOKEN is required (or set ALLOW_INSECURE_FEDERATION=true for local dev)",
                },
                status=503,
            )
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and hmac.compare_digest(auth[7:], api_token):
            return None
        _count_auth_failure("federation_401")
        return web.json_response(
            {
                "error": "unauthorized",
                "message": "Invalid or missing federation API token",
            },
            status=401,
        )

    @web.middleware
    async def federation_auth_middleware(request: web.Request, handler):
        """Apply token verification to /api/ paths."""
        if request.path.startswith("/api/"):
            response = await verify_federation_token(request)
            if response:
                return response
        return await handler(request)

    app.middlewares.append(federation_auth_middleware)

    async def health(request: web.Request) -> web.Response:
        from db import get_pool as _get_pool

        db_ok = False
        try:
            pool = await _get_pool()
            conn = await pool.acquire()
            await conn.execute("SELECT 1")
            await pool.release(conn)
            db_ok = True
        except Exception:
            pass

        return web.json_response(
            {
                "status": "ok" if db_ok else "degraded",
                "service": "orchestrator-agent",
                "postgresql": "up" if db_ok else "down",
            }
        )

    async def metrics(request: web.Request) -> web.Response:
        """Prometheus /metrics endpoint."""
        pyver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        lines = [
            "# HELP orchestrator_agent_info Static info about the agent",
            "# TYPE orchestrator_agent_info gauge",
            f'orchestrator_agent_info{{service="orchestrator-agent"}} 1',
            "",
            "# HELP rbac_persist_failures_total RBAC persistence failures",
            "# TYPE rbac_persist_failures_total counter",
            f"rbac_persist_failures_total {rbac_store.rbac_persist_failures}",
            "",
            "# HELP orchestrator_auth_failures_total Security rejections by outcome",
            "# TYPE orchestrator_auth_failures_total counter",
            *(
                f'orchestrator_auth_failures_total{{outcome="{outcome}"}} {count}'
                for outcome, count in sorted(_auth_failure_counters.items())
            ),
            "",
            "# HELP python_info Python runtime info",
            "# TYPE python_info gauge",
            f'python_info{{version="{pyver}"}} 1',
            "",
        ]

        # Process metrics (psutil field names differ per OS: Linux exposes
        # vms/rss, macOS vss/rss – fall back so /metrics never 500s).
        proc = psutil.Process()
        with proc.oneshot():
            mem = proc.memory_info()
            vsize = getattr(mem, "vms", getattr(mem, "vss", 0))
            lines.append(
                "# HELP process_virtual_memory_bytes Virtual memory size in bytes"
            )
            lines.append("# TYPE process_virtual_memory_bytes gauge")
            lines.append(f"process_virtual_memory_bytes {vsize}")
            lines.append(
                "# HELP process_resident_memory_bytes Resident memory size in bytes"
            )
            lines.append("# TYPE process_resident_memory_bytes gauge")
            lines.append(f"process_resident_memory_bytes {mem.rss}")
            cpu_percent = proc.cpu_percent(interval=0)
            lines.append("# HELP process_cpu_percent CPU usage percentage")
            lines.append("# TYPE process_cpu_percent gauge")
            lines.append(f"process_cpu_percent {cpu_percent}")
            lines.append("")

        # VPS instance metrics (from VPSManager, no Discord dependency)
        try:
            from vps_manager import VPSManager

            vm = VPSManager()
            instances = getattr(vm, "vps_instances", {})
            total = len(instances)
            running = sum(1 for i in instances.values() if i.get("status") == "running")
            stopped = sum(1 for i in instances.values() if i.get("status") == "stopped")
            lines.append("# HELP orchestrator_vps_instances_total Total VPS instances")
            lines.append("# TYPE orchestrator_vps_instances_total gauge")
            lines.append(f"orchestrator_vps_instances_total {total}")
            lines.append(
                "# HELP orchestrator_vps_instances_running Running VPS instances"
            )
            lines.append("# TYPE orchestrator_vps_instances_running gauge")
            lines.append(f"orchestrator_vps_instances_running {running}")
            lines.append(
                "# HELP orchestrator_vps_instances_stopped Stopped VPS instances"
            )
            lines.append("# TYPE orchestrator_vps_instances_stopped gauge")
            lines.append(f"orchestrator_vps_instances_stopped {stopped}")
            lines.append("")
        except Exception as exc:
            logger.warning("VPS metrics unavailable: %s", exc)

        return web.Response(
            text="\n".join(lines),
            content_type="text/plain",
            charset="utf-8",
        )

    async def federation_status(request: web.Request) -> web.Response:
        """Federation peer status endpoint (requires valid token)."""
        return web.json_response(
            {
                "status": "ok",
                "service": "orchestrator-agent",
                "federation": {"enabled": bool(os.getenv("FEDERATION_API_TOKEN", ""))},
                "version": "1.0.0",
            }
        )

    async def ready(request: web.Request) -> web.Response:
        """Readiness probe – requires DB connectivity (distinct from liveness /health)."""
        from db import get_pool as _get_pool

        pool = None
        conn = None
        try:
            pool = await _get_pool()
            conn = await pool.acquire()
            await conn.execute("SELECT 1")
            return web.json_response(
                {"status": "ready", "service": "orchestrator-agent"}
            )
        except Exception as exc:
            # Log full exception server-side, return fixed message to avoid leaking driver details
            logger.warning("readiness check failed: %s", exc, exc_info=True)
            return web.json_response(
                {"status": "not_ready", "error": "service not ready"}, status=503
            )
        finally:
            if conn is not None and pool is not None:
                try:
                    await pool.release(conn)
                except Exception:
                    pass

    app.router.add_get("/health", health)
    app.router.add_get("/api/health", health)
    app.router.add_get("/ready", ready)
    app.router.add_get("/api/ready", ready)
    app.router.add_get("/metrics", metrics)
    app.router.add_get("/api/v1/federation/status", federation_status)
    app.router.add_get("/api/v1/rbac/roles", rbac_roles_list)
    app.router.add_post("/api/v1/rbac/roles", rbac_role_create)
    app.router.add_delete("/api/v1/rbac/roles/{role_name}", rbac_role_delete)
    app.router.add_post("/api/v1/rbac/orgs", rbac_org_create)
    app.router.add_get("/api/v1/rbac/orgs", rbac_orgs_for_user)
    app.router.add_delete("/api/v1/rbac/orgs/{org_id}", rbac_org_delete)
    app.router.add_post("/api/v1/rbac/assign", rbac_role_assign)
    app.router.add_delete("/api/v1/rbac/assign", rbac_membership_delete)
    app.router.add_get("/api/v1/rbac/orgs/{org_id}/permissions", rbac_org_permissions)
    app.router.add_get("/api/v1/rbac/orgs/{org_id}/members", rbac_org_members)
    app.router.add_post("/api/v1/deployments", deployment_apply)
    app.router.add_get("/api/v1/providers", deployment_providers)

    # GitOps push webhook: converge toward the manifest sent in the body.
    # Runs the same reconcile path as POST /api/v1/deployments, guarded by
    # an HMAC-SHA256 signature over the timestamp + body instead of the
    # federation token.
    async def gitops_webhook(request: web.Request) -> web.Response:
        return await verify_gitops_token(request, deployment_apply)

    app.router.add_post("/webhook/gitops", gitops_webhook)

    return app
