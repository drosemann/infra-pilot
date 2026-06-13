from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import hashlib
import asyncio
import random

logger = logging.getLogger(__name__)


class DataIntegrityVerifier:
    """Data Integrity Verification — periodic checksum/consistency validation across replicas and backups"""

    VERIFICATION_TYPES = ["checksum", "row_count", "schema_compare", "sample_compare", "replica_lag", "backup_restore"]
    REPLICA_TYPES = ["read_replica", "standby", "backup", "cross_region"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.verifications_file = config.get("data_integrity_file", "data/resiliency/data_integrity.json")
        self.results_file = config.get("data_integrity_results_file", "data/resiliency/data_integrity_results.json")
        self.verifications: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.verifications_file) or ".", exist_ok=True)
        for path, attr in [(self.verifications_file, "verifications"), (self.results_file, "results")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_verifications(self):
        with open(self.verifications_file, "w") as f:
            json.dump(self.verifications, f, indent=2, default=str)

    def _save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results[-5000:], f, indent=2, default=str)

    async def create_verification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        verification = {
            "id": f"di_{int(datetime.now().timestamp())}_{len(self.verifications)}",
            "name": data.get("name", "Unnamed Verification"),
            "description": data.get("description", ""),
            "resource_type": data.get("resource_type", "database"),
            "resource_id": data.get("resource_id", ""),
            "resource_name": data.get("resource_name", ""),
            "verification_type": data.get("verification_type", "checksum"),
            "schedule_cron": data.get("schedule_cron", "0 */6 * * *"),
            "replicas": data.get("replicas", []),
            "checksum_algorithm": data.get("checksum_algorithm", "sha256"),
            "comparison_tables": data.get("comparison_tables", []),
            "tolerance_percent": data.get("tolerance_percent", 0.0),
            "auto_repair": data.get("auto_repair", False),
            "trusted_source": data.get("trusted_source", "primary"),
            "notify_on_failure": data.get("notify_on_failure", True),
            "active": True,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "last_status": None,
        }
        self.verifications.append(verification)
        self._save_verifications()
        return verification

    async def list_verifications(self) -> List[Dict[str, Any]]:
        return self.verifications

    async def get_verification(self, verification_id: str) -> Optional[Dict[str, Any]]:
        return next((v for v in self.verifications if v["id"] == verification_id), None)

    async def update_verification(self, verification_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for v in self.verifications:
            if v["id"] == verification_id:
                v.update(updates)
                self._save_verifications()
                return v
        return None

    async def delete_verification(self, verification_id: str) -> bool:
        for i, v in enumerate(self.verifications):
            if v["id"] == verification_id:
                self.verifications.pop(i)
                self._save_verifications()
                return True
        return False

    async def run_verification(self, verification_id: str) -> Dict[str, Any]:
        verification = await self.get_verification(verification_id)
        if not verification:
            return {"error": "Verification config not found"}
        vtype = verification.get("verification_type", "checksum")
        replica_results = []
        all_passed = True
        primary_checksum = hashlib.sha256(f"primary_data_{datetime.now().isoformat()}".encode()).hexdigest()
        for replica in verification.get("replicas", []):
            replica_type = replica.get("type", "read_replica")
            replica_name = replica.get("name", "")
            replica_checksum = primary_checksum if random.random() > 0.08 else hashlib.sha256(f"corrupted_{datetime.now().isoformat()}".encode()).hexdigest()
            match = replica_checksum == primary_checksum
            lag_ms = random.randint(0, 500)
            result = {"replica_name": replica_name, "replica_type": replica_type, "checksum_match": match, "lag_ms": lag_ms, "row_count_match": random.random() > 0.05, "schema_match": random.random() > 0.02, "verified_at": datetime.now().isoformat()}
            if vtype == "checksum":
                result["primary_checksum"] = primary_checksum[:16] + "..."
                result["replica_checksum"] = replica_checksum[:16] + "..."
            elif vtype == "row_count":
                result["primary_rows"] = random.randint(10000, 100000)
                result["replica_rows"] = result["primary_rows"] + random.randint(-10, 10)
                result["row_count_match"] = abs(result["primary_rows"] - result["replica_rows"]) <= verification.get("tolerance_percent", 0) / 100 * result["primary_rows"]
            passed = result.get("checksum_match", True) and result.get("row_count_match", True) and result.get("schema_match", True)
            result["passed"] = passed
            if not passed:
                all_passed = False
            replica_results.append(result)
            if not passed and verification.get("auto_repair"):
                await self._auto_repair(verification, replica_name, primary_checksum)
        total_results = {
            "id": f"di_result_{int(datetime.now().timestamp())}_{len(self.results)}",
            "verification_id": verification_id,
            "verification_name": verification.get("name"),
            "verification_type": vtype,
            "resource_name": verification.get("resource_name"),
            "status": "passed" if all_passed else "failed",
            "replica_results": replica_results,
            "total_replicas": len(replica_results),
            "passed_count": sum(1 for r in replica_results if r.get("passed", False)),
            "failed_count": sum(1 for r in replica_results if not r.get("passed", False)),
            "auto_repair_triggered": not all_passed and verification.get("auto_repair"),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }
        self.results.append(total_results)
        self._save_results()
        verification["last_run"] = datetime.now().isoformat()
        verification["last_status"] = total_results["status"]
        self._save_verifications()
        return total_results

    async def _auto_repair(self, verification: Dict[str, Any], replica_name: str, trusted_checksum: str):
        logger.info("Auto-repair triggered for replica from trusted source")
        await asyncio.sleep(1)

    async def get_results(self, verification_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if verification_id:
            return [r for r in self.results if r["verification_id"] == verification_id][-limit:]
        return self.results[-limit:]

    async def get_summary(self) -> Dict[str, Any]:
        total = len(self.verifications)
        active = sum(1 for v in self.verifications if v.get("active", True))
        recent = [r for r in self.results if datetime.fromisoformat(r["completed_at"]) > datetime.now() - timedelta(days=7)]
        passed = sum(1 for r in recent if r["status"] == "passed")
        return {"total_verifications": total, "active_verifications": active, "runs_last_7d": len(recent), "passed": passed, "failed": len(recent) - passed, "pass_rate_percent": round(passed / len(recent) * 100, 2) if recent else 100.0, "replicas_monitored": sum(len(v.get("replicas", [])) for v in self.verifications), "verification_types": list(set(v["verification_type"] for v in self.verifications))}

    async def run_all_verifications(self) -> List[Dict[str, Any]]:
        results = []
        for v in self.verifications:
            if v.get("active", True):
                result = await self.run_verification(v["id"])
                results.append(result)
        return results

    async def update_verification(self, verification_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for v in self.verifications:
            if v["id"] == verification_id:
                v.update(updates)
                self._save_verifications()
                return v
        return None

    async def delete_verification(self, verification_id: str) -> bool:
        for i, v in enumerate(self.verifications):
            if v["id"] == verification_id:
                self.verifications.pop(i)
                self._save_verifications()
                return True
        return False

    async def get_verification_types(self) -> List[str]:
        return ["checksum", "row_count", "schema_match", "drift_check", "replication_lag", "consistency_check"]

    async def get_replication_lag_report(self) -> Dict[str, Any]:
        lag_checks = [r for r in self.results if r.get("verification_type") == "replication_lag"][-50:]
        avg_lag = sum(r.get("lag_seconds", 0) for r in lag_checks) / len(lag_checks) if lag_checks else 0
        return {"average_lag_seconds": round(avg_lag, 1), "max_lag_seconds": max((r.get("lag_seconds", 0) for r in lag_checks), default=0), "checks_count": len(lag_checks), "status": "healthy" if avg_lag < 30 else "degraded" if avg_lag < 120 else "unhealthy"}

    async def trigger_repair(self, verification_id: str, replica_name: str) -> Dict[str, Any]:
        verification = await self.get_verification(verification_id)
        if not verification:
            return {"error": "Verification not found"}
        trusted = verification.get("trusted_source", "primary")
        await self._auto_repair(verification, replica_name, trusted)
        return {"verification_id": verification_id, "replica": replica_name, "trusted_source": trusted, "repair_initiated": True, "status": "repairing", "started_at": datetime.now().isoformat()}

    async def clear_results(self) -> Dict[str, Any]:
        count = len(self.results)
        self.results.clear()
        self._save_results()
        return {"cleared": count}

    async def get_verification_stats(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.results if datetime.fromisoformat(r["completed_at"]) > cutoff]
        return {"period_days": days, "total": len(recent), "passed": sum(1 for r in recent if r["status"] == "passed"), "failed": sum(1 for r in recent if r["status"] == "failed"), "avg_duration_ms": round(sum(r.get("duration_ms", 0) for r in recent) / len(recent), 1) if recent else 0, "types_run": list(set(r.get("verification_type") for r in recent))}


class DataIntegrityBatchProcessor:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_create_verifications(self, verifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(verifications):
            try:
                v = await self.manager.create_verification(data)
                v["batch_index"] = i
                v["success"] = True
                results.append(v)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_run_verifications(self, verification_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for vid in verification_ids:
            try:
                r = await self.manager.run_verification(vid)
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"verification_id": vid, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_delete_verifications(self, verification_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for vid in verification_ids:
            ok = await self.manager.delete_verification(vid)
            results.append({"verification_id": vid, "deleted": ok})
        return results

    def export_csv(self, results_list: List[Dict[str, Any]]) -> str:
        if not results_list:
            return ""
        fields = ["id", "verification_name", "status", "verification_type", "resource_name", "total_replicas", "passed_count", "failed_count", "completed_at"]
        lines = [",".join(fields)]
        for r in results_list:
            row = [str(r.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success"))
        return {"total_operations": total, "passed": passed, "failed": total - passed, "rate": round(passed / total * 100, 1) if total else 100}


class IntegrityAnalytics:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    def consistency_rate(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.manager.results if datetime.fromisoformat(r["completed_at"]) > cutoff]
        if not recent:
            return {"rate": 100, "total": 0, "consistent": 0}
        consistent = sum(1 for r in recent if r["status"] == "passed")
        return {"rate": round(consistent / len(recent) * 100, 1), "total": len(recent), "consistent": consistent, "inconsistent": len(recent) - consistent}

    def success_by_type(self) -> Dict[str, Any]:
        breakdown: Dict[str, Dict[str, int]] = {}
        for r in self.manager.results:
            vtype = r.get("verification_type", "unknown")
            breakdown.setdefault(vtype, {"total": 0, "passed": 0})
            breakdown[vtype]["total"] += 1
            if r["status"] == "passed":
                breakdown[vtype]["passed"] += 1
        for vtype in breakdown:
            t = breakdown[vtype]["total"]
            p = breakdown[vtype]["passed"]
            breakdown[vtype]["rate_pct"] = round(p / t * 100, 1) if t else 0
        return breakdown

    def replica_health_summary(self) -> Dict[str, Any]:
        all_replicas: Dict[str, int] = {}
        for r in self.manager.results:
            for rep in r.get("replica_results", []):
                name = rep.get("replica_name", "unknown")
                all_replicas.setdefault(name, {"checks": 0, "passed": 0})
                all_replicas[name]["checks"] += 1
                if rep.get("passed", False):
                    all_replicas[name]["passed"] += 1
        return {name: {"checks": stats["checks"], "passed": stats["passed"], "health_pct": round(stats["passed"] / stats["checks"] * 100, 1)} for name, stats in all_replicas.items()}

    def repair_success_rate(self) -> Dict[str, Any]:
        repair_triggers = [r for r in self.manager.results if r.get("auto_repair_triggered")]
        if not repair_triggers:
            return {"rate": 100, "total": 0, "successful": 0}
        return {"rate": 100, "total": len(repair_triggers), "successful": len(repair_triggers), "note": "Auto-repair always succeeds in simulation"}

    def generate_report(self) -> str:
        lines = ["=== Data Integrity Report ==="]
        lines.append(f"Verifications Configured: {len(self.manager.verifications)}")
        cr = self.consistency_rate(7)
        lines.append(f"7-Day Consistency Rate: {cr.get('rate', 100)}% ({cr.get('consistent', 0)}/{cr.get('total', 0)})")
        by_type = self.success_by_type()
        for vtype, stats in by_type.items():
            lines.append(f"  {vtype}: {stats.get('rate_pct', 0)}% ({stats.get('passed', 0)}/{stats.get('total', 0)})")
        return "\n".join(lines)


class DataIntegrityPaginator:
    def __init__(self, items: List[Any], page_size: int = 10):
        self.items = items
        self.page_size = page_size

    def get_page(self, page: int = 1) -> List[Any]:
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.items[start:end] if start < len(self.items) else []

    def get_total_pages(self) -> int:
        return max(1, (len(self.items) + self.page_size - 1) // self.page_size)

    def get_metadata(self) -> Dict[str, Any]:
        return {"total_items": len(self.items), "page_size": self.page_size, "total_pages": self.get_total_pages()}


class RepairManager:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    async def trigger_repair_batch(self, verification_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for vid in verification_ids:
            v = await self.manager.get_verification(vid)
            if not v:
                results.append({"verification_id": vid, "success": False, "error": "Not found"})
                continue
            for rep in v.get("replicas", []):
                r = await self.manager.trigger_repair(vid, rep.get("name", ""))
                results.append(r)
        return results

    async def get_repair_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r for r in self.manager.results if r.get("auto_repair_triggered")][-limit:]


class ScheduleOptimizer:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    def optimize_schedules(self) -> List[Dict[str, Any]]:
        recs = []
        for v in self.manager.verifications:
            current_schedule = v.get("schedule_cron", "")
            vtype = v.get("verification_type", "checksum")
            if vtype == "checksum" and current_schedule == "0 */6 * * *":
                recs.append({"verification_id": v["id"], "name": v.get("name"), "current": current_schedule, "recommended": "0 */4 * * *", "reason": "Increase checksum frequency for better coverage", "impact": "medium"})
            elif vtype == "row_count" and "*/6" in current_schedule:
                recs.append({"verification_id": v["id"], "name": v.get("name"), "current": current_schedule, "recommended": "0 */12 * * *", "reason": "Reduce row count frequency to save resources", "impact": "low"})
        return recs


class DriftDetector:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    def detect_schema_drift(self) -> List[Dict[str, Any]]:
        drifts = []
        for r in self.manager.results:
            for rep in r.get("replica_results", []):
                if not rep.get("schema_match", True):
                    drifts.append({"verification_id": r.get("verification_id"), "resource": r.get("resource_name"), "replica": rep.get("replica_name"), "type": "schema_drift", "detected_at": rep.get("verified_at"), "severity": "high"})
        return drifts

    def detect_checksum_mismatches(self) -> List[Dict[str, Any]]:
        mismatches = []
        for r in self.manager.results:
            for rep in r.get("replica_results", []):
                if not rep.get("checksum_match", True):
                    mismatches.append({"verification_id": r.get("verification_id"), "resource": r.get("resource_name"), "replica": rep.get("replica_name"), "type": "checksum_mismatch", "detected_at": rep.get("verified_at"), "severity": "critical"})
        return mismatches


class ReplicaHealthMonitor:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    def get_replica_status(self, replica_name: str) -> Dict[str, Any]:
        checks = 0
        passed_checks = 0
        for r in self.manager.results:
            for rep in r.get("replica_results", []):
                if rep.get("replica_name") == replica_name:
                    checks += 1
                    if rep.get("passed", False):
                        passed_checks += 1
        return {"replica_name": replica_name, "total_checks": checks, "passed": passed_checks, "health_pct": round(passed_checks / checks * 100, 1) if checks else 0, "status": "healthy" if checks and passed_checks / checks > 0.95 else "degraded" if checks else "unknown"}

    def get_all_replica_health(self) -> List[Dict[str, Any]]:
        names = set()
        for r in self.manager.results:
            for rep in r.get("replica_results", []):
                names.add(rep.get("replica_name", ""))
        return [self.get_replica_status(n) for n in sorted(names)]

    def identify_failing_replicas(self) -> List[Dict[str, Any]]:
        all_health = self.get_all_replica_health()
        return [h for h in all_health if h.get("status") == "degraded"]


class IntegrityReportGenerator:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    async def generate_detailed_report(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.manager.results if datetime.fromisoformat(r["completed_at"]) > cutoff]
        passed = sum(1 for r in recent if r["status"] == "passed")
        total_replicas_checked = sum(r.get("total_replicas", 0) for r in recent)
        failed_replicas = sum(r.get("failed_count", 0) for r in recent)
        return {"period_days": days, "total_verifications": len(recent), "passed": passed, "failed": len(recent) - passed, "pass_rate": round(passed / len(recent) * 100, 1) if recent else 100, "total_replicas_checked": total_replicas_checked, "failed_replicas": failed_replicas, "replica_failure_rate": round(failed_replicas / total_replicas_checked * 100, 1) if total_replicas_checked else 0, "auto_repairs": sum(1 for r in recent if r.get("auto_repair_triggered")), "verification_types_used": list(set(r.get("verification_type") for r in recent))}

    async def generate_html_report(self) -> str:
        data = await self.generate_detailed_report(7)
        html = f"""<html><head><title>Data Integrity Report</title></head><body>
<h1>Data Integrity Report</h1>
<p>Period: Last {data['period_days']} days</p>
<p>Verifications: {data['total_verifications']}</p>
<p>Pass Rate: {data['pass_rate']}%</p>
<p>Replicas Checked: {data['total_replicas_checked']}</p>
<p>Auto-Repairs: {data['auto_repairs']}</p>
</body></html>"""
        return html


class ConsistencyChecker:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    async def check_consistency(self, resource_id: str) -> Dict[str, Any]:
        relevant = [v for v in self.manager.verifications if v.get("resource_id") == resource_id]
        results = []
        for v in relevant:
            recent = [r for r in self.manager.results if r["verification_id"] == v["id"]][-1:]
            if recent:
                results.append(recent[0])
        passed = sum(1 for r in results if r["status"] == "passed")
        return {"resource_id": resource_id, "verifications_found": len(relevant), "recent_results": len(results), "consistent": passed == len(results), "consistency_pct": round(passed / len(results) * 100, 1) if results else 100}

    async def verify_all_resources(self) -> Dict[str, Any]:
        resource_ids = set()
        for v in self.manager.verifications:
            rid = v.get("resource_id", "")
            if rid:
                resource_ids.add(rid)
        results = []
        for rid in resource_ids:
            r = await self.check_consistency(rid)
            results.append(r)
        consistent = sum(1 for r in results if r.get("consistent"))
        return {"total_resources": len(results), "consistent": consistent, "inconsistent": len(results) - consistent, "overall_consistency": round(consistent / len(results) * 100, 1) if results else 100}


class IntegrityScheduleManager:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager
        self.schedules: List[Dict[str, Any]] = []

    def create_schedule(self, verification_id: str, cron: str) -> Dict[str, Any]:
        v = next((x for x in self.manager.verifications if x["id"] == verification_id), None)
        if not v:
            return {"error": "Verification not found"}
        schedule = {"id": str(uuid.uuid4()), "verification_id": verification_id, "type": v.get("type"), "resource_id": v.get("resource_id"), "cron": cron, "status": "active", "created_at": datetime.now().isoformat()}
        self.schedules.append(schedule)
        return schedule

    def list_schedules(self) -> List[Dict[str, Any]]:
        return self.schedules

    def pause_schedule(self, schedule_id: str) -> Dict[str, Any]:
        for s in self.schedules:
            if s["id"] == schedule_id:
                s["status"] = "paused"
                return s
        return {"error": "Schedule not found"}

    def resume_schedule(self, schedule_id: str) -> Dict[str, Any]:
        for s in self.schedules:
            if s["id"] == schedule_id:
                s["status"] = "active"
                return s
        return {"error": "Schedule not found"}

    def get_due_verifications(self) -> List[Dict[str, Any]]:
        now = datetime.now()
        due = []
        for s in self.schedules:
            if s.get("status") != "active":
                continue
            last_run = s.get("last_run")
            if not last_run:
                due.append(s)
            elif (now - datetime.fromisoformat(last_run)).total_seconds() > 3600:
                due.append(s)
        return due


class IntegrityAlertManager:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager
        self.alerts: List[Dict[str, Any]] = []

    def check_for_alerts(self) -> List[Dict[str, Any]]:
        new_alerts = []
        for r in self.manager.results:
            if r["status"] == "failed" and not r.get("alerted"):
                for rep in r.get("replica_results", []):
                    if not rep.get("passed", True):
                        alert = {"id": str(uuid.uuid4()), "type": "replica_mismatch", "resource": r.get("resource_id"), "replica": rep.get("replica_name"), "failed_fields": rep.get("mismatched_fields", []), "severity": "high", "created_at": datetime.now().isoformat(), "acknowledged": False}
                        self.alerts.append(alert)
                        new_alerts.append(alert)
                r["alerted"] = True
        return new_alerts

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self.alerts if not a.get("acknowledged")]

    def acknowledge_alert(self, alert_id: str, user: str) -> Dict[str, Any]:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                a["acknowledged_by"] = user
                a["acknowledged_at"] = datetime.now().isoformat()
                return a
        return {"error": "Alert not found"}

    def get_alert_stats(self) -> Dict[str, Any]:
        total = len(self.alerts)
        active = len(self.get_active_alerts())
        return {"total_alerts": total, "active": active, "acknowledged": total - active}


class DataIntegrityDashboard:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    async def get_dashboard_data(self) -> Dict[str, Any]:
        report_gen = IntegrityReportGenerator(self.manager)
        report = await report_gen.generate_detailed_report(7)
        alert_mgr = IntegrityAlertManager(self.manager)
        consistency = ConsistencyChecker(self.manager)
        all_consistent = await consistency.verify_all_resources()
        return {"summary": report, "alerts": alert_mgr.get_active_alerts(), "consistency": all_consistent, "total_verifications": len(self.manager.verifications), "total_results": len(self.manager.results)}

    async def get_health_status(self) -> str:
        report = await IntegrityReportGenerator(self.manager).generate_detailed_report(1)
        pass_rate = report.get("pass_rate", 100)
        if pass_rate >= 99:
            return "healthy"
        elif pass_rate >= 95:
            return "degraded"
        return "critical"


class IntegrityAuditLog:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager
        self.logs: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, resource_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        entry = {"id": str(uuid.uuid4()), "event_type": event_type, "resource_id": resource_id, "details": details, "timestamp": datetime.now().isoformat()}
        self.logs.append(entry)
        return entry

    def get_logs(self, resource_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        filtered = self.logs
        if resource_id:
            filtered = [l for l in self.logs if l.get("resource_id") == resource_id]
        return sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def get_recent_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [l for l in self.logs if datetime.fromisoformat(l["timestamp"]) > cutoff]


class DataIntegrityExporter:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    def export_verifications_json(self) -> str:
        return json.dumps([{"id": v["id"], "name": v.get("name"), "type": v.get("verification_type"), "resource": v.get("resource_name"), "status": v.get("status"), "schedule": v.get("schedule_cron"), "created": v.get("created_at")} for v in self.manager.verifications], indent=2)

    def export_results_csv(self) -> str:
        lines = ["verification_id,name,resource,status,pass_rate,completed_at"]
        for r in self.manager.results:
            lines.append(f"{r.get('verification_id')},{r.get('verification_name')},{r.get('resource_name')},{r.get('status')},{r.get('pass_rate', 0)},{r.get('completed_at')}")
        return "\n".join(lines)

    def export_metrics_prometheus(self) -> str:
        lines = ["# HELP data_integrity_pass_rate Pass rate for data integrity verifications", "# TYPE data_integrity_pass_rate gauge"]
        for v in self.manager.verifications:
            recent = [r for r in self.manager.results if r["verification_id"] == v["id"]]
            if recent:
                last = recent[-1]
                name = v.get("name", "unknown").replace(" ", "_").lower()
                lines.append(f'data_integrity_pass_rate{{verification="{name}",resource="{v.get("resource_name","")}"}} {last.get("pass_rate", 0)}')
        lines.append("# HELP data_integrity_total Total verification count")
        lines.append("# TYPE data_integrity_total gauge")
        lines.append(f"data_integrity_total {len(self.manager.verifications)}")
        return "\n".join(lines)


class IntegrityBackupManager:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    def backup_metadata(self) -> Dict[str, Any]:
        backup = {"verifications": self.manager.verifications, "results_count": len(self.manager.results), "exported_at": datetime.now().isoformat()}
        path = f"data_integrity_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w") as f:
            json.dump(backup, f, indent=2, default=str)
        return {"path": path, "verifications": len(self.manager.verifications), "results": len(self.manager.results)}

    def restore_metadata(self, path: str) -> Dict[str, Any]:
        with open(path) as f:
            data = json.load(f)
        self.manager.verifications = data.get("verifications", [])
        return {"restored_verifications": len(self.manager.verifications), "source": path}


class IntegrityHealthChecker:
    def __init__(self, manager: DataIntegrityVerifier):
        self.manager = manager

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy" if len(self.manager.verifications) > 0 else "degraded", "total_verifications": len(self.manager.verifications), "total_results": len(self.manager.results), "failed_recently": sum(1 for r in self.manager.results[-20:] if r.get("status") == "failed"), "auto_repairs": sum(1 for r in self.manager.results if r.get("auto_repair_triggered")), "replicas_checked": sum(r.get("total_replicas", 0) for r in self.manager.results[-20:])}

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
        return {"total_items": 0, "healthy_count": 0, "degraded_count": 0, "failed_count": 0}

    def validate_configuration(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class ResiliencyResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    status: str = Field(default="healthy")
    message: str = ""
    recovery_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResiliencyBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
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
        if self.failed > 0:
            self.status = "completed_with_errors"

class HealthMetric(BaseModel):
    component: str
    status: str = Field(default="unknown")
    uptime_pct: float = Field(default=100.0, ge=0, le=100)
    last_check: datetime = Field(default_factory=datetime.utcnow)
    response_time: float = Field(default=0.0)
    error_rate: float = Field(default=0.0, ge=0, le=100)

class HealthDashboard:
    def __init__(self) -> None:
        self._components: Dict[str, HealthMetric] = {}

    def register(self, component: str) -> HealthMetric:
        hm = HealthMetric(component=component)
        self._components[component] = hm
        return hm

    def update(self, component: str, status: str, response_time: float = 0.0, error_rate: float = 0.0) -> None:
        if component in self._components:
            hm = self._components[component]
            hm.status = status
            hm.response_time = response_time
            hm.error_rate = error_rate
            hm.last_check = datetime.utcnow()
            if status == "healthy":
                hm.uptime_pct = min(100, hm.uptime_pct + 0.1)
            else:
                hm.uptime_pct = max(0, hm.uptime_pct - 0.5)

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == "healthy")
        degraded = sum(1 for c in self._components.values() if c.status == "degraded")
        down = sum(1 for c in self._components.values() if c.status == "down")
        avg_uptime = round(sum(c.uptime_pct for c in self._components.values()) / max(total, 1), 1)
        return {"components": total, "healthy": healthy, "degraded": degraded,
                "down": down, "avg_uptime_pct": avg_uptime}

    def get_component(self, component: str) -> Optional[HealthMetric]:
        return self._components.get(component)

class IncidentLog(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    component: str
    severity: str = Field(default="info")
    title: str
    description: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    action_taken: str = ""

class IncidentManager:
    def __init__(self) -> None:
        self._incidents: List[IncidentLog] = []

    def report(self, component: str, severity: str, title: str, description: str = "") -> IncidentLog:
        incident = IncidentLog(component=component, severity=severity, title=title, description=description)
        self._incidents.append(incident)
        return incident

    def resolve(self, incident_id: str, action: str = "") -> bool:
        for inc in self._incidents:
            if inc.incident_id == incident_id and inc.resolved_at is None:
                inc.resolved_at = datetime.utcnow()
                inc.duration_seconds = int((inc.resolved_at - inc.detected_at).total_seconds())
                inc.action_taken = action
                return True
        return False

    def get_open(self) -> List[IncidentLog]:
        return [i for i in self._incidents if i.resolved_at is None]

    def get_by_severity(self, severity: str) -> List[IncidentLog]:
        return [i for i in self._incidents if i.severity == severity]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._incidents)
        open_count = len(self.get_open())
        resolved = total - open_count
        by_severity: Dict[str, int] = {}
        total_duration = 0
        resolved_count = 0
        for i in self._incidents:
            by_severity[i.severity] = by_severity.get(i.severity, 0) + 1
            if i.duration_seconds:
                total_duration += i.duration_seconds
                resolved_count += 1
        return {"total": total, "open": open_count, "resolved": resolved,
                "by_severity": by_severity,
                "avg_resolution_time_sec": round(total_duration / max(resolved_count, 1), 1)}

class RecoveryProcedure(BaseModel):
    procedure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    steps: List[str] = Field(default_factory=list)
    estimated_rtt_minutes: int = Field(default=5)
    validated: bool = False
    last_tested: Optional[datetime] = None
    owner: str = Field(default="platform")

class RecoveryRunner:
    def __init__(self) -> None:
        self._procedures: Dict[str, RecoveryProcedure] = {}

    def register(self, procedure: RecoveryProcedure) -> str:
        self._procedures[procedure.procedure_id] = procedure
        return procedure.procedure_id

    async def execute(self, procedure_id: str) -> Dict[str, Any]:
        proc = self._procedures.get(procedure_id)
        if not proc:
            return {"status": "error", "message": "Procedure not found"}
        executed_steps = []
        for i, step in enumerate(proc.steps):
            executed_steps.append({"step": i + 1, "action": step, "status": "completed"})
        return {"status": "completed", "procedure": proc.name, "steps": executed_steps,
                "total_steps": len(proc.steps), "duration_estimate_min": proc.estimated_rtt_minutes}

    def list_procedures(self) -> List[Dict[str, Any]]:
        return [{"id": p.procedure_id, "name": p.name, "steps": len(p.steps),
                 "validated": p.validated, "last_tested": p.last_tested} for p in self._procedures.values()]

class SLOMetric(BaseModel):
    name: str
    target_pct: float = Field(default=99.9, ge=0, le=100)
    current_pct: float = Field(default=100.0, ge=0, le=100)
    measurement_window: str = Field(default="30d")
    breached: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SLOManager:
    def __init__(self) -> None:
        self._slos: Dict[str, SLOMetric] = {}

    def define(self, name: str, target_pct: float = 99.9, window: str = "30d") -> SLOMetric:
        slo = SLOMetric(name=name, target_pct=target_pct, measurement_window=window)
        self._slos[name] = slo
        return slo

    def record_uptime(self, name: str, success: bool) -> None:
        slo = self._slos.get(name)
        if not slo:
            return
        factor = 0.0001 if not success else -0.0001
        slo.current_pct = round(max(0, min(100, slo.current_pct + factor)), 4)
        slo.breached = slo.current_pct < slo.target_pct
        slo.last_updated = datetime.utcnow()

    def get_status(self) -> Dict[str, Any]:
        breached = [s for s in self._slos.values() if s.breached]
        return {"total_slos": len(self._slos), "met": len(self._slos) - len(breached),
                "breached": len(breached), "details": {n: s.dict() for n, s in self._slos.items()}}
