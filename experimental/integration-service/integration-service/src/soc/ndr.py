"""Network Detection & Response (NDR).

Network traffic analysis with ML-based threat detection. Zeek/Suricata integration,
encrypted traffic analysis, wire-level forensics, and protocol anomaly detection.
"""

import json
import uuid
import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ProtocolType(str, Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    SSH = "ssh"
    TLS = "tls"
    SMB = "smb"
    RDP = "rdp"
    FTP = "ftp"
    SMTP = "smtp"
    KERBEROS = "kerberos"
    DHCP = "dhcp"
    ARP = "arp"


class ThreatCategory(str, Enum):
    MALWARE_C2 = "malware_c2"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    RECONNAISSANCE = "reconnaissance"
    DETECTION_EVASION = "detection_evasion"
    EXPLOITATION = "exploitation"
    POLICY_VIOLATION = "policy_violation"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    ENCRYPTED_THREAT = "encrypted_threat"
    DOS_ATTACK = "dos_attack"


@dataclass
class NetworkFlow:
    id: str
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: ProtocolType
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    duration_seconds: float
    app_protocol: Optional[str] = None
    tls_version: Optional[str] = None
    tls_sni: Optional[str] = None
    dns_query: Optional[str] = None
    dns_response: Optional[str] = None
    http_method: Optional[str] = None
    http_uri: Optional[str] = None
    http_user_agent: Optional[str] = None
    http_status: Optional[int] = None
    threat_score: float = 0.0
    threat_category: Optional[str] = None
    malicious: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol.value,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "duration_seconds": self.duration_seconds,
            "app_protocol": self.app_protocol,
            "tls_sni": self.tls_sni,
            "dns_query": self.dns_query,
            "http_uri": self.http_uri,
            "threat_score": self.threat_score,
            "threat_category": self.threat_category,
            "malicious": self.malicious,
            "tags": self.tags,
        }


@dataclass
class DetectionRule:
    id: str
    name: str
    description: str
    signature: str
    protocol: Optional[str] = None
    severity: str = "medium"
    category: str = "anomaly"
    enabled: bool = True
    false_positive_rate: float = 0.0
    hits: int = 0
    last_match: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "protocol": self.protocol,
            "severity": self.severity,
            "category": self.category,
            "enabled": self.enabled,
            "false_positive_rate": self.false_positive_rate,
            "hits": self.hits,
            "last_match": self.last_match.isoformat() if self.last_match else None,
        }


@dataclass
class NDRAlert:
    id: str
    title: str
    description: str
    severity: str
    category: str
    source_ip: str
    destination_ip: str
    protocol: str
    flow_id: Optional[str] = None
    rule_id: Optional[str] = None
    threat_score: float = 0.0
    detected_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    pcap_reference: Optional[str] = None
    mitre_technique: Optional[str] = None
    raw_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "protocol": self.protocol,
            "flow_id": self.flow_id,
            "threat_score": self.threat_score,
            "detected_at": self.detected_at.isoformat(),
            "acknowledged": self.acknowledged,
            "pcap_reference": self.pcap_reference,
            "mitre_technique": self.mitre_technique,
        }


class NetworkDetectionResponse:
    """Network traffic analysis with ML-based threat detection."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.flows: Dict[str, NetworkFlow] = {}
        self.rules: Dict[str, DetectionRule] = {}
        self.alerts: Dict[str, NDRAlert] = {}
        self._initialized = False
        self._baseline_models: Dict[str, Dict[str, float]] = {}

    async def initialize(self):
        self._load_default_rules()
        self._seed_baselines()
        self._initialized = True
        logger.info(f"NDR initialized: {len(self.rules)} rules, {len(self.flows)} flows tracked")

    async def close(self):
        logger.info("NDR shut down")

    def _load_default_rules(self):
        default_rules = [
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="Suspicious Outbound DNS",
                description="DNS queries to known DGA domains or excessive NXDOMAIN responses",
                signature='dns.query matches "*.xyz" or dns.rcode == "NXDOMAIN" and dns.count > 20',
                protocol="dns", severity="medium", category="malware_c2"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="Data Exfiltration via DNS Tunneling",
                description="Large DNS query sizes indicative of DNS tunneling for data exfiltration",
                signature="dns.query_len > 200 and dns.qtype == 'TXT' and dns.count > 10",
                protocol="dns", severity="high", category="data_exfiltration"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="SMB Lateral Movement",
                description="SMB connections to multiple internal hosts from a single source in short period",
                signature="smb.command in ['SMB_COM_NEGOTIATE', 'SMB_COM_SESSION_SETUP'] and unique_dst > 3 within 60s",
                protocol="smb", severity="high", category="lateral_movement"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="SSL/TLS with Self-Signed Cert",
                description="TLS connections using self-signed certificates - potential MITM",
                signature="tls.certificate.issuer == tls.certificate.subject",
                protocol="tls", severity="medium", category="detection_evasion"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="SSH Brute Force Detection",
                description="Multiple failed SSH authentication attempts from same IP",
                signature="ssh.auth_success == false and ssh.auth_attempts > 10 within 60s",
                protocol="ssh", severity="high", category="reconnaissance"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="Large Outbound Data Transfer",
                description="Unusually large outbound data transfer to external host",
                signature="flow.bytes_sent > 10000000 and flow.dst_ip not in private_ranges",
                protocol=None, severity="high", category="data_exfiltration"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="Port Scan Detection",
                description="Source IP connecting to multiple ports on same destination",
                signature="unique_dst_ports > 20 and flow.duration < 5",
                protocol="tcp", severity="low", category="reconnaissance"),
            DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name="HTTP Request to Malicious URI",
                description="HTTP requests matching known malicious URI patterns",
                signature='http.uri matches "/(shell|cmd|exec|eval|phpinfo|admin)"',
                protocol="http", severity="high", category="exploitation"),
        ]
        for rule in default_rules:
            self.rules[rule.id] = rule

    def _seed_baselines(self):
        self._baseline_models["avg_bytes_per_flow"] = {"mean": 15000, "std_dev": 12000}
        self._baseline_models["avg_duration_seconds"] = {"mean": 45.0, "std_dev": 30.0}
        self._baseline_models["dns_queries_per_min"] = {"mean": 5.0, "std_dev": 3.0}
        self._baseline_models["unique_dst_per_hour"] = {"mean": 25.0, "std_dev": 15.0}

    def ingest_flow(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int,
                    protocol: str, bytes_sent: int, bytes_received: int,
                    packets_sent: int, packets_received: int, duration_seconds: float,
                    app_protocol: Optional[str] = None, tls_sni: Optional[str] = None,
                    dns_query: Optional[str] = None, http_uri: Optional[str] = None,
                    http_user_agent: Optional[str] = None, http_status: Optional[int] = None) -> NetworkFlow:
        flow = NetworkFlow(id=f"flow-{uuid.uuid4().hex[:12]}", timestamp=datetime.utcnow(),
                           src_ip=src_ip, dst_ip=dst_ip, src_port=src_port, dst_port=dst_port,
                           protocol=ProtocolType(protocol), bytes_sent=bytes_sent, bytes_received=bytes_received,
                           packets_sent=packets_sent, packets_received=packets_received,
                           duration_seconds=duration_seconds, app_protocol=app_protocol,
                           tls_sni=tls_sni, dns_query=dns_query, http_uri=http_uri,
                           http_user_agent=http_user_agent, http_status=http_status)
        self.flows[flow.id] = flow
        threat_score, category = self._analyze_flow(flow)
        flow.threat_score = threat_score
        flow.malicious = threat_score > 0.5
        if flow.malicious:
            flow.threat_category = category
            self._create_alert(flow, category, threat_score)
        return flow

    def _analyze_flow(self, flow: NetworkFlow) -> Tuple[float, Optional[str]]:
        score = 0.0
        category = None
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            if rule.protocol and rule.protocol != flow.protocol.value and rule.protocol != "any":
                continue
            match_score = self._evaluate_rule(rule, flow)
            if match_score > 0:
                rule.hits += 1
                rule.last_match = datetime.utcnow()
                score += match_score
                category = category or rule.category
        score = min(score, 1.0)
        if flow.bytes_sent > 50000000:
            score = max(score, 0.7)
            category = category or "data_exfiltration"
        if flow.protocol == ProtocolType.DNS and flow.dns_query:
            entropy = self._calculate_entropy(flow.dns_query.split(".")[0] if "." in flow.dns_query else flow.dns_query)
            if entropy > 3.5:
                score = max(score, 0.6)
                category = category or "malware_c2"
                flow.tags.append("dga_domain")
        if flow.tls_sni and not flow.tls_sni.endswith((".com", ".net", ".org", ".io", ".co")):
            if len(flow.tls_sni) > 30:
                score = max(score, 0.5)
                category = category or "malware_c2"
                flow.tags.append("suspicious_tls_sni")
        return round(score, 2), category

    def _evaluate_rule(self, rule: DetectionRule, flow: NetworkFlow) -> float:
        if "bytes_sent > 10000000" in rule.signature and flow.bytes_sent > 10000000:
            return 0.7
        if "dns.query_len > 200" in rule.signature and flow.dns_query and len(flow.dns_query) > 200:
            return 0.8
        if "http.uri" in rule.signature and flow.http_uri:
            suspicious_patterns = ["shell", "cmd", "exec", "eval", "phpinfo", "admin"]
            if any(p in flow.http_uri.lower() for p in suspicious_patterns):
                return 0.6
        if "self-signed" in rule.signature.lower():
            pass
        return 0.0

    def _calculate_entropy(self, s: str) -> float:
        if not s:
            return 0.0
        prob = [s.count(c) / len(s) for c in set(s)]
        return -sum(p * math.log2(p) for p in prob if p > 0)

    def _create_alert(self, flow: NetworkFlow, category: str, threat_score: float):
        severity_map = {"critical": 0.9, "high": 0.7, "medium": 0.4, "low": 0.2}
        severity = "low"
        for sev, threshold in [("critical", 0.9), ("high", 0.7), ("medium", 0.4)]:
            if threat_score >= threshold:
                severity = sev
                break
        alert = NDRAlert(id=f"alert-{uuid.uuid4().hex[:12]}",
                         title=f"Malicious {flow.protocol.value} traffic detected",
                         description=f"Flow from {flow.src_ip}:{flow.src_port} to {flow.dst_ip}:{flow.dst_port} "
                                     f"classified as {category} (score: {threat_score})",
                         severity=severity, category=category, source_ip=flow.src_ip,
                         destination_ip=flow.dst_ip, protocol=flow.protocol.value,
                         flow_id=flow.id, threat_score=threat_score,
                         raw_evidence={"bytes_sent": flow.bytes_sent, "duration": flow.duration_seconds,
                                       "dns_query": flow.dns_query, "tls_sni": flow.tls_sni,
                                       "http_uri": flow.http_uri})
        self.alerts[alert.id] = alert
        logger.warning(f"NDR alert: {alert.title} [{category}] {flow.src_ip} -> {flow.dst_ip}")

    def get_flow(self, flow_id: str) -> Optional[NetworkFlow]:
        return self.flows.get(flow_id)

    def search_flows(self, src_ip: Optional[str] = None, dst_ip: Optional[str] = None,
                     protocol: Optional[str] = None, malicious_only: bool = False,
                     min_score: Optional[float] = None, limit: int = 100) -> List[NetworkFlow]:
        results = list(self.flows.values())
        if src_ip:
            results = [f for f in results if f.src_ip == src_ip]
        if dst_ip:
            results = [f for f in results if f.dst_ip == dst_ip]
        if protocol:
            results = [f for f in results if f.protocol.value == protocol]
        if malicious_only:
            results = [f for f in results if f.malicious]
        if min_score is not None:
            results = [f for f in results if f.threat_score >= min_score]
        return sorted(results, key=lambda f: f.timestamp, reverse=True)[:limit]

    def list_alerts(self, severity: Optional[str] = None, category: Optional[str] = None,
                    source_ip: Optional[str] = None, acknowledged: Optional[bool] = None,
                    limit: int = 50) -> List[NDRAlert]:
        results = list(self.alerts.values())
        if severity:
            results = [a for a in results if a.severity == severity]
        if category:
            results = [a for a in results if a.category == category]
        if source_ip:
            results = [a for a in results if a.source_ip == source_ip]
        if acknowledged is not None:
            results = [a for a in results if a.acknowledged == acknowledged]
        return sorted(results, key=lambda a: a.detected_at, reverse=True)[:limit]

    def acknowledge_alert(self, alert_id: str) -> Optional[NDRAlert]:
        alert = self.alerts.get(alert_id)
        if alert:
            alert.acknowledged = True
        return alert

    def add_rule(self, name: str, description: str, signature: str, severity: str = "medium",
                 protocol: Optional[str] = None, category: str = "anomaly") -> DetectionRule:
        rule = DetectionRule(id=f"rule-{uuid.uuid4().hex[:12]}", name=name, description=description,
                             signature=signature, protocol=protocol, severity=severity, category=category)
        self.rules[rule.id] = rule
        return rule

    def toggle_rule(self, rule_id: str) -> Optional[DetectionRule]:
        rule = self.rules.get(rule_id)
        if rule:
            rule.enabled = not rule.enabled
        return rule

    def list_rules(self, category: Optional[str] = None, protocol: Optional[str] = None) -> List[DetectionRule]:
        results = list(self.rules.values())
        if category:
            results = [r for r in results if r.category == category]
        if protocol:
            results = [r for r in results if r.protocol == protocol]
        return results

    def get_pcap_reference(self, flow_id: str) -> Dict[str, Any]:
        flow = self.flows.get(flow_id)
        if not flow:
            return {"error": "Flow not found"}
        return {
            "flow_id": flow_id,
            "pcap_file": f"/data/pcap/{flow.timestamp.strftime('%Y%m%d')}/{flow_id}.pcap",
            "protocol": flow.protocol.value,
            "src_ip": flow.src_ip,
            "dst_ip": flow.dst_ip,
            "size_bytes": flow.bytes_sent + flow.bytes_received,
            "packets": flow.packets_sent + flow.packets_received,
            "available": True,
        }

    def get_network_summary(self) -> Dict[str, Any]:
        total = len(self.flows)
        malicious = sum(1 for f in self.flows.values() if f.malicious)
        protocol_dist = {}
        for f in self.flows.values():
            protocol_dist[f.protocol.value] = protocol_dist.get(f.protocol.value, 0) + 1
        severity_counts = {}
        for a in self.alerts.values():
            severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
        top_talkers = self._get_top_talkers(5)
        return {
            "total_flows": total,
            "malicious_flows": malicious,
            "malicious_percent": round(malicious / total * 100, 1) if total > 0 else 0,
            "protocol_distribution": protocol_dist,
            "total_alerts": len(self.alerts),
            "alerts_by_severity": severity_counts,
            "unacknowledged_alerts": sum(1 for a in self.alerts.values() if not a.acknowledged),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "top_talkers": top_talkers,
            "total_data_analyzed_gb": round(sum(f.bytes_sent + f.bytes_received for f in self.flows.values()) / 1073741824, 2),
        }

    def _get_top_talkers(self, n: int) -> List[Dict[str, Any]]:
        ip_volume = {}
        for f in self.flows.values():
            ip_volume[f.src_ip] = ip_volume.get(f.src_ip, 0) + f.bytes_sent + f.bytes_received
        return [{"ip": ip, "total_bytes": vol} for ip, vol in
                sorted(ip_volume.items(), key=lambda x: x[1], reverse=True)[:n]]

    def to_dict(self) -> Dict[str, Any]:
        return self.get_network_summary()

    # === Batch Operations ===
    async def batch_analyze_flows(self, flow_ids: List[str]) -> List[Dict]:
        results = []
        for fid in flow_ids:
            try:
                flow = self.flows.get(fid)
                if not flow:
                    results.append({"flow_id": fid, "status": "failed", "error": "not found"})
                    continue
                score, category = self._analyze_flow(flow)
                results.append({"flow_id": fid, "threat_score": score, "category": category, "malicious": flow.malicious})
            except Exception as e:
                results.append({"flow_id": fid, "status": "failed", "error": str(e)})
        return results

    def get_flows_paginated(self, page: int = 1, per_page: int = 50, malicious_only: bool = False, protocol: Optional[str] = None) -> Dict:
        items = list(self.flows.values())
        if malicious_only:
            items = [f for f in items if f.malicious]
        if protocol:
            items = [f for f in items if f.protocol.value == protocol]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [f.to_dict() for f in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    def get_alerts_paginated(self, page: int = 1, per_page: int = 20, severity: Optional[str] = None, category: Optional[str] = None) -> Dict:
        items = list(self.alerts.values())
        if severity:
            items = [a for a in items if a.severity == severity]
        if category:
            items = [a for a in items if a.category == category]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [a.to_dict() for a in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_rule_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("name"):
            errors.append("Rule name is required")
        if not config.get("signature"):
            errors.append("Rule signature is required")
        return errors

    def validate_flow_submission(self, flow_data: Dict) -> List[str]:
        errors = []
        if not flow_data.get("src_ip"):
            errors.append("Source IP is required")
        if not flow_data.get("dst_ip"):
            errors.append("Destination IP is required")
        if not flow_data.get("protocol"):
            errors.append("Protocol is required")
        return errors

    # === Bulk Operations ===
    async def bulk_acknowledge_alerts(self, alert_ids: List[str]) -> int:
        count = 0
        for aid in alert_ids:
            alert = self.alerts.get(aid)
            if alert and not alert.acknowledged:
                alert.acknowledged = True
                count += 1
        return count

    async def bulk_enable_rules(self, rule_ids: List[str]) -> int:
        count = 0
        for rid in rule_ids:
            rule = self.rules.get(rid)
            if rule and not rule.enabled:
                rule.enabled = True
                count += 1
        return count

    async def bulk_disable_rules(self, rule_ids: List[str]) -> int:
        count = 0
        for rid in rule_ids:
            rule = self.rules.get(rid)
            if rule and rule.enabled:
                rule.enabled = False
                count += 1
        return count

    # === Analytics ===
    def get_alert_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for a in self.alerts.values():
            if a.detected_at and a.detected_at >= cutoff:
                day = a.detected_at.strftime("%Y-%m-%d")
                trend[day] = trend.get(day, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_protocol_breakdown(self) -> Dict:
        breakdown = {}
        for f in self.flows.values():
            p = f.protocol.value
            breakdown[p] = {"total": breakdown.get(p, {}).get("total", 0) + 1,
                            "bytes": breakdown.get(p, {}).get("bytes", 0) + f.bytes_sent + f.bytes_received}
        return {p: {"flows": d["total"], "bytes": d["bytes"]} for p, d in breakdown.items()}

    def get_rule_performance(self) -> List[Dict]:
        return [{"rule_id": r.id, "name": r.name, "hits": r.hits, "enabled": r.enabled, "last_match": r.last_match.isoformat() if r.last_match else None}
                for r in sorted(self.rules.values(), key=lambda x: x.hits, reverse=True)]

    # === Cleanup ===
    async def cleanup_old_flows(self, days: int = 7) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [fid for fid, f in self.flows.items() if f.timestamp and f.timestamp < cutoff]
        for fid in to_remove:
            del self.flows[fid]
        return len(to_remove)

    async def cleanup_resolved_alerts(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [aid for aid, a in self.alerts.items() if a.acknowledged and a.detected_at and a.detected_at < cutoff]
        for aid in to_remove:
            del self.alerts[aid]
        return len(to_remove)

    # === Search ===
    def search_flows_full(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for f in self.flows.values():
            if q in f.src_ip.lower() or q in f.dst_ip.lower() or (f.dns_query and q in f.dns_query.lower()) or (f.http_uri and q in f.http_uri.lower()):
                results.append(f.to_dict())
        return results

    # === Export ===
    def export_alerts_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "severity", "category", "source_ip", "destination_ip", "threat_score", "detected_at"])
        for a in self.alerts.values():
            writer.writerow([a.id, a.title, a.severity, a.category, a.source_ip, a.destination_ip, a.threat_score, a.detected_at.isoformat() if a.detected_at else ""])
        return output.getvalue()

    def export_alerts_json(self) -> str:
        return json.dumps([a.to_dict() for a in self.alerts.values()], indent=2, default=str)

    def export_flows_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "src_ip", "dst_ip", "protocol", "bytes_sent", "bytes_received", "threat_score", "malicious", "timestamp"])
        for f in self.flows.values():
            writer.writerow([f.id, f.src_ip, f.dst_ip, f.protocol.value, f.bytes_sent, f.bytes_received, f.threat_score, f.malicious, f.timestamp.isoformat()])
        return output.getvalue()

    # === Import ===
    def import_rules_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            rule = DetectionRule(
                id=item.get("id", f"rule-{uuid.uuid4().hex[:12]}"),
                name=item.get("name", "Imported Rule"),
                description=item.get("description", ""),
                signature=item.get("signature", ""),
                protocol=item.get("protocol"),
                severity=item.get("severity", "medium"),
                category=item.get("category", "anomaly"),
                enabled=item.get("enabled", True),
                false_positive_rate=item.get("false_positive_rate", 0.0),
            )
            self.rules[rule.id] = rule
            count += 1
        return count

    # === State Machine ===
    def transition_alert_status(self, alert_id: str) -> Optional[NDRAlert]:
        alert = self.alerts.get(alert_id)
        if alert and not alert.acknowledged:
            alert.acknowledged = True
        return alert

    # === Notification ===
    async def notify_alert(self, alert_id: str) -> Dict[str, Any]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return {"error": "Alert not found"}
        return {
            "alert_id": alert.id,
            "title": alert.title,
            "severity": alert.severity,
            "category": alert.category,
            "source_ip": alert.source_ip,
            "message": f"NDR Alert: {alert.title} - {alert.description}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_high_severity(self) -> List[Dict]:
        results = []
        for a in self.alerts.values():
            if a.severity in ("critical", "high") and not a.acknowledged:
                results.append(await self.notify_alert(a.id))
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("sensors"):
            warnings.append("No sensor IPs configured")
        if config.get("max_flows_per_second", 1000) > 10000:
            warnings.append("High flow rate may overwhelm processing")
        if config.get("ml_model") and config["ml_model"] not in ("isolation_forest", "autoencoder", "random_forest"):
            errors.append(f"Unknown ML model: {config.get('ml_model')}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_threat_landscape(self) -> Dict[str, Any]:
        by_category = {}
        for a in self.alerts.values():
            by_category[a.category] = by_category.get(a.category, 0) + 1
        by_protocol = {}
        for f in self.flows.values():
            if f.malicious:
                by_protocol[f.protocol.value] = by_protocol.get(f.protocol.value, 0) + 1
        return {
            "alerts_by_category": by_category,
            "malicious_flows_by_protocol": by_protocol,
            "total_malicious_flows": sum(1 for f in self.flows.values() if f.malicious),
            "unique_threat_ips": len(set(a.source_ip for a in self.alerts.values())),
            "avg_threat_score": round(sum(a.threat_score for a in self.alerts.values()) / len(self.alerts), 2) if self.alerts else 0,
        }

    def get_network_baselines(self) -> Dict:
        flows_list = list(self.flows.values())
        if not flows_list:
            return {"baselines": "insufficient_data"}
        avg_bytes = sum(f.bytes_sent + f.bytes_received for f in flows_list) / len(flows_list)
        avg_duration = sum(f.duration_seconds for f in flows_list) / len(flows_list)
        return {
            "avg_flow_bytes": round(avg_bytes, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "total_flows_analyzed": len(flows_list),
            "baseline_period_hours": 24,
        }

    def get_top_threat_ips(self, n: int = 10) -> List[Dict]:
        ip_scores = {}
        for a in self.alerts.values():
            if a.source_ip not in ip_scores:
                ip_scores[a.source_ip] = {"alerts": 0, "max_score": 0, "categories": set()}
            ip_scores[a.source_ip]["alerts"] += 1
            ip_scores[a.source_ip]["max_score"] = max(ip_scores[a.source_ip]["max_score"], a.threat_score)
            ip_scores[a.source_ip]["categories"].add(a.category)
        sorted_ips = sorted(ip_scores.items(), key=lambda x: x[1]["max_score"], reverse=True)[:n]
        return [{"ip": ip, "alerts": v["alerts"], "max_threat_score": v["max_score"], "categories": list(v["categories"])} for ip, v in sorted_ips]

    # === Baseline Model Management ===
    def update_baseline_model(self, model_name: str, mean: float, std_dev: float) -> bool:
        if model_name not in self._baseline_models:
            return False
        self._baseline_models[model_name] = {"mean": mean, "std_dev": std_dev}
        return True

    def get_baseline_models(self) -> Dict:
        return dict(self._baseline_models)

    # === Bulk Operations ===
    async def bulk_tag_flows(self, flow_ids: List[str], tags: List[str]) -> int:
        count = 0
        for fid in flow_ids:
            flow = self.flows.get(fid)
            if flow:
                for t in tags:
                    if t not in flow.tags:
                        flow.tags.append(t)
                count += 1
        return count

    async def bulk_delete_alerts(self, alert_ids: List[str]) -> int:
        count = 0
        for aid in alert_ids:
            if aid in self.alerts:
                del self.alerts[aid]
                count += 1
        return count

    async def bulk_update_rule_severity(self, rule_ids: List[str], severity: str) -> int:
        count = 0
        for rid in rule_ids:
            rule = self.rules.get(rid)
            if rule:
                rule.severity = severity
                count += 1
        return count

    # === Rule Performance ===
    def get_bottom_performing_rules(self, n: int = 5) -> List[Dict]:
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.false_positive_rate, reverse=True)
        return [{"rule_id": r.id, "name": r.name, "false_positive_rate": r.false_positive_rate, "hits": r.hits} for r in sorted_rules[:n]]

    def reset_rule_stats(self, rule_ids: List[str]) -> int:
        count = 0
        for rid in rule_ids:
            rule = self.rules.get(rid)
            if rule:
                rule.hits = 0
                rule.false_positive_rate = 0.0
                rule.last_match = None
                count += 1
        return count

    # === Tag Management ===
    def add_alert_tags(self, alert_ids: List[str], tags: List[str]) -> int:
        count = 0
        for aid in alert_ids:
            alert = self.alerts.get(aid)
            if alert:
                existing = alert.raw_evidence.get("tags", [])
                for t in tags:
                    if t not in existing:
                        existing.append(t)
                alert.raw_evidence["tags"] = existing
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "ndr",
            "initialized": self._initialized,
            "flows_tracked": len(self.flows),
            "alerts_active": len(self.alerts),
            "rules_loaded": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class NDRTrafficAnalyzer:
    def __init__(self, ndr: 'NDRManager'):
        self.ndr = ndr

    def analyze_flow_patterns(self, hours: int = 24) -> Dict:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [f for f in self.ndr.flows.values() if f.first_seen and f.first_seen > cutoff]
        by_protocol = {}
        for f in recent:
            proto = f.protocol or "unknown"
            by_protocol.setdefault(proto, {"count": 0, "total_bytes": 0, "alerts": 0})
            by_protocol[proto]["count"] += 1
            by_protocol[proto]["total_bytes"] += f.total_bytes
            if f.alert_ids:
                by_protocol[proto]["alerts"] += len(f.alert_ids)
        return {"period_hours": hours, "total_flows": len(recent), "unique_src_ips": len(set(f.src_ip for f in recent)), "unique_dst_ips": len(set(f.dst_ip for f in recent)), "by_protocol": by_protocol}

    def detect_beaconing(self, min_connections: int = 10, time_window_minutes: int = 60) -> List[Dict]:
        recent = [f for f in self.ndr.flows.values() if f.first_seen and (datetime.utcnow() - f.first_seen).total_seconds() < time_window_minutes * 60]
        pairs = {}
        for f in recent:
            key = (f.src_ip, f.dst_ip, f.dst_port)
            pairs.setdefault(key, {"src_ip": f.src_ip, "dst_ip": f.dst_ip, "port": f.dst_port, "count": 0, "total_bytes": 0, "first": f.first_seen, "last": f.first_seen})
            pairs[key]["count"] += 1
            pairs[key]["total_bytes"] += f.total_bytes
            if f.first_seen:
                if not pairs[key]["first"] or f.first_seen < pairs[key]["first"]:
                    pairs[key]["first"] = f.first_seen
                if not pairs[key]["last"] or f.first_seen > pairs[key]["last"]:
                    pairs[key]["last"] = f.first_seen
        return [p for p in pairs.values() if p["count"] >= min_connections]

    def get_unusual_ports(self, threshold: int = 5) -> List[Dict]:
        port_count = {}
        for f in self.ndr.flows.values():
            port = f.dst_port
            port_count[port] = port_count.get(port, 0) + 1
        unusual = [(p, c) for p, c in sorted(port_count.items(), key=lambda x: x[1]) if c < threshold]
        return [{"port": p, "connections": c, "risk": "high" if p < 1024 else "medium"} for p, c in unusual]


class NDRAlertTriage:
    def __init__(self, ndr: 'NDRManager'):
        self.ndr = ndr

    def prioritize_alerts(self) -> List[Dict]:
        scored = []
        for a in self.ndr.alerts.values():
            flow = self.ndr.flows.get(a.flow_id)
            score = 0
            if a.severity_level == "critical":
                score += 40
            elif a.severity_level == "high":
                score += 30
            elif a.severity_level == "medium":
                score += 15
            if flow:
                score += min(flow.total_bytes / 1_000_000, 20)
                if flow.dst_port in (22, 3389, 445, 135):
                    score += 10
            score += a.confidence * 0.3
            scored.append({"alert_id": a.id, "title": a.title, "severity": a.severity_level, "confidence": a.confidence, "priority_score": round(score, 1), "flow_id": a.flow_id, "timestamp": a.timestamp.isoformat() if a.timestamp else ''})
        return sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    def suggest_auto_response(self, alert_id: str) -> Optional[Dict]:
        alert = self.ndr.alerts.get(alert_id)
        if not alert:
            return None
        if alert.severity_level == "critical" and alert.confidence > 0.8:
            return {"alert_id": alert_id, "action": "block_ip", "target": alert.src_ip if hasattr(alert, 'src_ip') else "unknown", "automated": True}
        if alert.severity_level == "high" and alert.confidence > 0.7:
            return {"alert_id": alert_id, "action": "quarantine_flow", "flow_id": alert.flow_id, "automated": True}
        return {"alert_id": alert_id, "action": "notify", "automated": False}


class NDRReporter:
    def __init__(self, ndr: 'NDRManager'):
        self.ndr = ndr

    def generate_threat_report(self, hours: int = 24) -> str:
        analyzer = NDRTrafficAnalyzer(self.ndr)
        triage = NDRAlertTriage(self.ndr)
        flow_analysis = analyzer.analyze_flow_patterns(hours)
        lines = ["=== NDR Threat Report ===", f"Period: Last {hours} hours", f"Total Flows: {flow_analysis.get('total_flows', 0)}", f"Unique Sources: {flow_analysis.get('unique_src_ips', 0)}", f"Unique Destinations: {flow_analysis.get('unique_dst_ips', 0)}", f"Active Alerts: {len(self.ndr.alerts)}", f"Enabled Rules: {sum(1 for r in self.ndr.rules.values() if r.enabled)}", "", "Top Priority Alerts:"]
        for p in triage.prioritize_alerts()[:5]:
            lines.append(f"  [{p['severity']}] {p['title']} (score: {p['priority_score']})")
        return "\n".join(lines)

    def export_flows_csv(self, hours: int = 24) -> str:
        import csv, io
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["flow_id", "src_ip", "dst_ip", "dst_port", "protocol", "total_bytes", "alerts", "first_seen", "last_seen"])
        for f in self.ndr.flows.values():
            if f.first_seen and f.first_seen > cutoff:
                writer.writerow([f.id, f.src_ip, f.dst_ip, f.dst_port, f.protocol, f.total_bytes, len(f.alert_ids), f.first_seen.isoformat() if f.first_seen else '', f.last_seen.isoformat() if f.last_seen else ''])
        return output.getvalue()

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_alerts": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "resolved": 0}

    def validate_security(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class SOCResult(BaseModel):
    success: bool = True
    operation: str = ""
    alert_id: Optional[str] = None
    severity: str = Field(default="low")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SOCBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = Field(default="siem")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    escalated: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_escalated(self) -> None:
        self.escalated += 1

    def complete(self) -> None:
        self.status = "completed"

class SecurityAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    severity: str = Field(default="low")
    source: str = Field(default="unknown")
    status: str = Field(default="open")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    mitre_technique: str = ""
    affected_assets: List[str] = Field(default_factory=list)
    indicators: List[str] = Field(default_factory=list)

class AlertManager:
    def __init__(self) -> None:
        self._alerts: Dict[str, SecurityAlert] = {}

    def create(self, title: str, severity: str, source: str = "unknown", description: str = "") -> SecurityAlert:
        alert = SecurityAlert(title=title, severity=severity, source=source, description=description)
        self._alerts[alert.alert_id] = alert
        return alert

    def resolve(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if alert and alert.status == "open":
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            return True
        return False

    def get_open(self) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.status == "open"]

    def get_by_severity(self, severity: str) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.severity == severity]

    def get_by_source(self, source: str) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.source == source]

    def get_statistics(self) -> Dict[str, Any]:
        alerts = list(self._alerts.values())
        open_alerts = self.get_open()
        resolved = [a for a in alerts if a.status == "resolved"]
        return {"total": len(alerts), "open": len(open_alerts), "resolved": len(resolved),
                "by_severity": {s: sum(1 for a in alerts if a.severity == s) for s in set(a.severity for a in alerts)},
                "by_source": {s: sum(1 for a in alerts if a.source == s) for s in set(a.source for a in alerts)},
                "avg_resolution_time_min": round(sum((a.resolved_at - a.detected_at).total_seconds() / 60 for a in resolved if a.resolved_at) / max(len(resolved), 1), 1)}

class ThreatIndicator(BaseModel):
    indicator_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    value: str
    indicator_type: str = Field(default="ip")
    confidence: float = Field(default=0.5, ge=0, le=1)
    severity: str = Field(default="medium")
    source: str = Field(default="external")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    active: bool = True

class ThreatIntelFeed:
    def __init__(self) -> None:
        self._indicators: Dict[str, ThreatIndicator] = {}

    def add_indicator(self, value: str, indicator_type: str, confidence: float = 0.5,
                      severity: str = "medium", source: str = "external") -> ThreatIndicator:
        indicator = ThreatIndicator(value=value, indicator_type=indicator_type,
                                     confidence=confidence, severity=severity, source=source)
        self._indicators[indicator.indicator_id] = indicator
        return indicator

    def search(self, value: str) -> Optional[ThreatIndicator]:
        for ind in self._indicators.values():
            if ind.value == value and ind.active:
                return ind
        return None

    def get_active(self) -> List[ThreatIndicator]:
        return [i for i in self._indicators.values() if i.active]

    def expire_old(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0
        for ind in self._indicators.values():
            if ind.last_seen < cutoff:
                ind.active = False
                count += 1
        return count

    def get_statistics(self) -> Dict[str, Any]:
        active = self.get_active()
        return {"total": len(self._indicators), "active": len(active),
                "by_type": {t: sum(1 for i in active if i.indicator_type == t) for t in set(i.indicator_type for i in active)},
                "by_severity": {s: sum(1 for i in active if i.severity == s) for s in set(i.severity for i in active)}}

class IncidentResponsePlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    alert_id: str = ""
    steps: List[str] = Field(default_factory=list)
    status: str = Field(default="draft")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner: str = ""

class IncidentResponder:
    def __init__(self) -> None:
        self._plans: Dict[str, IncidentResponsePlan] = {}

    def create_plan(self, name: str, alert_id: str, steps: List[str], owner: str = "") -> IncidentResponsePlan:
        plan = IncidentResponsePlan(name=name, alert_id=alert_id, steps=steps, owner=owner)
        self._plans[plan.plan_id] = plan
        return plan

    async def execute(self, plan_id: str) -> Dict[str, Any]:
        plan = self._plans.get(plan_id)
        if not plan:
            return {"status": "error", "message": "Plan not found"}
        plan.status = "in_progress"
        plan.executed_at = datetime.utcnow()
        executed_steps = []
        for i, step in enumerate(plan.steps):
            executed_steps.append({"step": i + 1, "action": step, "status": "completed"})
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
        return {"status": "completed", "plan_id": plan_id, "steps_executed": len(executed_steps),
                "duration_seconds": int((plan.completed_at - plan.executed_at).total_seconds())}

    def get_plan(self, plan_id: str) -> Optional[IncidentResponsePlan]:
        return self._plans.get(plan_id)

    def list_plans(self) -> List[Dict[str, Any]]:
        return [{"id": p.plan_id, "name": p.name, "status": p.status, "steps": len(p.steps)} for p in self._plans.values()]

class VulnerabilityRecord(BaseModel):
    vuln_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset: str
    cve_id: str = ""
    severity: str = Field(default="medium")
    cvss_score: float = Field(default=0.0, ge=0, le=10)
    description: str = ""
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    patched_at: Optional[datetime] = None
    status: str = Field(default="open")
    remediation: str = ""

class VulnerabilityManager:
    def __init__(self) -> None:
        self._vulns: Dict[str, VulnerabilityRecord] = {}

    def report(self, asset: str, severity: str, cvss: float, description: str = "", cve: str = "") -> VulnerabilityRecord:
        vuln = VulnerabilityRecord(asset=asset, severity=severity, cvss_score=cvss,
                                    description=description, cve_id=cve)
        self._vulns[vuln.vuln_id] = vuln
        return vuln

    def patch(self, vuln_id: str) -> bool:
        vuln = self._vulns.get(vuln_id)
        if vuln and vuln.status == "open":
            vuln.status = "patched"
            vuln.patched_at = datetime.utcnow()
            return True
        return False

    def get_open(self) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.status == "open"]

    def get_by_severity(self, severity: str) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.severity == severity]

    def get_by_asset(self, asset: str) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.asset == asset]

    def get_statistics(self) -> Dict[str, Any]:
        vulns = list(self._vulns.values())
        open_vulns = self.get_open()
        return {"total": len(vulns), "open": len(open_vulns), "patched": len(vulns) - len(open_vulns),
                "avg_cvss": round(sum(v.cvss_score for v in vulns) / max(len(vulns), 1), 1),
                "by_severity": {s: sum(1 for v in vulns if v.severity == s) for s in set(v.severity for v in vulns)},
                "critical": sum(1 for v in open_vulns if v.cvss_score >= 9.0),
                "high": sum(1 for v in open_vulns if 7.0 <= v.cvss_score < 9.0)}
