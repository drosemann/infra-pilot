"""Deception Technology for proactive threat detection.

Deploy decoy resources including honeypots, honey tokens, fake databases, and
simulated environments. Alert on engagement, capture attacker forensics.
"""

import json
import uuid
import hashlib
import logging
import asyncio
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DecoyType(str, Enum):
    HONEYPOT = "honeypot"
    HONEYTOKEN = "honeytoken"
    FAKE_DATABASE = "fake_database"
    FAKE_FILE = "fake_file"
    FAKE_CREDENTIAL = "fake_credential"
    FAKE_ENDPOINT = "fake_endpoint"
    FAKE_SERVICE = "fake_service"
    FAKE_API_KEY = "fake_api_key"
    FAKE_SSL_CERT = "fake_ssl_cert"
    FAKE_CONFIG = "fake_config"
    FAKE_BUCKET = "fake_bucket"
    FAKE_DNS_RECORD = "fake_dns_record"


class DecoyStatus(str, Enum):
    DEPLOYED = "deployed"
    ENGAGED = "engaged"
    COMPROMISED = "compromised"
    DECOMMISSIONED = "decommissioned"
    PENDING = "pending"


class AlertSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Decoy:
    id: str
    name: str
    decoy_type: DecoyType
    status: DecoyStatus = DecoyStatus.PENDING
    deployed_at: Optional[datetime] = None
    last_engaged: Optional[datetime] = None
    engagement_count: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    network_zone: str = "internal"
    ttl_hours: int = 168
    forensics: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "decoy_type": self.decoy_type.value,
            "status": self.status.value,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "last_engaged": self.last_engaged.isoformat() if self.last_engaged else None,
            "engagement_count": self.engagement_count,
            "tags": self.tags,
            "network_zone": self.network_zone,
            "ttl_hours": self.ttl_hours,
            "forensics_count": len(self.forensics),
            "alerts_count": len(self.alerts),
        }


@dataclass
class HoneyToken:
    id: str
    name: str
    value: str
    decoy_type: DecoyType
    deployed_at: datetime
    status: DecoyStatus = DecoyStatus.DEPLOYED
    last_accessed: Optional[datetime] = None
    accessed_by: Optional[str] = None
    access_count: int = 0
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    location: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "value": f"{self.value[:8]}...{self.value[-4:]}",
            "decoy_type": self.decoy_type.value,
            "deployed_at": self.deployed_at.isoformat(),
            "status": self.status.value,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "source_ip": self.source_ip,
        }


@dataclass
class DeceptionEvent:
    id: str
    decoy_id: str
    decoy_name: str
    decoy_type: str
    event_type: str
    severity: AlertSeverity
    timestamp: datetime
    source_ip: str
    description: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    mitre_technique: Optional[str] = None
    user_agent: Optional[str] = None
    geo_country: Optional[str] = None
    processed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "decoy_id": self.decoy_id,
            "decoy_name": self.decoy_name,
            "decoy_type": self.decoy_type,
            "event_type": self.event_type,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "description": self.description,
            "mitre_technique": self.mitre_technique,
            "processed": self.processed,
        }


class DeceptionTechnology:
    """Deploy and manage decoy resources for proactive threat detection."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.decoys: Dict[str, Decoy] = {}
        self.honey_tokens: Dict[str, HoneyToken] = {}
        self.events: Dict[str, DeceptionEvent] = {}
        self._initialized = False

    def _generate_honey_token_value(self, decoy_type: DecoyType) -> str:
        if decoy_type == DecoyType.FAKE_CREDENTIAL:
            return f"svc_{uuid.uuid4().hex[:12]}:P@ssw0rd_{uuid.uuid4().hex[:8]}"
        elif decoy_type == DecoyType.FAKE_API_KEY:
            return f"sk-{uuid.uuid4().hex[:24]}"
        elif decoy_type == DecoyType.FAKE_SSL_CERT:
            return f"-----BEGIN CERTIFICATE-----\n{random.choice(['MII', 'MIIB', 'MIIC'])}+{uuid.uuid4().hex[:40]}\n-----END CERTIFICATE-----"
        elif decoy_type == DecoyType.FAKE_DNS_RECORD:
            return f"internal-db-{uuid.uuid4().hex[:8]}.corp.example.com"
        elif decoy_type == DecoyType.FAKE_CONFIG:
            return json.dumps({"database": {"host": f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}",
                                            "port": 5432, "db": "prod_main",
                                            "user": "dbadmin", "password": uuid.uuid4().hex[:16]}})
        else:
            return uuid.uuid4().hex[:24]

    async def initialize(self):
        self._deploy_default_decoys()
        self._initialized = True
        logger.info(f"Deception Technology initialized: {len(self.decoys)} decoys, {len(self.honey_tokens)} honey tokens")

    async def close(self):
        logger.info("Deception Technology shut down")

    def _deploy_default_decoys(self):
        default_decoys = [
            Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name="SSH Honeypot (22)", decoy_type=DecoyType.HONEYPOT,
                  status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(), tags=["ssh", "cowrie"],
                  network_zone="dmz", config={"port": 22, "type": "cowrie", "log_auth_attempts": True,
                                               "capture_downloads": True, "max_connections": 10}),
            Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name="HTTP Honeypot (80/443)", decoy_type=DecoyType.HONEYPOT,
                  status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(), tags=["http", "web", "apache"],
                  network_zone="dmz", config={"port": 80, "type": "heralding", "ssl_port": 443,
                                               "serve_fake_content": True, "log_requests": True}),
            Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name="MySQL Fake Database", decoy_type=DecoyType.FAKE_DATABASE,
                  status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(), tags=["database", "mysql", "sql-injection"],
                  network_zone="internal", config={"port": 3306, "db_type": "mysql", "fake_tables": ["users", "customers", "payments"],
                                                    "rows_count": 1000, "log_queries": True}),
            Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name="RDP Honeypot (3389)", decoy_type=DecoyType.HONEYPOT,
                  status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(), tags=["rdp", "windows", "brute-force"],
                  network_zone="dmz", config={"port": 3389, "type": "rdpy", "fake_domain": "corp.local",
                                               "capture_credentials": True}),
            Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name="Fake S3 Bucket", decoy_type=DecoyType.FAKE_BUCKET,
                  status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(), tags=["s3", "cloud", "data-exfil"],
                  network_zone="cloud", config={"bucket_name": f"prod-backup-{uuid.uuid4().hex[:8]}",
                                                 "region": "us-east-1", "fake_files": 50}),
            Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name="Internal GitLab Clone", decoy_type=DecoyType.FAKE_ENDPOINT,
                  status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(), tags=["gitlab", "ci-cd", "source-code"],
                  network_zone="internal", config={"service": "gitlab", "fake_repos": 10, "fake_tokens": 5}),
        ]
        for decoy in default_decoys:
            self.decoys[decoy.id] = decoy
            for _ in range(3):
                ht = HoneyToken(
                    id=f"ht-{uuid.uuid4().hex[:12]}", name=f"{decoy.name} Token #{_+1}",
                    value=self._generate_honey_token_value(decoy.decoy_type),
                    decoy_type=decoy.decoy_type, deployed_at=datetime.utcnow(),
                )
                self.honey_tokens[ht.id] = ht

    def deploy_decoy(self, name: str, decoy_type: str, network_zone: str = "internal",
                     tags: Optional[List[str]] = None, config: Optional[Dict[str, Any]] = None) -> Decoy:
        decoy = Decoy(id=f"decoy-{uuid.uuid4().hex[:12]}", name=name, decoy_type=DecoyType(decoy_type),
                      status=DecoyStatus.DEPLOYED, deployed_at=datetime.utcnow(),
                      tags=tags or [], network_zone=network_zone, config=config or {})
        self.decoys[decoy.id] = decoy
        for _ in range(2):
            ht = HoneyToken(id=f"ht-{uuid.uuid4().hex[:12]}", name=f"{name} Token #{_+1}",
                            value=self._generate_honey_token_value(decoy.decoy_type),
                            decoy_type=decoy.decoy_type, deployed_at=datetime.utcnow())
            self.honey_tokens[ht.id] = ht
        return decoy

    def decommission_decoy(self, decoy_id: str) -> bool:
        decoy = self.decoys.get(decoy_id)
        if not decoy:
            return False
        decoy.status = DecoyStatus.DECOMMISSIONED
        for ht in self.honey_tokens.values():
            if ht.decoy_type == decoy.decoy_type and ht.status == DecoyStatus.DEPLOYED:
                ht.status = DecoyStatus.DECOMMISSIONED
        return True

    def get_decoy(self, decoy_id: str) -> Optional[Decoy]:
        return self.decoys.get(decoy_id)

    def list_decoys(self, decoy_type: Optional[str] = None, status: Optional[str] = None,
                    network_zone: Optional[str] = None) -> List[Decoy]:
        results = list(self.decoys.values())
        if decoy_type:
            results = [d for d in results if d.decoy_type.value == decoy_type]
        if status:
            results = [d for d in results if d.status.value == status]
        if network_zone:
            results = [d for d in results if d.network_zone == network_zone]
        return sorted(results, key=lambda d: d.deployed_at or datetime.min, reverse=True)

    def simulate_engagement(self, decoy_id: str, attacker_ip: str, event_type: str = "connection",
                            user_agent: Optional[str] = None) -> DeceptionEvent:
        decoy = self.decoys.get(decoy_id)
        if not decoy:
            raise ValueError(f"Decoy {decoy_id} not found")
        decoy.status = DecoyStatus.ENGAGED
        decoy.last_engaged = datetime.utcnow()
        decoy.engagement_count += 1
        severity_map = {
            "connection": AlertSeverity.LOW, "authentication_attempt": AlertSeverity.MEDIUM,
            "credential_use": AlertSeverity.HIGH, "data_access": AlertSeverity.CRITICAL,
            "file_download": AlertSeverity.HIGH, "command_execution": AlertSeverity.CRITICAL,
            "scanning": AlertSeverity.LOW, "brute_force": AlertSeverity.MEDIUM,
        }
        event = DeceptionEvent(
            id=f"ev-{uuid.uuid4().hex[:12]}", decoy_id=decoy_id, decoy_name=decoy.name,
            decoy_type=decoy.decoy_type.value, event_type=event_type,
            severity=severity_map.get(event_type, AlertSeverity.INFO),
            timestamp=datetime.utcnow(), source_ip=attacker_ip,
            description=f"Decoy {decoy.name} engaged by {attacker_ip} via {event_type}",
            user_agent=user_agent,
        )
        self.events[event.id] = event
        forensics_entry = {
            "id": f"fr-{uuid.uuid4().hex[:12]}",
            "timestamp": event.timestamp.isoformat(),
            "source_ip": attacker_ip,
            "event_type": event_type,
            "user_agent": user_agent,
            "payload": event.raw_data,
            "pcap_file": f"/data/forensics/pcap/{event.id}.pcap",
        }
        decoy.forensics.append(forensics_entry)
        alert = {
            "id": f"alert-{uuid.uuid4().hex[:12]}",
            "severity": event.severity.value,
            "title": f"Decoy Engagement: {decoy.name}",
            "description": event.description,
            "timestamp": event.timestamp.isoformat(),
            "acknowledged": False,
        }
        decoy.alerts.append(alert)
        logger.warning(f"Deception engagement: {decoy.name} touched by {attacker_ip} ({event_type})")
        return event

    def create_honey_token(self, name: str, decoy_type: str) -> HoneyToken:
        dt = DecoyType(decoy_type)
        ht = HoneyToken(id=f"ht-{uuid.uuid4().hex[:12]}", name=name,
                        value=self._generate_honey_token_value(dt),
                        decoy_type=dt, deployed_at=datetime.utcnow())
        self.honey_tokens[ht.id] = ht
        return ht

    def list_honey_tokens(self, decoy_type: Optional[str] = None, status: Optional[str] = None) -> List[HoneyToken]:
        results = list(self.honey_tokens.values())
        if decoy_type:
            results = [h for h in results if h.decoy_type.value == decoy_type]
        if status:
            results = [h for h in results if h.status.value == status]
        return results

    def get_honey_token(self, token_id: str) -> Optional[HoneyToken]:
        return self.honey_tokens.get(token_id)

    def simulate_token_access(self, token_id: str, source_ip: str, user_agent: Optional[str] = None) -> HoneyToken:
        ht = self.honey_tokens.get(token_id)
        if not ht:
            raise ValueError(f"Honey token {token_id} not found")
        ht.status = DecoyStatus.ENGAGED
        ht.last_accessed = datetime.utcnow()
        ht.access_count += 1
        ht.source_ip = source_ip
        ht.user_agent = user_agent
        event = DeceptionEvent(
            id=f"ev-{uuid.uuid4().hex[:12]}", decoy_id=token_id, decoy_name=ht.name,
            decoy_type=ht.decoy_type.value, event_type="honeytoken_access",
            severity=AlertSeverity.CRITICAL, timestamp=datetime.utcnow(),
            source_ip=source_ip,
            description=f"Honey token '{ht.name}' accessed from {source_ip}",
            user_agent=user_agent, mitre_technique="T1552.001",
        )
        self.events[event.id] = event
        logger.error(f"HONEY TOKEN TRIGGERED: {ht.name} accessed by {source_ip}")
        return ht

    def list_events(self, decoy_id: Optional[str] = None, severity: Optional[str] = None,
                    limit: int = 100) -> List[DeceptionEvent]:
        results = list(self.events.values())
        if decoy_id:
            results = [e for e in results if e.decoy_id == decoy_id]
        if severity:
            results = [e for e in results if e.severity.value == severity]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_forensics(self, decoy_id: str) -> List[Dict[str, Any]]:
        decoy = self.decoys.get(decoy_id)
        if not decoy:
            return []
        return decoy.forensics

    def get_deception_summary(self) -> Dict[str, Any]:
        engaged_decoys = [d for d in self.decoys.values() if d.status == DecoyStatus.ENGAGED]
        compromised = [d for d in self.decoys.values() if d.status == DecoyStatus.COMPROMISED]
        return {
            "total_decoys": len(self.decoys),
            "total_honey_tokens": len(self.honey_tokens),
            "deployed_decoys": sum(1 for d in self.decoys.values() if d.status == DecoyStatus.DEPLOYED),
            "engaged_decoys": len(engaged_decoys),
            "compromised_decoys": len(compromised),
            "total_events": len(self.events),
            "critical_events": sum(1 for e in self.events.values() if e.severity == AlertSeverity.CRITICAL),
            "high_events": sum(1 for e in self.events.values() if e.severity == AlertSeverity.HIGH),
            "total_forensics_entries": sum(len(d.forensics) for d in self.decoys.values()),
            "engaged_ips": list(set(e.source_ip for e in self.events.values())),
            "decoys_by_type": {t.value: sum(1 for d in self.decoys.values() if d.decoy_type == t) for t in DecoyType},
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_deception_summary()

    # === Batch Operations ===
    async def batch_deploy_decoys(self, decoy_defs: List[Dict]) -> List[Dict]:
        results = []
        for ddef in decoy_defs:
            try:
                decoy = self.deploy_decoy(
                    name=ddef.get("name", "Batch Decoy"),
                    decoy_type=ddef.get("decoy_type", "honeypot"),
                    network_zone=ddef.get("network_zone", "dmz"),
                    ip_address=ddef.get("ip_address", "10.0.0.1"),
                    services=ddef.get("services", ["ssh", "http"]),
                    tags=ddef.get("tags", []),
                    configuration=ddef.get("configuration", {}),
                )
                results.append({"decoy_id": decoy.id, "name": decoy.name, "status": "deployed"})
            except Exception as e:
                results.append({"name": ddef.get("name"), "status": "failed", "error": str(e)})
        return results

    async def batch_create_tokens(self, token_defs: List[Dict]) -> List[Dict]:
        results = []
        for tdef in token_defs:
            try:
                token = self.create_honey_token(
                    token_type=tdef.get("token_type", "credential"),
                    name=tdef.get("name", "Batch Token"),
                    deployment_location=tdef.get("deployment_location", "github"),
                    trigger_conditions=tdef.get("trigger_conditions", {}),
                    tags=tdef.get("tags", []),
                )
                results.append({"token_id": token.id, "name": token.name, "status": "created"})
            except Exception as e:
                results.append({"name": tdef.get("name"), "status": "failed", "error": str(e)})
        return results

    def get_decoys_paginated(self, page: int = 1, per_page: int = 20, status: Optional[str] = None, decoy_type: Optional[str] = None) -> Dict:
        items = list(self.decoys.values())
        if status:
            items = [d for d in items if d.status.value == status]
        if decoy_type:
            items = [d for d in items if d.decoy_type.value == decoy_type]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [d.to_dict() for d in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_decoy_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("name"):
            errors.append("Decoy name is required")
        if not config.get("decoy_type"):
            errors.append("Decoy type is required")
        if not config.get("network_zone"):
            errors.append("Network zone is required")
        return errors

    def validate_token_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("token_type"):
            errors.append("Token type is required")
        if not config.get("name"):
            errors.append("Token name is required")
        return errors

    # === Bulk Operations ===
    async def bulk_disable_decoys(self, decoy_ids: List[str]) -> int:
        count = 0
        for did in decoy_ids:
            decoy = self.decoys.get(did)
            if decoy and decoy.status in (DecoyStatus.DEPLOYED, DecoyStatus.ENGAGED):
                decoy.status = DecoyStatus.INACTIVE
                count += 1
        return count

    async def bulk_remove_tokens(self, token_ids: List[str]) -> int:
        count = 0
        for tid in token_ids:
            if tid in self.honey_tokens:
                del self.honey_tokens[tid]
                count += 1
        return count

    # === Analytics ===
    def get_engagement_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for decoy in self.decoys.values():
            for evt in decoy.forensics:
                if evt.get("timestamp"):
                    try:
                        ts = datetime.fromisoformat(evt["timestamp"])
                        if ts >= cutoff:
                            day = ts.strftime("%Y-%m-%d")
                            trend[day] = trend.get(day, 0) + 1
                    except (ValueError, TypeError):
                        continue
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_attacker_intel(self) -> Dict:
        ips = set()
        for decoy in self.decoys.values():
            if decoy.engaged_by:
                ips.update(decoy.engaged_by)
        return {"unique_attacker_ips": len(ips), "attacker_ips": list(ips), "total_engagements": sum(1 for d in self.decoys.values() if d.status == DecoyStatus.ENGAGED)}

    # === Cleanup ===
    async def cleanup_inactive_decoys(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [did for did, d in self.decoys.items() if d.status == DecoyStatus.INACTIVE and d.last_engaged and d.last_engaged < cutoff]
        for did in to_remove:
            del self.decoys[did]
        return len(to_remove)

    # === Export ===
    def export_forensics_csv(self, decoy_id: str) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "event_type", "source_ip", "details"])
        decoy = self.decoys.get(decoy_id)
        if decoy:
            for f in decoy.forensics:
                writer.writerow([f.get("timestamp"), f.get("event_type"), f.get("source_ip"), f.get("details")])
        return output.getvalue()

    def export_events_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "decoy_name", "event_type", "severity", "source_ip", "timestamp", "description"])
        for e in self.events.values():
            writer.writerow([e.id, e.decoy_name, e.event_type, e.severity.value, e.source_ip, e.timestamp.isoformat(), e.description])
        return output.getvalue()

    def export_decoys_json(self) -> str:
        return json.dumps([d.to_dict() for d in self.decoys.values()], indent=2, default=str)

    # === Import ===
    def import_decoys_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            decoy = Decoy(
                id=item.get("id", f"decoy-{uuid.uuid4().hex[:12]}"),
                name=item.get("name", "Imported Decoy"),
                decoy_type=DecoyType(item.get("decoy_type", "honeypot")),
                status=DecoyStatus(item.get("status", "pending")),
                deployed_at=datetime.fromisoformat(item["deployed_at"]) if item.get("deployed_at") else datetime.utcnow(),
                last_engaged=datetime.fromisoformat(item["last_engaged"]) if item.get("last_engaged") else None,
                engagement_count=item.get("engagement_count", 0),
                config=item.get("config", {}),
                tags=item.get("tags", []),
                network_zone=item.get("network_zone", "internal"),
                ttl_hours=item.get("ttl_hours", 168),
            )
            self.decoys[decoy.id] = decoy
            count += 1
        return count

    # === State Machine ===
    def transition_decoy_status(self, decoy_id: str, target_status: str) -> Optional[Decoy]:
        decoy = self.decoys.get(decoy_id)
        if not decoy:
            return None
        valid = {
            DecoyStatus.PENDING: [DecoyStatus.DEPLOYED, DecoyStatus.DECOMMISSIONED],
            DecoyStatus.DEPLOYED: [DecoyStatus.ENGAGED, DecoyStatus.DECOMMISSIONED],
            DecoyStatus.ENGAGED: [DecoyStatus.COMPROMISED, DecoyStatus.DEPLOYED, DecoyStatus.DECOMMISSIONED],
            DecoyStatus.COMPROMISED: [DecoyStatus.DECOMMISSIONED],
            DecoyStatus.DECOMMISSIONED: [],
        }
        new_status = DecoyStatus(target_status)
        if new_status in valid.get(decoy.status, []):
            decoy.status = new_status
            return decoy
        return None

    def get_allowed_decoy_transitions(self, decoy_id: str) -> List[str]:
        decoy = self.decoys.get(decoy_id)
        if not decoy:
            return []
        transitions = {
            DecoyStatus.PENDING: ["deployed", "decommissioned"],
            DecoyStatus.DEPLOYED: ["engaged", "decommissioned"],
            DecoyStatus.ENGAGED: ["compromised", "deployed", "decommissioned"],
            DecoyStatus.COMPROMISED: ["decommissioned"],
            DecoyStatus.DECOMMISSIONED: [],
        }
        return transitions.get(decoy.status, [])

    # === Notification ===
    async def notify_engagement(self, event: DeceptionEvent) -> Dict[str, Any]:
        return {
            "event_id": event.id,
            "decoy_name": event.decoy_name,
            "severity": event.severity.value,
            "message": f"Decoy engagement: {event.description}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_all_engagements(self) -> List[Dict]:
        results = []
        for e in self.events.values():
            if not e.processed:
                results.append(await self.notify_engagement(e))
                e.processed = True
        return results

    # === Config Validation ===
    def validate_decoy_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("name"):
            errors.append("Decoy name is required")
        if not config.get("decoy_type"):
            errors.append("Decoy type is required")
        if config.get("ttl_hours", 168) < 1:
            errors.append("TTL must be positive")
        if config.get("max_connections", 10) > 100:
            warnings.append("High max connections may exhaust resources")
        if config.get("network_zone") and config["network_zone"] not in ("dmz", "internal", "cloud", "external"):
            errors.append("Network zone must be dmz, internal, cloud, or external")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_engagement_summary(self) -> Dict[str, Any]:
        total_engagements = sum(1 for d in self.decoys.values() if d.engagement_count > 0)
        total_events = len(self.events)
        by_type = {}
        for e in self.events.values():
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        by_severity = {}
        for e in self.events.values():
            by_severity[e.severity.value] = by_severity.get(e.severity.value, 0) + 1
        top_targets = sorted(
            [(d.name, d.engagement_count) for d in self.decoys.values()],
            key=lambda x: x[1], reverse=True
        )[:5]
        return {
            "total_decoys": len(self.decoys),
            "total_honey_tokens": len(self.honey_tokens),
            "engaged_decoys": total_engagements,
            "total_events": total_events,
            "events_by_type": by_type,
            "events_by_severity": by_severity,
            "top_decoys": [{"name": n, "engagements": c} for n, c in top_targets],
            "attacker_ips": len(set(e.source_ip for e in self.events.values())),
        }

    def get_decoy_deployment_stats(self) -> Dict:
        by_zone = {}
        for d in self.decoys.values():
            by_zone[d.network_zone] = by_zone.get(d.network_zone, 0) + 1
        by_type = {}
        for d in self.decoys.values():
            by_type[d.decoy_type.value] = by_type.get(d.decoy_type.value, 0) + 1
        return {"by_network_zone": by_zone, "by_decoy_type": by_type, "total": len(self.decoys)}

    def get_ttl_summary(self) -> Dict:
        expired = sum(1 for d in self.decoys.values() if d.deployed_at and (datetime.utcnow() - d.deployed_at).total_seconds() > d.ttl_hours * 3600)
        expiring_soon = sum(1 for d in self.decoys.values() if d.deployed_at and 0 < (d.ttl_hours * 3600 - (datetime.utcnow() - d.deployed_at).total_seconds()) < 86400)
        return {"total": len(self.decoys), "expired": expired, "expiring_within_24h": expiring_soon}

    # === Forensics ===
    def get_forensics_by_ip(self, ip: str) -> List[Dict]:
        results = []
        for d in self.decoys.values():
            for f in d.forensics:
                if f.get("source_ip") == ip:
                    results.append({"decoy": d.name, "forensics": f})
        return results

    def get_forensic_timeline(self, decoy_id: str) -> List[Dict]:
        decoy = self.decoys.get(decoy_id)
        if not decoy:
            return []
        timeline = []
        for f in sorted(decoy.forensics, key=lambda x: x.get("timestamp", "")):
            timeline.append({"timestamp": f.get("timestamp"), "event": f.get("event_type"), "source": f.get("source_ip"), "detail": f.get("payload")})
        for a in sorted(decoy.alerts, key=lambda x: x.get("timestamp", "")):
            timeline.append({"timestamp": a.get("timestamp"), "event": "alert", "source": a.get("title"), "detail": a.get("description")})
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    # === Bulk Operations ===
    async def bulk_extend_ttl(self, decoy_ids: List[str], extra_hours: int = 24) -> int:
        count = 0
        for did in decoy_ids:
            decoy = self.decoys.get(did)
            if decoy:
                decoy.ttl_hours += extra_hours
                count += 1
        return count

    async def bulk_reset_engagement_counts(self, decoy_ids: List[str]) -> int:
        count = 0
        for did in decoy_ids:
            decoy = self.decoys.get(did)
            if decoy:
                decoy.engagement_count = 0
                count += 1
        return count

    # === Tag Management ===
    def add_decoy_tags(self, decoy_ids: List[str], tags: List[str]) -> int:
        count = 0
        for did in decoy_ids:
            decoy = self.decoys.get(did)
            if decoy:
                for t in tags:
                    if t not in decoy.tags:
                        decoy.tags.append(t)
                count += 1
        return count

    def remove_decoy_tags(self, decoy_ids: List[str], tags: List[str]) -> int:
        count = 0
        for did in decoy_ids:
            decoy = self.decoys.get(did)
            if decoy:
                decoy.tags = [t for t in decoy.tags if t not in tags]
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "deception_tech",
            "initialized": self._initialized,
            "decoys_deployed": len(self.decoys),
            "honey_tokens_active": len(self.honey_tokens),
            "total_events": len(self.events),
            "total_forensics": sum(len(d.forensics) for d in self.decoys.values()),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class DecoyOrchestrator:
    def __init__(self, dt: 'DeceptionTechManager'):
        self.dt = dt
        self.campaigns: Dict[str, Dict] = {}

    def create_campaign(self, name: str, decoy_ids: List[str], description: str = "") -> Dict:
        campaign = {"id": f"camp-{uuid.uuid4().hex[:8]}", "name": name, "decoy_ids": decoy_ids, "description": description, "status": "active", "engagements": 0, "created_at": datetime.utcnow().isoformat()}
        self.campaigns[campaign["id"]] = campaign
        return campaign

    def get_campaign_stats(self, campaign_id: str) -> Optional[Dict]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return None
        total_engagements = sum(self.dt.decoys[did].engagement_count for did in campaign["decoy_ids"] if did in self.dt.decoys)
        return {**campaign, "total_engagements": total_engagements, "active_decoys": sum(1 for did in campaign["decoy_ids"] if did in self.dt.decoys and self.dt.decoys[did].active)}

    def list_campaigns(self) -> List[Dict]:
        return list(self.campaigns.values())

    def pause_campaign(self, campaign_id: str) -> bool:
        campaign = self.campaigns.get(campaign_id)
        if campaign and campaign["status"] == "active":
            campaign["status"] = "paused"
            return True
        return False

    def resume_campaign(self, campaign_id: str) -> bool:
        campaign = self.campaigns.get(campaign_id)
        if campaign and campaign["status"] == "paused":
            campaign["status"] = "active"
            return True
        return False


class ThreatIntelFeeder:
    def __init__(self, dt: 'DeceptionTechManager'):
        self.dt = dt

    def extract_iocs_from_engagements(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        iocs = []
        for d in self.dt.decoys.values():
            for f in d.forensics:
                ts = f.get("timestamp", "")
                if ts and datetime.fromisoformat(ts) > cutoff:
                    src_ip = f.get("source_ip")
                    if src_ip:
                        iocs.append({"decoy": d.name, "source_ip": src_ip, "timestamp": ts, "ioc_type": "ip", "confidence": 75})
                    payload = f.get("payload", {})
                    if isinstance(payload, dict):
                        for k, v in payload.items():
                            if k in ("file_hash", "domain", "url"):
                                iocs.append({"decoy": d.name, "value": v, "ioc_type": k, "timestamp": ts, "confidence": 60})
        return iocs

    def get_attacker_profiles(self) -> List[Dict]:
        by_ip = {}
        for d in self.dt.decoys.values():
            for f in d.forensics:
                ip = f.get("source_ip", "unknown")
                by_ip.setdefault(ip, {"ip": ip, "decoys_hit": set(), "techniques": set(), "first_seen": None, "last_seen": None})
                by_ip[ip]["decoys_hit"].add(d.name)
                by_ip[ip]["techniques"].add(f.get("event_type", "unknown"))
                ts = f.get("timestamp")
                if ts:
                    dt_ts = datetime.fromisoformat(ts)
                    if not by_ip[ip]["first_seen"] or dt_ts < by_ip[ip]["first_seen"]:
                        by_ip[ip]["first_seen"] = dt_ts
                    if not by_ip[ip]["last_seen"] or dt_ts > by_ip[ip]["last_seen"]:
                        by_ip[ip]["last_seen"] = dt_ts
        return [{"ip": v["ip"], "decoys_hit": list(v["decoys_hit"]), "techniques": list(v["techniques"]), "first_seen": v["first_seen"].isoformat() if v["first_seen"] else None, "last_seen": v["last_seen"].isoformat() if v["last_seen"] else None, "total_engagements": len(v["decoys_hit"])} for v in by_ip.values()]


class DeceptionAnalytics:
    def __init__(self, dt: 'DeceptionTechManager'):
        self.dt = dt

    def engagement_trend(self, days: int = 7) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        daily = {}
        for d in self.dt.decoys.values():
            for f in d.forensics:
                ts = f.get("timestamp", "")
                if ts and datetime.fromisoformat(ts) > cutoff:
                    day = ts[:10]
                    daily[day] = daily.get(day, 0) + 1
        return {"period_days": days, "daily_counts": daily, "total": sum(daily.values()), "avg_per_day": round(sum(daily.values()) / days, 1) if daily else 0}

    def top_targeted_techniques(self, n: int = 5) -> List[Dict]:
        techniques = {}
        for d in self.dt.decoys.values():
            for f in d.forensics:
                tech = f.get("event_type", "unknown")
                techniques[tech] = techniques.get(tech, 0) + 1
        return sorted([{"technique": t, "count": c} for t, c in techniques.items()], key=lambda x: x["count"], reverse=True)[:n]

    def decoy_effectiveness(self) -> List[Dict]:
        return [{"decoy_id": did, "name": d.name, "type": d.type.value, "engagements": d.engagement_count, "alerts": len(d.alerts), "forensics": len(d.forensics), "effectiveness_score": round((d.engagement_count * 10 + len(d.alerts) * 5 + len(d.forensics) * 3) / max(d.ttl_hours, 1), 1)} for did, d in self.dt.decoys.items()]


class DeceptionReporter:
    def __init__(self, dt: 'DeceptionTechManager'):
        self.dt = dt

    def generate_threat_report(self) -> str:
        analytics = DeceptionAnalytics(self.dt)
        feeder = ThreatIntelFeeder(self.dt)
        lines = ["=== Deception Technology Threat Report ===", f"Generated: {datetime.utcnow().isoformat()}", f"Active Decoys: {sum(1 for d in self.dt.decoys.values() if d.active)}/{len(self.dt.decoys)}", f"Honey Tokens: {len(self.dt.honey_tokens)}", f"Total Engagements: {sum(d.engagement_count for d in self.dt.decoys.values())}", f"Forensic Events: {sum(len(d.forensics) for d in self.dt.decoys.values())}", "", "Top Techniques:"]
        for t in analytics.top_targeted_techniques():
            lines.append(f"  - {t['technique']}: {t['count']}")
        lines.append("")
        profiles = feeder.get_attacker_profiles()
        lines.append(f"Unique Attackers: {len(profiles)}")
        return "\n".join(lines)

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
