"""Persistent mapping of application instances to their compute provider.

The InfraFile manifest is the authoritative source for which backend runs an
instance, but reconciliation is transient: after a deploy the operator still
needs to know "where does ``web-01`` live?" without re-parsing every
manifest.  :class:`ManifestStore` records that mapping (and the last
observed outcome) in a JSON file guarded by the same advisory lock used by
the VM inventory, so concurrent deploy/GitOps requests never lose an entry.

This store is intentionally small: it caches decisions, it does not
override the manifest.  When the manifest and the store disagree, the
manifest wins and the store is rewritten.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config import config

from compute.file_lock import read_json, update_json_locked

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ManifestStore:
    """File-backed record of instance/manifest -> provider assignments."""

    def __init__(self, path: Optional[str] = None, lock_timeout: float = 10.0):
        self._path_override = path
        self.lock_timeout = lock_timeout

    @property
    def path(self) -> str:
        # Resolved per access so tests and multi-tenant deployments can
        # retarget the file without rebuilding every consumer.
        return self._path_override or config.MANIFEST_STORE_FILE

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def _read(self) -> Dict[str, Any]:
        raw = read_json(self.path, default=None)
        if not isinstance(raw, dict):
            return {"instances": {}, "manifests": {}}
        raw.setdefault("instances", {})
        raw.setdefault("manifests", {})
        return raw

    def provider_for(self, instance_name: str) -> Optional[str]:
        """Return the provider an instance was last reconciled onto."""
        entry = self._read()["instances"].get(instance_name)
        if isinstance(entry, dict):
            return entry.get("provider")
        return None

    def record_for(self, instance_name: str) -> Dict[str, Any]:
        entry = self._read()["instances"].get(instance_name)
        return dict(entry) if isinstance(entry, dict) else {}

    def providers_by_instance(self) -> Dict[str, str]:
        """Return ``{instance: provider}`` for every recorded instance."""
        instances = self._read()["instances"]
        return {
            name: entry.get("provider", "")
            for name, entry in instances.items()
            if isinstance(entry, dict)
        }

    def manifest_record(self, manifest_name: str) -> Dict[str, Any]:
        entry = self._read()["manifests"].get(manifest_name)
        return dict(entry) if isinstance(entry, dict) else {}

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def record(
        self,
        instance_name: str,
        provider: str,
        manifest_name: str = "",
        namespace: str = "",
        instance_id: str = "",
        status: str = "",
        error: str = "",
    ) -> Dict[str, Any]:
        """Persist the provider an instance runs on."""

        def _mutate(current: Dict[str, Any]) -> Dict[str, Any]:
            instances = current.setdefault("instances", {})
            manifests = current.setdefault("manifests", {})
            instances[instance_name] = {
                "provider": provider,
                "manifest": manifest_name,
                "namespace": namespace,
                "instance_id": instance_id,
                "status": status,
                "error": error,
                "updated_at": _utcnow(),
            }
            if manifest_name:
                manifest = manifests.setdefault(manifest_name, {})
                manifest.setdefault("instances", {})[instance_name] = provider
                manifest["provider"] = provider
                manifest["updated_at"] = _utcnow()
            current["updated_at"] = _utcnow()
            return current

        return update_json_locked(
            self.path, _mutate, default={"instances": {}, "manifests": {}},
            timeout=self.lock_timeout,
        )

    def record_manifest(
        self, manifest_name: str, assignments: Dict[str, str], error: str = ""
    ) -> None:
        """Persist a whole manifest's instance -> provider mapping."""

        def _mutate(current: Dict[str, Any]) -> Dict[str, Any]:
            instances = current.setdefault("instances", {})
            manifests = current.setdefault("manifests", {})
            for instance_name, provider in assignments.items():
                existing = instances.get(instance_name)
                if not isinstance(existing, dict):
                    existing = {}
                existing.update(
                    {
                        "provider": provider,
                        "manifest": manifest_name,
                        "updated_at": _utcnow(),
                    }
                )
                instances[instance_name] = existing
            manifests[manifest_name] = {
                "instances": dict(assignments),
                "provider": (
                    next(iter(assignments.values())) if assignments else ""
                ),
                "error": error,
                "updated_at": _utcnow(),
            }
            current["updated_at"] = _utcnow()
            return current

        update_json_locked(
            self.path, _mutate, default={"instances": {}, "manifests": {}},
            timeout=self.lock_timeout,
        )

    def remove(self, instance_name: str) -> bool:
        removed = {"value": False}

        def _mutate(current: Dict[str, Any]) -> Dict[str, Any]:
            instances = current.setdefault("instances", {})
            if instance_name in instances:
                instances.pop(instance_name)
                removed["value"] = True
            return current

        update_json_locked(
            self.path, _mutate, default={"instances": {}, "manifests": {}},
            timeout=self.lock_timeout,
        )
        return removed["value"]

    def clear(self) -> None:
        update_json_locked(
            self.path,
            lambda _current: {"instances": {}, "manifests": {}},
            default={"instances": {}, "manifests": {}},
            timeout=self.lock_timeout,
        )


# Shared singleton so the engine and any HTTP handler observe the same file.
manifest_store = ManifestStore()
