import json
import uuid
import re
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


PII_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "ssn_us": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "phone_us": re.compile(r'\b(?:\+1)?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    "passport_us": re.compile(r'\b\d{9}\b'),
    "driver_license_us": re.compile(r'\b[A-Z]\d{7}\b'),
    "date_of_birth": re.compile(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b'),
    "street_address": re.compile(r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b', re.IGNORECASE),
    "zip_code": re.compile(r'\b\d{5}(?:-\d{4})?\b'),
    "bank_account": re.compile(r'\b\d{8,17}\b'),
    "routing_number": re.compile(r'\b\d{9}\b'),
}

PHI_PATTERNS = {
    "medical_record_number": re.compile(r'\b(?:MRN|MR|MED)[-:]?\d{5,10}\b', re.IGNORECASE),
    "health_insurance_id": re.compile(r'\b(?:HIID|HIC|HICN)[-:]?\d{5,15}\b', re.IGNORECASE),
    "diagnosis_code": re.compile(r'\b[A-Z]\d{2}\.\d{1,2}\b'),
    "procedure_code": re.compile(r'\b\d{4}[A-Z0-9]{0,2}\b'),
    "patient_name_indicator": re.compile(r'\b(?:patient|diagnosis|diagnose|treatment|prescription)\s*(?::|is|was|name)\b', re.IGNORECASE),
}

PCI_PATTERNS = {
    "pan": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    "cvv": re.compile(r'\b\d{3,4}\b'),
    "track_data": re.compile(r'%?[A-Z]\d{1,20}\^[A-Z/\s]+\^\d{5,10}\?\d+;'),
    "pin": re.compile(r'\b\d{4,6}\b(?:.*(?:pin|pin\s*code))', re.IGNORECASE),
}


@dataclass
class ClassificationResult:
    scan_id: str
    resource_id: str
    resource_type: str
    classifications: Dict[str, str]
    pii_found: List[Dict[str, Any]]
    phi_found: List[Dict[str, Any]]
    pci_found: List[Dict[str, Any]]
    overall_level: str
    confidence: float
    scanned_at: datetime
    raw_snippet: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "classifications": self.classifications,
            "pii_found": self.pii_found[:20],
            "phi_found": self.phi_found[:20],
            "pci_found": self.pci_found[:20],
            "overall_level": self.overall_level,
            "confidence": round(self.confidence, 3),
            "scanned_at": self.scanned_at.isoformat(),
        }


CLASSIFICATION_LEVELS = [
    {"level": "public", "description": "No sensitivity, can be freely shared", "score": 0},
    {"level": "internal", "description": "Internal use only, not for public disclosure", "score": 1},
    {"level": "confidential", "description": "Business confidential information", "score": 2},
    {"level": "restricted", "description": "Highly sensitive, limited access", "score": 3},
    {"level": "regulated", "description": "Subject to compliance (PII/PHI/PCI)", "score": 4},
]


class ClassificationEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._results: Dict[str, ClassificationResult] = {}
        self._inventory: Dict[str, Dict[str, Any]] = {}
        self._policies: Dict[str, Dict[str, Any]] = {}
        self._patterns = {
            "pii": PII_PATTERNS,
            "phi": PHI_PATTERNS,
            "pci": PCI_PATTERNS,
        }
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("ClassificationEngine initialized")

    async def close(self) -> None:
        self._results.clear()
        self._inventory.clear()
        logger.info("ClassificationEngine closed")

    def scan_text(self, text: str, resource_id: str, resource_type: str) -> ClassificationResult:
        scan_id = str(uuid.uuid4())
        pii_found = []
        phi_found = []
        pci_found = []

        for pattern_name, pattern in PII_PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches[:10]:
                pii_found.append({
                    "type": pattern_name,
                    "value": self._mask_value(match),
                    "position": text.find(match),
                    "confidence": self._get_confidence(pattern_name, match),
                })

        for pattern_name, pattern in PHI_PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches[:10]:
                phi_found.append({
                    "type": pattern_name,
                    "value": self._mask_value(match),
                    "position": text.find(match),
                    "confidence": self._get_confidence(pattern_name, match),
                })

        for pattern_name, pattern in PCI_PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches[:10]:
                pci_found.append({
                    "type": pattern_name,
                    "value": self._mask_value(match),
                    "position": text.find(match),
                    "confidence": self._get_confidence(pattern_name, match),
                })

        overall_level = self._determine_overall_level(pii_found, phi_found, pci_found)
        confidence = self._calculate_confidence(pii_found, phi_found, pci_found)

        classifications = {
            "has_pii": len(pii_found) > 0,
            "has_phi": len(phi_found) > 0,
            "has_pci": len(pci_found) > 0,
            "pii_types": list(set(p["type"] for p in pii_found)),
            "phi_types": list(set(p["type"] for p in phi_found)),
            "pci_types": list(set(p["type"] for p in pci_found)),
        }

        result = ClassificationResult(
            scan_id=scan_id,
            resource_id=resource_id,
            resource_type=resource_type,
            classifications=classifications,
            pii_found=pii_found,
            phi_found=phi_found,
            pci_found=pci_found,
            overall_level=overall_level,
            confidence=confidence,
            scanned_at=datetime.utcnow(),
            raw_snippet=text[:500],
        )

        self._results[scan_id] = result
        self._update_inventory(resource_id, resource_type, overall_level, classifications)
        logger.info(f"Classification scan {scan_id}: {overall_level} level for {resource_id}")
        return result

    def scan_database_column(self, column_name: str, sample_values: List[str],
                             resource_id: str) -> ClassificationResult:
        text = f"column:{column_name} " + " ".join(sample_values[:100])
        return self.scan_text(text, f"{resource_id}:{column_name}", "database_column")

    def scan_file(self, file_name: str, content: str, file_path: str) -> ClassificationResult:
        return self.scan_text(content, file_path, f"file:{file_name.split('.')[-1]}")

    def _determine_overall_level(self, pii_found: List[Dict],
                                  phi_found: List[Dict],
                                  pci_found: List[Dict]) -> str:
        if pci_found:
            return "restricted"
        if phi_found:
            return "restricted"
        if pii_found:
            high_risk = {"ssn_us", "credit_card", "bank_account", "passport_us"}
            pii_types = set(p["type"] for p in pii_found)
            if pii_types & high_risk:
                return "restricted"
            return "confidential"
        return "internal"

    def _calculate_confidence(self, pii_found: List[Dict],
                               phi_found: List[Dict],
                               pci_found: List[Dict]) -> float:
        if not pii_found and not phi_found and not pci_found:
            return 1.0
        confidences = (
            [p.get("confidence", 0.5) for p in pii_found] +
            [p.get("confidence", 0.5) for p in phi_found] +
            [p.get("confidence", 0.5) for p in pci_found]
        )
        if not confidences:
            return 0.5
        high_conf = sum(1 for c in confidences if c >= 0.8)
        return min(1.0, sum(confidences) / len(confidences) + (high_conf * 0.05))

    def _get_confidence(self, pattern_type: str, match: str) -> float:
        confidence_map = {
            "email": 0.95,
            "ssn_us": 0.98,
            "phone_us": 0.85,
            "credit_card": 0.90,
            "ip_address": 0.80,
            "passport_us": 0.85,
            "driver_license_us": 0.80,
            "date_of_birth": 0.75,
            "street_address": 0.70,
            "zip_code": 0.65,
            "bank_account": 0.75,
            "routing_number": 0.80,
            "medical_record_number": 0.85,
            "health_insurance_id": 0.80,
            "diagnosis_code": 0.70,
            "procedure_code": 0.65,
            "patient_name_indicator": 0.50,
            "pan": 0.90,
            "cvv": 0.70,
            "track_data": 0.95,
            "pin": 0.60,
        }
        return confidence_map.get(pattern_type, 0.5)

    def _mask_value(self, value: str) -> str:
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]

    def _update_inventory(self, resource_id: str, resource_type: str,
                           overall_level: str, classifications: Dict[str, Any]) -> None:
        self._inventory[resource_id] = {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "classification_level": overall_level,
            "classifications": classifications,
            "last_scanned": datetime.utcnow().isoformat(),
            "scan_count": self._inventory.get(resource_id, {}).get("scan_count", 0) + 1,
        }

    def get_result(self, scan_id: str) -> Optional[ClassificationResult]:
        return self._results.get(scan_id)

    def get_inventory(self, classification_level: Optional[str] = None,
                      resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        items = list(self._inventory.values())
        if classification_level:
            items = [i for i in items if i["classification_level"] == classification_level]
        if resource_type:
            items = [i for i in items if i["resource_type"] == resource_type]
        return sorted(items, key=lambda i: i.get("last_scanned", ""), reverse=True)

    def label_resource(self, resource_id: str, label: str) -> bool:
        if resource_id not in self._inventory:
            return False
        valid_labels = [l["level"] for l in CLASSIFICATION_LEVELS]
        if label not in valid_labels:
            raise ValueError(f"Invalid label: {label}. Valid: {valid_labels}")
        self._inventory[resource_id]["classification_level"] = label
        self._inventory[resource_id]["manual_label"] = True
        self._inventory[resource_id]["labeled_at"] = datetime.utcnow().isoformat()
        logger.info(f"Resource {resource_id} manually labeled as {label}")
        return True

    def create_policy(self, name: str, description: str,
                      conditions: Dict[str, Any], actions: List[str]) -> Dict[str, Any]:
        policy_id = str(uuid.uuid4())
        policy = {
            "policy_id": policy_id,
            "name": name,
            "description": description,
            "conditions": conditions,
            "actions": actions,
            "enabled": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._policies[policy_id] = policy
        return policy

    def evaluate_policies(self, resource_id: str, classification: ClassificationResult) -> List[Dict[str, Any]]:
        triggered = []
        for pid, policy in self._policies.items():
            if not policy["enabled"]:
                continue
            conditions = policy["conditions"]
            match = True
            if "level" in conditions:
                level_map = {l["level"]: l["score"] for l in CLASSIFICATION_LEVELS}
                resource_score = level_map.get(classification.overall_level, 0)
                required_score = level_map.get(conditions["level"], 0)
                match = match and resource_score >= required_score
            if "has_pii" in conditions and conditions["has_pii"]:
                match = match and len(classification.pii_found) > 0
            if "has_phi" in conditions and conditions["has_phi"]:
                match = match and len(classification.phi_found) > 0
            if "has_pci" in conditions and conditions["has_pci"]:
                match = match and len(classification.pci_found) > 0
            if match:
                triggered.append({
                    "policy_id": pid,
                    "policy_name": policy["name"],
                    "actions": policy["actions"],
                })
        return triggered

    def get_statistics(self) -> Dict[str, Any]:
        level_counts = Counter(i["classification_level"] for i in self._inventory.values())
        type_counts = Counter(i["resource_type"] for i in self._inventory.values())
        total_pii = sum(
            1 for r in self._results.values()
            if r.classifications.get("has_pii")
        )
        total_phi = sum(
            1 for r in self._results.values()
            if r.classifications.get("has_phi")
        )
        total_pci = sum(
            1 for r in self._results.values()
            if r.classifications.get("has_pci")
        )
        return {
            "total_scans": len(self._results),
            "resources_tracked": len(self._inventory),
            "classification_levels": dict(level_counts),
            "resource_types": dict(type_counts),
            "resources_with_pii": total_pii,
            "resources_with_phi": total_phi,
            "resources_with_pci": total_pci,
            "active_policies": len(self._policies),
        }
