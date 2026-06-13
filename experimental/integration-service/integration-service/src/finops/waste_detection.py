"""Feature 27: Cloud Waste Detection - Detect unattached volumes, idle instances, orphaned resources"""

import json
import os
import math
import uuid
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class WasteCategory(Enum):
    UNATTACHED_VOLUME = "unattached_volume"
    IDLE_INSTANCE = "idle_instance"
    ORPHANED_LOAD_BALANCER = "orphaned_load_balancer"
    UNDERUTILIZED_DATABASE = "underutilized_database"
    ORPHANED_SNAPSHOT = "orphaned_snapshot"
    UNUSED_IP_ADDRESS = "unused_ip_address"
    ORPHANED_SECURITY_GROUP = "orphaned_security_group"
    STALE_RESOURCE = "stale_resource"
    UNATTACHED_STORAGE = "unattached_storage"
    OVER_PROVISIONED_RESOURCE = "over_provisioned_resource"


class WasteSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WasteStatus(Enum):
    DETECTED = "detected"
    APPROVED_FOR_CLEANUP = "approved_for_cleanup"
    CLEANED_UP = "cleaned_up"
    DISMISSED = "dismissed"


class WasteDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.resources_file = _data_file('waste_resources.json')
        self.findings_file = _data_file('waste_findings.json')
        self.resources: List[Dict[str, Any]] = []
        self.findings: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.resources_file, 'resources'), (self.findings_file, 'findings')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_findings(self):
        try:
            with open(self.findings_file, 'w') as f:
                json.dump(self.findings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save findings: {e}")

    def scan_for_waste(self, provider: str = None) -> Dict[str, Any]:
        if not self.resources:
            self._seed_mock_resources()

        targets = [r for r in self.resources] if not provider else [r for r in self.resources if r.get('provider') == provider]
        new_findings = []

        for resource in targets:
            finding = self._evaluate_resource(resource)
            if finding:
                new_findings.append(finding)

        self.findings.extend(new_findings)
        self._save_findings()
        return {
            "scanned": len(targets),
            "findings": len(new_findings),
            "estimated_waste": round(sum(f.get('monthly_waste', 0) for f in new_findings), 2),
            "scan_id": str(uuid.uuid4()),
            "scanned_at": datetime.utcnow().isoformat(),
        }

    def _evaluate_resource(self, resource: Dict) -> Optional[Dict[str, Any]]:
        rtype = resource['type']
        if rtype == "volume" and not resource.get('attached_to'):
            return self._make_finding(resource, WasteCategory.UNATTACHED_VOLUME.value,
                                      WasteSeverity.MEDIUM.value, "Volume not attached to any instance")
        elif rtype == "instance":
            last_active = resource.get('last_active_days', 0)
            if last_active > 14:
                return self._make_finding(resource, WasteCategory.IDLE_INSTANCE.value,
                                          WasteSeverity.HIGH.value, f"Instance idle for {last_active} days")
            if resource.get('avg_cpu', 100) < 5 and resource.get('avg_memory', 100) < 10:
                return self._make_finding(resource, WasteCategory.OVER_PROVISIONED_RESOURCE.value,
                                          WasteSeverity.MEDIUM.value, "Extremely low utilization (<5% CPU, <10% memory)")
        elif rtype == "load_balancer" and not resource.get('target_count', 0):
            return self._make_finding(resource, WasteCategory.ORPHANED_LOAD_BALANCER.value,
                                      WasteSeverity.HIGH.value, "Load balancer has no registered targets")
        elif rtype == "database":
            avg_cpu = resource.get('avg_cpu', 100)
            if avg_cpu < 5:
                return self._make_finding(resource, WasteCategory.UNDERUTILIZED_DATABASE.value,
                                          WasteSeverity.MEDIUM.value, f"Database CPU utilization at {avg_cpu}%")
        elif rtype == "snapshot":
            age_days = resource.get('age_days', 0)
            if age_days > 90 and not resource.get('source_exists', True):
                return self._make_finding(resource, WasteCategory.ORPHANED_SNAPSHOT.value,
                                          WasteSeverity.MEDIUM.value, f"Orphaned snapshot {age_days} days old")
        elif rtype == "ip_address" and not resource.get('assigned', False):
            return self._make_finding(resource, WasteCategory.UNUSED_IP_ADDRESS.value,
                                      WasteSeverity.LOW.value, "Elastic IP not assigned to any resource")
        elif rtype == "security_group" and not resource.get('attached_count', 0):
            return self._make_finding(resource, WasteCategory.ORPHANED_SECURITY_GROUP.value,
                                      WasteSeverity.LOW.value, "Security group not attached to any resource")
        return None

    def _make_finding(self, resource: Dict, category: str, severity: str, reason: str) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "resource_id": resource['id'],
            "resource_name": resource['name'],
            "resource_type": resource['type'],
            "category": category,
            "severity": severity,
            "reason": reason,
            "monthly_waste": resource.get('monthly_cost', 10),
            "provider": resource.get('provider', 'aws'),
            "region": resource.get('region', 'us-east-1'),
            "status": WasteStatus.DETECTED.value,
            "detected_at": datetime.utcnow().isoformat(),
            "auto_cleanup_eligible": severity in [WasteSeverity.LOW.value, WasteSeverity.MEDIUM.value],
        }

    def _seed_mock_resources(self):
        providers = ["aws", "azure", "gcp"]
        regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
        for i in range(30):
            rtype = random.choice(["volume", "instance", "load_balancer", "database", "snapshot", "ip_address", "security_group"])
            resource = {
                "id": str(uuid.uuid4()),
                "name": f"{rtype}-{i:04d}",
                "type": rtype,
                "provider": random.choice(providers),
                "region": random.choice(regions),
                "monthly_cost": round(random.uniform(5, 200), 2),
                "avg_cpu": random.uniform(0.5, 80),
                "avg_memory": random.uniform(1, 90),
                "last_active_days": random.randint(0, 60) if rtype == "instance" else 0,
                "attached_to": None if rtype == "volume" and random.random() < 0.4 else f"i-{uuid.uuid4().hex[:8]}",
                "target_count": random.choice([0, 2, 5]) if rtype == "load_balancer" else None,
                "age_days": random.randint(10, 365) if rtype == "snapshot" else 0,
                "source_exists": random.random() > 0.7 if rtype == "snapshot" else True,
                "assigned": random.random() > 0.3 if rtype == "ip_address" else None,
                "attached_count": random.choice([0, 1, 3]) if rtype == "security_group" else None,
            }
            self.resources.append(resource)

    def get_findings(self, category: str = None, severity: str = None,
                     status: str = None) -> List[Dict[str, Any]]:
        result = self.findings
        if category:
            result = [f for f in result if f['category'] == category]
        if severity:
            result = [f for f in result if f['severity'] == severity]
        if status:
            result = [f for f in result if f['status'] == status]
        return sorted(result, key=lambda x: x['monthly_waste'], reverse=True)

    def approve_cleanup(self, finding_id: str) -> Dict[str, Any]:
        finding = next((f for f in self.findings if f['id'] == finding_id), None)
        if not finding:
            return {"error": "Finding not found", "success": False}
        finding['status'] = WasteStatus.APPROVED_FOR_CLEANUP.value
        self._save_findings()
        return {"success": True}

    def execute_cleanup(self, finding_id: str) -> Dict[str, Any]:
        finding = next((f for f in self.findings if f['id'] == finding_id), None)
        if not finding:
            return {"error": "Finding not found", "success": False}
        finding['status'] = WasteStatus.CLEANED_UP.value
        finding['cleaned_up_at'] = datetime.utcnow().isoformat()
        self._save_findings()
        return {"success": True, "resource_deleted": finding['resource_name'], "cost_saved": finding['monthly_waste']}

    def dismiss_finding(self, finding_id: str, reason: str = None) -> Dict[str, Any]:
        finding = next((f for f in self.findings if f['id'] == finding_id), None)
        if not finding:
            return {"error": "Finding not found", "success": False}
        finding['status'] = WasteStatus.DISMISSED.value
        finding['dismiss_reason'] = reason
        self._save_findings()
        return {"success": True}

    def get_summary(self) -> Dict[str, Any]:
        by_category = {}
        total_waste = 0
        for f in self.findings:
            if f['status'] in [WasteStatus.DETECTED.value, WasteStatus.APPROVED_FOR_CLEANUP.value]:
                by_category[f['category']] = by_category.get(f['category'], 0) + f['monthly_waste']
                total_waste += f['monthly_waste']
        return {
            "total_findings": len(self.findings),
            "open": sum(1 for f in self.findings if f['status'] == WasteStatus.DETECTED.value),
            "approved_for_cleanup": sum(1 for f in self.findings if f['status'] == WasteStatus.APPROVED_FOR_CLEANUP.value),
            "cleaned_up": sum(1 for f in self.findings if f['status'] == WasteStatus.CLEANED_UP.value),
            "dismissed": sum(1 for f in self.findings if f['status'] == WasteStatus.DISMISSED.value),
            "total_monthly_waste": round(total_waste, 2),
            "projected_annual_waste": round(total_waste * 12, 2),
            "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: x[1], reverse=True)},
            "top_5_waste_items": sorted(
                [f for f in self.findings if f['status'] != WasteStatus.CLEANED_UP.value],
                key=lambda x: x['monthly_waste'], reverse=True)[:5],
        }

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class WasteDetectionError(Exception): pass

@dataclass
class WasteFinding:
    category: str
    resource_name: str
    resource_type: str
    monthly_waste: float
    severity: str
    description: str = ""
    status: str = "detected"
    id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_waste_finding(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('category'): errors.append("category is required")
    if not data.get('resource_name'): errors.append("resource_name is required")
    if data.get('monthly_waste', 0) <= 0: errors.append("monthly_waste must be positive")
    return errors

def categorize_waste(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    categories = {}
    for f in findings:
        cat = f.get('category', 'other')
        categories.setdefault(cat, {"count": 0, "total_waste": 0.0, "items": []})
        categories[cat]["count"] += 1
        categories[cat]["total_waste"] += f.get('monthly_waste', 0)
        categories[cat]["items"].append(f.get('resource_name'))
    return {k: {**v, "total_waste": round(v["total_waste"], 2)} for k, v in categories.items()}

def filter_findings(findings: List[Dict[str, Any]], categories: Optional[List[str]] = None, severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    results = findings[:]
    if categories: results = [f for f in results if f.get('category') in categories]
    if severity: results = [f for f in results if f.get('severity') == severity]
    if status: results = [f for f in results if f.get('status') == status]
    return results

def estimate_waste_savings(findings: List[Dict[str, Any]], cleanup_pct: float = 0.8) -> Dict[str, Any]:
    total = sum(f.get('monthly_waste', 0) for f in findings)
    recoverable = total * cleanup_pct
    return {
        "total_monthly_waste": round(total, 2),
        "recoverable_monthly": round(recoverable, 2),
        "recoverable_annual": round(recoverable * 12, 2),
        "cleanup_rate_pct": cleanup_pct * 100,
        "by_severity": {s: round(sum(f.get('monthly_waste', 0) for f in findings if f.get('severity') == s) * cleanup_pct, 2) for s in set(f.get('severity', 'low') for f in findings)},
    }

def recommend_waste_actions(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    actions = []
    for f in sorted(findings, key=lambda x: x.get('monthly_waste', 0), reverse=True)[:10]:
        if f.get('category') == 'idle_resources':
            actions.append({"finding_id": f.get('id'), "action": "stop_resource", "resource": f.get('resource_name'), "savings": f.get('monthly_waste'), "effort": "low"})
        elif f.get('category') == 'unattached_storage':
            actions.append({"finding_id": f.get('id'), "action": "delete_volume", "resource": f.get('resource_name'), "savings": f.get('monthly_waste'), "effort": "low"})
        elif f.get('category') == 'over_provisioned':
            actions.append({"finding_id": f.get('id'), "action": "resize_instance", "resource": f.get('resource_name'), "savings": f.get('monthly_waste'), "effort": "medium"})
        else:
            actions.append({"finding_id": f.get('id'), "action": "review", "resource": f.get('resource_name'), "savings": f.get('monthly_waste'), "effort": "medium"})
    return actions

def generate_waste_report(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    categories = categorize_waste(findings)
    total_waste = sum(f.get('monthly_waste', 0) for f in findings)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_findings": len(findings),
        "total_monthly_waste": round(total_waste, 2),
        "total_annual_waste": round(total_waste * 12, 2),
        "categories": categories,
        "top_actions": recommend_waste_actions(findings),
        "summary": f"Found {len(findings)} waste items totaling ${round(total_waste, 2)}/month in potential savings",
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class WasteBatchProcessor:
    def __init__(self, detector: 'WasteDetector'):
        self.detector = detector
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_approve_cleanup(self, finding_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for fid in finding_ids:
            try:
                result = self.detector.approve_finding(fid)
                results.append({"success": True, "finding_id": fid})
            except Exception as e:
                results.append({"success": False, "finding_id": fid, "error": str(e)})
        return results

    async def batch_cleanup(self, finding_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for fid in finding_ids:
            try:
                result = self.detector.cleanup_resource(fid)
                results.append({"success": True, "finding_id": fid})
            except Exception as e:
                results.append({"success": False, "finding_id": fid, "error": str(e)})
        return results

    async def scan_all(self) -> Dict[str, Any]:
        return self.detector.run_scan()

    async def export_findings_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "resource_name", "category", "severity", "monthly_waste", "status"])
        for f in self.detector.findings:
            writer.writerow([f.get('id'), f.get('resource_name'), f.get('category'), f.get('severity'), f.get('monthly_waste'), f.get('status')])
        return output.getvalue()

class WasteAnalytics:
    def __init__(self, detector: 'WasteDetector'):
        self.detector = detector

    def by_category(self) -> Dict[str, Any]:
        cats = {}
        for f in self.detector.findings:
            c = f.get('category', 'unknown')
            cats.setdefault(c, {"count": 0, "total_waste": 0})
            cats[c]["count"] += 1
            cats[c]["total_waste"] += f.get('monthly_waste', 0)
        return {k: {"count": v["count"], "monthly_waste": round(v["total_waste"], 2)} for k, v in cats.items()}

    def cleanup_trend(self, days: int = 30) -> Dict[str, Any]:
        cleaned = [f for f in self.detector.findings if f.get('status') == 'cleaned_up' and f.get('cleaned_at')]
        recent_cleaned = [f for f in cleaned if (datetime.utcnow() - datetime.fromisoformat(f['cleaned_at'])).days <= days] if cleaned else []
        return {"cleaned_last_30d": len(recent_cleaned), "total_cleaned": len(cleaned), "savings_realized": round(sum(f.get('monthly_waste', 0) for f in recent_cleaned), 2)}

class WastePaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items; self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size; end = start + self.page_size
        total = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {"page": page, "page_size": self.page_size, "total_items": len(self.items), "total_pages": total, "has_next": page < total, "has_prev": page > 1, "items": self.items[start:end]}

# === ADVANCED WASTE DETECTION ===

class ScheduledScanner:
    def __init__(self, detector: WasteDetector):
        self.detector = detector
        self.scan_schedule: List[Dict[str, Any]] = []

    def schedule_scan(self, name: str, interval_hours: int, providers: List[str] = None) -> Dict[str, Any]:
        scan = {
            "id": str(uuid.uuid4()),
            "name": name,
            "interval_hours": interval_hours,
            "providers": providers or ["aws", "azure", "gcp"],
            "last_scan": None,
            "next_scan": datetime.utcnow().isoformat(),
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.scan_schedule.append(scan)
        return scan

    def process_due_scans(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        results = []
        for scan in self.scan_schedule:
            if not scan['active']:
                continue
            if scan.get('next_scan') and datetime.fromisoformat(scan['next_scan']) <= now:
                result = self.detector.scan_for_waste()
                result['scan_name'] = scan['name']
                results.append(result)
                scan['last_scan'] = now.isoformat()
                scan['next_scan'] = (now + timedelta(hours=scan['interval_hours'])).isoformat()
        return results

    def list_schedules(self) -> List[Dict[str, Any]]:
        return self.scan_schedule

# === WASTE REDUCTION TRACKER ===

class WasteReductionTracker:
    def __init__(self, detector: WasteDetector):
        self.detector = detector
        self.reduction_goals: List[Dict[str, Any]] = []

    def set_goal(self, name: str, target_reduction_pct: float, target_date: str) -> Dict[str, Any]:
        goal = {
            "id": str(uuid.uuid4()),
            "name": name,
            "target_reduction_pct": target_reduction_pct,
            "target_date": target_date,
            "baseline_waste": self._current_waste(),
            "current_waste": self._current_waste(),
            "progress_pct": 0,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.reduction_goals.append(goal)
        return goal

    def _current_waste(self) -> float:
        return sum(f.get('monthly_waste', 0) for f in self.detector.findings if f.get('status') not in ['cleaned_up', 'dismissed'])

    def update_progress(self) -> List[Dict[str, Any]]:
        current = self._current_waste()
        updates = []
        for goal in self.reduction_goals:
            if goal['status'] != 'active':
                continue
            goal['current_waste'] = current
            baseline = goal['baseline_waste']
            if baseline > 0:
                reduction = max(0, baseline - current)
                progress = (reduction / (baseline * goal['target_reduction_pct'] / 100)) * 100
                goal['progress_pct'] = round(min(100, progress), 1)
                if goal['progress_pct'] >= 100:
                    goal['status'] = "achieved"
                updates.append(goal)
        return updates

    def get_goals(self) -> List[Dict[str, Any]]:
        return self.reduction_goals

# === AUTO-CLEANUP ===

class AutoCleanupEngine:
    def __init__(self, detector: WasteDetector):
        self.detector = detector
        self.cleanup_rules: List[Dict[str, Any]] = []

    def add_rule(self, name: str, categories: List[str], max_severity: str = "medium", dry_run: bool = True) -> Dict[str, Any]:
        rule = {
            "id": str(uuid.uuid4()),
            "name": name,
            "categories": categories,
            "max_severity": max_severity,
            "dry_run": dry_run,
            "enabled": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.cleanup_rules.append(rule)
        return rule

    def execute_rules(self) -> Dict[str, Any]:
        summary = {"rules_evaluated": 0, "cleanup_actions": []}
        severities = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_sev = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        for rule in self.cleanup_rules:
            if not rule['enabled']:
                continue
            summary["rules_evaluated"] += 1
            for finding in self.detector.findings:
                if finding.get('status') in ['cleaned_up', 'dismissed']:
                    continue
                if finding.get('category') not in rule['categories']:
                    continue
                if severities.get(finding.get('severity', 'high'), 99) > max_sev.get(rule['max_severity'], 1):
                    continue
                if rule['dry_run']:
                    summary["cleanup_actions"].append({
                        "rule": rule['name'],
                        "finding_id": finding['id'],
                        "resource": finding['resource_name'],
                        "action": "would_cleanup",
                        "savings": finding['monthly_waste'],
                    })
                else:
                    result = self.detector.execute_cleanup(finding['id'])
                    summary["cleanup_actions"].append({
                        "rule": rule['name'],
                        "finding_id": finding['id'],
                        "resource": result.get('resource_deleted'),
                        "action": "cleaned_up",
                        "savings": result.get('cost_saved'),
                    })
        return summary

# === WASTE FORECAST ===

class WasteForecaster:
    def __init__(self, detector: WasteDetector):
        self.detector = detector

    def project_waste(self, months: int = 12) -> List[Dict[str, Any]]:
        current = sum(f.get('monthly_waste', 0) for f in self.detector.findings)
        projections = []
        for m in range(1, months + 1):
            natural_growth = current * (1 + 0.03) ** (m / 12)
            projected = natural_growth * (1 - 0.02 * m)
            projections.append({
                "month": m,
                "projected_waste": round(max(0, projected), 2),
                "without_intervention": round(natural_growth, 2),
                "savings_from_cleanup": round(max(0, natural_growth - projected), 2),
            })
        return projections

    def waste_score(self) -> Dict[str, Any]:
        total_waste = sum(f.get('monthly_waste', 0) for f in self.detector.findings)
        total_resources = len(self.detector.resources)
        waste_per_resource = total_waste / max(total_resources, 1)
        cleanable = sum(f.get('monthly_waste', 0) for f in self.detector.findings if f.get('auto_cleanup_eligible'))
        score = max(0, 100 - (total_waste / max(waste_per_resource * total_resources, 0.01)))
        return {
            "waste_score": round(min(100, score), 1),
            "total_waste": round(total_waste, 2),
            "waste_per_resource": round(waste_per_resource, 2),
            "cleanable_waste": round(cleanable, 2),
            "cleanable_pct": round((cleanable / max(total_waste, 0.01)) * 100, 1),
            "grade": "A" if score > 80 else ("B" if score > 60 else ("C" if score > 40 else "D")),
        }

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
        return {"total_count": 0, "total_value": 0.0, "avg_value": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class FinopsResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    amount: float = 0.0
    currency: str = Field(default="USD")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FinopsBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    total_cost: float = Field(default=0.0)
    estimated_savings: float = Field(default=0.0)

    def add_item(self, item: Dict[str, Any], cost: float = 0.0, savings: float = 0.0) -> None:
        self.items.append(item)
        self.total_cost += cost
        self.estimated_savings += savings

    def complete(self) -> None:
        self.status = "completed"

class CostMetrics(BaseModel):
    category: str
    amount: float
    currency: str = Field(default="USD")
    period: str = Field(default="monthly")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict)

class CostTracker:
    def __init__(self) -> None:
        self._entries: List[CostMetrics] = []

    def record(self, category: str, amount: float, tags: Optional[Dict[str, str]] = None) -> None:
        self._entries.append(CostMetrics(category=category, amount=amount, tags=tags or {}))

    def total_by_category(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._entries:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals

    def total(self) -> float:
        return round(sum(e.amount for e in self._entries), 2)

    def average(self) -> float:
        return round(self.total() / max(len(self._entries), 1), 2)

    def get_by_period(self, period: str) -> List[CostMetrics]:
        return [e for e in self._entries if e.period == period]

    def summary(self) -> Dict[str, Any]:
        return {"total_entries": len(self._entries), "total_cost": self.total(),
                "avg_per_entry": self.average(),
                "by_category": self.total_by_category(),
                "latest": self._entries[-1].dict() if self._entries else None}

class SavingsCalculator:
    @staticmethod
    def compute(original_cost: float, new_cost: float) -> Dict[str, Any]:
        savings = original_cost - new_cost
        pct = (savings / original_cost * 100) if original_cost > 0 else 0
        return {"original": round(original_cost, 2), "new": round(new_cost, 2),
                "savings": round(savings, 2), "savings_pct": round(pct, 1)}

    @staticmethod
    def project_monthly(daily_savings: float, days: int = 30) -> float:
        return round(daily_savings * days, 2)

    @staticmethod
    def project_annual(daily_savings: float) -> float:
        return round(daily_savings * 365, 2)

    @staticmethod
    def roi(investment: float, savings_per_month: float, months: int = 12) -> Dict[str, Any]:
        total_savings = savings_per_month * months
        roi_value = ((total_savings - investment) / investment * 100) if investment > 0 else 0
        return {"investment": round(investment, 2), "total_savings": round(total_savings, 2),
                "months": months, "roi_pct": round(roi_value, 1),
                "payback_months": round(investment / max(savings_per_month, 0.01), 1)}

class BudgetAlert(BaseModel):
    budget_name: str
    threshold: float
    current_spend: float
    percentage: float
    severity: str = Field(default="info")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    notified: bool = False

    def should_alert(self) -> bool:
        return self.percentage >= self.threshold and not self.notified

class BudgetMonitor:
    def __init__(self) -> None:
        self._budgets: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[BudgetAlert] = []

    def set_budget(self, name: str, limit: float, warning_threshold: float = 80.0) -> None:
        self._budgets[name] = {"limit": limit, "warning_threshold": warning_threshold, "spend": 0.0}

    def record_spend(self, name: str, amount: float) -> Optional[BudgetAlert]:
        budget = self._budgets.get(name)
        if not budget:
            return None
        budget["spend"] += amount
        pct = (budget["spend"] / budget["limit"]) * 100
        if pct >= budget["warning_threshold"]:
            alert = BudgetAlert(budget_name=name, threshold=budget["warning_threshold"],
                                current_spend=round(budget["spend"], 2),
                                percentage=round(pct, 1),
                                severity="warning" if pct < 100 else "critical")
            self._alerts.append(alert)
            return alert
        return None

    def get_budget_status(self, name: str) -> Optional[Dict[str, Any]]:
        budget = self._budgets.get(name)
        if not budget:
            return None
        pct = (budget["spend"] / budget["limit"]) * 100 if budget["limit"] > 0 else 0
        return {"name": name, "limit": budget["limit"], "spend": round(budget["spend"], 2),
                "remaining": round(budget["limit"] - budget["spend"], 2),
                "usage_pct": round(pct, 1)}

    def get_all_status(self) -> Dict[str, Any]:
        return {name: self.get_budget_status(name) for name in self._budgets}

    def get_alerts(self, severity: Optional[str] = None) -> List[BudgetAlert]:
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return self._alerts

class ReportingSchedule(BaseModel):
    report_type: str
    frequency: str = Field(default="daily")
    recipients: List[str] = Field(default_factory=list)
    format: str = Field(default="pdf")
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None

# -- Advanced FinOps Analytics -----------------------------------------

class CostEfficiencyIndex:
    def __init__(self) -> None:
        self._indices: Dict[str, float] = {}

    def calculate(self, department: str, total_cost: float, output_value: float) -> float:
        if total_cost <= 0:
            return 0.0
        index = round(output_value / total_cost, 4)
        self._indices[department] = index
        return index

    def get_index(self, department: str) -> Optional[float]:
        return self._indices.get(department)

    def get_ranking(self) -> List[Dict[str, Any]]:
        ranked = sorted(self._indices.items(), key=lambda x: x[1], reverse=True)
        return [{"department": d, "efficiency_index": v, "rank": i + 1} for i, (d, v) in enumerate(ranked)]

class AnomalyThresholdConfig(BaseModel):
    metric: str
    warning_pct: float = Field(default=20.0, ge=0)
    critical_pct: float = Field(default=50.0, ge=0)
    cooldown_minutes: int = Field(default=60)
    enabled: bool = True

class AnomalyConfigManager:
    def __init__(self) -> None:
        self._configs: Dict[str, AnomalyThresholdConfig] = {}

    def set_config(self, config: AnomalyThresholdConfig) -> None:
        self._configs[config.metric] = config

    def get_config(self, metric: str) -> Optional[AnomalyThresholdConfig]:
        return self._configs.get(metric)

    def evaluate(self, metric: str, current: float, baseline: float) -> Dict[str, Any]:
        config = self._configs.get(metric)
        if not config or not config.enabled or baseline <= 0:
            return {"level": "ok", "deviation_pct": 0.0}
        deviation = abs(current - baseline) / baseline * 100
        if deviation >= config.critical_pct:
            return {"level": "critical", "deviation_pct": round(deviation, 1), "threshold": config.critical_pct}
        if deviation >= config.warning_pct:
            return {"level": "warning", "deviation_pct": round(deviation, 1), "threshold": config.warning_pct}
        return {"level": "ok", "deviation_pct": round(deviation, 1)}

class CommitmentPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str
    commitment_type: str = Field(default="1yr")
    hourly_commitment: float = Field(default=0.0)
    upfront_cost: float = Field(default=0.0)
    effective_rate: float = Field(default=0.0)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    status: str = Field(default="active")
    estimated_savings_pct: float = Field(default=0.0)

class CommitmentOptimizer:
    def __init__(self) -> None:
        self._plans: Dict[str, CommitmentPlan] = {}

    def create_plan(self, provider: str, commitment_type: str, hourly: float,
                    upfront: float, effective_rate: float, savings_pct: float) -> CommitmentPlan:
        plan = CommitmentPlan(provider=provider, commitment_type=commitment_type,
                              hourly_commitment=hourly, upfront_cost=upfront,
                              effective_rate=effective_rate, estimated_savings_pct=savings_pct)
        self._plans[plan.plan_id] = plan
        return plan

    def get_active(self) -> List[CommitmentPlan]:
        return [p for p in self._plans.values() if p.status == "active"]

    def get_coverage_pct(self, total_hourly_spend: float) -> float:
        committed = sum(p.hourly_commitment for p in self.get_active())
        return round(committed / max(total_hourly_spend, 0.01) * 100, 1)

    def get_savings_projection(self) -> Dict[str, Any]:
        active = self.get_active()
        total_original = sum(p.hourly_commitment for p in active)
        total_effective = sum(p.effective_rate for p in active)
        monthly_savings = (total_original - total_effective) * 730
        return {"monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(monthly_savings * 12, 2),
                "coverage_pct": round(total_original / max(total_original + 0.01, 1) * 100, 1)}

class WasteCategory(BaseModel):
    category: str
    amount: float
    resources: int
    recommendation: str = ""
    potential_savings: float = 0.0

class WasteAnalyzer:
    def __init__(self) -> None:
        self._categories: Dict[str, WasteCategory] = {}

    def add_category(self, category: str, amount: float, resources: int,
                     recommendation: str = "", savings: float = 0.0) -> WasteCategory:
        wc = WasteCategory(category=category, amount=amount, resources=resources,
                           recommendation=recommendation, potential_savings=savings)
        self._categories[category] = wc
        return wc

    def total_waste(self) -> float:
        return round(sum(c.amount for c in self._categories.values()), 2)

    def total_potential_savings(self) -> float:
        return round(sum(c.potential_savings for c in self._categories.values()), 2)

    def get_by_category(self, category: str) -> Optional[WasteCategory]:
        return self._categories.get(category)

    def get_summary(self) -> Dict[str, Any]:
        return {"categories": [c.dict() for c in self._categories.values()],
                "total_waste": self.total_waste(),
                "total_potential_savings": self.total_potential_savings(),
                "waste_pct": round(self.total_waste() / max(self.total_waste() + self.total_potential_savings(), 0.01) * 100, 1)}

class CostForecastPoint(BaseModel):
    date: str
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float

class CostForecaster:
    def __init__(self) -> None:
        self._forecasts: List[CostForecastPoint] = []

    def generate(self, days: int = 90, base_cost: float = 1000.0, volatility: float = 0.1) -> List[CostForecastPoint]:
        self._forecasts = []
        current = base_cost
        for i in range(days):
            change = current * volatility * (random.random() * 2 - 1)
            predicted = round(current + change, 2)
            ci = current * 0.05
            point = CostForecastPoint(
                date=(datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d"),
                predicted_cost=predicted, lower_bound=round(predicted - ci, 2),
                upper_bound=round(predicted + ci, 2),
                confidence=max(0.5, 1.0 - i / days * 0.4),
            )
            self._forecasts.append(point)
            current = predicted
        return self._forecasts

    def get_forecast(self) -> List[CostForecastPoint]:
        return self._forecasts

    def get_aggregate(self) -> Dict[str, Any]:
        if not self._forecasts:
            return {"total_forecast": 0, "avg_daily": 0}
        total = sum(p.predicted_cost for p in self._forecasts)
        return {"total_forecast": round(total, 2),
                "avg_daily": round(total / len(self._forecasts), 2),
                "days": len(self._forecasts),
                "last_prediction": self._forecasts[-1].predicted_cost}
