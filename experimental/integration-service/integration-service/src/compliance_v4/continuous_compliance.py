import json
import uuid
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ComplianceControl:
    control_id: str
    framework: str
    category: str
    title: str
    description: str
    severity: str
    status: str
    score: float
    last_checked: datetime
    evidence_refs: List[str]
    remediation_steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "control_id": self.control_id,
            "framework": self.framework,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "score": round(self.score, 2),
            "last_checked": self.last_checked.isoformat(),
            "evidence_refs": self.evidence_refs,
            "remediation_steps": self.remediation_steps,
        }


@dataclass
class FrameworkPosture:
    framework: str
    version: str
    overall_score: float
    control_count: int
    passed: int
    failed: int
    waived: int
    not_applicable: int
    status: str
    last_assessment: datetime
    controls: List[ComplianceControl]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework,
            "version": self.version,
            "overall_score": round(self.overall_score, 1),
            "summary": {
                "control_count": self.control_count,
                "passed": self.passed,
                "failed": self.failed,
                "waived": self.waived,
                "not_applicable": self.not_applicable,
            },
            "status": self.status,
            "last_assessment": self.last_assessment.isoformat(),
            "controls": [c.to_dict() for c in self.controls],
        }


FRAMEWORK_DEFINITIONS = {
    "SOC_2": {
        "version": "2025",
        "categories": ["Security", "Availability", "Processing Integrity", "Confidentiality", "Privacy"],
        "controls": [
            {"id": "SOC2-CC1", "title": "Control Environment", "severity": "critical"},
            {"id": "SOC2-CC2", "title": "Risk Assessment", "severity": "critical"},
            {"id": "SOC2-CC3", "title": "Information & Communication", "severity": "high"},
            {"id": "SOC2-CC4", "title": "Monitoring Activities", "severity": "high"},
            {"id": "SOC2-CC5", "title": "Control Activities", "severity": "critical"},
            {"id": "SOC2-A1", "title": "Availability Commitments", "severity": "high"},
            {"id": "SOC2-C1", "title": "Confidentiality Commitments", "severity": "high"},
            {"id": "SOC2-P1", "title": "Processing Integrity Commitments", "severity": "medium"},
            {"id": "SOC2-PI1", "title": "Privacy Commitments", "severity": "high"},
        ],
    },
    "HIPAA": {
        "version": "2025",
        "categories": ["Administrative Safeguards", "Physical Safeguards", "Technical Safeguards", "Organizational Requirements"],
        "controls": [
            {"id": "HIPAA-164.308", "title": "Security Management Process", "severity": "critical"},
            {"id": "HIPAA-164.310", "title": "Facility Access Controls", "severity": "high"},
            {"id": "HIPAA-164.312", "title": "Access Control", "severity": "critical"},
            {"id": "HIPAA-164.314", "title": "Business Associate Contracts", "severity": "high"},
            {"id": "HIPAA-164.316", "title": "Policies & Procedures", "severity": "medium"},
        ],
    },
    "PCI_DSS": {
        "version": "4.0",
        "categories": ["Build & Maintain Secure Network", "Protect Cardholder Data", "Vulnerability Management",
                        "Access Control", "Network Monitoring", "Information Security Policy"],
        "controls": [
            {"id": "PCI-1.1", "title": "Firewall Configuration", "severity": "critical"},
            {"id": "PCI-3.1", "title": "Data at Rest Protection", "severity": "critical"},
            {"id": "PCI-6.1", "title": "Patch Management", "severity": "high"},
            {"id": "PCI-8.1", "title": "Access Control", "severity": "critical"},
            {"id": "PCI-10.1", "title": "Logging & Monitoring", "severity": "high"},
            {"id": "PCI-12.1", "title": "Security Policy", "severity": "medium"},
        ],
    },
    "ISO_27001": {
        "version": "2022",
        "categories": ["Information Security Policies", "Asset Management", "Access Control", "Cryptography",
                        "Physical Security", "Operations Security", "Communications Security"],
        "controls": [
            {"id": "ISO-5.1", "title": "Information Security Policy", "severity": "critical"},
            {"id": "ISO-8.1", "title": "Asset Inventory", "severity": "high"},
            {"id": "ISO-9.1", "title": "Access Control Policy", "severity": "critical"},
            {"id": "ISO-10.1", "title": "Cryptographic Controls", "severity": "high"},
            {"id": "ISO-11.1", "title": "Physical Security Perimeter", "severity": "medium"},
            {"id": "ISO-12.1", "title": "Operational Procedures", "severity": "high"},
            {"id": "ISO-13.1", "title": "Network Security", "severity": "critical"},
        ],
    },
    "FEDRAMP": {
        "version": "Rev 5",
        "categories": ["Access Control", "Audit & Accountability", "Configuration Management",
                        "Identification & Authentication", "Incident Response", "System & Communications Protection"],
        "controls": [
            {"id": "FEDRAMP-AC-1", "title": "Access Control Policy", "severity": "critical"},
            {"id": "FEDRAMP-AU-2", "title": "Audit Events", "severity": "high"},
            {"id": "FEDRAMP-CM-2", "title": "Baseline Configuration", "severity": "high"},
            {"id": "FEDRAMP-IA-2", "title": "Identification & Authentication", "severity": "critical"},
            {"id": "FEDRAMP-IR-4", "title": "Incident Handling", "severity": "high"},
            {"id": "FEDRAMP-SC-7", "title": "Boundary Protection", "severity": "critical"},
        ],
    },
    "GDPR": {
        "version": "2018",
        "categories": ["Data Processing Principles", "Data Subject Rights", "Data Protection by Design",
                        "Data Breach Notification", "Data Transfers", "Accountability & Governance"],
        "controls": [
            {"id": "GDPR-ART5", "title": "Processing Principles", "severity": "critical"},
            {"id": "GDPR-ART15", "title": "Right of Access", "severity": "high"},
            {"id": "GDPR-ART25", "title": "Data Protection by Design", "severity": "high"},
            {"id": "GDPR-ART33", "title": "Breach Notification", "severity": "critical"},
            {"id": "GDPR-ART44", "title": "Data Transfer Safeguards", "severity": "critical"},
        ],
    },
}


class ContinuousComplianceMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.frameworks = FRAMEWORK_DEFINITIONS
        self.postures: Dict[str, FrameworkPosture] = {}
        self.assessment_history: List[Dict[str, Any]] = []
        self.alert_threshold = config.get("compliance_alert_threshold", 0.7)
        self.scan_interval = config.get("compliance_scan_interval", 300)
        self.data_file = config.get("compliance_data_file", "data/continuous_compliance.json")
        self._running = False
        self._load()

    def _load(self):
        import os
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.postures = data.get("postures", {})
                    self.assessment_history = data.get("history", [])
        except Exception as e:
            logger.warning(f"Failed to load compliance data: {e}")

    def _save(self):
        import os
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({
                    "postures": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.postures.items()},
                    "history": self.assessment_history[-1000:],
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save compliance data: {e}")

    def _simulate_control_evaluation(self, control_def: Dict[str, Any]) -> Tuple[str, float, List[str]]:
        import random
        base_score = random.uniform(0.6, 1.0)
        severity_map = {"critical": 0.85, "high": 0.75, "medium": 0.65, "low": 0.55}
        threshold = severity_map.get(control_def.get("severity", "medium"), 0.7)
        passed = base_score >= threshold
        status = "passed" if passed else "failed"
        steps = [
            f"Review {control_def['title']} configuration",
            f"Verify evidence for {control_def['id']}",
            f"Update control documentation",
        ]
        if not passed:
            steps.append(f"Implement remediation for {control_def['id']}")
        return status, base_score, steps

    def assess_framework(self, framework: str) -> FrameworkPosture:
        fw_def = self.frameworks.get(framework)
        if not fw_def:
            raise ValueError(f"Unknown framework: {framework}")

        controls_list = []
        passed = failed = waived = na = 0

        for ctrl_def in fw_def["controls"]:
            status, score, steps = self._simulate_control_evaluation(ctrl_def)
            control = ComplianceControl(
                control_id=ctrl_def["id"],
                framework=framework,
                category=ctrl_def.get("severity", "medium"),
                title=ctrl_def["title"],
                description=f"Control {ctrl_def['id']} - {ctrl_def['title']}",
                severity=ctrl_def.get("severity", "medium"),
                status=status,
                score=score,
                last_checked=datetime.utcnow(),
                evidence_refs=[f"ev_{uuid.uuid4().hex[:8]}"],
                remediation_steps=steps,
            )
            controls_list.append(control)
            if status == "passed":
                passed += 1
            elif status == "failed":
                failed += 1
            elif status == "waived":
                waived += 1
            else:
                na += 1

        total = len(controls_list)
        overall_score = (passed / total * 100) if total > 0 else 0.0
        posture = FrameworkPosture(
            framework=framework,
            version=fw_def["version"],
            overall_score=overall_score,
            control_count=total,
            passed=passed,
            failed=failed,
            waived=waived,
            not_applicable=na,
            status="compliant" if overall_score >= 80 else "non_compliant",
            last_assessment=datetime.utcnow(),
            controls=controls_list,
        )
        self.postures[framework] = posture
        self.assessment_history.append({
            "framework": framework,
            "score": overall_score,
            "timestamp": datetime.utcnow().isoformat(),
            "status": posture.status,
        })
        self._save()
        return posture

    def assess_all_frameworks(self) -> Dict[str, FrameworkPosture]:
        results = {}
        for fw in self.frameworks:
            try:
                results[fw] = self.assess_framework(fw)
            except Exception as e:
                logger.error(f"Failed to assess {fw}: {e}")
        return results

    def get_posture(self, framework: Optional[str] = None) -> Any:
        if framework:
            return self.postures.get(framework)
        return self.postures

    def get_summary(self) -> Dict[str, Any]:
        total_controls = sum(p.control_count for p in self.postures.values())
        total_passed = sum(p.passed for p in self.postures.values())
        total_failed = sum(p.failed for p in self.postures.values())
        compliant_frameworks = sum(1 for p in self.postures.values() if p.status == "compliant")
        return {
            "frameworks_assessed": len(self.postures),
            "compliant_frameworks": compliant_frameworks,
            "total_controls": total_controls,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_compliance_rate": round((total_passed / total_controls * 100) if total_controls else 0, 1),
            "last_assessment": max((p.last_assessment for p in self.postures.values()), default=datetime.utcnow()).isoformat(),
            "status": "compliant" if compliant_frameworks == len(self.postures) else "attention_needed",
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        for fw_name, posture in self.postures.items():
            if posture.overall_score < self.alert_threshold * 100:
                alerts.append({
                    "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                    "framework": fw_name,
                    "severity": "critical" if posture.overall_score < 50 else "high",
                    "message": f"{fw_name} compliance score dropped to {posture.overall_score:.1f}%",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "open",
                })
            for control in posture.controls:
                if control.status == "failed" and control.severity == "critical":
                    alerts.append({
                        "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                        "framework": fw_name,
                        "control_id": control.control_id,
                        "severity": "critical",
                        "message": f"Critical control {control.control_id} failed: {control.title}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "open",
                    })
        return alerts

    def get_trend(self, framework: str, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            h for h in self.assessment_history
            if h["framework"] == framework and datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]

    async def start_continuous_monitoring(self):
        self._running = True
        logger.info("Starting continuous compliance monitoring")
        while self._running:
            try:
                self.assess_all_frameworks()
                alerts = self.get_alerts()
                if alerts:
                    logger.warning(f"Compliance alerts: {len(alerts)} open issues")
            except Exception as e:
                logger.error(f"Compliance monitoring cycle failed: {e}")
            await asyncio.sleep(self.scan_interval)

    async def stop_continuous_monitoring(self):
        self._running = False
        logger.info("Stopped continuous compliance monitoring")

    def detect_drift(self, framework: str) -> List[Dict[str, Any]]:
        posture = self.postures.get(framework)
        if not posture:
            return []
        drift_items = []
        for control in posture.controls:
            prev_entries = [h for h in self.assessment_history if h["framework"] == framework and h.get("control_id") == control.control_id]
            if prev_entries:
                prev_score = prev_entries[-1].get("score", control.score)
                delta = control.score - prev_score
                if abs(delta) > 0.1:
                    drift_items.append({
                        "control_id": control.control_id,
                        "title": control.title,
                        "previous_score": round(prev_score, 2),
                        "current_score": round(control.score, 2),
                        "delta": round(delta, 2),
                        "drift_type": "improvement" if delta > 0 else "regression",
                        "detected_at": datetime.utcnow().isoformat(),
                    })
        return drift_items

    def compare_frameworks(self) -> Dict[str, Any]:
        scores = {fw: p.overall_score for fw, p in self.postures.items()}
        return {
            "comparison": scores,
            "highest": max(scores, key=scores.get) if scores else None,
            "lowest": min(scores, key=scores.get) if scores else None,
            "average": round(sum(scores.values()) / len(scores), 1) if scores else 0,
            "variance": round(max(scores.values()) - min(scores.values()), 1) if scores and len(scores) > 1 else 0,
        }

    def generate_report(self, framework: str, format: str = "json") -> Dict[str, Any]:
        posture = self.postures.get(framework)
        if not posture:
            return {"error": f"No posture for {framework}"}
        return {
            "report_id": f"rpt_{uuid.uuid4().hex[:12]}",
            "framework": framework,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_score": posture.overall_score,
            "status": posture.status,
            "control_summary": {
                "total": posture.control_count,
                "passed": posture.passed,
                "failed": posture.failed,
                "waived": posture.waived,
                "not_applicable": posture.not_applicable,
            },
            "failed_controls": [c.to_dict() for c in posture.controls if c.status == "failed"],
            "remediation_priority": sorted(
                [c.to_dict() for c in posture.controls if c.status == "failed"],
                key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity"), 99),
            ),
            "history": self.get_trend(framework, days=90),
        }

    def assess_batch(self, frameworks: List[str]) -> Dict[str, FrameworkPosture]:
        results = {}
        for fw in frameworks:
            if fw in self.frameworks:
                results[fw] = self.assess_framework(fw)
        return results

    def schedule_scans(self, interval_minutes: int = 60) -> Dict[str, Any]:
        schedule_id = f"scan_sched_{uuid.uuid4().hex[:8]}"
        self.scan_interval = interval_minutes * 60
        return {
            "schedule_id": schedule_id,
            "interval_minutes": interval_minutes,
            "frameworks": list(self.frameworks.keys()),
            "next_scan": (datetime.utcnow() + timedelta(seconds=self.scan_interval)).isoformat(),
            "status": "active",
        }

    def get_remediation_plan(self, framework: str) -> List[Dict[str, Any]]:
        posture = self.postures.get(framework)
        if not posture:
            return []
        plan = []
        for c in sorted(posture.controls, key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x.severity, 99)):
            if c.status == "failed":
                plan.append({
                    "control_id": c.control_id,
                    "title": c.title,
                    "severity": c.severity,
                    "current_score": c.score,
                    "steps": c.remediation_steps,
                    "estimated_effort": "high" if c.severity == "critical" else "medium" if c.severity == "high" else "low",
                })
        return plan

    def get_compliance_trend(self, days: int = 90) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        relevant = [h for h in self.assessment_history if datetime.fromisoformat(h["timestamp"]) >= cutoff]
        by_date = {}
        for h in relevant:
            date_key = h["timestamp"][:10]
            if date_key not in by_date:
                by_date[date_key] = {}
            by_date[date_key][h["framework"]] = h["score"]
        return {
            "period_days": days,
            "daily_scores": [{"date": d, **scores} for d, scores in sorted(by_date.items())],
            "overall_trend": "improving" if len(by_date) > 1 and list(by_date.values())[-1].get("average", 0) > list(by_date.values())[0].get("average", 0) else "declining",
        }

    def set_notification_hook(self, hook_url: str, events: List[str]) -> Dict[str, Any]:
        hook_id = f"hook_{uuid.uuid4().hex[:8]}"
        logger.info(f"Registered notification hook {hook_id} for events: {events}")
        return {"hook_id": hook_id, "url": hook_url, "events": events, "status": "active"}

    def get_recent_assessments(self, count: int = 10) -> List[Dict[str, Any]]:
        return sorted(self.assessment_history, key=lambda h: h["timestamp"], reverse=True)[:count]

    def get_framework_summary(self, framework: str) -> Dict[str, Any]:
        posture = self.postures.get(framework)
        if not posture:
            return {"error": f"No posture for {framework}"}
        return {
            "framework": framework,
            "score": posture.overall_score,
            "status": posture.status,
            "controls_passed": posture.passed,
            "controls_failed": posture.failed,
            "last_assessment": posture.last_assessment.isoformat(),
            "total_controls": posture.control_count,
        }

    def find_weakest_controls(self, framework: str, limit: int = 5) -> List[ComplianceControl]:
        posture = self.postures.get(framework)
        if not posture:
            return []
        failed = [c for c in posture.controls if c.status == "failed"]
        return sorted(failed, key=lambda c: c.score)[:limit]

    def bulk_remediate(self, control_ids: List[str], framework: str) -> Dict[str, Any]:
        results = {}
        for cid in control_ids:
            posture = self.postures.get(framework)
            if not posture:
                results[cid] = {"error": "Framework not found"}
                continue
            control = next((c for c in posture.controls if c.control_id == cid), None)
            if not control:
                results[cid] = {"error": "Control not found"}
                continue
            control.status = "passed"
            control.score = 1.0
            posture.passed += 1
            posture.failed -= 1
            results[cid] = {"status": "remediated", "new_score": 1.0}
        if results:
            self._save()
        return results

    def export_compliance_data(self, framework: Optional[str] = None) -> Dict[str, Any]:
        if framework:
            posture = self.postures.get(framework)
            return {"framework": framework, "data": posture.to_dict() if posture else None}
        return {"frameworks": {k: v.to_dict() for k, v in self.postures.items()}}


class FrameworkComplianceCalculator:
    def __init__(self, postures: Dict[str, FrameworkPosture]):
        self.postures = postures

    def overall_score(self) -> float:
        scores = [p.overall_score for p in self.postures.values()]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    def compliant_percentage(self) -> float:
        compliant = sum(1 for p in self.postures.values() if p.status == "compliant")
        total = len(self.postures)
        return round(compliant / total * 100, 1) if total else 0.0

    def total_findings(self) -> Dict[str, int]:
        return {
            "passed": sum(p.passed for p in self.postures.values()),
            "failed": sum(p.failed for p in self.postures.values()),
            "waived": sum(p.waived for p in self.postures.values()),
        }

    def framework_ranking(self) -> List[Dict[str, Any]]:
        ranked = sorted(self.postures.values(), key=lambda p: p.overall_score, reverse=True)
        return [
            {"framework": p.framework, "score": p.overall_score, "status": p.status}
            for p in ranked
        ]


def compute_trend_analysis(history: List[Dict[str, Any]], framework: str) -> Dict[str, Any]:
    fw_history = [h for h in history if h["framework"] == framework]
    if len(fw_history) < 2:
        return {"framework": framework, "trend": "insufficient_data"}
    scores = [h["score"] for h in sorted(fw_history, key=lambda x: x["timestamp"])]
    first, last = scores[0], scores[-1]
    return {
        "framework": framework,
        "first_score": first,
        "last_score": last,
        "delta": round(last - first, 1),
        "trend": "improving" if last > first else "declining" if last < first else "stable",
        "data_points": len(scores),
    }


def merge_postures(postures_list: List[FrameworkPosture]) -> FrameworkPosture:
    if not postures_list:
        raise ValueError("No postures to merge")
    base = postures_list[0]
    for p in postures_list[1:]:
        base.passed += p.passed
        base.failed += p.failed
        base.waived += p.waived
        base.not_applicable += p.not_applicable
        base.control_count += p.control_count
        base.controls.extend(p.controls)
    total = base.passed + base.failed + base.waived + base.not_applicable
    base.overall_score = round(base.passed / total * 100, 1) if total else 0.0
    base.status = "compliant" if base.overall_score >= 80 else "non_compliant"
    return base


def filter_frameworks_by_score(postures: Dict[str, FrameworkPosture], min_score: float) -> List[str]:
    return [fw for fw, p in postures.items() if p.overall_score >= min_score]


def format_compliance_summary_text(posture: FrameworkPosture) -> str:
    lines = [
        f"Framework: {posture.framework}",
        f"Overall Score: {posture.overall_score:.1f}%",
        f"Status: {posture.status}",
        f"Controls: {posture.passed} passed / {posture.failed} failed / {posture.waived} waived",
        f"Last Assessed: {posture.last_assessment.isoformat()}",
    ]
    return "\n".join(lines)


def categorize_controls_by_status(controls: List[ComplianceControl]) -> Dict[str, List[ComplianceControl]]:
    categories = {}
    for c in controls:
        categories.setdefault(c.status, []).append(c)
    return categories


def build_scorecard(posture: FrameworkPosture) -> Dict[str, Any]:
    return {
        "framework": posture.framework,
        "score": posture.overall_score,
        "grade": "A" if posture.overall_score >= 90 else "B" if posture.overall_score >= 80 else "C" if posture.overall_score >= 70 else "D" if posture.overall_score >= 60 else "F",
        "controls": {
            "total": posture.control_count,
            "passed": posture.passed,
            "failed": posture.failed,
        },
        "remediation_priority": "high" if posture.failed > 0 else "low",
    }


class ComplianceBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_assess(self, engine: ContinuousComplianceEngine, frameworks: List[str]) -> Dict[str, Any]:
        results = {}
        for fw in frameworks:
            try:
                posture = engine.assess_framework(fw)
                results[fw] = {"score": posture.overall_score, "status": posture.status, "controls": posture.control_count}
                self.batch_log.append({"action": "assess", "framework": fw, "status": "success"})
            except Exception as e:
                results[fw] = {"error": str(e)}
                self.batch_log.append({"action": "assess", "framework": fw, "status": "error", "error": str(e)})
        return results


async def paginate_assessments(history: List[Dict[str, Any]], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(history)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": history[start:end],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def export_compliance_snapshot(postures: Dict[str, FrameworkPosture]) -> Dict[str, Any]:
    export_id = f"comp_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id, "exported_at": datetime.utcnow().isoformat(),
        "frameworks": {fw: p.to_dict() for fw, p in postures.items()},
        "summary": {"total_frameworks": len(postures)},
    }


def import_compliance_snapshot(engine: ContinuousComplianceEngine, import_data: Dict[str, Any]) -> Dict[str, Any]:
    import_id = f"comp_import_{uuid.uuid4().hex[:8]}"
    imported = 0
    for fw, pdata in import_data.get("frameworks", {}).items():
        if fw in engine.frameworks:
            engine.postures[fw] = FrameworkPosture(**pdata)
            imported += 1
    return {"import_id": import_id, "imported": imported}


class ComplianceConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        if not self.config.get("compliance_data_file"):
            self.errors.append("compliance_data_file is required")
        threshold = self.config.get("compliance_alert_threshold")
        if threshold is not None and not (0 < threshold <= 1):
            self.errors.append("compliance_alert_threshold must be between 0 and 1")
        return len(self.errors) == 0


def compute_compliance_statistics(postures: Dict[str, FrameworkPosture]) -> Dict[str, Any]:
    scores = [p.overall_score for p in postures.values()]
    compliant = sum(1 for p in postures.values() if p.status == "compliant")
    total_failed = sum(p.failed for p in postures.values())
    return {
        "total_frameworks": len(postures), "compliant": compliant,
        "non_compliant": len(postures) - compliant,
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "min_score": round(min(scores), 1) if scores else 0,
        "max_score": round(max(scores), 1) if scores else 0,
        "total_failed_controls": total_failed,
    }

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class continuous_compliance_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class continuous_compliance_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class continuous_compliance_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class continuous_compliance_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class continuous_compliance_Cache:
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

class continuous_compliance_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class continuous_compliance_Queue:
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

class continuous_compliance_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class continuous_compliance_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_cc_controls_store: Dict[str, ComplianceControl] = {}
_cc_scans_store: Dict[str, ComplianceScan] = {}


def add_cc_control(control: ComplianceControl) -> str:
    _cc_controls_store[control.control_id] = control
    return control.control_id


def get_cc_control(control_id: str) -> Optional[ComplianceControl]:
    return _cc_controls_store.get(control_id)


def search_cc_controls(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for c in _cc_controls_store.values():
        if query.lower() in c.title.lower() or query.lower() in c.framework.lower():
            results.append({"id": c.control_id, "title": c.title, "framework": c.framework, "status": c.status, "score": c.score})
            if len(results) >= limit:
                break
    return results


def batch_remediate_controls(control_ids: List[str], remediation_notes: str = "") -> Dict[str, Any]:
    op = {"operation": "remediate", "succeeded": [], "failed": [], "total": len(control_ids)}
    for cid in control_ids:
        c = _cc_controls_store.get(cid)
        if c:
            c.status = "remediated"
            c.remediation_steps.append(remediation_notes)
            op["succeeded"].append(cid)
        else:
            op["failed"].append(cid)
    return op


def get_cc_summary() -> Dict[str, Any]:
    total = len(_cc_controls_store)
    compliant = sum(1 for c in _cc_controls_store.values() if c.status == "compliant")
    non_compliant = sum(1 for c in _cc_controls_store.values() if c.status == "non_compliant")
    remediated = sum(1 for c in _cc_controls_store.values() if c.status == "remediated")
    not_evaluated = sum(1 for c in _cc_controls_store.values() if c.status == "not_evaluated")
    avg_score = round(sum(c.score for c in _cc_controls_store.values()) / max(total, 1), 2)
    return {"total": total, "compliant": compliant, "non_compliant": non_compliant, "remediated": remediated, "not_evaluated": not_evaluated, "avg_score": avg_score}


class ComplianceTrendAnalyzer:
    def __init__(self):
        self._controls = _cc_controls_store
        self._history: List[Dict[str, Any]] = []

    def snapshot(self) -> Dict[str, Any]:
        snap = {
            "timestamp": datetime.utcnow().isoformat(),
            "total": len(self._controls),
            "compliant": sum(1 for c in self._controls.values() if c.status == "compliant"),
            "non_compliant": sum(1 for c in self._controls.values() if c.status == "non_compliant"),
            "avg_score": round(sum(c.score for c in self._controls.values()) / max(len(self._controls), 1), 2),
        }
        self._history.append(snap)
        return snap

    def get_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [h for h in self._history if datetime.fromisoformat(h["timestamp"]) >= cutoff]

    def get_improvement_rate(self, days: int = 30) -> float:
        recent = self.get_trend(days)
        if len(recent) < 2:
            return 0.0
        first, last = recent[0]["avg_score"], recent[-1]["avg_score"]
        return round((last - first) / max(first, 0.01) * 100, 2)


class ContinuousComplianceNotifier:
    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []

    def check_thresholds(self, threshold: float = 80.0) -> List[Dict[str, Any]]:
        alerts = []
        for c in _cc_controls_store.values():
            if c.score < threshold and c.status == "non_compliant":
                alert = {"control_id": c.control_id, "framework": c.framework, "score": c.score, "threshold": threshold, "severity": "critical" if c.score < 50 else "high", "detected_at": datetime.utcnow().isoformat(), "acknowledged": False}
                self._alerts.append(alert)
                alerts.append(alert)
        return alerts

    def acknowledge_alert(self, control_id: str) -> bool:
        for a in self._alerts:
            if a["control_id"] == control_id and not a["acknowledged"]:
                a["acknowledged"] = True
                a["acknowledged_at"] = datetime.utcnow().isoformat()
                return True
        return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self._alerts if not a["acknowledged"]]


class ComplianceFrameworkMapper:
    def __init__(self):
        self._controls = _cc_controls_store

    def get_frameworks(self) -> List[str]:
        return list(set(c.framework for c in self._controls.values()))

    def get_controls_by_framework(self, framework: str) -> List[Dict[str, Any]]:
        return [{"id": c.control_id, "title": c.title, "severity": c.severity, "status": c.status, "score": c.score} for c in self._controls.values() if c.framework == framework]

    def get_worst_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        sorted_controls = sorted(self._controls.values(), key=lambda c: c.score)[:limit]
        return [{"id": c.control_id, "title": c.title, "framework": c.framework, "score": c.score, "severity": c.severity} for c in sorted_controls]

    def get_best_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        sorted_controls = sorted(self._controls.values(), key=lambda c: c.score, reverse=True)[:limit]
        return [{"id": c.control_id, "title": c.title, "framework": c.framework, "score": c.score, "severity": c.severity} for c in sorted_controls]


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
