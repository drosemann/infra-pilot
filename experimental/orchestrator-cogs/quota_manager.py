import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


QUOTA_DIMENSIONS = {
    "cpu_cores": {"type": "float", "unit": "cores", "description": "CPU core limit"},
    "memory_gb": {"type": "float", "unit": "GB", "description": "Memory limit"},
    "storage_gb": {"type": "float", "unit": "GB", "description": "Persistent storage limit"},
    "containers": {"type": "integer", "unit": "count", "description": "Container count limit"},
    "public_ips": {"type": "integer", "unit": "count", "description": "Public IP address limit"},
    "load_balancers": {"type": "integer", "unit": "count", "description": "Load balancer count"},
    "databases": {"type": "integer", "unit": "count", "description": "Database instance count"},
    "backup_storage_gb": {"type": "float", "unit": "GB", "description": "Backup storage limit"},
    "network_bandwidth_mbps": {"type": "integer", "unit": "Mbps", "description": "Network bandwidth limit"},
    "snapshots": {"type": "integer", "unit": "count", "description": "Snapshot count limit"},
}


class QuotaManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._quotas: Dict[str, Dict] = {}
        self._usage: Dict[str, Dict] = {}
        self._requests: Dict[str, Dict] = {}
        self._hierarchy: Dict[str, List[str]] = {}
        self._enforcement_mode = config.get("enforcement_mode", "hard")
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("QuotaManager initialized with enforcement: {self._enforcement_mode}")

    async def close(self) -> None:
        self._quotas.clear()
        self._usage.clear()
        logger.info("QuotaManager closed")

    def create_quota(self, name: str, entity_type: str, entity_id: str,
                     limits: Dict[str, Any], parent_id: Optional[str] = None,
                     description: str = "") -> Dict:
        quota_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        quota = {
            "quota_id": quota_id,
            "name": name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "parent_id": parent_id,
            "limits": self._validate_limits(limits),
            "usage": {dim: 0.0 for dim in QUOTA_DIMENSIONS},
            "description": description,
            "enforcement_mode": self._enforcement_mode,
            "created_at": now,
            "updated_at": now,
            "status": "active",
        }
        self._quotas[quota_id] = quota

        if parent_id:
            if parent_id not in self._hierarchy:
                self._hierarchy[parent_id] = []
            self._hierarchy[parent_id].append(quota_id)

        logger.info(f"Quota {quota_id} created for {entity_type}:{entity_id}")
        return quota

    def get_quota(self, quota_id: str) -> Optional[Dict]:
        return self._quotas.get(quota_id)

    def update_quota(self, quota_id: str, limits: Dict[str, Any]) -> Optional[Dict]:
        quota = self._quotas.get(quota_id)
        if not quota:
            return None
        quota["limits"] = self._validate_limits(limits)
        quota["updated_at"] = datetime.utcnow().isoformat()
        return quota

    def delete_quota(self, quota_id: str) -> bool:
        if quota_id not in self._quotas:
            return False
        del self._quotas[quota_id]
        for parent, children in list(self._hierarchy.items()):
            if quota_id in children:
                children.remove(quota_id)
        logger.info(f"Quota {quota_id} deleted")
        return True

    def _validate_limits(self, limits: Dict[str, Any]) -> Dict[str, Any]:
        validated = {}
        for dim, dim_config in QUOTA_DIMENSIONS.items():
            value = limits.get(dim)
            if value is not None:
                if dim_config["type"] == "float":
                    validated[dim] = float(value)
                elif dim_config["type"] == "integer":
                    validated[dim] = int(value)
        return validated

    def get_effective_limits(self, quota_id: str) -> Dict[str, Any]:
        quota = self._quotas.get(quota_id)
        if not quota:
            return {}
        effective = dict(quota["limits"])
        if quota.get("parent_id"):
            parent_limits = self.get_effective_limits(quota["parent_id"])
            for dim, parent_val in parent_limits.items():
                child_val = effective.get(dim)
                if child_val is None or child_val > parent_val:
                    effective[dim] = parent_val
        return effective

    def update_usage(self, quota_id: str, usage_delta: Dict[str, float]) -> Optional[Dict]:
        quota = self._quotas.get(quota_id)
        if not quota:
            return None
        for dim, delta in usage_delta.items():
            if dim in quota["usage"]:
                quota["usage"][dim] = max(0, quota["usage"][dim] + delta)
        quota["updated_at"] = datetime.utcnow().isoformat()
        return self._check_quota_violations(quota_id)

    def check_quota(self, quota_id: str, requested: Dict[str, Any]) -> Dict:
        quota = self._quotas.get(quota_id)
        if not quota:
            return {"allowed": False, "reason": "Quota not found"}

        limits = self.get_effective_limits(quota_id)
        current_usage = quota["usage"]
        violations = []

        for dim, request_amount in requested.items():
            if dim not in limits:
                continue
            new_total = current_usage.get(dim, 0) + float(request_amount)
            limit = limits.get(dim)
            if limit is not None and new_total > limit:
                violations.append({
                    "dimension": dim,
                    "current": current_usage.get(dim, 0),
                    "requested": float(request_amount),
                    "new_total": new_total,
                    "limit": limit,
                    "overshoot": round(new_total - limit, 2),
                })

        if violations and self._enforcement_mode == "hard":
            return {"allowed": False, "violations": violations, "mode": "hard"}
        if violations and self._enforcement_mode == "soft":
            return {"allowed": True, "violations": violations, "mode": "soft", "warning": True}
        return {"allowed": True, "violations": [], "mode": self._enforcement_mode}

    def _check_quota_violations(self, quota_id: str) -> Dict:
        quota = self._quotas.get(quota_id)
        if not quota:
            return {"violations": []}
        limits = self.get_effective_limits(quota_id)
        violations = []
        for dim, limit in limits.items():
            usage = quota["usage"].get(dim, 0)
            if usage > limit:
                violations.append({
                    "quota_id": quota_id,
                    "dimension": dim,
                    "usage": usage,
                    "limit": limit,
                    "overshoot": round(usage - limit, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return {"violations": violations, "has_violations": len(violations) > 0}

    def request_increase(self, quota_id: str, requested_limits: Dict[str, Any],
                          reason: str, requested_by: str) -> Dict:
        request_id = str(uuid.uuid4())
        request = {
            "request_id": request_id,
            "quota_id": quota_id,
            "requested_limits": self._validate_limits(requested_limits),
            "reason": reason,
            "requested_by": requested_by,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "approved_by": None,
            "approved_at": None,
        }
        self._requests[request_id] = request
        logger.info(f"Quota increase request {request_id} for {quota_id}")
        return request

    def approve_increase(self, request_id: str, approved_by: str) -> Optional[Dict]:
        request = self._requests.get(request_id)
        if not request or request["status"] != "pending":
            return None
        request["status"] = "approved"
        request["approved_by"] = approved_by
        request["approved_at"] = datetime.utcnow().isoformat()
        quota = self._quotas.get(request["quota_id"])
        if quota:
            for dim, val in request["requested_limits"].items():
                if dim in quota["limits"]:
                    quota["limits"][dim] = val
            quota["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Quota increase request {request_id} approved by {approved_by}")
        return request

    def deny_increase(self, request_id: str, denied_by: str, reason: str = "") -> Optional[Dict]:
        request = self._requests.get(request_id)
        if not request or request["status"] != "pending":
            return None
        request["status"] = "denied"
        request["denied_by"] = denied_by
        request["denied_reason"] = reason
        return request

    def list_quotas(self, entity_type: Optional[str] = None) -> List[Dict]:
        quotas = list(self._quotas.values())
        if entity_type:
            quotas = [q for q in quotas if q["entity_type"] == entity_type]
        return sorted(quotas, key=lambda q: q["name"])

    def get_hierarchy(self, root_id: Optional[str] = None) -> Dict:
        if root_id:
            return self._build_tree(root_id)
        roots = [qid for qid, q in self._quotas.items() if not q.get("parent_id")]
        tree = {}
        for root_id in roots:
            tree[root_id] = self._build_tree(root_id)
        return tree

    def _build_tree(self, quota_id: str) -> Dict:
        quota = self._quotas.get(quota_id)
        if not quota:
            return {}
        children = self._hierarchy.get(quota_id, [])
        return {
            "quota": {
                "quota_id": quota["quota_id"],
                "name": quota["name"],
                "limits": quota["limits"],
                "usage": quota["usage"],
            },
            "children": {cid: self._build_tree(cid) for cid in children},
        }

    def get_pending_requests(self) -> List[Dict]:
        return [r for r in self._requests.values() if r["status"] == "pending"]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._quotas)
        violated = 0
        for q in self._quotas.values():
            for dim, limit in q["limits"].items():
                if q["usage"].get(dim, 0) > limit:
                    violated += 1
                    break
        return {
            "total_quotas": total,
            "quotas_with_violations": violated,
            "dimensions_tracked": list(QUOTA_DIMENSIONS.keys()),
            "enforcement_mode": self._enforcement_mode,
            "pending_requests": sum(1 for r in self._requests.values() if r["status"] == "pending"),
        }
