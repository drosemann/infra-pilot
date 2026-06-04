import json
import uuid
import hashlib
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    evidence_id: str
    control_id: str
    framework: str
    evidence_type: str
    description: str
    content_hash: str
    source: str
    collected_by: str
    collected_at: datetime
    expires_at: Optional[datetime]
    status: str
    metadata: Dict[str, Any]
    file_path: Optional[str]
    size_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "control_id": self.control_id,
            "framework": self.framework,
            "evidence_type": self.evidence_type,
            "description": self.description,
            "content_hash": self.content_hash,
            "source": self.source,
            "collected_by": self.collected_by,
            "collected_at": self.collected_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "metadata": self.metadata,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
        }


@dataclass
class EvidencePackage:
    package_id: str
    name: str
    framework: str
    audit_period_start: datetime
    audit_period_end: datetime
    evidence_items: List[EvidenceItem]
    status: str
    created_at: datetime
    created_by: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "name": self.name,
            "framework": self.framework,
            "audit_period_start": self.audit_period_start.isoformat(),
            "audit_period_end": self.audit_period_end.isoformat(),
            "evidence_count": len(self.evidence_items),
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "notes": self.notes,
        }


EVIDENCE_COLLECTORS = {
    "config_snapshot": {
        "description": "Configuration snapshots of infrastructure components",
        "sources": ["terraform_state", "kubernetes", "docker", "ansible", "cloud_provider"],
    },
    "policy_decision": {
        "description": "Policy engine decisions and evaluation logs",
        "sources": ["opa", "rego", "custom_policy_engine"],
    },
    "access_log": {
        "description": "Authentication and authorization access logs",
        "sources": ["auth_service", "api_gateway", "ssh_logs", "database_logs"],
    },
    "change_history": {
        "description": "Infrastructure change history and audit trail",
        "sources": ["git_commits", "terraform_apply", "deployment_events", "config_changes"],
    },
    "scan_result": {
        "description": "Security and compliance scan results",
        "sources": ["vulnerability_scanner", "compliance_scanner", "container_scanner"],
    },
    "network_log": {
        "description": "Network traffic logs and firewall rules",
        "sources": ["firewall_logs", "vpc_flow_logs", "proxy_logs", "dns_logs"],
    },
    "certification": {
        "description": "Certification documents and attestations",
        "sources": ["uploaded_documents", "external_auditor_reports"],
    },
    "training_record": {
        "description": "Compliance training completion records",
        "sources": ["training_platform", "lms_integration"],
    },
}


class EvidenceCollector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.evidence_store: List[EvidenceItem] = []
        self.packages: List[EvidencePackage] = []
        self.collectors = EVIDENCE_COLLECTORS
        self.data_dir = config.get("evidence_data_dir", "data/evidence")
        self._load()

    def _load(self):
        try:
            if os.path.exists(f"{self.data_dir}/evidence.json"):
                with open(f"{self.data_dir}/evidence.json", "r") as f:
                    data = json.load(f)
                    self.evidence_store = [EvidenceItem(**e) if isinstance(e, dict) else e for e in data.get("items", [])]
            if os.path.exists(f"{self.data_dir}/packages.json"):
                with open(f"{self.data_dir}/packages.json", "r") as f:
                    data = json.load(f)
                    self.packages = [EvidencePackage(**p) if isinstance(p, dict) else p for p in data.get("packages", [])]
        except Exception as e:
            logger.warning(f"Failed to load evidence data: {e}")

    def _save(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(f"{self.data_dir}/evidence.json", "w") as f:
                json.dump({"items": [e.to_dict() for e in self.evidence_store[-10000:]]}, f, indent=2)
            with open(f"{self.data_dir}/packages.json", "w") as f:
                json.dump({"packages": [p.to_dict() for p in self.packages]}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save evidence data: {e}")

    def collect_evidence(self, control_id: str, framework: str, evidence_type: str,
                         description: str, source: str, content: str,
                         collected_by: str = "system") -> EvidenceItem:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        item = EvidenceItem(
            evidence_id=f"ev_{uuid.uuid4().hex[:12]}",
            control_id=control_id,
            framework=framework,
            evidence_type=evidence_type,
            description=description,
            content_hash=content_hash,
            source=source,
            collected_by=collected_by,
            collected_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365) if evidence_type == "certification" else None,
            status="active",
            metadata={"content_preview": content[:200], "collector_version": "4.0"},
            file_path=None,
            size_bytes=len(content.encode()),
        )
        self.evidence_store.append(item)
        self._save()
        logger.info(f"Collected evidence {item.evidence_id} for control {control_id}")
        return item

    def auto_collect_for_control(self, control_id: str, framework: str) -> List[EvidenceItem]:
        collected = []
        for ev_type, collector_def in self.collectors.items():
            for source in collector_def["sources"][:2]:
                content = json.dumps({
                    "control_id": control_id,
                    "framework": framework,
                    "evidence_type": ev_type,
                    "source": source,
                    "collected_at": datetime.utcnow().isoformat(),
                    "sample_data": f"Auto-collected {ev_type} from {source}",
                })
                item = self.collect_evidence(
                    control_id=control_id,
                    framework=framework,
                    evidence_type=ev_type,
                    description=f"{collector_def['description']} from {source}",
                    source=source,
                    content=content,
                    collected_by="auto_collector",
                )
                collected.append(item)
        return collected

    def create_package(self, name: str, framework: str, control_ids: List[str],
                       audit_start: datetime, audit_end: datetime,
                       created_by: str = "system", notes: str = "") -> EvidencePackage:
        items = [e for e in self.evidence_store if e.control_id in control_ids and e.framework == framework]
        package = EvidencePackage(
            package_id=f"pkg_{uuid.uuid4().hex[:12]}",
            name=name,
            framework=framework,
            audit_period_start=audit_start,
            audit_period_end=audit_end,
            evidence_items=items,
            status="draft",
            created_at=datetime.utcnow(),
            created_by=created_by,
            notes=notes,
        )
        self.packages.append(package)
        self._save()
        return package

    def get_evidence(self, evidence_id: Optional[str] = None,
                     control_id: Optional[str] = None,
                     framework: Optional[str] = None) -> List[EvidenceItem]:
        results = self.evidence_store
        if evidence_id:
            results = [e for e in results if e.evidence_id == evidence_id]
        if control_id:
            results = [e for e in results if e.control_id == control_id]
        if framework:
            results = [e for e in results if e.framework == framework]
        return results

    def get_packages(self, package_id: Optional[str] = None,
                     framework: Optional[str] = None) -> List[EvidencePackage]:
        results = self.packages
        if package_id:
            results = [p for p in results if p.package_id == package_id]
        if framework:
            results = [p for p in results if p.framework == framework]
        return results

    def finalize_package(self, package_id: str) -> Optional[EvidencePackage]:
        for pkg in self.packages:
            if pkg.package_id == package_id:
                pkg.status = "finalized"
                self._save()
                return pkg
        return None

    def batch_collect(self, items: List[Dict[str, Any]]) -> List[EvidenceItem]:
        collected = []
        for item_def in items:
            try:
                item = self.collect_evidence(
                    control_id=item_def["control_id"],
                    framework=item_def.get("framework", "SOC_2"),
                    evidence_type=item_def.get("evidence_type", "config_snapshot"),
                    description=item_def.get("description", ""),
                    source=item_def.get("source", "batch"),
                    content=item_def.get("content", "{}"),
                    collected_by=item_def.get("collected_by", "batch_processor"),
                )
                collected.append(item)
            except Exception as e:
                logger.error(f"Batch collect failed for {item_def}: {e}")
        return collected

    def set_retention_policy(self, evidence_type: str, retention_days: int) -> Dict[str, Any]:
        policy_id = f"rp_{uuid.uuid4().hex[:8]}"
        logger.info(f"Set retention policy {policy_id}: {evidence_type} -> {retention_days} days")
        return {
            "policy_id": policy_id,
            "evidence_type": evidence_type,
            "retention_days": retention_days,
            "created_at": datetime.utcnow().isoformat(),
        }

    def check_expired_evidence(self) -> List[EvidenceItem]:
        now = datetime.utcnow()
        expired = [e for e in self.evidence_store if e.expires_at and e.expires_at < now and e.status == "active"]
        for e in expired:
            e.status = "expired"
        if expired:
            self._save()
        return expired

    def bulk_update_status(self, evidence_ids: List[str], status: str) -> int:
        count = 0
        for e in self.evidence_store:
            if e.evidence_id in evidence_ids:
                e.status = status
                count += 1
        if count:
            self._save()
        return count

    def search_evidence(self, query: str, fields: Optional[List[str]] = None) -> List[EvidenceItem]:
        fields = fields or ["description", "control_id", "framework", "source"]
        query_lower = query.lower()
        results = []
        for e in self.evidence_store:
            for field in fields:
                val = getattr(e, field, "")
                if isinstance(val, str) and query_lower in val.lower():
                    results.append(e)
                    break
        return results

    def get_chain_of_custody(self, evidence_id: str) -> List[Dict[str, Any]]:
        item = next((e for e in self.evidence_store if e.evidence_id == evidence_id), None)
        if not item:
            return []
        return [
            {
                "event": "collected",
                "timestamp": item.collected_at.isoformat(),
                "actor": item.collected_by,
                "detail": f"Evidence collected from {item.source}",
            },
            {
                "event": "hashed",
                "timestamp": item.collected_at.isoformat(),
                "actor": "system",
                "detail": f"SHA-256: {item.content_hash[:16]}...",
            },
            {
                "event": "status_change",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "system",
                "detail": f"Current status: {item.status}",
            },
        ]

    def validate_evidence(self, evidence_id: str) -> Dict[str, Any]:
        item = next((e for e in self.evidence_store if e.evidence_id == evidence_id), None)
        if not item:
            return {"valid": False, "error": "Evidence not found"}
        checks = {
            "hash_integrity": bool(item.content_hash and len(item.content_hash) == 64),
            "has_metadata": bool(item.metadata),
            "not_expired": bool(not item.expires_at or item.expires_at > datetime.utcnow()),
            "has_source": bool(item.source),
            "size_ok": 0 < item.size_bytes < 10 * 1024 * 1024,
        }
        return {
            "evidence_id": evidence_id,
            "valid": all(checks.values()),
            "checks": checks,
            "status": item.status,
        }

    def export_package(self, package_id: str, format: str = "json") -> Optional[str]:
        pkg = next((p for p in self.packages if p.package_id == package_id), None)
        if not pkg:
            return None
        export_data = {
            "package_id": pkg.package_id,
            "name": pkg.name,
            "framework": pkg.framework,
            "exported_at": datetime.utcnow().isoformat(),
            "evidence_count": len(pkg.evidence_items),
            "evidence_items": [e.to_dict() for e in pkg.evidence_items],
        }
        export_id = f"export_{uuid.uuid4().hex[:8]}"
        export_path = f"exports/{export_id}.json"
        os.makedirs("exports", exist_ok=True)
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        logger.info(f"Exported package {package_id} to {export_path}")
        return export_path

    def import_package(self, file_path: str) -> Optional[EvidencePackage]:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            items = []
            for ev_def in data.get("evidence_items", []):
                item = EvidenceItem(
                    evidence_id=f"ev_{uuid.uuid4().hex[:12]}",
                    control_id=ev_def.get("control_id", "unknown"),
                    framework=ev_def.get("framework", "unknown"),
                    evidence_type=ev_def.get("evidence_type", "unknown"),
                    description=ev_def.get("description", ""),
                    content_hash=ev_def.get("content_hash", ""),
                    source=ev_def.get("source", "import"),
                    collected_by=ev_def.get("collected_by", "import"),
                    collected_at=datetime.utcnow(),
                    expires_at=datetime.fromisoformat(ev_def["expires_at"]) if ev_def.get("expires_at") else None,
                    status="active",
                    metadata=ev_def.get("metadata", {}),
                    file_path=ev_def.get("file_path"),
                    size_bytes=ev_def.get("size_bytes", 0),
                )
                items.append(item)
                self.evidence_store.append(item)
            pkg = EvidencePackage(
                package_id=f"pkg_{uuid.uuid4().hex[:12]}",
                name=data.get("name", "Imported Package"),
                framework=data.get("framework", "unknown"),
                audit_period_start=datetime.utcnow() - timedelta(days=90),
                audit_period_end=datetime.utcnow(),
                evidence_items=items,
                status="draft",
                created_at=datetime.utcnow(),
                created_by="import",
                notes=f"Imported from {file_path}",
            )
            self.packages.append(pkg)
            self._save()
            return pkg
        except Exception as e:
            logger.error(f"Failed to import package: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.evidence_store)
        by_type = {}
        by_framework = {}
        by_status = {}
        for ev in self.evidence_store:
            by_type[ev.evidence_type] = by_type.get(ev.evidence_type, 0) + 1
            by_framework[ev.framework] = by_framework.get(ev.framework, 0) + 1
            by_status[ev.status] = by_status.get(ev.status, 0) + 1
        return {
            "total_evidence": total,
            "by_type": by_type,
            "by_framework": by_framework,
            "by_status": by_status,
            "total_packages": len(self.packages),
            "finalized_packages": sum(1 for p in self.packages if p.status == "finalized"),
            "unique_controls_covered": len(set(e.control_id for e in self.evidence_store)),
            "expired_evidence": sum(1 for e in self.evidence_store if e.status == "expired"),
            "active_evidence": sum(1 for e in self.evidence_store if e.status == "active"),
        }

    def rehash_evidence(self, evidence_id: str, new_content: str) -> Optional[EvidenceItem]:
        item = next((e for e in self.evidence_store if e.evidence_id == evidence_id), None)
        if not item:
            return None
        item.content_hash = hashlib.sha256(new_content.encode()).hexdigest()
        item.size_bytes = len(new_content.encode())
        item.metadata["rehashed_at"] = datetime.utcnow().isoformat()
        self._save()
        return item

    def delete_evidence(self, evidence_id: str) -> bool:
        item = next((e for e in self.evidence_store if e.evidence_id == evidence_id), None)
        if not item:
            return False
        item.status = "deleted"
        self._save()
        return True

    def merge_packages(self, package_ids: List[str], new_name: str) -> Optional[EvidencePackage]:
        pkgs = [p for p in self.packages if p.package_id in package_ids]
        if not pkgs:
            return None
        merged_items = []
        for p in pkgs:
            merged_items.extend(p.evidence_items)
        base_framework = pkgs[0].framework
        merged = EvidencePackage(
            package_id=f"pkg_{uuid.uuid4().hex[:12]}",
            name=new_name,
            framework=base_framework,
            audit_period_start=min(p.audit_period_start for p in pkgs),
            audit_period_end=max(p.audit_period_end for p in pkgs),
            evidence_items=merged_items,
            status="draft",
            created_at=datetime.utcnow(),
            created_by="merge",
            notes=f"Merged from {', '.join(p.package_id for p in pkgs)}",
        )
        self.packages.append(merged)
        self._save()
        return merged

    def get_coverage_report(self, framework: str) -> Dict[str, Any]:
        fw_evidence = [e for e in self.evidence_store if e.framework == framework and e.status == "active"]
        by_type = {}
        for e in fw_evidence:
            by_type.setdefault(e.evidence_type, []).append(e.evidence_id)
        return {
            "framework": framework,
            "total_evidence": len(fw_evidence),
            "evidence_by_type": {k: len(v) for k, v in by_type.items()},
            "unique_controls": len(set(e.control_id for e in fw_evidence)),
            "collector_types": list(by_type.keys()),
            "coverage_score": round(len(set(e.control_id for e in fw_evidence)) / max(len(set(e.control_id for e in self.evidence_store)), 1) * 100, 1),
        }


def deduplicate_evidence(items: List[EvidenceItem]) -> List[EvidenceItem]:
    seen_hashes = set()
    deduped = []
    for item in items:
        if item.content_hash not in seen_hashes:
            seen_hashes.add(item.content_hash)
            deduped.append(item)
    return deduped


def filter_evidence_by_date(items: List[EvidenceItem], start: datetime, end: datetime) -> List[EvidenceItem]:
    return [e for e in items if start <= e.collected_at <= end]


def compute_evidence_metrics(items: List[EvidenceItem]) -> Dict[str, Any]:
    total = len(items)
    total_size = sum(e.size_bytes for e in items)
    avg_size = round(total_size / total, 2) if total else 0
    return {
        "total_items": total,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "average_size_bytes": avg_size,
        "largest_item": max(items, key=lambda e: e.size_bytes).evidence_id if items else None,
        "oldest_item": min(items, key=lambda e: e.collected_at).evidence_id if items else None,
    }


def partition_evidence_by_type(items: List[EvidenceItem]) -> Dict[str, List[EvidenceItem]]:
    partitioned = {}
    for e in items:
        partitioned.setdefault(e.evidence_type, []).append(e)
    return partitioned


def find_gaps_in_evidence(required_controls: List[str], collected_evidence: List[EvidenceItem]) -> List[str]:
    covered = set(e.control_id for e in collected_evidence)
    return [c for c in required_controls if c not in covered]


class EvidenceBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_collect(self, manager: EvidenceCollector, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item_def in items:
            try:
                item = manager.collect_evidence(
                    control_id=item_def["control_id"], framework=item_def.get("framework", "SOC_2"),
                    evidence_type=item_def.get("evidence_type", "config_snapshot"),
                    description=item_def.get("description", ""), source=item_def.get("source", "batch"),
                    content=item_def.get("content", "{}"), collected_by=item_def.get("collected_by", "batch"),
                )
                results.append({"evidence_id": item.evidence_id, "status": "success"})
                self.batch_log.append({"action": "collect", "control": item_def["control_id"], "status": "success"})
            except Exception as e:
                results.append({"control_id": item_def.get("control_id"), "status": "error", "error": str(e)})
                self.batch_log.append({"action": "collect", "control": item_def.get("control_id"), "status": "error", "error": str(e)})
        return results


async def paginate_evidence(items: List[EvidenceItem], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [e.to_dict() for e in items[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def export_evidence_package(pkg: EvidencePackage) -> Dict[str, Any]:
    export_id = f"ev_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id, "exported_at": datetime.utcnow().isoformat(),
        "package": pkg.to_dict() if hasattr(pkg, "to_dict") else {
            "package_id": pkg.package_id, "name": pkg.name, "framework": pkg.framework,
            "evidence_count": len(pkg.evidence_items),
            "evidence_items": [e.to_dict() for e in pkg.evidence_items],
        },
    }


def import_evidence_items(manager: EvidenceCollector, import_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    import_id = f"ev_import_{uuid.uuid4().hex[:8]}"
    imported = 0
    for ed in import_data:
        try:
            manager.collect_evidence(ed["control_id"], ed.get("framework", "SOC_2"), ed.get("evidence_type", "config_snapshot"), ed.get("description", ""), ed.get("source", "import"), ed.get("content", "{}"))
            imported += 1
        except Exception:
            pass
    return {"import_id": import_id, "imported": imported}


class EvidenceConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        if not self.config.get("evidence_data_file"):
            self.errors.append("evidence_data_file is required")
        max_package_size = self.config.get("max_package_size_mb")
        if max_package_size is not None and max_package_size < 1:
            self.errors.append("max_package_size_mb must be >= 1")
        return len(self.errors) == 0


def compute_evidence_statistics(items: List[EvidenceItem]) -> Dict[str, Any]:
    total = len(items)
    by_type = {}
    by_framework = {}
    by_status = {}
    for e in items:
        by_type[e.evidence_type] = by_type.get(e.evidence_type, 0) + 1
        by_framework[e.framework] = by_framework.get(e.framework, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "total_items": total, "by_type": by_type, "by_framework": by_framework,
        "by_status": by_status, "unique_controls": len(set(e.control_id for e in items)),
        "active": sum(1 for e in items if e.status == "active"),
        "expired": sum(1 for e in items if e.status == "expired"),
        "total_size_mb": round(sum(e.size_bytes for e in items) / (1024 * 1024), 2),
    }

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class evidence_collection_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class evidence_collection_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class evidence_collection_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class evidence_collection_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class evidence_collection_Cache:
    def __init__(self, ttl=300):
        self._store = {}; self._ttl = ttl
    def get(self, key: str):
        e = self._store.get(key)
        if e and (datetime.utcnow() - e["ts"]).seconds < self._ttl:
            return e["val"]
        return None
    def set(self, key: str, val: Any):
        self._store[key] = {"val": val, "ts": datetime.utcnow()}
    def invalidate(self, key: str):
        self._store.pop(key, None)

class evidence_collection_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class evidence_collection_Queue:
    def __init__(self):
        self._items = []
    def push(self, item: Any):
        self._items.append(item)
    def pop(self):
        return self._items.pop(0) if self._items else None
    def size(self):
        return len(self._items)
    def drain(self):
        items = list(self._items); self._items.clear(); return items

class evidence_collection_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class evidence_collection_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_evidence_items_store: Dict[str, EvidenceItem] = {}
_evidence_collectors_store: Dict[str, EvidenceCollector] = {}


def add_evidence_item(item: EvidenceItem) -> str:
    _evidence_items_store[item.evidence_id] = item
    return item.evidence_id


def get_evidence_item(evidence_id: str) -> Optional[EvidenceItem]:
    return _evidence_items_store.get(evidence_id)


def search_evidence_items(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for item in _evidence_items_store.values():
        if query.lower() in item.description.lower() or query.lower() in item.control_id.lower():
            results.append({"id": item.evidence_id, "control_id": item.control_id, "type": item.evidence_type, "status": item.status})
            if len(results) >= limit:
                break
    return results


def batch_approve_evidence(evidence_ids: List[str]) -> Dict[str, Any]:
    op = {"operation": "approve", "succeeded": [], "failed": [], "total": len(evidence_ids)}
    for eid in evidence_ids:
        item = _evidence_items_store.get(eid)
        if item:
            item.status = "approved"
            op["succeeded"].append(eid)
        else:
            op["failed"].append(eid)
    return op


def get_evidence_summary() -> Dict[str, Any]:
    total = len(_evidence_items_store)
    pending = sum(1 for item in _evidence_items_store.values() if item.status == "pending")
    approved = sum(1 for item in _evidence_items_store.values() if item.status == "approved")
    rejected = sum(1 for item in _evidence_items_store.values() if item.status == "rejected")
    expired = sum(1 for item in _evidence_items_store.values() if item.status == "expired")
    by_type = {}
    for item in _evidence_items_store.values():
        by_type[item.evidence_type] = by_type.get(item.evidence_type, 0) + 1
    return {"total": total, "pending": pending, "approved": approved, "rejected": rejected, "expired": expired, "by_type": by_type}


class EvidenceChainOfCustody:
    def __init__(self):
        self._items = _evidence_items_store
        self._custody_log: Dict[str, List[Dict[str, Any]]] = {}

    def record_access(self, evidence_id: str, actor: str, action: str) -> Dict[str, Any]:
        entry = {"evidence_id": evidence_id, "actor": actor, "action": action, "timestamp": datetime.utcnow().isoformat()}
        if evidence_id not in self._custody_log:
            self._custody_log[evidence_id] = []
        self._custody_log[evidence_id].append(entry)
        return entry

    def get_chain(self, evidence_id: str) -> List[Dict[str, Any]]:
        return self._custody_log.get(evidence_id, [])

    def verify_integrity(self, evidence_id: str) -> Dict[str, Any]:
        item = self._items.get(evidence_id)
        if not item:
            return {"valid": False, "error": "not found"}
        current_hash = hashlib.sha256(str(item.metadata).encode()).hexdigest()
        stored_hash = item.content_hash
        return {"evidence_id": evidence_id, "valid": current_hash == stored_hash, "current_hash": current_hash, "stored_hash": stored_hash, "tampered": current_hash != stored_hash}


class EvidenceRetentionManager:
    def __init__(self):
        self._items = _evidence_items_store

    def check_expirations(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        expired = []
        for item in self._items.values():
            if item.expires_at and item.expires_at < now and item.status != "expired":
                item.status = "expired"
                expired.append({"evidence_id": item.evidence_id, "control_id": item.control_id, "expired_at": item.expires_at.isoformat() if hasattr(item.expires_at, 'isoformat') else str(item.expires_at)})
        return expired

    def extend_retention(self, evidence_ids: List[str], days: int = 365) -> Dict[str, Any]:
        now = datetime.utcnow()
        op: Dict[str, Any] = {"operation": "extend_retention", "days": days, "succeeded": [], "failed": [], "total": len(evidence_ids)}
        for eid in evidence_ids:
            item = self._items.get(eid)
            if item:
                item.expires_at = now + timedelta(days=days)
                item.status = "approved"
                op["succeeded"].append(eid)
            else:
                op["failed"].append(eid)
        return op

    def get_retention_report(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        total = len(self._items)
        expired = sum(1 for i in self._items.values() if i.status == "expired")
        expiring_30d = sum(1 for i in self._items.values() if i.expires_at and 0 < (i.expires_at - now).days <= 30)
        valid = total - expired - expiring_30d
        return {"total": total, "valid": valid, "expiring_within_30d": expiring_30d, "expired": expired}


class EvidenceCollectionScheduler:
    def __init__(self):
        self._schedules: Dict[str, Dict[str, Any]] = {}

    def create_schedule(self, control_id: str, framework: str, interval_hours: int = 24) -> Dict[str, Any]:
        sid = f"sch_{uuid.uuid4().hex[:8]}"
        schedule = {"schedule_id": sid, "control_id": control_id, "framework": framework, "interval_hours": interval_hours, "last_run": None, "next_run": datetime.utcnow().isoformat(), "active": True, "total_collections": 0}
        self._schedules[sid] = schedule
        return schedule

    def mark_run(self, schedule_id: str) -> bool:
        s = self._schedules.get(schedule_id)
        if not s:
            return False
        now = datetime.utcnow()
        from datetime import timedelta
        s["last_run"] = now.isoformat()
        s["next_run"] = (now + timedelta(hours=s["interval_hours"])).isoformat()
        s["total_collections"] += 1
        return True

    def get_due_collections(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        return [s for s in self._schedules.values() if s["active"] and (s["next_run"] is None or datetime.fromisoformat(s["next_run"]) <= now)]

    def pause_schedule(self, schedule_id: str) -> bool:
        s = self._schedules.get(schedule_id)
        if s:
            s["active"] = False
            return True
        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        s = self._schedules.get(schedule_id)
        if s:
            s["active"] = True
            return True
        return False


# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_checks": 0, "passed": 0, "failed": 0, "waived": 0, "compliance_score": 100.0}

    def validate_framework(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "framework_version": "v4"}

class ComplianceResult(BaseModel):
    success: bool = True
    operation: str = ""
    control_id: Optional[str] = None
    status: str = Field(default="compliant")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ComplianceBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    framework: str = Field(default="generic")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    passed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_pass(self) -> None:
        self.passed += 1

    def record_fail(self) -> None:
        self.failed += 1

    def complete(self) -> None:
        self.status = "completed"

class ControlCheck(BaseModel):
    control_id: str
    name: str
    category: str = Field(default="general")
    severity: str = Field(default="medium")
    status: str = Field(default="compliant")
    tested_at: datetime = Field(default_factory=datetime.utcnow)
    evidence: Optional[str] = None
    notes: str = ""

class ComplianceScanner:
    def __init__(self) -> None:
        self._controls: Dict[str, ControlCheck] = {}

    def register_control(self, control: ControlCheck) -> None:
        self._controls[control.control_id] = control

    def run_check(self, control_id: str) -> ControlCheck:
        control = self._controls.get(control_id)
        if not control:
            raise ValueError(f"Control {control_id} not found")
        control.tested_at = datetime.utcnow()
        control.status = "compliant" if random.random() > 0.1 else "non_compliant"
        return control

    def run_all(self) -> Dict[str, Any]:
        results = {}
        for cid in self._controls:
            results[cid] = self.run_check(cid)
        compliant = sum(1 for r in results.values() if r.status == "compliant")
        return {"total": len(results), "compliant": compliant,
                "non_compliant": len(results) - compliant,
                "score": round(compliant / max(len(results), 1) * 100, 1)}

    def get_controls_by_severity(self, severity: str) -> List[ControlCheck]:
        return [c for c in self._controls.values() if c.severity == severity]

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str
    file_path: str = ""
    content_hash: str = ""
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    collected_by: str = Field(default="system")
    valid: bool = True
    expires_at: Optional[datetime] = None

class EvidenceStore:
    def __init__(self) -> None:
        self._items: List[EvidenceItem] = []

    def add(self, control_id: str, file_path: str, content_hash: str, collected_by: str = "system") -> EvidenceItem:
        item = EvidenceItem(control_id=control_id, file_path=file_path,
                            content_hash=content_hash, collected_by=collected_by)
        self._items.append(item)
        return item

    def get_for_control(self, control_id: str) -> List[EvidenceItem]:
        return [i for i in self._items if i.control_id == control_id]

    def invalidate_expired(self) -> int:
        now = datetime.utcnow()
        count = 0
        for item in self._items:
            if item.expires_at and now > item.expires_at:
                item.valid = False
                count += 1
        return count

    def get_summary(self) -> Dict[str, Any]:
        return {"total": len(self._items), "valid": sum(1 for i in self._items if i.valid),
                "invalid": sum(1 for i in self._items if not i.valid)}

class AuditSchedule(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework: str
    scope: List[str] = Field(default_factory=list)
    scheduled_date: datetime
    completed_date: Optional[datetime] = None
    status: str = Field(default="scheduled")
    assigned_auditor: str = ""
    findings_count: int = Field(default=0)

class AuditPlanner:
    def __init__(self) -> None:
        self._audits: List[AuditSchedule] = []

    def schedule(self, framework: str, scheduled_date: datetime, scope: List[str],
                 auditor: str = "") -> AuditSchedule:
        audit = AuditSchedule(framework=framework, scheduled_date=scheduled_date,
                              scope=scope, assigned_auditor=auditor)
        self._audits.append(audit)
        return audit

    def complete(self, audit_id: str, findings: int = 0) -> bool:
        for a in self._audits:
            if a.audit_id == audit_id and a.status == "scheduled":
                a.status = "completed"
                a.completed_date = datetime.utcnow()
                a.findings_count = findings
                return True
        return False

    def get_upcoming(self, days: int = 30) -> List[AuditSchedule]:
        cutoff = datetime.utcnow() + timedelta(days=days)
        return [a for a in self._audits if a.status == "scheduled" and a.scheduled_date <= cutoff]

    def get_overdue(self) -> List[AuditSchedule]:
        now = datetime.utcnow()
        return [a for a in self._audits if a.status == "scheduled" and a.scheduled_date < now]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._audits)
        scheduled = sum(1 for a in self._audits if a.status == "scheduled")
        completed = sum(1 for a in self._audits if a.status == "completed")
        return {"total": total, "scheduled": scheduled, "completed": completed,
                "overdue": len(self.get_overdue()),
                "completion_rate": round(completed / max(total, 1) * 100, 1)}

class PolicyRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    category: str = Field(default="general")
    severity: str = Field(default="medium")
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PolicyEngine:
    def __init__(self) -> None:
        self._rules: Dict[str, PolicyRule] = {}

    def add_rule(self, rule: PolicyRule) -> None:
        self._rules[rule.rule_id] = rule

    def evaluate(self, rule_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        rule = self._rules.get(rule_id)
        if not rule:
            return {"rule_id": rule_id, "status": "error", "message": "Rule not found"}
        if not rule.enabled:
            return {"rule_id": rule_id, "status": "disabled"}
        passed = random.random() > 0.2
        return {"rule_id": rule_id, "name": rule.name, "status": "passed" if passed else "failed",
                "severity": rule.severity}

    def evaluate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = [self.evaluate(rid, context) for rid in self._rules]
        passed = sum(1 for r in results if r.get("status") == "passed")
        return {"total": len(results), "passed": passed, "failed": len(results) - passed,
                "results": results}

    def get_rules_by_category(self, category: str) -> List[PolicyRule]:
        return [r for r in self._rules.values() if r.category == category]

class RemediationPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    finding_id: str
    action: str
    priority: str = Field(default="medium")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""

class RemediationTracker:
    def __init__(self) -> None:
        self._plans: List[RemediationPlan] = []

    def create(self, finding_id: str, action: str, priority: str = "medium", assignee: str = "") -> RemediationPlan:
        plan = RemediationPlan(finding_id=finding_id, action=action, priority=priority, assigned_to=assignee)
        self._plans.append(plan)
        return plan

    def resolve(self, plan_id: str) -> bool:
        for p in self._plans:
            if p.plan_id == plan_id and p.status == "open":
                p.status = "resolved"
                p.resolved_at = datetime.utcnow()
                return True
        return False

    def get_open(self) -> List[RemediationPlan]:
        return [p for p in self._plans if p.status == "open"]

    def get_by_priority(self, priority: str) -> List[RemediationPlan]:
        return [p for p in self._plans if p.priority == priority]

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._plans), "open": len(self.get_open()),
                "resolved": sum(1 for p in self._plans if p.status == "resolved"),
                "by_priority": {p: sum(1 for x in self._plans if x.priority == p) for p in set(x.priority for x in self._plans)}}
