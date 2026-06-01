import json
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Vendor:
    vendor_id: str
    name: str
    website: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    category: str
    risk_tier: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "name": self.name,
            "website": self.website,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "category": self.category,
            "risk_tier": self.risk_tier,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Assessment:
    assessment_id: str
    vendor_id: str
    template_type: str
    status: str
    score: Optional[float]
    responses: Dict[str, Any]
    findings: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    assessor: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "vendor_id": self.vendor_id,
            "template_type": self.template_type,
            "status": self.status,
            "score": round(self.score, 1) if self.score else None,
            "findings_count": len(self.findings),
            "critical_findings": sum(1 for f in self.findings if f.get("severity") == "critical"),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assessor": self.assessor,
        }


SIG_QUESTIONS = {
    "security": {
        "domains": [
            {
                "name": "Access Control",
                "questions": [
                    {"id": "AC-1", "question": "Do you have an access control policy?", "weight": 3},
                    {"id": "AC-2", "question": "Is multi-factor authentication enforced?", "weight": 4},
                    {"id": "AC-3", "question": "Are access reviews performed quarterly?", "weight": 3},
                    {"id": "AC-4", "question": "Is least privilege principle enforced?", "weight": 3},
                    {"id": "AC-5", "question": "Are terminated users' access removed within 24 hours?", "weight": 4},
                ],
            },
            {
                "name": "Encryption",
                "questions": [
                    {"id": "EN-1", "question": "Is data encrypted at rest (AES-256)?", "weight": 5},
                    {"id": "EN-2", "question": "Is data encrypted in transit (TLS 1.2+)?", "weight": 5},
                    {"id": "EN-3", "question": "Are encryption keys managed via HSM?", "weight": 4},
                    {"id": "EN-4", "question": "Is key rotation performed annually?", "weight": 3},
                ],
            },
            {
                "name": "Incident Response",
                "questions": [
                    {"id": "IR-1", "question": "Do you have an incident response plan?", "weight": 5},
                    {"id": "IR-2", "question": "Is IR tested at least annually?", "weight": 4},
                    {"id": "IR-3", "question": "Do you have a 24/7 security operations center?", "weight": 4},
                    {"id": "IR-4", "question": "Is there a defined breach notification process?", "weight": 5},
                    {"id": "IR-5", "question": "Is forensic capability available?", "weight": 3},
                ],
            },
            {
                "name": "Vulnerability Management",
                "questions": [
                    {"id": "VM-1", "question": "Do you perform regular vulnerability scans?", "weight": 4},
                    {"id": "VM-2", "question": "Are critical vulnerabilities patched within 48 hours?", "weight": 5},
                    {"id": "VM-3", "question": "Do you perform penetration testing annually?", "weight": 4},
                    {"id": "VM-4", "question": "Is there a bug bounty program?", "weight": 2},
                ],
            },
            {
                "name": "Data Protection",
                "questions": [
                    {"id": "DP-1", "question": "Is data classified by sensitivity?", "weight": 3},
                    {"id": "DP-2", "question": "Are backup and restore procedures tested?", "weight": 4},
                    {"id": "DP-3", "question": "Is data retention policy defined?", "weight": 3},
                    {"id": "DP-4", "question": "Is data securely destroyed at end of life?", "weight": 3},
                ],
            },
        ],
    },
    "privacy": {
        "domains": [
            {
                "name": "Data Collection",
                "questions": [
                    {"id": "DC-1", "question": "Do you have a privacy policy?", "weight": 3},
                    {"id": "DC-2", "question": "Is consent obtained for data collection?", "weight": 4},
                    {"id": "DC-3", "question": "Is data minimization practiced?", "weight": 3},
                ],
            },
            {
                "name": "GDPR Compliance",
                "questions": [
                    {"id": "GD-1", "question": "Is a DPO appointed?", "weight": 4},
                    {"id": "GD-2", "question": "Is right to erasure supported?", "weight": 4},
                    {"id": "GD-3", "question": "Is data portability supported?", "weight": 3},
                    {"id": "GD-4", "question": "Are DPAs executed with subprocessors?", "weight": 4},
                ],
            },
        ],
    },
    "compliance": {
        "domains": [
            {
                "name": "Certifications",
                "questions": [
                    {"id": "CE-1", "question": "Is SOC 2 Type II report available?", "weight": 5},
                    {"id": "CE-2", "question": "Is ISO 27001 certified?", "weight": 5},
                    {"id": "CE-3", "question": "Is PCI DSS compliant?", "weight": 5},
                    {"id": "CE-4", "question": "Is HIPAA compliant?", "weight": 4},
                    {"id": "CE-5", "question": "Are FedRAMP authorized?", "weight": 3},
                ],
            },
        ],
    },
    "business_continuity": {
        "domains": [
            {
                "name": "BCP/DR",
                "questions": [
                    {"id": "BC-1", "question": "Is there a business continuity plan?", "weight": 5},
                    {"id": "BC-2", "question": "Is DR tested at least annually?", "weight": 4},
                    {"id": "BC-3", "question": "Is RTO defined and measured?", "weight": 4},
                    {"id": "BC-4", "question": "Is RPO defined and measured?", "weight": 4},
                    {"id": "BC-5", "question": "Are critical systems redundant?", "weight": 4},
                ],
            },
        ],
    },
}

CAIQ_QUESTIONS = [
    {"id": "CAIQ-01", "domain": "AUDIT", "question": "Do you maintain audit logs of privileged user access?", "weight": 4},
    {"id": "CAIQ-02", "domain": "AUDIT", "question": "Are audit logs protected from modification?", "weight": 5},
    {"id": "CAIQ-03", "domain": "AUDIT", "question": "Are audit logs retained for at least 12 months?", "weight": 3},
    {"id": "CAIQ-04", "domain": "AUDIT", "question": "Is automated log analysis performed?", "weight": 3},
    {"id": "CAIQ-05", "domain": "AUTH", "question": "Is unique user identification required?", "weight": 4},
    {"id": "CAIQ-06", "domain": "AUTH", "question": "Is MFA required for privileged access?", "weight": 5},
    {"id": "CAIQ-07", "domain": "AUTH", "question": "Are passwords hashed and salted?", "weight": 5},
    {"id": "CAIQ-08", "domain": "AUTH", "question": "Is session timeout configured?", "weight": 2},
    {"id": "CAIQ-09", "domain": "AUTH", "question": "Are failed login attempts limited?", "weight": 3},
    {"id": "CAIQ-10", "domain": "BCM", "question": "Is there a business continuity plan?", "weight": 5},
    {"id": "CAIQ-11", "domain": "BCM", "question": "Is DR tested at least annually?", "weight": 4},
    {"id": "CAIQ-12", "domain": "BCM", "question": "Are backups encrypted?", "weight": 4},
    {"id": "CAIQ-13", "domain": "BCM", "question": "Is RTO/RPO defined?", "weight": 4},
    {"id": "CAIQ-14", "domain": "CCC", "question": "Are configuration management processes defined?", "weight": 3},
    {"id": "CAIQ-15", "domain": "CCC", "question": "Is change management process in place?", "weight": 3},
    {"id": "CAIQ-16", "domain": "CCC", "question": "Is vulnerability scanning performed?", "weight": 4},
    {"id": "CAIQ-17", "domain": "CCC", "question": "Are security baselines enforced?", "weight": 3},
    {"id": "CAIQ-18", "domain": "DSP", "question": "Is data classified by sensitivity?", "weight": 3},
    {"id": "CAIQ-19", "domain": "DSP", "question": "Is data encrypted at rest?", "weight": 5},
    {"id": "CAIQ-20", "domain": "DSP", "question": "Is data encrypted in transit?", "weight": 5},
    {"id": "CAIQ-21", "domain": "DSP", "question": "Is data retention policy defined?", "weight": 3},
    {"id": "CAIQ-22", "domain": "DSP", "question": "Is data securely disposed?", "weight": 3},
    {"id": "CAIQ-23", "domain": "DSP", "question": "Are data processing agreements in place?", "weight": 4},
    {"id": "CAIQ-24", "domain": "IAM", "question": "Is user provisioning/deprovisioning automated?", "weight": 3},
    {"id": "CAIQ-25", "domain": "IAM", "question": "Are access reviews performed?", "weight": 3},
    {"id": "CAIQ-26", "domain": "IAM", "question": "Is least privilege enforced?", "weight": 4},
    {"id": "CAIQ-27", "domain": "IAM", "question": "Are service accounts managed?", "weight": 3},
    {"id": "CAIQ-28", "domain": "IVS", "question": "Is anti-malware software deployed?", "weight": 4},
    {"id": "CAIQ-29", "domain": "IVS", "question": "Are intrusion detection systems in place?", "weight": 4},
    {"id": "CAIQ-30", "domain": "IVS", "question": "Is network segmentation implemented?", "weight": 4},
    {"id": "CAIQ-31", "domain": "IVS", "question": "Are firewalls configured?", "weight": 4},
    {"id": "CAIQ-32", "domain": "IVS", "question": "Is DDoS protection in place?", "weight": 3},
    {"id": "CAIQ-33", "domain": "STA", "question": "Are third-party vendors assessed?", "weight": 4},
    {"id": "CAIQ-34", "domain": "STA", "question": "Is vendor risk tier defined?", "weight": 3},
    {"id": "CAIQ-35", "domain": "STA", "question": "Are contract reviews performed?", "weight": 3},
]


class VendorRiskManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._vendors: Dict[str, Vendor] = {}
        self._assessments: Dict[str, Assessment] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("VendorRiskManager initialized")

    async def close(self) -> None:
        self._vendors.clear()
        self._assessments.clear()
        logger.info("VendorRiskManager closed")

    def add_vendor(self, name: str, category: str, website: Optional[str] = None,
                   contact_name: Optional[str] = None, contact_email: Optional[str] = None,
                   risk_tier: str = "medium", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        vendor_id = str(uuid.uuid4())
        vendor = Vendor(
            vendor_id=vendor_id,
            name=name,
            website=website,
            contact_name=contact_name,
            contact_email=contact_email,
            category=category,
            risk_tier=risk_tier,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._vendors[vendor_id] = vendor
        logger.info(f"Vendor {vendor_id} added: {name}")
        return vendor.to_dict()

    def get_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        vendor = self._vendors.get(vendor_id)
        if not vendor:
            return None
        result = vendor.to_dict()
        assessments = self.get_vendor_assessments(vendor_id)
        result["assessments"] = assessments
        result["latest_score"] = assessments[0]["score"] if assessments else None
        return result

    def update_vendor(self, vendor_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        vendor = self._vendors.get(vendor_id)
        if not vendor:
            return None
        for key, value in updates.items():
            if hasattr(vendor, key) and key not in ("vendor_id", "created_at"):
                setattr(vendor, key, value)
        vendor.updated_at = datetime.utcnow()
        return vendor.to_dict()

    def delete_vendor(self, vendor_id: str) -> bool:
        if vendor_id not in self._vendors:
            return False
        del self._vendors[vendor_id]
        expired = [aid for aid, a in self._assessments.items() if a.vendor_id == vendor_id]
        for aid in expired:
            del self._assessments[aid]
        logger.info(f"Vendor {vendor_id} deleted")
        return True

    def list_vendors(self, category: Optional[str] = None, risk_tier: Optional[str] = None,
                     status: Optional[str] = None) -> List[Dict[str, Any]]:
        vendors = list(self._vendors.values())
        if category:
            vendors = [v for v in vendors if v.category == category]
        if risk_tier:
            vendors = [v for v in vendors if v.risk_tier == risk_tier]
        if status:
            vendors = [v for v in vendors if v.status == status]
        return [v.to_dict() for v in sorted(vendors, key=lambda v: v.name)]

    def create_assessment(self, vendor_id: str, template_type: str,
                          assessor: str = "system") -> Dict[str, Any]:
        if vendor_id not in self._vendors:
            raise ValueError(f"Vendor {vendor_id} not found")
        if template_type not in ("sig", "caiq", "custom"):
            raise ValueError(f"Invalid template type: {template_type}")

        assessment_id = str(uuid.uuid4())
        assessment = Assessment(
            assessment_id=assessment_id,
            vendor_id=vendor_id,
            template_type=template_type,
            status="in_progress",
            score=None,
            responses={},
            findings=[],
            created_at=datetime.utcnow(),
            completed_at=None,
            assessor=assessor,
        )
        self._assessments[assessment_id] = assessment
        logger.info(f"Assessment {assessment_id} created for vendor {vendor_id}")
        return assessment.to_dict()

    def submit_responses(self, vendor_id: str, assessment_id: str,
                         responses: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        assessment = self._assessments.get(assessment_id)
        if not assessment or assessment.vendor_id != vendor_id:
            return None
        assessment.responses = responses
        assessment.status = "submitted"
        return assessment.to_dict()

    def score_assessment(self, vendor_id: str, assessment_id: str) -> Optional[Dict[str, Any]]:
        assessment = self._assessments.get(assessment_id)
        if not assessment or assessment.vendor_id != vendor_id:
            return None

        if assessment.template_type == "sig":
            score, findings = self._score_sig(assessment.responses)
        elif assessment.template_type == "caiq":
            score, findings = self._score_caiq(assessment.responses)
        else:
            score, findings = self._score_custom(assessment.responses)

        assessment.score = score
        assessment.findings = findings
        assessment.status = "completed"
        assessment.completed_at = datetime.utcnow()

        self._update_vendor_risk_tier(vendor_id, score)
        logger.info(f"Assessment {assessment_id} scored: {score:.1f}")
        return self.get_assessment(vendor_id, assessment_id)

    def get_assessment(self, vendor_id: str, assessment_id: str) -> Optional[Dict[str, Any]]:
        assessment = self._assessments.get(assessment_id)
        if not assessment or assessment.vendor_id != vendor_id:
            return None
        result = assessment.to_dict()
        result["responses"] = assessment.responses
        result["findings"] = self._score_findings_with_remediation(assessment.findings)
        return result

    def get_vendor_assessments(self, vendor_id: str) -> List[Dict[str, Any]]:
        return [
            a.to_dict() for a in sorted(
                self._assessments.values(), key=lambda a: a.created_at, reverse=True
            ) if a.vendor_id == vendor_id
        ]

    def _score_sig(self, responses: Dict[str, Any]) -> Tuple[float, List[Dict]]:
        total_weight = 0
        weighted_score = 0
        findings = []

        for category, cat_data in SIG_QUESTIONS.items():
            for domain in cat_data["domains"]:
                for question in domain["questions"]:
                    qid = question["id"]
                    weight = question["weight"]
                    total_weight += weight
                    answer = responses.get(qid, "No")
                    if isinstance(answer, str):
                        answer_score = 1.0 if answer.lower() in ("yes", "true", "implemented") else 0.0
                    else:
                        answer_score = float(answer) / 100.0 if answer > 1 else float(answer)
                    weighted_score += weight * answer_score
                    if answer_score < 0.5:
                        findings.append({
                            "id": qid,
                            "question": question["question"],
                            "domain": domain["name"],
                            "category": category,
                            "severity": "critical" if weight >= 5 else "high" if weight >= 4 else "medium",
                            "weight": weight,
                            "score": round(answer_score * 100, 1),
                        })

        overall = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        return overall, findings

    def _score_caiq(self, responses: Dict[str, Any]) -> Tuple[float, List[Dict]]:
        total_weight = sum(q["weight"] for q in CAIQ_QUESTIONS)
        weighted_score = 0
        findings = []

        for question in CAIQ_QUESTIONS:
            qid = question["id"]
            weight = question["weight"]
            answer = responses.get(qid, "No")
            if isinstance(answer, str):
                answer_score = 1.0 if answer.lower() in ("yes", "true", "implemented") else 0.0
            else:
                answer_score = float(answer) / 100.0 if answer > 1 else float(answer)
            weighted_score += weight * answer_score
            if answer_score < 0.5:
                findings.append({
                    "id": qid,
                    "question": question["question"],
                    "domain": question["domain"],
                    "severity": "critical" if weight >= 5 else "high" if weight >= 4 else "medium",
                    "weight": weight,
                    "score": round(answer_score * 100, 1),
                })

        overall = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        return overall, findings

    def _score_custom(self, responses: Dict[str, Any]) -> Tuple[float, List[Dict]]:
        if not responses:
            return 0.0, []
        scores = []
        findings = []
        for qid, answer in responses.items():
            if isinstance(answer, str):
                answer_score = 1.0 if answer.lower() in ("yes", "true", "implemented") else 0.0
            else:
                answer_score = min(1.0, max(0.0, float(answer) / 100.0))
            scores.append(answer_score)
            if answer_score < 0.5:
                findings.append({"id": qid, "score": round(answer_score * 100, 1), "severity": "medium"})
        overall = (sum(scores) / len(scores) * 100) if scores else 0
        return overall, findings

    def _score_findings_with_remediation(self, findings: List[Dict]) -> List[Dict]:
        remediation_map = {
            "Access Control": "Implement role-based access control with quarterly reviews",
            "Encryption": "Enable AES-256 encryption at rest and TLS 1.2+ in transit",
            "Incident Response": "Develop and test incident response plan annually",
            "Vulnerability Management": "Implement regular vulnerability scanning and patching SLA",
            "Data Protection": "Classify data and implement backup/retention policies",
            "AUDIT": "Enable comprehensive audit logging with SIEM integration",
            "AUTH": "Enforce MFA and strong password policies",
            "BCM": "Develop business continuity plan with annual DR testing",
            "DSP": "Implement data classification and encryption controls",
        }
        for finding in findings:
            domain = finding.get("domain", "")
            if domain in remediation_map:
                finding["remediation"] = remediation_map[domain]
            else:
                finding["remediation"] = "Review and address identified gap"
        return findings

    def _update_vendor_risk_tier(self, vendor_id: str, score: float) -> None:
        vendor = self._vendors.get(vendor_id)
        if not vendor:
            return
        if score >= 80:
            vendor.risk_tier = "low"
        elif score >= 60:
            vendor.risk_tier = "medium"
        elif score >= 40:
            vendor.risk_tier = "high"
        else:
            vendor.risk_tier = "critical"
        vendor.updated_at = datetime.utcnow()

    def get_statistics(self) -> Dict[str, Any]:
        tier_counts = {}
        for v in self._vendors.values():
            tier_counts[v.risk_tier] = tier_counts.get(v.risk_tier, 0) + 1
        completed = sum(1 for a in self._assessments.values() if a.status == "completed")
        avg_score = statistics.mean(
            [a.score for a in self._assessments.values() if a.score is not None]
        ) if completed > 0 else 0
        return {
            "total_vendors": len(self._vendors),
            "risk_tiers": tier_counts,
            "total_assessments": len(self._assessments),
            "completed_assessments": completed,
            "avg_score": round(avg_score, 1) if avg_score else None,
            "template_types": {
                "sig": "Standard Information Gathering",
                "caiq": "Consensus Assessments Initiative Questionnaire",
                "custom": "Custom Questionnaire",
            },
        }
