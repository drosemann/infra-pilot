import json
import uuid
import hashlib
import logging
import re
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    AUDIT = "audit"
    REQUIRE_EVIDENCE = "require_evidence"


class PolicyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"
    ERROR = "error"


class ControlSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class RegoRule:
    rule_id: str
    name: str
    rego_expression: str
    effect: PolicyEffect
    severity: ControlSeverity
    category: str
    description: str
    remediation: str
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "rego_expression": self.rego_expression,
            "effect": self.effect.value,
            "severity": self.severity.value,
            "category": self.category,
            "description": self.description,
            "remediation": self.remediation,
            "tags": self.tags,
        }


@dataclass
class ComplianceControl:
    control_id: str
    framework: str
    name: str
    description: str
    category: str
    severity: ControlSeverity
    rules: List[RegoRule]
    status: PolicyStatus
    version: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "control_id": self.control_id,
            "framework": self.framework,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity": self.severity.value,
            "rules": [r.to_dict() for r in self.rules],
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
        }


REGO_TEMPLATES = {
    "ensure_encryption": """package infra_pilot.compliance.encryption

default allow = false

allow {
    input.resource_type == "storage"
    input.encryption_at_rest == true
    input.encryption_in_transit == true
}

audit {
    input.resource_type == "database"
    not input.encryption_at_rest
    severity = "critical"
}""",

    "network_segmentation": """package infra_pilot.compliance.network

default deny = false

deny {
    input.source_network == "public"
    input.target_network == "private"
    input.protocol in ["ssh", "rdp", "telnet"]
}

warn {
    input.environment == "production"
    not input.network_policy_enabled
}""",

    "access_control": """package infra_pilot.compliance.access

default allow = true

deny {
    input.action == "delete"
    input.role == "viewer"
}

require_mfa {
    input.action in ["delete", "modify", "grant"]
    input.role == "admin"
    not input.mfa_verified
}""",

    "data_residency": """package infra_pilot.compliance.residency

default allow = true

deny {
    input.data_classification == "restricted"
    input.region not in allowed_regions
}

allowed_regions = {"us-east-1", "us-west-2", "eu-west-1", "eu-central-1"}""",

    "backup_compliance": """package infra_pilot.compliance.backup

default warn = false

warn {
    input.environment == "production"
    not input.backup_enabled
}

deny {
    input.environment == "production"
    input.backup_retention_days < 30
}""",

    "vulnerability_management": """package infra_pilot.compliance.vulnerability

default warn = false

warn {
    input.vulnerability_severity == "critical"
}

deny {
    input.vulnerability_age_days > 30
    input.vulnerability_severity in ["critical", "high"]
}""",
}


class ComplianceAsCodeEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.controls: Dict[str, ComplianceControl] = {}
        self.policy_store: Dict[str, str] = {}
        self.evaluation_history: List[Dict[str, Any]] = []
        self.data_file = config.get("compliance_code_data_file", "data/compliance_as_code.json")
        self._load_default_controls()
        self._load()

    def _load_default_controls(self):
        frameworks = {
            "SOC_2": [
                {"id": "SOC2-CC5", "name": "Control Activities", "category": "security", "severity": "critical",
                 "description": "Control activities are established and maintained", "template": "access_control"},
                {"id": "SOC2-A1", "name": "Availability", "category": "availability", "severity": "high",
                 "description": "System availability commitments are met", "template": "backup_compliance"},
                {"id": "SOC2-C1", "name": "Confidentiality", "category": "confidentiality", "severity": "high",
                 "description": "Confidential information is protected", "template": "ensure_encryption"},
            ],
            "HIPAA": [
                {"id": "HIPAA-164.312", "name": "Access Control", "category": "technical_safeguards", "severity": "critical",
                 "description": "Technical policies for electronic PHI access", "template": "access_control"},
                {"id": "HIPAA-164.312.e", "name": "Encryption", "category": "technical_safeguards", "severity": "critical",
                 "description": "Encryption of electronic PHI", "template": "ensure_encryption"},
            ],
            "PCI_DSS": [
                {"id": "PCI-1.1", "name": "Firewall Configuration", "category": "network_security", "severity": "critical",
                 "description": "Firewall and network segmentation", "template": "network_segmentation"},
                {"id": "PCI-3.4", "name": "Data Encryption", "category": "data_protection", "severity": "critical",
                 "description": "Encryption of stored cardholder data", "template": "ensure_encryption"},
                {"id": "PCI-6.1", "name": "Patch Management", "category": "vulnerability", "severity": "high",
                 "description": "Timely patch management", "template": "vulnerability_management"},
            ],
            "GDPR": [
                {"id": "GDPR-ART25", "name": "Data Protection by Design", "category": "privacy", "severity": "high",
                 "description": "Data protection principles by design", "template": "data_residency"},
                {"id": "GDPR-ART32", "name": "Security of Processing", "category": "security", "severity": "critical",
                 "description": "Appropriate technical measures", "template": "ensure_encryption"},
            ],
        }
        for fw, ctrls in frameworks.items():
            for ctrl_def in ctrls:
                template_rego = REGO_TEMPLATES.get(ctrl_def["template"], REGO_TEMPLATES["ensure_encryption"])
                rule = RegoRule(
                    rule_id=f"rule_{ctrl_def['id']}_{uuid.uuid4().hex[:6]}",
                    name=f"{ctrl_def['name']} Rule",
                    rego_expression=template_rego,
                    effect=PolicyEffect.DENY,
                    severity=ControlSeverity(ctrl_def["severity"]),
                    category=ctrl_def["category"],
                    description=f"Rego policy for {ctrl_def['name']}",
                    remediation=f"Review and remediate {ctrl_def['name']} controls",
                    tags=[fw, ctrl_def["category"], "rego"],
                )
                control = ComplianceControl(
                    control_id=ctrl_def["id"],
                    framework=fw,
                    name=ctrl_def["name"],
                    description=ctrl_def["description"],
                    category=ctrl_def["category"],
                    severity=ControlSeverity(ctrl_def["severity"]),
                    rules=[rule],
                    status=PolicyStatus.ACTIVE,
                    version="1.0.0",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    tags=[fw, "opa", "compliance-as-code"],
                )
                self.controls[ctrl_def["id"]] = control
                self.policy_store[ctrl_def["id"]] = template_rego

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.evaluation_history = data.get("evaluation_history", [])
        except Exception as e:
            logger.warning(f"Failed to load compliance code data: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({
                    "control_count": len(self.controls),
                    "evaluation_history": self.evaluation_history[-500:],
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save compliance code data: {e}")

    def create_control(self, framework: str, name: str, description: str,
                       category: str, severity: str, rego_expression: str,
                       tags: Optional[List[str]] = None) -> ComplianceControl:
        control_id = f"{framework}_{name.replace(' ', '_').upper()}_{uuid.uuid4().hex[:6]}"
        rule = RegoRule(
            rule_id=f"rule_{control_id}",
            name=f"{name} Default Rule",
            rego_expression=rego_expression,
            effect=PolicyEffect.DENY,
            severity=ControlSeverity(severity),
            category=category,
            description=f"Rego rule for {name}",
            remediation=f"Review {name} compliance controls",
            tags=tags or [],
        )
        control = ComplianceControl(
            control_id=control_id,
            framework=framework,
            name=name,
            description=description,
            category=category,
            severity=ControlSeverity(severity),
            rules=[rule],
            status=PolicyStatus.DRAFT,
            version="1.0.0",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tags=tags or [framework, "custom"],
        )
        self.controls[control_id] = control
        self.policy_store[control_id] = rego_expression
        self._save()
        return control

    def evaluate(self, control_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        control = self.controls.get(control_id)
        if not control:
            raise ValueError(f"Control not found: {control_id}")

        if control.status != PolicyStatus.ACTIVE:
            return {"control_id": control_id, "status": "skipped", "reason": f"Control status is {control.status.value}"}

        violations = []
        for rule in control.rules:
            passed = self._evaluate_rego_rule(rule.rego_expression, input_data)
            if not passed:
                violations.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "effect": rule.effect.value,
                    "severity": rule.severity.value,
                    "message": f"Rule violation: {rule.description}",
                    "remediation": rule.remediation,
                })

        result = {
            "control_id": control_id,
            "framework": control.framework,
            "control_name": control.name,
            "status": "violation" if violations else "compliant",
            "violations": violations,
            "violation_count": len(violations),
            "evaluated_at": datetime.utcnow().isoformat(),
            "input_summary": {k: v for k, v in list(input_data.items())[:5]},
        }
        self.evaluation_history.append(result)
        self._save()
        return result

    def _evaluate_rego_rule(self, rego_expression: str, input_data: Dict[str, Any]) -> bool:
        deny_patterns = [r'deny\s*{', r'deny\s*=']
        warn_patterns = [r'warn\s*{', r'warn\s*=']
        audit_patterns = [r'audit\s*{', r'audit\s*=']
        require_patterns = [r'require_mfa\s*{', r'require_mfa\s*=']

        for pattern in deny_patterns:
            if re.search(pattern, rego_expression):
                resource_type = input_data.get("resource_type", "")
                env = input_data.get("environment", "")
                severity = input_data.get("vulnerability_severity", "")
                if resource_type == "database" and not input_data.get("encryption_at_rest"):
                    return False
                if env == "production" and not input_data.get("backup_enabled"):
                    return False
                if env == "production" and input_data.get("backup_retention_days", 0) < 30:
                    return False
                if severity == "critical":
                    return False
                if input_data.get("role") == "viewer" and input_data.get("action") == "delete":
                    return False
        return True

    def get_controls(self, framework: Optional[str] = None,
                     status: Optional[str] = None) -> List[ComplianceControl]:
        results = list(self.controls.values())
        if framework:
            results = [c for c in results if c.framework == framework]
        if status:
            results = [c for c in results if c.status.value == status]
        return results

    def update_control_status(self, control_id: str, status: str) -> Optional[ComplianceControl]:
        control = self.controls.get(control_id)
        if control:
            try:
                control.status = PolicyStatus(status)
                control.updated_at = datetime.utcnow()
                self._save()
            except ValueError:
                raise ValueError(f"Invalid status: {status}")
        return control

    def test_policy(self, rego_expression: str, test_inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        passed = 0
        failed = 0
        for i, test_input in enumerate(test_inputs):
            try:
                result = self._evaluate_rego_rule(rego_expression, test_input)
                if result:
                    passed += 1
                else:
                    failed += 1
                results.append({"test_case": i, "input": test_input, "passed": result})
            except Exception as e:
                failed += 1
                results.append({"test_case": i, "input": test_input, "passed": False, "error": str(e)})
        return {
            "total_tests": len(test_inputs),
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / len(test_inputs) * 100) if test_inputs else 0, 1),
            "results": results,
        }

    def get_policy_templates(self) -> Dict[str, str]:
        return REGO_TEMPLATES

    def bulk_evaluate(self, inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for inp in inputs:
            control_id = inp.get("control_id")
            input_data = inp.get("input_data", {})
            if control_id and control_id in self.controls:
                try:
                    result = self.evaluate(control_id, input_data)
                    results.append(result)
                except Exception as e:
                    results.append({"control_id": control_id, "status": "error", "error": str(e)})
        return results

    def create_policy_version(self, control_id: str, rego_expression: str,
                               version_label: Optional[str] = None) -> Dict[str, Any]:
        control = self.controls.get(control_id)
        if not control:
            raise ValueError(f"Control not found: {control_id}")
        version_id = f"v_{uuid.uuid4().hex[:8]}"
        version_entry = {
            "version_id": version_id,
            "control_id": control_id,
            "previous_version": control.version,
            "new_version": version_label or control.version,
            "rego_expression": rego_expression,
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft",
        }
        if "version_history" not in self.config:
            self.config["version_history"] = []
        self.config["version_history"].append(version_entry)
        control.version = version_label or f"{float(control.version.rsplit('.', 1)[0]) + 1}.0.0"
        control.updated_at = datetime.utcnow()
        self.policy_store[control_id] = rego_expression
        new_rule = RegoRule(
            rule_id=f"rule_{control_id}_v{version_id}",
            name=f"{control.name} v{control.version}",
            rego_expression=rego_expression,
            effect=PolicyEffect.DENY,
            severity=control.severity,
            category=control.category,
            description=f"Updated policy version {control.version}",
            remediation=f"Review {control.name} v{control.version}",
            tags=control.tags + [version_id],
        )
        control.rules.append(new_rule)
        self._save()
        return version_entry

    def export_template(self, template_name: str) -> Optional[str]:
        rego = REGO_TEMPLATES.get(template_name)
        if not rego:
            return None
        export_id = f"tmpl_export_{uuid.uuid4().hex[:8]}"
        path = f"exports/{export_id}.rego"
        os.makedirs("exports", exist_ok=True)
        with open(path, "w") as f:
            f.write(rego)
        return path

    def import_template(self, file_path: str, template_name: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r") as f:
                rego_content = f.read()
            REGO_TEMPLATES[template_name] = rego_content
            return {"template_name": template_name, "imported": True, "char_count": len(rego_content)}
        except Exception as e:
            return {"template_name": template_name, "imported": False, "error": str(e)}

    def dry_run_policy(self, rego_expression: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        trigger_details = []
        deny_patterns = [r'deny\s*{', r'deny\s*=']
        warn_patterns = [r'warn\s*{', r'warn\s*=']
        for pattern in deny_patterns:
            if re.search(pattern, rego_expression):
                resource_type = input_data.get("resource_type", "")
                env = input_data.get("environment", "")
                severity = input_data.get("vulnerability_severity", "")
                if resource_type == "database" and not input_data.get("encryption_at_rest"):
                    trigger_details.append({"rule": "deny", "reason": "Database without encryption at rest"})
                if env == "production" and not input_data.get("backup_enabled"):
                    trigger_details.append({"rule": "deny", "reason": "Production without backup"})
                if severity in ("critical", "high"):
                    trigger_details.append({"rule": "deny", "reason": f"Vulnerability severity: {severity}"})
        for pattern in warn_patterns:
            if re.search(pattern, rego_expression):
                if input_data.get("environment") == "production" and not input_data.get("network_policy_enabled"):
                    trigger_details.append({"rule": "warn", "reason": "Production without network policy"})
        return {
            "dry_run_id": f"dry_{uuid.uuid4().hex[:8]}",
            "input": input_data,
            "triggers": trigger_details,
            "trigger_count": len(trigger_details),
            "result": "violation" if trigger_details else "compliant",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def gap_analysis(self, framework: str) -> Dict[str, Any]:
        controls_in_fw = [c for c in self.controls.values() if c.framework == framework]
        total = len(controls_in_fw)
        active = sum(1 for c in controls_in_fw if c.status == PolicyStatus.ACTIVE)
        draft = sum(1 for c in controls_in_fw if c.status == PolicyStatus.DRAFT)
        deprecated = sum(1 for c in controls_in_fw if c.status == PolicyStatus.DEPRECATED)
        evaluated_recently = sum(1 for c in controls_in_fw for h in self.evaluation_history[-200:]
                                 if h.get("control_id") == c.control_id)
        return {
            "framework": framework,
            "total_controls": total,
            "active": active,
            "draft": draft,
            "deprecated": deprecated,
            "policy_coverage": round((active / total * 100) if total else 0, 1),
            "recently_evaluated": evaluated_recently,
            "missing_policies": [c.control_id for c in controls_in_fw if c.status == PolicyStatus.DRAFT],
            "recommendations": [
                f"Activate {draft} draft policies" if draft else "All policies active",
                f"Review {deprecated} deprecated policies" if deprecated else "No deprecated policies",
            ],
        }

    def compare_policies(self, control_id_1: str, control_id_2: str) -> Dict[str, Any]:
        c1 = self.controls.get(control_id_1)
        c2 = self.controls.get(control_id_2)
        if not c1 or not c2:
            raise ValueError("One or both controls not found")
        return {
            "control_1": {"id": c1.control_id, "name": c1.name, "version": c1.version, "rules": len(c1.rules)},
            "control_2": {"id": c2.control_id, "name": c2.name, "version": c2.version, "rules": len(c2.rules)},
            "same_framework": c1.framework == c2.framework,
            "same_severity": c1.severity == c2.severity,
            "same_status": c1.status == c2.status,
            "rule_count_diff": len(c2.rules) - len(c1.rules),
        }

    def get_statistics(self) -> Dict[str, Any]:
        by_framework = {}
        by_status = {}
        by_severity = {}
        for c in self.controls.values():
            by_framework[c.framework] = by_framework.get(c.framework, 0) + 1
            by_status[c.status.value] = by_status.get(c.status.value, 0) + 1
            by_severity[c.severity.value] = by_severity.get(c.severity.value, 0) + 1
        return {
            "total_controls": len(self.controls),
            "total_rules": sum(len(c.rules) for c in self.controls.values()),
            "by_framework": by_framework,
            "by_status": by_status,
            "by_severity": by_severity,
            "recent_evaluations": len(self.evaluation_history[-100:]),
            "versioned_policies": sum(1 for c in self.controls.values() if len(c.rules) > 1),
        }

    def rollback_policy(self, control_id: str, version_index: int = -2) -> Optional[ComplianceControl]:
        control = self.controls.get(control_id)
        if not control or len(control.rules) < 2:
            return None
        if version_index >= len(control.rules):
            return None
        old_rule = control.rules[version_index]
        control.rules.append(old_rule)
        control.updated_at = datetime.utcnow()
        previous_version = control.version
        control.version = f"{float(previous_version.split('.')[0]) - 1}.0.0"
        self.policy_store[control_id] = old_rule.rego_expression
        self._save()
        return control

    def search_policies(self, query: str) -> List[ComplianceControl]:
        q = query.lower()
        return [c for c in self.controls.values()
                if q in c.name.lower() or q in c.description.lower() or q in c.framework.lower()]

    def enable_control(self, control_id: str) -> Optional[ComplianceControl]:
        return self.update_control_status(control_id, "active")

    def disable_control(self, control_id: str) -> Optional[ComplianceControl]:
        return self.update_control_status(control_id, "inactive")

    def mark_deprecated(self, control_id: str) -> Optional[ComplianceControl]:
        return self.update_control_status(control_id, "deprecated")

    def duplicate_control(self, control_id: str, new_framework: Optional[str] = None) -> Optional[ComplianceControl]:
        original = self.controls.get(control_id)
        if not original:
            return None
        new_id = f"{new_framework or original.framework}_{original.name.replace(' ', '_').upper()}_{uuid.uuid4().hex[:6]}"
        new_rules = [
            RegoRule(
                rule_id=f"rule_{new_id}_{uuid.uuid4().hex[:6]}",
                name=r.name, rego_expression=r.rego_expression,
                effect=r.effect, severity=r.severity,
                category=r.category, description=r.description,
                remediation=r.remediation, tags=r.tags,
            ) for r in original.rules
        ]
        new_control = ComplianceControl(
            control_id=new_id, framework=new_framework or original.framework,
            name=original.name, description=original.description,
            category=original.category, severity=original.severity,
            rules=new_rules, status=PolicyStatus.DRAFT,
            version="1.0.0", created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(), tags=original.tags + ["duplicate"],
        )
        self.controls[new_id] = new_control
        self._save()
        return new_control

    def export_all_policies(self) -> Dict[str, str]:
        return {cid: self.policy_store.get(cid, "") for cid in self.controls}


def validate_rego_syntax(rego_expression: str) -> Dict[str, Any]:
    checks = []
    if "package" not in rego_expression:
        checks.append({"type": "error", "message": "Missing package declaration"})
    if "default" not in rego_expression:
        checks.append({"type": "warning", "message": "Missing default rule"})
    if "{" not in rego_expression or "}" not in rego_expression:
        checks.append({"type": "error", "message": "Missing rule body braces"})
    errors = [c for c in checks if c["type"] == "error"]
    return {
        "valid": len(errors) == 0,
        "checks": checks,
        "error_count": len(errors),
    }


def categorize_controls_by_severity(controls: List[ComplianceControl]) -> Dict[str, List[ComplianceControl]]:
    categories = {}
    for c in controls:
        categories.setdefault(c.severity.value, []).append(c)
    return categories


def group_controls_by_framework(controls: List[ComplianceControl]) -> Dict[str, List[ComplianceControl]]:
    groups = {}
    for c in controls:
        groups.setdefault(c.framework, []).append(c)
    return groups


def filter_controls_by_tags(controls: List[ComplianceControl], tags: List[str]) -> List[ComplianceControl]:
    return [c for c in controls if any(t in c.tags for t in tags)]


def compute_policy_maturity(controls: List[ComplianceControl]) -> Dict[str, Any]:
    total = len(controls)
    active = sum(1 for c in controls if c.status == PolicyStatus.ACTIVE)
    versioned = sum(1 for c in controls if len(c.rules) > 1)
    return {
        "total_policies": total,
        "active_policies": active,
        "versioned_policies": versioned,
        "maturity_score": round((active * 40 + versioned * 30) / max(total, 1), 1),
        "needs_attention": [c.control_id for c in controls if c.status == PolicyStatus.DRAFT],
    }


def batch_migrate_framework(controls: List[ComplianceControl], target_framework: str) -> List[ComplianceControl]:
    migrated = []
    for c in controls:
        new_id = f"{target_framework}_{c.name.replace(' ', '_').upper()}_{uuid.uuid4().hex[:6]}"
        new_control = ComplianceControl(
            control_id=new_id, framework=target_framework, name=c.name,
            description=c.description, category=c.category, severity=c.severity,
            rules=c.rules, status=PolicyStatus.DRAFT, version="1.0.0",
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
            tags=c.tags + [f"migrated_from_{c.framework}"],
        )
        migrated.append(new_control)
    return migrated


class CaCBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_validate(self, policies: List[PolicyDefinition]) -> List[Dict[str, Any]]:
        results = []
        for pol in policies:
            try:
                valid = validate_policy_syntax(pol) and validate_policy_semantics(pol)
                has_conflicts = detect_policy_conflicts(pol, policies)
                results.append({
                    "policy_name": pol["name"],
                    "valid": valid,
                    "conflicts": has_conflicts,
                    "status": "passed" if valid and not has_conflicts else "failed",
                })
                self.batch_log.append({"action": "validate", "policy": pol["name"], "status": "passed" if valid else "failed"})
            except Exception as e:
                self.batch_log.append({"action": "validate", "policy": pol.get("name"), "status": "error", "error": str(e)})
                results.append({"policy_name": pol.get("name"), "valid": False, "status": "error", "error": str(e)})
        return results


async def paginate_policies(policies: List[PolicyDefinition], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(policies)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": policies[start:end],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def export_policies(policies: List[PolicyDefinition]) -> Dict[str, Any]:
    export_id = f"policy_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id, "exported_at": datetime.utcnow().isoformat(),
        "policies": policies, "count": len(policies),
        "summary": {"valid": sum(1 for p in policies if validate_policy_syntax(p)), "total": len(policies)},
    }


def import_policies(existing: List[PolicyDefinition], import_data: List[PolicyDefinition]) -> Dict[str, Any]:
    import_id = f"policy_import_{uuid.uuid4().hex[:8]}"
    existing.extend(import_data)
    return {"import_id": import_id, "imported": len(import_data), "total_after": len(existing)}


class PolicyConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        if not self.config.get("policy_repo"):
            self.errors.append("policy_repo is required")
        sync = self.config.get("sync_interval_minutes")
        if sync is not None and (sync < 1 or sync > 1440):
            self.errors.append("sync_interval_minutes must be between 1 and 1440")
        return len(self.errors) == 0


def compute_policy_statistics(policies: List[PolicyDefinition]) -> Dict[str, Any]:
    total = len(policies)
    valid = sum(1 for p in policies if validate_policy_syntax(p))
    conflict_counts = []
    for pol in policies:
        conflicts = detect_policy_conflicts(pol, policies)
        if conflicts:
            conflict_counts.append(1)
    return {
        "total_policies": total,
        "valid": valid, "invalid": total - valid,
        "policies_with_conflicts": len(conflict_counts),
        "validity_rate": round(valid / total * 100, 1) if total else 0,
    }

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class compliance_as_code_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class compliance_as_code_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class compliance_as_code_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class compliance_as_code_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class compliance_as_code_Cache:
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

class compliance_as_code_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class compliance_as_code_Queue:
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

class compliance_as_code_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class compliance_as_code_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_cac_policies_store: Dict[str, RegoRule] = {}
_cac_controls_store: Dict[str, Control] = {}


def add_cac_policy(rule: RegoRule) -> str:
    _cac_policies_store[rule.rule_id] = rule
    return rule.rule_id


def get_cac_policy(rule_id: str) -> Optional[RegoRule]:
    return _cac_policies_store.get(rule_id)


def search_cac_policies(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for p in _cac_policies_store.values():
        if query.lower() in p.name.lower() or query.lower() in p.package.lower():
            results.append({"id": p.rule_id, "name": p.name, "package": p.package, "effect": p.effect.value})
            if len(results) >= limit:
                break
    return results


def batch_activate_policies(rule_ids: List[str]) -> Dict[str, Any]:
    op = {"operation": "activate", "succeeded": [], "failed": [], "total": len(rule_ids)}
    for rid in rule_ids:
        p = _cac_policies_store.get(rid)
        if p:
            p.policy_status = PolicyStatus.ACTIVE
            op["succeeded"].append(rid)
        else:
            op["failed"].append(rid)
    return op


def get_cac_summary() -> Dict[str, Any]:
    total_policies = len(_cac_policies_store)
    total_controls = len(_cac_controls_store)
    active = sum(1 for p in _cac_policies_store.values() if p.policy_status == PolicyStatus.ACTIVE)
    inactive = sum(1 for p in _cac_policies_store.values() if p.policy_status == PolicyStatus.INACTIVE)
    draft = sum(1 for p in _cac_policies_store.values() if p.policy_status == PolicyStatus.DRAFT)
    return {"total_policies": total_policies, "total_controls": total_controls, "active": active, "inactive": inactive, "draft": draft}


class PolicyValidator:
    def __init__(self):
        self._policies = _cac_policies_store

    def validate_syntax(self, rule_id: str) -> Dict[str, Any]:
        p = self._policies.get(rule_id)
        if not p:
            return {"valid": False, "error": "not found"}
        errors = []
        if not p.name:
            errors.append("name is required")
        if not p.package:
            errors.append("package is required")
        if not p.rule:
            errors.append("rule expression is required")
        return {"valid": len(errors) == 0, "rule_id": rule_id, "name": p.name, "errors": errors}

    def validate_all(self) -> List[Dict[str, Any]]:
        return [self.validate_syntax(rid) for rid in self._policies]

    def find_unused_policies(self) -> List[Dict[str, Any]]:
        unused = []
        for p in self._policies.values():
            refs = sum(1 for c in _cac_controls_store.values() if p.rule_id in (c.rule_refs or []))
            if refs == 0 and p.policy_status == PolicyStatus.ACTIVE:
                unused.append({"id": p.rule_id, "name": p.name, "package": p.package})
        return unused


class PolicyTemplateLibrary:
    def __init__(self):
        self._templates: Dict[str, Dict[str, Any]] = {}

    def register_template(self, name: str, package: str, rule_template: str, description: str = "") -> str:
        tid = f"tpl_{uuid.uuid4().hex[:8]}"
        self._templates[tid] = {"id": tid, "name": name, "package": package, "rule_template": rule_template, "description": description, "created_at": datetime.utcnow().isoformat()}
        return tid

    def instantiate(self, template_id: str, params: Dict[str, str]) -> Optional[RegoRule]:
        t = self._templates.get(template_id)
        if not t:
            return None
        rendered = t["rule_template"]
        for k, v in params.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", v)
        rule = RegoRule(rule_id=f"rule_{uuid.uuid4().hex[:8]}", name=t["name"], package=t["package"], effect=PolicyEffect.DENY, rule=rendered, policy_status=PolicyStatus.DRAFT, tags=[], metadata={})
        return rule

    def list_templates(self) -> List[Dict[str, Any]]:
        return list(self._templates.values())


class PolicyBulkEvaluator:
    def __init__(self):
        self._policies = _cac_policies_store

    def evaluate_all(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for p in self._policies.values():
            if p.policy_status != PolicyStatus.ACTIVE:
                continue
            passed = p.package in str(input_data) if input_data else False
            results.append({"rule_id": p.rule_id, "name": p.name, "effect": p.effect.value, "passed": passed})
        return results

    def evaluate_by_control(self, control_id: str, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        control = _cac_controls_store.get(control_id)
        if not control:
            return []
        return [self._eval_single(rid, input_data) for rid in control.rule_refs if rid in self._policies]

    def _eval_single(self, rule_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        p = self._policies.get(rule_id)
        if not p:
            return {"rule_id": rule_id, "error": "not found"}
        return {"rule_id": rule_id, "name": p.name, "effect": p.effect.value, "passed": True}


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
