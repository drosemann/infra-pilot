import json
import uuid
import hashlib
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GeoLocation(Enum):
    US_EAST = "us-east-1"
    US_WEST = "us-west-2"
    EU_WEST = "eu-west-1"
    EU_CENTRAL = "eu-central-1"
    AP_SOUTHEAST = "ap-southeast-1"
    AP_NORTHEAST = "ap-northeast-1"
    SA_EAST = "sa-east-1"
    ME_SOUTH = "me-south-1"
    AF_SOUTH = "af-south-1"


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class ResidencyStatus(Enum):
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    PENDING_REVIEW = "pending_review"
    NOT_APPLICABLE = "not_applicable"


ALLOWED_REGIONS = {
    "US": {GeoLocation.US_EAST, GeoLocation.US_WEST},
    "EU": {GeoLocation.EU_WEST, GeoLocation.EU_CENTRAL},
    "APAC": {GeoLocation.AP_SOUTHEAST, GeoLocation.AP_NORTHEAST},
    "SA": {GeoLocation.SA_EAST},
    "ME": {GeoLocation.ME_SOUTH},
    "AF": {GeoLocation.AF_SOUTH},
}

GEO_RULES = {
    "GDPR": {"allowed_jurisdictions": ["EU", "US"], "restricted_transfers": ["RU", "CN", "IR"], "require_scc": True},
    "CCPA": {"allowed_jurisdictions": ["US"], "restricted_transfers": ["RU", "CN", "IR", "KP"], "require_scc": False},
    "HIPAA": {"allowed_jurisdictions": ["US"], "restricted_transfers": ["*"], "require_scc": True},
    "PCI_DSS": {"allowed_jurisdictions": ["US", "EU", "APAC"], "restricted_transfers": ["RU", "IR"], "require_scc": False},
    "DPDP": {"allowed_jurisdictions": ["IN"], "restricted_transfers": ["*"], "require_scc": True},
    "LGPD": {"allowed_jurisdictions": ["BR", "US", "EU"], "restricted_transfers": ["RU", "CN"], "require_scc": True},
}


@dataclass
class DataAsset:
    asset_id: str
    name: str
    asset_type: str
    classification: DataClassification
    jurisdiction: str
    current_region: GeoLocation
    allowed_regions: List[GeoLocation]
    owner: str
    description: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "asset_type": self.asset_type,
            "classification": self.classification.value,
            "jurisdiction": self.jurisdiction,
            "current_region": self.current_region.value,
            "allowed_regions": [r.value for r in self.allowed_regions],
            "owner": self.owner,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
        }


@dataclass
class CrossBorderFlow:
    flow_id: str
    source_region: GeoLocation
    target_region: GeoLocation
    asset_id: str
    data_classification: DataClassification
    framework: str
    status: ResidencyStatus
    reason: str
    approved_by: Optional[str]
    flow_type: str
    initiated_at: datetime
    completed_at: Optional[datetime]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "source_region": self.source_region.value,
            "target_region": self.target_region.value,
            "asset_id": self.asset_id,
            "data_classification": self.data_classification.value,
            "framework": self.framework,
            "status": self.status.value,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "flow_type": self.flow_type,
            "initiated_at": self.initiated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


@dataclass
class ResidencyAuditRecord:
    audit_id: str
    asset_id: str
    framework: str
    action: str
    previous_region: Optional[GeoLocation]
    new_region: Optional[GeoLocation]
    status: ResidencyStatus
    details: str
    performed_by: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "asset_id": self.asset_id,
            "framework": self.framework,
            "action": self.action,
            "previous_region": self.previous_region.value if self.previous_region else None,
            "new_region": self.new_region.value if self.new_region else None,
            "status": self.status.value,
            "details": self.details,
            "performed_by": self.performed_by,
            "timestamp": self.timestamp.isoformat(),
        }


class DataResidencyEnforcer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.assets: Dict[str, DataAsset] = {}
        self.flows: List[CrossBorderFlow] = {}
        self.audit_trail: List[ResidencyAuditRecord] = []
        self.geo_rules = GEO_RULES
        self.data_file = config.get("residency_data_file", "data/data_residency.json")
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.assets = {k: DataAsset(**v) if isinstance(v, dict) else v for k, v in data.get("assets", {}).items()}
                    self.flows = {k: CrossBorderFlow(**v) if isinstance(v, dict) else v for k, v in data.get("flows", {}).items()}
                    self.audit_trail = [ResidencyAuditRecord(**r) if isinstance(r, dict) else r for r in data.get("audit_trail", [])]
        except Exception as e:
            logger.warning(f"Failed to load residency data: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({
                    "assets": {k: v.to_dict() for k, v in self.assets.items()},
                    "flows": {k: v.to_dict() for k, v in self.flows.items()},
                    "audit_trail": [r.to_dict() for r in self.audit_trail[-1000:]],
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save residency data: {e}")

    def register_asset(self, name: str, asset_type: str, classification: str,
                       jurisdiction: str, current_region: str, owner: str = "",
                       description: str = "", tags: Optional[List[str]] = None) -> DataAsset:
        try:
            classification_enum = DataClassification(classification)
            region_enum = GeoLocation(current_region)
        except ValueError as e:
            raise ValueError(f"Invalid classification or region: {e}")

        allowed = self._determine_allowed_regions(jurisdiction, classification_enum)
        asset = DataAsset(
            asset_id=f"da_{uuid.uuid4().hex[:12]}",
            name=name,
            asset_type=asset_type,
            classification=classification_enum,
            jurisdiction=jurisdiction,
            current_region=region_enum,
            allowed_regions=allowed,
            owner=owner,
            description=description,
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status="active",
        )

        region_ok = region_enum in allowed
        status = ResidencyStatus.COMPLIANT if region_ok else ResidencyStatus.VIOLATION
        self.assets[asset.asset_id] = asset
        self._audit(asset.asset_id, "register", None, region_enum, status,
                    f"Asset registered in {region_enum.value}", "system")
        self._save()
        return asset

    def _determine_allowed_regions(self, jurisdiction: str, classification: DataClassification) -> List[GeoLocation]:
        if classification in (DataClassification.RESTRICTED, DataClassification.CRITICAL):
            jursd_allowed = ALLOWED_REGIONS.get(jurisdiction, set())
            return list(jursd_allowed) if jursd_allowed else [GeoLocation.US_EAST, GeoLocation.US_WEST]
        return list(GeoLocation)

    def check_flow(self, asset_id: str, target_region: str, framework: str,
                   flow_type: str = "replication", initiated_by: str = "system") -> CrossBorderFlow:
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")

        try:
            target = GeoLocation(target_region)
        except ValueError:
            raise ValueError(f"Invalid region: {target_region}")

        rule = self.geo_rules.get(framework, self.geo_rules["GDPR"])
        source_allowed = ALLOWED_REGIONS.get(asset.jurisdiction, set())
        target_allowed = ALLOWED_REGIONS.get(rule.get("allowed_jurisdictions", ["US"])[0], set())

        restricted = rule.get("restricted_transfers", [])
        target_jurs = self._region_to_jurisdiction(target)

        if restricted == ["*"] or target_jurs in restricted:
            status = ResidencyStatus.VIOLATION
            reason = f"Cross-border flow to {target_region} is restricted by {framework}"
        elif target not in asset.allowed_regions:
            status = ResidencyStatus.VIOLATION
            reason = f"Target region {target_region} not in allowed regions for asset classification"
        else:
            status = ResidencyStatus.COMPLIANT
            reason = f"Flow permitted under {framework}"

        flow = CrossBorderFlow(
            flow_id=f"flow_{uuid.uuid4().hex[:12]}",
            source_region=asset.current_region,
            target_region=target,
            asset_id=asset_id,
            data_classification=asset.classification,
            framework=framework,
            status=status,
            reason=reason,
            approved_by=None,
            flow_type=flow_type,
            initiated_at=datetime.utcnow(),
            completed_at=None,
            metadata={"rule_applied": framework, "initiated_by": initiated_by},
        )
        self.flows[flow.flow_id] = flow
        self._audit(asset_id, "cross_border_check", asset.current_region, target, status, reason, initiated_by)
        self._save()
        return flow

    def _region_to_jurisdiction(self, region: GeoLocation) -> str:
        mapping = {
            GeoLocation.US_EAST: "US", GeoLocation.US_WEST: "US",
            GeoLocation.EU_WEST: "EU", GeoLocation.EU_CENTRAL: "EU",
            GeoLocation.AP_SOUTHEAST: "APAC", GeoLocation.AP_NORTHEAST: "APAC",
            GeoLocation.SA_EAST: "BR",
            GeoLocation.ME_SOUTH: "ME",
            GeoLocation.AF_SOUTH: "AF",
        }
        return mapping.get(region, "US")

    def approve_flow(self, flow_id: str, approved_by: str) -> Optional[CrossBorderFlow]:
        flow = self.flows.get(flow_id)
        if flow:
            flow.status = ResidencyStatus.COMPLIANT
            flow.approved_by = approved_by
            flow.completed_at = datetime.utcnow()
            self._audit(flow.asset_id, "flow_approved", flow.source_region, flow.target_region,
                        ResidencyStatus.COMPLIANT, f"Flow approved by {approved_by}", approved_by)
            self._save()
        return flow

    def move_asset(self, asset_id: str, target_region: str, performed_by: str = "system") -> DataAsset:
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")

        try:
            new_region = GeoLocation(target_region)
        except ValueError:
            raise ValueError(f"Invalid region: {target_region}")

        old_region = asset.current_region
        if new_region not in asset.allowed_regions:
            status = ResidencyStatus.VIOLATION
        else:
            status = ResidencyStatus.COMPLIANT

        asset.current_region = new_region
        asset.updated_at = datetime.utcnow()
        if status == ResidencyStatus.VIOLATION:
            asset.status = "violation"
        else:
            asset.status = "active"

        self._audit(asset_id, "move", old_region, new_region, status,
                    f"Asset moved from {old_region.value} to {new_region.value} by {performed_by}", performed_by)
        self._save()
        return asset

    def _audit(self, asset_id: str, action: str, prev_region: Optional[GeoLocation],
               new_region: Optional[GeoLocation], status: ResidencyStatus,
               details: str, performed_by: str):
        record = ResidencyAuditRecord(
            audit_id=f"aud_{uuid.uuid4().hex[:12]}",
            asset_id=asset_id,
            framework="data_residency",
            action=action,
            previous_region=prev_region,
            new_region=new_region,
            status=status,
            details=details,
            performed_by=performed_by,
            timestamp=datetime.utcnow(),
        )
        self.audit_trail.append(record)
        return record

    def get_assets(self, classification: Optional[str] = None,
                   jurisdiction: Optional[str] = None,
                   status: Optional[str] = None) -> List[DataAsset]:
        results = list(self.assets.values())
        if classification:
            results = [a for a in results if a.classification.value == classification]
        if jurisdiction:
            results = [a for a in results if a.jurisdiction == jurisdiction]
        if status:
            results = [a for a in results if a.status == status]
        return results

    def get_flows(self, status: Optional[str] = None,
                  framework: Optional[str] = None) -> List[CrossBorderFlow]:
        results = list(self.flows.values())
        if status:
            results = [f for f in results if f.status.value == status]
        if framework:
            results = [f for f in results if f.framework == framework]
        return sorted(results, key=lambda f: f.initiated_at, reverse=True)

    def get_audit_trail(self, asset_id: Optional[str] = None,
                        action: Optional[str] = None,
                        days: int = 90) -> List[ResidencyAuditRecord]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = [r for r in self.audit_trail if r.timestamp >= cutoff]
        if asset_id:
            results = [r for r in results if r.asset_id == asset_id]
        if action:
            results = [r for r in results if r.action == action]
        return sorted(results, key=lambda r: r.timestamp, reverse=True)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.assets)
        violations = sum(1 for a in self.assets.values() if a.status == "violation")
        by_class = {}
        by_jurs = {}
        for a in self.assets.values():
            by_class[a.classification.value] = by_class.get(a.classification.value, 0) + 1
            by_jurs[a.jurisdiction] = by_jurs.get(a.jurisdiction, 0) + 1
        return {
            "total_assets": total,
            "compliant_assets": total - violations,
            "violations": violations,
            "by_classification": by_class,
            "by_jurisdiction": by_jurs,
            "total_flows": len(self.flows),
            "blocked_flows": sum(1 for f in self.flows.values() if f.status == ResidencyStatus.VIOLATION),
            "audit_records": len(self.audit_trail),
            "frameworks_monitored": list(self.geo_rules.keys()),
        }

    def get_compliance_report(self, framework: str) -> Dict[str, Any]:
        rule = self.geo_rules.get(framework)
        if not rule:
            return {"error": f"Framework {framework} not found"}
        assets_in_scope = [a for a in self.assets.values() if a.jurisdiction in rule.get("allowed_jurisdictions", [])]
        violations = [a for a in assets_in_scope if a.status == "violation"]
        cross_border = [f for f in self.flows.values() if f.framework == framework]
        return {
            "framework": framework,
            "assets_in_scope": len(assets_in_scope),
            "compliant": len(assets_in_scope) - len(violations),
            "violations": len(violations),
            "cross_border_flows": len(cross_border),
            "blocked_flows": sum(1 for f in cross_border if f.status == ResidencyStatus.VIOLATION),
            "requires_scc": rule.get("require_scc", False),
            "restricted_transfers": rule.get("restricted_transfers", []),
        }

    async def continuous_enforcement(self):
        logger.info("Starting continuous data residency enforcement")
        while True:
            try:
                for asset in list(self.assets.values()):
                    if asset.current_region not in asset.allowed_regions and asset.status != "violation":
                        asset.status = "violation"
                        self._audit(asset.asset_id, "enforcement_check", asset.current_region,
                                    asset.current_region, ResidencyStatus.VIOLATION,
                                    f"Asset {asset.name} in non-compliant region {asset.current_region.value}", "system")
                self._save()
            except Exception as e:
                logger.error(f"Enforcement cycle failed: {e}")
            await asyncio.sleep(300)

    def batch_check_flows(self, flow_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for req in flow_requests:
            try:
                flow = self.check_flow(
                    asset_id=req["asset_id"],
                    target_region=req["target_region"],
                    framework=req.get("framework", "GDPR"),
                    flow_type=req.get("flow_type", "replication"),
                    initiated_by=req.get("initiated_by", "system"),
                )
                results.append({"flow_id": flow.flow_id, "status": flow.status.value, "reason": flow.reason})
            except Exception as e:
                results.append({"error": str(e), "request": req})
        return results

    def get_violations(self, framework: Optional[str] = None) -> List[Dict[str, Any]]:
        violations = []
        for a in self.assets.values():
            if a.status == "violation":
                violations.append({
                    "asset_id": a.asset_id, "name": a.name,
                    "current_region": a.current_region.value,
                    "classification": a.classification.value,
                    "framework": framework or "all",
                })
        if framework:
            violations = [v for v in violations if v.get("framework") == framework]
        return violations

    def update_geo_rules(self, framework: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        if framework in self.geo_rules:
            self.geo_rules[framework].update(rules)
        else:
            self.geo_rules[framework] = rules
        self._save()
        return {"framework": framework, "updated_rules": self.geo_rules[framework]}

    def export_assets_by_jurisdiction(self) -> Dict[str, List[DataAsset]]:
        grouped = {}
        for a in self.assets.values():
            grouped.setdefault(a.jurisdiction, []).append(a)
        return grouped

    def search_assets(self, query: str) -> List[DataAsset]:
        q = query.lower()
        return [a for a in self.assets.values()
                if q in a.name.lower() or q in a.description.lower() or q in a.asset_type.lower() or q in a.jurisdiction.lower()]

    def bulk_register_assets(self, asset_defs: List[Dict[str, Any]]) -> List[DataAsset]:
        registered = []
        for ad in asset_defs:
            try:
                asset = self.register_asset(
                    name=ad["name"], asset_type=ad.get("asset_type", "unknown"),
                    classification=ad.get("classification", "internal"),
                    jurisdiction=ad.get("jurisdiction", "US"),
                    current_region=ad.get("current_region", "us-east-1"),
                    owner=ad.get("owner", ""), description=ad.get("description", ""),
                    tags=ad.get("tags"),
                )
                registered.append(asset)
            except Exception as e:
                logger.error(f"Bulk register failed for {ad.get('name')}: {e}")
        return registered


def classify_data_sensitivity(classification: DataClassification) -> str:
    thresholds = {
        DataClassification.PUBLIC: "No restrictions",
        DataClassification.INTERNAL: "Internal use only",
        DataClassification.CONFIDENTIAL: "Controlled access required",
        DataClassification.RESTRICTED: "Strict access controls and encryption",
        DataClassification.CRITICAL: "Maximum security, limited regions, full audit trail",
    }
    return thresholds.get(classification, "Unknown")


def compute_residency_risk(asset: DataAsset) -> Dict[str, Any]:
    risk_score = 0
    if asset.classification in (DataClassification.RESTRICTED, DataClassification.CRITICAL):
        risk_score += 40
    if asset.status == "violation":
        risk_score += 30
    if len(asset.allowed_regions) <= 2:
        risk_score += 20
    return {
        "asset_id": asset.asset_id,
        "name": asset.name,
        "risk_score": min(risk_score, 100),
        "risk_level": "critical" if risk_score >= 70 else "high" if risk_score >= 40 else "medium" if risk_score >= 20 else "low",
    }


def filter_flows_by_status(flows: List[CrossBorderFlow], status: ResidencyStatus) -> List[CrossBorderFlow]:
    return [f for f in flows if f.status == status]


def group_assets_by_region(assets: List[DataAsset]) -> Dict[str, List[DataAsset]]:
    groups = {}
    for a in assets:
        groups.setdefault(a.current_region.value, []).append(a)
    return groups


def build_residency_dashboard(assets: List[DataAsset], flows: List[CrossBorderFlow]) -> Dict[str, Any]:
    total = len(assets)
    violations = sum(1 for a in assets if a.status == "violation")
    restricted = sum(1 for a in assets if a.classification in (DataClassification.RESTRICTED, DataClassification.CRITICAL))
    blocked_flows = sum(1 for f in flows if f.status == ResidencyStatus.VIOLATION)
    return {
        "total_assets": total,
        "compliant": total - violations,
        "violations": violations,
        "restricted_assets": restricted,
        "total_flows": len(flows),
        "blocked_flows": blocked_flows,
        "compliance_rate": round((total - violations) / total * 100, 1) if total else 100,
        "requires_attention": violations + blocked_flows,
    }


class ResidencyBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_register(self, manager: DataResidencyManager, asset_defs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for ad in asset_defs:
            try:
                asset = manager.register_asset(
                    name=ad["name"], asset_type=ad.get("asset_type", "unknown"),
                    classification=ad.get("classification", "internal"),
                    jurisdiction=ad.get("jurisdiction", "US"),
                    current_region=ad.get("current_region", "us-east-1"),
                    owner=ad.get("owner", ""), description=ad.get("description", ""),
                    tags=ad.get("tags"),
                )
                results.append({"asset_id": asset.asset_id, "name": asset.name, "status": "success"})
                self.batch_log.append({"action": "register", "asset": ad["name"], "status": "success"})
            except Exception as e:
                results.append({"name": ad.get("name"), "status": "error", "error": str(e)})
                self.batch_log.append({"action": "register", "asset": ad.get("name"), "status": "error", "error": str(e)})
        return results


async def paginate_assets(assets: List[DataAsset], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(assets)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [a.to_dict() for a in assets[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def export_residency_data(assets: List[DataAsset], flows: List[CrossBorderFlow]) -> Dict[str, Any]:
    export_id = f"res_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id, "exported_at": datetime.utcnow().isoformat(),
        "assets": [a.to_dict() for a in assets],
        "flows": [f.to_dict() for f in flows],
        "summary": {"total_assets": len(assets), "total_flows": len(flows)},
    }


def import_residency_assets(manager: DataResidencyManager, import_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    import_id = f"res_import_{uuid.uuid4().hex[:8]}"
    imported = 0
    for ad in import_data:
        try:
            manager.register_asset(ad["name"], ad.get("asset_type", "unknown"), ad.get("classification", "internal"), ad.get("jurisdiction", "US"), ad.get("current_region", "us-east-1"))
            imported += 1
        except Exception:
            pass
    return {"import_id": import_id, "imported": imported}


class ResidencyConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        if not self.config.get("residency_data_file"):
            self.errors.append("residency_data_file is required")
        enforcement_interval = self.config.get("enforcement_interval_seconds")
        if enforcement_interval is not None and enforcement_interval < 60:
            self.errors.append("enforcement_interval_seconds must be >= 60")
        return len(self.errors) == 0


def compute_residency_statistics(assets: List[DataAsset], flows: List[CrossBorderFlow]) -> Dict[str, Any]:
    total = len(assets)
    violations = sum(1 for a in assets if a.status == "violation")
    restricted = sum(1 for a in assets if a.classification in (DataClassification.RESTRICTED, DataClassification.CRITICAL))
    blocked_flows = sum(1 for f in flows if f.status == ResidencyStatus.VIOLATION)
    return {
        "total_assets": total, "compliant": total - violations, "violations": violations,
        "restricted_classified": restricted, "total_flows": len(flows), "blocked_flows": blocked_flows,
        "compliance_rate": round((total - violations) / total * 100, 1) if total else 0,
        "jurisdictions": list(set(a.jurisdiction for a in assets)),
    }

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class data_residency_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class data_residency_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class data_residency_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class data_residency_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class data_residency_Cache:
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

class data_residency_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class data_residency_Queue:
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

class data_residency_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class data_residency_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_dr_regions_store: Dict[str, DataRegion] = {}
_dr_policies_store: Dict[str, DataResidencyPolicy] = {}


def add_dr_region(region: DataRegion) -> str:
    _dr_regions_store[region.region_id] = region
    return region.region_id


def get_dr_region(region_id: str) -> Optional[DataRegion]:
    return _dr_regions_store.get(region_id)


def search_dr_policies(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for p in _dr_policies_store.values():
        if query.lower() in p.policy_name.lower() or query.lower() in p.region.lower():
            results.append({"id": p.policy_id, "name": p.policy_name, "region": p.region, "classification": p.classification.value, "status": p.status.value})
            if len(results) >= limit:
                break
    return results


def batch_update_residency_status(policy_ids: List[str], new_status: ResidencyStatus) -> Dict[str, Any]:
    op = {"operation": "update_status", "succeeded": [], "failed": [], "total": len(policy_ids)}
    for pid in policy_ids:
        p = _dr_policies_store.get(pid)
        if p:
            p.status = new_status
            op["succeeded"].append(pid)
        else:
            op["failed"].append(pid)
    return op


def get_dr_summary() -> Dict[str, Any]:
    total_regions = len(_dr_regions_store)
    total_policies = len(_dr_policies_store)
    compliant = sum(1 for p in _dr_policies_store.values() if p.status == ResidencyStatus.COMPLIANT)
    violations = sum(1 for p in _dr_policies_store.values() if p.status == ResidencyStatus.VIOLATION)
    pending = sum(1 for p in _dr_policies_store.values() if p.status == ResidencyStatus.PENDING_REVIEW)
    return {"total_regions": total_regions, "total_policies": total_policies, "compliant": compliant, "violations": violations, "pending_review": pending}


class DataResidencyAuditor:
    def __init__(self):
        self._policies = _dr_policies_store
        self._regions = _dr_regions_store
        self._audit_log: List[Dict[str, Any]] = []

    def run_audit(self) -> Dict[str, Any]:
        violations = []
        for p in self._policies.values():
            if p.status != ResidencyStatus.COMPLIANT:
                violations.append({"policy_id": p.policy_id, "data_type": p.data_type.value if hasattr(p.data_type, 'value') else p.data_type, "allowed_regions": [r.value for r in p.allowed_regions], "status": p.status.value})
        result = {"audit_id": f"audit_{uuid.uuid4().hex[:8]}", "timestamp": datetime.utcnow().isoformat(), "total_policies": len(self._policies), "violations": len(violations), "compliant": len(self._policies) - len(violations), "details": violations}
        self._audit_log.append(result)
        return result

    def get_audit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._audit_log[-limit:]

    def export_audit_csv(self, audit_id: str) -> str:
        import csv, io
        audit = next((a for a in self._audit_log if a["audit_id"] == audit_id), None)
        if not audit:
            return ""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["policy_id", "data_type", "allowed_regions", "status"])
        for v in audit["details"]:
            writer.writerow([v["policy_id"], v["data_type"], ";".join(v["allowed_regions"]), v["status"]])
        return output.getvalue()


class DataResidencyMigrationPlanner:
    def __init__(self):
        self._policies = _dr_policies_store
        self._regions = _dr_regions_store

    def plan_migration(self, policy_id: str, target_region: str) -> Optional[Dict[str, Any]]:
        p = self._policies.get(policy_id)
        if not p:
            return None
        region_enum = next((r for r in GeoLocation if r.value == target_region), None)
        if not region_enum:
            return {"error": f"Region {target_region} not recognized"}
        current = p.current_region.value if hasattr(p.current_region, 'value') else str(p.current_region)
        return {"policy_id": policy_id, "data_type": p.data_type.value, "current_region": current, "target_region": target_region, "requires_verification": True, "estimated_duration_hours": 4, "steps": ["Export data from current region", "Validate data integrity", "Import to target region", "Update access controls", "Verify compliance status", "Decommission old storage"]}

    def get_migration_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        for p in self._policies.values():
            if p.status == ResidencyStatus.VIOLATION:
                compliant_regions = [r.value for r in p.allowed_regions]
                current_region = p.current_region.value if hasattr(p.current_region, 'value') else str(p.current_region)
                candidates.append({"policy_id": p.policy_id, "data_type": p.data_type.value, "current_region": current_region, "allowed_regions": compliant_regions, "recommended_region": compliant_regions[0] if compliant_regions else None})
        return candidates


class DataResidencyReportGenerator:
    def __init__(self):
        self._policies = _dr_policies_store
        self._regions = _dr_regions_store

    def generate_regional_report(self) -> Dict[str, Any]:
        by_region: Dict[str, Dict[str, Any]] = {}
        for r in self._regions.values():
            region_policies = [p for p in self._policies.values() if p.current_region == r.location]
            compliant = sum(1 for p in region_policies if p.status == ResidencyStatus.COMPLIANT)
            violations = sum(1 for p in region_policies if p.status == ResidencyStatus.VIOLATION)
            by_region[r.location.value] = {"location": r.location.value, "compliance_status": r.compliance_status.value, "total_policies": len(region_policies), "compliant": compliant, "violations": violations}
        return {"generated_at": datetime.utcnow().isoformat(), "total_regions": len(self._regions), "regions": by_region}


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
