"""Threat Intelligence Management platform.

Aggregate threat feeds from MISP, AlienVault OTX, VirusTotal, CrowdStrike, and others.
IoC matching against infrastructure, automated blocklist updates, and threat scoring.
"""

import json
import uuid
import hashlib
import logging
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class IOCType(str, Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    EMAIL = "email"
    MUTEX = "mutex"
    REGISTRY_KEY = "registry_key"
    YARA_RULE = "yara_rule"
    CVE = "cve"
    ASN = "asn"
    FILE_PATH = "file_path"


class ThreatFeedStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"


class ThreatSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IoCConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ThreatFeed:
    id: str
    name: str
    provider: str
    url: str
    api_key: Optional[str] = None
    status: ThreatFeedStatus = ThreatFeedStatus.ACTIVE
    refresh_interval_minutes: int = 60
    last_refresh: Optional[datetime] = None
    ioc_count: int = 0
    ioc_types: List[str] = field(default_factory=lambda: ["ipv4", "domain", "sha256"])
    enabled: bool = True
    required_access: str = "read"
    health_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "url": self.url,
            "status": self.status.value,
            "refresh_interval_minutes": self.refresh_interval_minutes,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "ioc_count": self.ioc_count,
            "ioc_types": self.ioc_types,
            "enabled": self.enabled,
            "required_access": self.required_access,
            "health_score": self.health_score,
        }


@dataclass
class IOC:
    id: str
    type: IOCType
    value: str
    severity: ThreatSeverity
    confidence: IoCConfidence
    source: str
    source_feed: str
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = field(default_factory=list)
    description: str = ""
    reference_urls: List[str] = field(default_factory=list)
    tlp: str = "amber"
    expires_at: Optional[datetime] = None
    related_indicators: List[str] = field(default_factory=list)
    kill_chain_phase: str = ""
    mitre_attack_id: Optional[str] = None
    matched_assets: List[str] = field(default_factory=list)
    match_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "value": self.value,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "source": self.source,
            "source_feed": self.source_feed,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "tags": self.tags,
            "description": self.description,
            "reference_urls": self.reference_urls,
            "tlp": self.tlp,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "related_indicators": self.related_indicators,
            "kill_chain_phase": self.kill_chain_phase,
            "mitre_attack_id": self.mitre_attack_id,
            "matched_assets": self.matched_assets,
            "match_count": self.match_count,
            "age_days": (datetime.utcnow() - self.first_seen).days,
        }


@dataclass
class IoCMatchResult:
    id: str
    ioc_id: str
    ioc_value: str
    asset_id: str
    asset_type: str
    asset_name: str
    matched_at: datetime
    match_type: str
    risk_score: float
    auto_remediated: bool = False
    notified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ioc_id": self.ioc_id,
            "ioc_value": self.ioc_value,
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "asset_name": self.asset_name,
            "matched_at": self.matched_at.isoformat(),
            "match_type": self.match_type,
            "risk_score": self.risk_score,
            "auto_remediated": self.auto_remediated,
            "notified": self.notified,
        }


@dataclass
class BlocklistEntry:
    id: str
    value: str
    ioc_type: str
    source: str
    added_at: datetime
    expires_at: Optional[datetime]
    active: bool = True
    hits: int = 0
    last_hit: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "ioc_type": self.ioc_type,
            "source": self.source,
            "added_at": self.added_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.active,
            "hits": self.hits,
            "last_hit": self.last_hit.isoformat() if self.last_hit else None,
        }


class ThreatIntelligenceManager:
    """Aggregate and manage threat intelligence feeds, IoCs, and blocklists."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.feeds: Dict[str, ThreatFeed] = {}
        self.iocs: Dict[str, IOC] = {}
        self.matches: Dict[str, IoCMatchResult] = {}
        self.blocklist: Dict[str, BlocklistEntry] = {}
        self._initialized = False

    def _setup_default_feeds(self):
        default_feeds = [
            ThreatFeed(id="feed-misp", name="MISP Community Feed", provider="MISP",
                       url="https://misp.example.com/events", refresh_interval_minutes=30,
                       ioc_types=["ipv4", "domain", "sha256", "url"]),
            ThreatFeed(id="feed-otx", name="AlienVault OTX", provider="AlienVault",
                       url="https://otx.alienvault.com/api/v1/indicators", refresh_interval_minutes=60,
                       ioc_types=["ipv4", "domain", "url", "md5", "sha256"]),
            ThreatFeed(id="feed-vt", name="VirusTotal Live Feed", provider="VirusTotal",
                       url="https://www.virustotal.com/api/v3/feeds", refresh_interval_minutes=15,
                       ioc_types=["sha256", "url", "domain", "ipv4"]),
            ThreatFeed(id="feed-crowdstrike", name="CrowdStrike Falcon Intel", provider="CrowdStrike",
                       url="https://api.crowdstrike.com/indicator-aggregates", refresh_interval_minutes=30,
                       ioc_types=["ipv4", "domain", "sha256", "mutex", "registry_key"]),
            ThreatFeed(id="feed-abuseipdb", name="AbuseIPDB Blacklist", provider="AbuseIPDB",
                       url="https://api.abuseipdb.com/api/v2/blacklist", refresh_interval_minutes=60,
                       ioc_types=["ipv4"]),
            ThreatFeed(id="feed-emergingthreats", name="Emerging Threats Open", provider="Proofpoint",
                       url="https://rules.emergingthreats.net/open/snort-2.9.0/rules/compromised-ips.txt",
                       refresh_interval_minutes=120, ioc_types=["ipv4"]),
            ThreatFeed(id="feed-stix", name="STIX/TAXII Collection", provider="STIX",
                       url="https://taxii.example.com/collections/enterprise-attack",
                       refresh_interval_minutes=240, ioc_types=["ipv4", "domain", "sha256", "cve", "yara_rule"]),
            ThreatFeed(id="feed-urlhaus", name="URLhaus Malicious URLs", provider="Abuse.ch",
                       url="https://urlhaus-api.abuse.ch/v1/urls/recent", refresh_interval_minutes=30,
                       ioc_types=["url", "domain"]),
        ]
        for feed in default_feeds:
            self.feeds[feed.id] = feed

    async def initialize(self):
        self._setup_default_feeds()
        self._seed_sample_iocs()
        self._initialized = True
        logger.info(f"Threat Intel Manager initialized: {len(self.feeds)} feeds, {len(self.iocs)} IoCs")

    async def close(self):
        logger.info("Threat Intel Manager shut down")

    def _seed_sample_iocs(self):
        sample_iocs = [
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.IPV4, value="185.220.101.42",
                severity=ThreatSeverity.HIGH, confidence=IoCConfidence.HIGH,
                source="MISP", source_feed="feed-misp", first_seen=datetime.utcnow() - timedelta(days=7),
                last_seen=datetime.utcnow(), tags=["c2", "botnet"], description="Known Cobalt Strike C2 server",
                kill_chain_phase="command-and-control", mitre_attack_id="T1071.001"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.IPV4, value="91.121.89.27",
                severity=ThreatSeverity.MEDIUM, confidence=IoCConfidence.MEDIUM,
                source="AlienVault OTX", source_feed="feed-otx", first_seen=datetime.utcnow() - timedelta(days=14),
                last_seen=datetime.utcnow() - timedelta(days=1), tags=["scanner", "portscan"],
                description="Port scanning node observed scanning SSH ports",
                kill_chain_phase="reconnaissance", mitre_attack_id="T1595"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.DOMAIN, value="evil-malware-download.xyz",
                severity=ThreatSeverity.CRITICAL, confidence=IoCConfidence.VERY_HIGH,
                source="CrowdStrike Falcon", source_feed="feed-crowdstrike", first_seen=datetime.utcnow() - timedelta(days=1),
                last_seen=datetime.utcnow(), tags=["malware-distribution", "phishing"],
                description="Domain distributing RedLine Stealer malware",
                kill_chain_phase="delivery", mitre_attack_id="T1566.001"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.URL, value="https://phish-bank.example.com/login",
                severity=ThreatSeverity.HIGH, confidence=IoCConfidence.HIGH,
                source="URLhaus", source_feed="feed-urlhaus", first_seen=datetime.utcnow() - timedelta(hours=6),
                last_seen=datetime.utcnow(), tags=["phishing", "credential-theft"],
                description="Phishing page mimicking a major bank login",
                kill_chain_phase="delivery", mitre_attack_id="T1566.002"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.SHA256, value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                severity=ThreatSeverity.CRITICAL, confidence=IoCConfidence.VERY_HIGH,
                source="VirusTotal", source_feed="feed-vt", first_seen=datetime.utcnow() - timedelta(days=3),
                last_seen=datetime.utcnow(), tags=["ransomware", "lockbit"],
                description="LockBit 3.0 ransomware binary",
                kill_chain_phase="execution", mitre_attack_id="T1204.002"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.CVE, value="CVE-2024-3094",
                severity=ThreatSeverity.CRITICAL, confidence=IoCConfidence.VERY_HIGH,
                source="STIX/TAXII", source_feed="feed-stix", first_seen=datetime.utcnow() - timedelta(days=30),
                last_seen=datetime.utcnow(), tags=["xzf", "backdoor", "supply-chain"],
                description="XZ Utils backdoor (CVE-2024-3094) - SSHD compromise via liblzma",
                kill_chain_phase="initial-access", mitre_attack_id="T1195.001"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.EMAIL, value="phishing-attempt@malicious-sender.ru",
                severity=ThreatSeverity.MEDIUM, confidence=IoCConfidence.MEDIUM,
                source="AbuseIPDB", source_feed="feed-abuseipdb", first_seen=datetime.utcnow() - timedelta(days=5),
                last_seen=datetime.utcnow(), tags=["spam", "phishing"],
                description="Known phishing email sender address",
                kill_chain_phase="delivery", mitre_attack_id="T1566.003"),
            IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType.YARA_RULE, value="rule_stealer_loader_v1",
                severity=ThreatSeverity.HIGH, confidence=IoCConfidence.HIGH,
                source="MISP", source_feed="feed-misp", first_seen=datetime.utcnow() - timedelta(days=10),
                last_seen=datetime.utcnow(), tags=["stealer", "yara"],
                description="YARA rule detecting info-stealer loader variants",
                kill_chain_phase="execution", mitre_attack_id="T1204.002"),
        ]
        for ioc in sample_iocs:
            self.iocs[ioc.id] = ioc

    async def add_feed(self, name: str, provider: str, url: str, api_key: Optional[str] = None,
                       refresh_interval: int = 60, ioc_types: Optional[List[str]] = None) -> ThreatFeed:
        feed = ThreatFeed(id=f"feed-{uuid.uuid4().hex[:12]}", name=name, provider=provider, url=url,
                          api_key=api_key, refresh_interval_minutes=refresh_interval,
                          ioc_types=ioc_types or ["ipv4", "domain"])
        self.feeds[feed.id] = feed
        return feed

    def update_feed(self, feed_id: str, updates: Dict[str, Any]) -> Optional[ThreatFeed]:
        feed = self.feeds.get(feed_id)
        if not feed:
            return None
        for key, value in updates.items():
            if hasattr(feed, key) and key not in ("id",):
                setattr(feed, key, value)
        return feed

    def delete_feed(self, feed_id: str) -> bool:
        return self.feeds.pop(feed_id, None) is not None

    def get_feed(self, feed_id: str) -> Optional[ThreatFeed]:
        return self.feeds.get(feed_id)

    def list_feeds(self, provider: Optional[str] = None, status: Optional[str] = None) -> List[ThreatFeed]:
        results = list(self.feeds.values())
        if provider:
            results = [f for f in results if f.provider.lower() == provider.lower()]
        if status:
            results = [f for f in results if f.status.value == status]
        return results

    async def refresh_feed(self, feed_id: str) -> Dict[str, Any]:
        feed = self.feeds.get(feed_id)
        if not feed:
            return {"error": "Feed not found"}
        simulated_ioc_count = 15
        feed.last_refresh = datetime.utcnow()
        feed.status = ThreatFeedStatus.ACTIVE
        feed.ioc_count = simulated_ioc_count
        for _ in range(simulated_ioc_count):
            ioc = IOC(
                id=f"ioc-{uuid.uuid4().hex[:12]}",
                type=IOCType.IPV4 if "ipv4" in feed.ioc_types else IOCType.DOMAIN,
                value=f"{uuid.uuid4().hex[:8]}.{'malicious' if _ % 2 == 0 else 'suspicious'}.example.com" if "domain" in feed.ioc_types else f"{hashlib.sha256(str(_).encode()).hexdigest()}",
                severity=ThreatSeverity.HIGH if _ % 3 == 0 else ThreatSeverity.MEDIUM,
                confidence=IoCConfidence.HIGH if _ % 2 == 0 else IoCConfidence.MEDIUM,
                source=feed.name, source_feed=feed.id,
                first_seen=datetime.utcnow(), last_seen=datetime.utcnow(),
                tags=[feed.provider.lower(), "automated"],
            )
            self.iocs[ioc.id] = ioc
        return {"status": "refreshed", "feed_id": feed_id, "new_iocs": simulated_ioc_count, "total_iocs": feed.ioc_count}

    def add_ioc(self, ioc_type: str, value: str, severity: str, confidence: str, source: str,
                source_feed: str = "", tags: Optional[List[str]] = None) -> IOC:
        ioc = IOC(id=f"ioc-{uuid.uuid4().hex[:12]}", type=IOCType(ioc_type), value=value,
                  severity=ThreatSeverity(severity), confidence=IoCConfidence(confidence),
                  source=source, source_feed=source_feed, first_seen=datetime.utcnow(),
                  last_seen=datetime.utcnow(), tags=tags or [])
        self.iocs[ioc.id] = ioc
        return ioc

    def update_ioc(self, ioc_id: str, updates: Dict[str, Any]) -> Optional[IOC]:
        ioc = self.iocs.get(ioc_id)
        if not ioc:
            return None
        for key, value in updates.items():
            if hasattr(ioc, key) and key not in ("id",):
                if key == "type":
                    setattr(ioc, key, IOCType(value))
                elif key == "severity":
                    setattr(ioc, key, ThreatSeverity(value))
                elif key == "confidence":
                    setattr(ioc, key, IoCConfidence(value))
                else:
                    setattr(ioc, key, value)
        ioc.last_seen = datetime.utcnow()
        return ioc

    def delete_ioc(self, ioc_id: str) -> bool:
        return self.iocs.pop(ioc_id, None) is not None

    def get_ioc(self, ioc_id: str) -> Optional[IOC]:
        return self.iocs.get(ioc_id)

    def list_iocs(self, ioc_type: Optional[str] = None, severity: Optional[str] = None,
                  confidence: Optional[str] = None, source: Optional[str] = None,
                  tags: Optional[List[str]] = None, search: Optional[str] = None,
                  page: int = 1, page_size: int = 50) -> Tuple[List[IOC], int]:
        results = list(self.iocs.values())
        if ioc_type:
            results = [i for i in results if i.type.value == ioc_type]
        if severity:
            results = [i for i in results if i.severity.value == severity]
        if confidence:
            results = [i for i in results if i.confidence.value == confidence]
        if source:
            results = [i for i in results if i.source.lower() == source.lower()]
        if tags:
            results = [i for i in results if any(t in i.tags for t in tags)]
        if search:
            results = [i for i in results if search.lower() in i.value.lower() or search.lower() in i.description.lower()]
        total = len(results)
        start = (page - 1) * page_size
        results = sorted(results, key=lambda i: i.first_seen, reverse=True)[start:start + page_size]
        return results, total

    async def match_iocs(self, assets: List[Dict[str, Any]]) -> List[IoCMatchResult]:
        matches = []
        for asset in assets:
            asset_id = asset.get("id", "")
            asset_type = asset.get("type", "unknown")
            asset_name = asset.get("name", "")
            for ioc in self.iocs.values():
                risk_score = self._calculate_risk_score(ioc)
                if ioc.type == IOCType.IPV4 and ioc.value == asset.get("ip"):
                    match = self._create_match(ioc, asset_id, asset_type, asset_name, "ip_match", risk_score)
                    matches.append(match)
                elif ioc.type == IOCType.DOMAIN and ioc.value == asset.get("domain"):
                    match = self._create_match(ioc, asset_id, asset_type, asset_name, "domain_match", risk_score)
                    matches.append(match)
                elif ioc.type == IOCType.URL and (ioc.value in str(asset.get("urls", [])) or ioc.value == asset.get("url")):
                    match = self._create_match(ioc, asset_id, asset_type, asset_name, "url_match", risk_score)
                    matches.append(match)
                elif ioc.type == IOCType.SHA256 and ioc.value == asset.get("hash"):
                    match = self._create_match(ioc, asset_id, asset_type, asset_name, "hash_match", risk_score)
                    matches.append(match)
        return matches

    def _calculate_risk_score(self, ioc: IOC) -> float:
        severity_weights = {ThreatSeverity.LOW: 0.2, ThreatSeverity.MEDIUM: 0.4, ThreatSeverity.HIGH: 0.7, ThreatSeverity.CRITICAL: 0.95}
        confidence_weights = {IoCConfidence.LOW: 0.2, IoCConfidence.MEDIUM: 0.5, IoCConfidence.HIGH: 0.8, IoCConfidence.VERY_HIGH: 0.95}
        age = (datetime.utcnow() - ioc.first_seen).days
        age_factor = max(1.0 - (age / 365), 0.3)
        sev = severity_weights.get(ioc.severity, 0.5)
        conf = confidence_weights.get(ioc.confidence, 0.5)
        return round(sev * 0.4 + conf * 0.4 + age_factor * 0.2, 2)

    def _create_match(self, ioc: IOC, asset_id: str, asset_type: str, asset_name: str,
                      match_type: str, risk_score: float) -> IoCMatchResult:
        ioc.match_count += 1
        if asset_name not in ioc.matched_assets:
            ioc.matched_assets.append(asset_name)
        match = IoCMatchResult(id=f"match-{uuid.uuid4().hex[:12]}", ioc_id=ioc.id, ioc_value=ioc.value,
                               asset_id=asset_id, asset_type=asset_type, asset_name=asset_name,
                               matched_at=datetime.utcnow(), match_type=match_type, risk_score=risk_score)
        self.matches[match.id] = match
        return match

    def list_matches(self, asset_id: Optional[str] = None, risk_min: Optional[float] = None,
                     limit: int = 100) -> List[IoCMatchResult]:
        results = list(self.matches.values())
        if asset_id:
            results = [m for m in results if m.asset_id == asset_id]
        if risk_min is not None:
            results = [m for m in results if m.risk_score >= risk_min]
        return sorted(results, key=lambda m: m.risk_score, reverse=True)[:limit]

    def add_to_blocklist(self, value: str, ioc_type: str, source: str, ttl_hours: int = 48) -> BlocklistEntry:
        expires = datetime.utcnow() + timedelta(hours=ttl_hours) if ttl_hours > 0 else None
        entry = BlocklistEntry(id=f"bl-{uuid.uuid4().hex[:12]}", value=value, ioc_type=ioc_type,
                               source=source, added_at=datetime.utcnow(), expires_at=expires)
        self.blocklist[entry.id] = entry
        return entry

    def remove_from_blocklist(self, entry_id: str) -> bool:
        return self.blocklist.pop(entry_id, None) is not None

    def list_blocklist(self, active_only: bool = True, ioc_type: Optional[str] = None) -> List[BlocklistEntry]:
        results = list(self.blocklist.values())
        if active_only:
            results = [e for e in results if e.active]
            now = datetime.utcnow()
            results = [e for e in results if e.expires_at is None or e.expires_at > now]
        if ioc_type:
            results = [e for e in results if e.ioc_type == ioc_type]
        return sorted(results, key=lambda e: e.added_at, reverse=True)

    def check_blocklist(self, value: str) -> Optional[BlocklistEntry]:
        for entry in self.blocklist.values():
            if entry.value == value and entry.active:
                entry.hits += 1
                entry.last_hit = datetime.utcnow()
                return entry
        return None

    def get_threat_summary(self) -> Dict[str, Any]:
        severity_counts = {}
        for ioc in self.iocs.values():
            sev = ioc.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        type_counts = {}
        for ioc in self.iocs.values():
            t = ioc.type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "total_feeds": len(self.feeds),
            "active_feeds": sum(1 for f in self.feeds.values() if f.status == ThreatFeedStatus.ACTIVE),
            "total_iocs": len(self.iocs),
            "iocs_by_severity": severity_counts,
            "iocs_by_type": type_counts,
            "total_matches": len(self.matches),
            "blocklist_entries": len(self.blocklist),
            "blocklist_active": sum(1 for e in self.blocklist.values() if e.active),
            "top_sources": self._get_top_sources(5),
            "top_tags": self._get_top_tags(10),
        }

    def _get_top_sources(self, n: int) -> List[Dict[str, Any]]:
        source_counts = {}
        for ioc in self.iocs.values():
            source_counts[ioc.source] = source_counts.get(ioc.source, 0) + 1
        return [{"source": s, "count": c} for s, c in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:n]]

    def _get_top_tags(self, n: int) -> List[Dict[str, Any]]:
        tag_counts = {}
        for ioc in self.iocs.values():
            for tag in ioc.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return [{"tag": t, "count": c} for t, c in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:n]]

    def to_dict(self) -> Dict[str, Any]:
        return self.get_threat_summary()

    # === Batch Operations ===
    async def batch_add_iocs(self, ioc_defs: List[Dict]) -> List[Dict]:
        results = []
        for i, idef in enumerate(ioc_defs):
            try:
                ioc = self.add_ioc(
                    indicator_type=IOCType(idef.get("type", "ip")),
                    value=idef.get("value", ""),
                    confidence=idef.get("confidence", 50),
                    severity=idef.get("severity", "medium"),
                    source=idef.get("source", "api"),
                    tags=idef.get("tags", []),
                    description=idef.get("description", ""),
                )
                results.append({"index": i, "ioc_id": ioc.id, "status": "added"})
            except Exception as e:
                results.append({"index": i, "status": "failed", "error": str(e)})
        return results

    async def batch_enrich_iocs(self, ioc_ids: List[str]) -> List[Dict]:
        results = []
        for ioc_id in ioc_ids:
            try:
                result = await self.enrich_ioc(ioc_id)
                results.append({"ioc_id": ioc_id, "status": "enriched", "result": result})
            except Exception as e:
                results.append({"ioc_id": ioc_id, "status": "failed", "error": str(e)})
        return results

    def get_iocs_paginated(self, page: int = 1, per_page: int = 20, ioc_type: Optional[str] = None, min_confidence: Optional[int] = None) -> Dict:
        items = list(self.iocs.values())
        if ioc_type:
            items = [i for i in items if i.indicator_type.value == ioc_type]
        if min_confidence is not None:
            items = [i for i in items if i.confidence >= min_confidence]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [i.to_dict() for i in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_ioc(self, ioc_type: str, value: str) -> List[str]:
        errors = []
        if not value:
            errors.append("IOC value is required")
        if ioc_type == "ip":
            import re
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
                errors.append("Invalid IP address format")
        elif ioc_type == "domain":
            if "." not in value:
                errors.append("Invalid domain format")
        elif ioc_type == "hash":
            if len(value) not in (32, 40, 64):
                errors.append("Hash must be MD5 (32), SHA1 (40), or SHA256 (64) chars")
        elif ioc_type == "url":
            if not value.startswith("http"):
                errors.append("URL must start with http:// or https://")
        else:
            errors.append(f"Unknown IOC type: {ioc_type}")
        return errors

    def validate_feed_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("url"):
            errors.append("Feed URL is required")
        if not config.get("name"):
            errors.append("Feed name is required")
        return errors

    # === Bulk Operations ===
    async def bulk_update_confidence(self, ioc_ids: List[str], confidence: int) -> int:
        count = 0
        for ioc_id in ioc_ids:
            if ioc_id in self.iocs:
                self.iocs[ioc_id].confidence = max(0, min(100, confidence))
                count += 1
        return count

    async def bulk_delete_by_source(self, source: str) -> int:
        to_delete = [iid for iid, ioc in self.iocs.items() if ioc.source == source]
        for iid in to_delete:
            del self.iocs[iid]
        return len(to_delete)

    async def cleanup_expired_iocs(self) -> int:
        now = datetime.utcnow()
        to_remove = [iid for iid, ioc in self.iocs.items() if ioc.expires_at and ioc.expires_at < now]
        for iid in to_remove:
            del self.iocs[iid]
        return len(to_remove)

    # === Analytics ===
    def get_ioc_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for ioc in self.iocs.values():
            if ioc.created_at and ioc.created_at >= cutoff:
                day = ioc.created_at.strftime("%Y-%m-%d")
                trend[day] = trend.get(day, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_ioc_type_distribution(self) -> Dict:
        dist = {}
        for ioc in self.iocs.values():
            t = ioc.indicator_type.value
            dist[t] = dist.get(t, 0) + 1
        total = sum(dist.values())
        return {"distribution": dist, "total": total}

    def get_confidence_distribution(self) -> Dict:
        buckets = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for ioc in self.iocs.values():
            if ioc.confidence >= 90:
                buckets["critical"] += 1
            elif ioc.confidence >= 70:
                buckets["high"] += 1
            elif ioc.confidence >= 40:
                buckets["medium"] += 1
            else:
                buckets["low"] += 1
        return buckets

    # === Feed Management ===
    async def refresh_all_feeds(self) -> List[Dict]:
        results = []
        for feed in self.feeds.values():
            try:
                feed.last_fetch = datetime.utcnow()
                results.append({"feed_id": feed.id, "name": feed.name, "status": "refreshed"})
            except Exception as e:
                results.append({"feed_id": feed.id, "name": feed.name, "status": "failed", "error": str(e)})
        return results

    def get_feed_health(self) -> Dict:
        total = len(self.feeds)
        healthy = sum(1 for f in self.feeds.values() if f.status == "active")
        return {"total": total, "healthy": healthy, "degraded": total - healthy, "health_pct": round(healthy / total * 100, 1) if total > 0 else 0}

    # === Search ===
    def search_iocs(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for ioc in self.iocs.values():
            if q in ioc.value.lower() or q in ioc.source.lower() or any(q in t.lower() for t in ioc.tags):
                results.append(ioc.to_dict())
        return results

    # === Export/Import ===
    def export_iocs_csv(self) -> str:
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "type", "value", "confidence", "severity", "source", "created_at"])
        for ioc in self.iocs.values():
            writer.writerow([ioc.id, ioc.indicator_type.value, ioc.value, ioc.confidence, ioc.severity, ioc.source, ioc.created_at.isoformat() if ioc.created_at else ""])
        return output.getvalue()

    def import_iocs_csv(self, csv_content: str) -> int:
        import io
        import csv
        reader = csv.DictReader(io.StringIO(csv_content))
        count = 0
        for row in reader:
            try:
                self.add_ioc(
                    indicator_type=IOCType(row.get("type", "ip")),
                    value=row.get("value", ""),
                    confidence=int(row.get("confidence", 50)),
                    severity=row.get("severity", "medium"),
                    source=row.get("source", "import"),
                    tags=[],
                )
                count += 1
            except Exception:
                continue
        return count

    def export_iocs_json(self) -> str:
        return json.dumps([ioc.to_dict() for ioc in self.iocs.values()], indent=2, default=str)

    def import_iocs_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            ioc = IOC(
                id=item.get("id", f"ioc-{uuid.uuid4().hex[:12]}"),
                type=IOCType(item.get("type", "ipv4")),
                value=item.get("value", ""),
                severity=ThreatSeverity(item.get("severity", "medium")),
                confidence=IoCConfidence(item.get("confidence", "medium")),
                source=item.get("source", "import"),
                source_feed=item.get("source_feed", ""),
                first_seen=datetime.fromisoformat(item["first_seen"]) if item.get("first_seen") else datetime.utcnow(),
                last_seen=datetime.fromisoformat(item["last_seen"]) if item.get("last_seen") else datetime.utcnow(),
                tags=item.get("tags", []),
                description=item.get("description", ""),
                reference_urls=item.get("reference_urls", []),
                tlp=item.get("tlp", "amber"),
                kill_chain_phase=item.get("kill_chain_phase", ""),
                mitre_attack_id=item.get("mitre_attack_id"),
            )
            self.iocs[ioc.id] = ioc
            count += 1
        return count

    # === State Machine ===
    def transition_ioc_status(self, ioc_id: str) -> Optional[IOC]:
        ioc = self.iocs.get(ioc_id)
        if not ioc:
            return None
        if ioc.expires_at and ioc.expires_at < datetime.utcnow():
            self.delete_ioc(ioc_id)
        return ioc

    # === Notification ===
    async def notify_ioc_match(self, match: IoCMatchResult) -> Dict[str, Any]:
        return {
            "match_id": match.id,
            "ioc_value": match.ioc_value,
            "asset_name": match.asset_name,
            "risk_score": match.risk_score,
            "match_type": match.match_type,
            "message": f"IOC match: {match.ioc_value} matched on {match.asset_name} (risk: {match.risk_score})",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_high_risk_matches(self, risk_threshold: float = 0.7) -> List[Dict]:
        results = []
        for m in self.matches.values():
            if m.risk_score >= risk_threshold and not m.notified:
                results.append(await self.notify_ioc_match(m))
                m.notified = True
        return results

    async def notify_feed_errors(self) -> List[Dict]:
        results = []
        for feed in self.feeds.values():
            if feed.status == ThreatFeedStatus.ERROR:
                results.append({"feed_id": feed.id, "name": feed.name, "message": f"Feed {feed.name} is in error state", "notified_at": datetime.utcnow().isoformat()})
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("feeds"):
            errors.append("At least one threat feed must be configured")
        if config.get("auto_blocklist", False) and not config.get("blocklist_provider"):
            warnings.append("Auto-blocklist enabled but no blocklist provider configured")
        if config.get("tlp_filter") and config["tlp_filter"] not in ("white", "green", "amber", "red"):
            errors.append("TLP filter must be white, green, amber, or red")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_ioc_lifecycle(self) -> Dict:
        active = sum(1 for i in self.iocs.values() if not i.expires_at or i.expires_at > datetime.utcnow())
        expired = sum(1 for i in self.iocs.values() if i.expires_at and i.expires_at <= datetime.utcnow())
        by_tlp = {}
        for i in self.iocs.values():
            by_tlp[i.tlp] = by_tlp.get(i.tlp, 0) + 1
        return {
            "active_iocs": active,
            "expired_iocs": expired,
            "by_tlp": by_tlp,
            "by_kill_chain": self._get_kill_chain_breakdown(),
        }

    def _get_kill_chain_breakdown(self) -> Dict:
        breakdown = {}
        for i in self.iocs.values():
            phase = i.kill_chain_phase or "unknown"
            breakdown[phase] = breakdown.get(phase, 0) + 1
        return breakdown

    def get_feed_performance(self) -> List[Dict]:
        return [
            {"feed_id": f.id, "name": f.name, "provider": f.provider, "ioc_count": f.ioc_count, "status": f.status.value, "last_refresh": f.last_refresh.isoformat() if f.last_refresh else None, "health": f.health_score}
            for f in self.feeds.values()
        ]

    def get_match_summary(self) -> Dict:
        by_type = {}
        for m in self.matches.values():
            by_type[m.match_type] = by_type.get(m.match_type, 0) + 1
        return {
            "total_matches": len(self.matches),
            "auto_remediated": sum(1 for m in self.matches.values() if m.auto_remediated),
            "by_match_type": by_type,
            "avg_risk": round(sum(m.risk_score for m in self.matches.values()) / len(self.matches), 2) if self.matches else 0,
        }

    # === Bulk Operations ===
    async def bulk_add_to_blocklist(self, ioc_ids: List[str], ttl_hours: int = 48) -> List[Dict]:
        results = []
        for iid in ioc_ids:
            ioc = self.iocs.get(iid)
            if ioc:
                entry = self.add_to_blocklist(ioc.value, ioc.type.value, ioc.source, ttl_hours)
                results.append({"ioc_id": iid, "value": ioc.value, "blocklist_id": entry.id, "status": "added"})
            else:
                results.append({"ioc_id": iid, "status": "failed", "error": "IOC not found"})
        return results

    async def bulk_clear_blocklist(self) -> int:
        count = len(self.blocklist)
        self.blocklist.clear()
        return count

    async def bulk_refresh_feeds(self, feed_ids: List[str]) -> List[Dict]:
        results = []
        for fid in feed_ids:
            result = await self.refresh_feed(fid)
            results.append(result)
        return results

    # === Tag Management ===
    def add_ioc_tags(self, ioc_ids: List[str], tags: List[str]) -> int:
        count = 0
        for iid in ioc_ids:
            ioc = self.iocs.get(iid)
            if ioc:
                for t in tags:
                    if t not in ioc.tags:
                        ioc.tags.append(t)
                count += 1
        return count

    def remove_ioc_tags(self, ioc_ids: List[str], tags: List[str]) -> int:
        count = 0
        for iid in ioc_ids:
            ioc = self.iocs.get(iid)
            if ioc:
                ioc.tags = [t for t in ioc.tags if t not in tags]
                count += 1
        return count

    # === TLP Management ===
    def bulk_update_tlp(self, ioc_ids: List[str], tlp: str) -> int:
        count = 0
        for iid in ioc_ids:
            ioc = self.iocs.get(iid)
            if ioc:
                ioc.tlp = tlp
                count += 1
        return count

    def get_iocs_by_tlp(self, tlp: str) -> List[IOC]:
        return [i for i in self.iocs.values() if i.tlp == tlp]

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "threat_intel",
            "initialized": self._initialized,
            "feeds": len(self.feeds),
            "active_feeds": sum(1 for f in self.feeds.values() if f.status == ThreatFeedStatus.ACTIVE),
            "iocs": len(self.iocs),
            "matches": len(self.matches),
            "blocklist_entries": len(self.blocklist),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class ThreatIntelAnalytics:
    def __init__(self, ti: 'ThreatIntelManager'):
        self.ti = ti

    def ioc_type_distribution(self) -> Dict:
        dist = {}
        for i in self.ti.iocs.values():
            t = i.type.value if hasattr(i.type, 'value') else str(i.type)
            dist[t] = dist.get(t, 0) + 1
        return dist

    def feed_health_summary(self) -> Dict:
        feeds = self.ti.feeds.values()
        return {"total_feeds": len(feeds), "active": sum(1 for f in feeds if f.status == ThreatFeedStatus.ACTIVE), "error": sum(1 for f in feeds if f.status == ThreatFeedStatus.ERROR), "paused": sum(1 for f in feeds if f.status == ThreatFeedStatus.PAUSED), "total_iocs": sum(f.ioc_count for f in feeds), "avg_health": round(sum(f.health_score for f in feeds) / len(feeds), 1) if feeds else 0}

    def top_indicators_by_risk(self, n: int = 10) -> List[Dict]:
        sorted_iocs = sorted(self.ti.iocs.values(), key=lambda i: i.confidence, reverse=True)
        return [{"ioc_id": i.id, "value": i.value, "type": i.type.value if hasattr(i.type, 'value') else str(i.type), "confidence": i.confidence, "source": i.source, "tlp": i.tlp, "kill_chain": i.kill_chain_phase} for i in sorted_iocs[:n]]

    def match_trend(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        daily = {}
        for m in self.ti.matches.values():
            if m.matched_at and m.matched_at > cutoff:
                day = m.matched_at.strftime("%Y-%m-%d")
                daily[day] = daily.get(day, 0) + 1
        return {"period_days": days, "daily_counts": daily, "total": sum(daily.values()), "avg_per_day": round(sum(daily.values()) / days, 1) if daily else 0}

    def mitre_attack_coverage(self) -> Dict:
        tactics = {}
        for i in self.ti.iocs.values():
            phase = i.kill_chain_phase or "unknown"
            tactics[phase] = tactics.get(phase, 0) + 1
        return {"tactics_covered": len(tactics), "total_iocs_mapped": sum(tactics.values()), "breakdown": tactics}


class ThreatIntelEnrichment:
    def __init__(self, ti: 'ThreatIntelManager'):
        self.ti = ti
        self.enrichment_cache: Dict[str, Dict] = {}

    def enrich_ioc(self, ioc_id: str) -> Optional[Dict]:
        ioc = self.ti.iocs.get(ioc_id)
        if not ioc:
            return None
        if ioc_id in self.enrichment_cache:
            return self.enrichment_cache[ioc_id]
        enrichment = {"ioc_id": ioc_id, "value": ioc.value, "type": ioc.type.value if hasattr(ioc.type, 'value') else str(ioc.type), "geo_data": {"country": "unknown", "asn": "unknown"}, "reputation": {"score": ioc.confidence, "malicious": ioc.confidence > 70, "first_seen": ioc.created_at.isoformat() if ioc.created_at else None}, "related_iocs": [], "tags": ioc.tags, "enriched_at": datetime.utcnow().isoformat()}
        self.enrichment_cache[ioc_id] = enrichment
        return enrichment

    def correlate_iocs(self, ioc_ids: List[str]) -> List[Dict]:
        correlations = []
        for i, iid_a in enumerate(ioc_ids):
            for iid_b in ioc_ids[i + 1:]:
                ioc_a = self.ti.iocs.get(iid_a)
                ioc_b = self.ti.iocs.get(iid_b)
                if ioc_a and ioc_b:
                    shared_tags = set(ioc_a.tags) & set(ioc_b.tags)
                    if shared_tags:
                        correlations.append({"ioc_a": iid_a, "ioc_b": iid_b, "shared_tags": list(shared_tags), "correlation_strength": len(shared_tags)})
        return sorted(correlations, key=lambda x: x["correlation_strength"], reverse=True)


class ThreatIntelExport:
    def __init__(self, ti: 'ThreatIntelManager'):
        self.ti = ti

    def export_iocs_json(self, tlp_filter: Optional[str] = None) -> List[Dict]:
        iocs = self.ti.iocs.values()
        if tlp_filter:
            iocs = [i for i in iocs if i.tlp == tlp_filter]
        return [{"value": i.value, "type": i.type.value if hasattr(i.type, 'value') else str(i.type), "confidence": i.confidence, "tlp": i.tlp, "source": i.source, "tags": i.tags, "kill_chain_phase": i.kill_chain_phase} for i in iocs]

    def export_iocs_csv(self, tlp_filter: Optional[str] = None) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["value", "type", "confidence", "tlp", "source", "kill_chain_phase", "tags"])
        for i in self.ti.iocs.values():
            if tlp_filter and i.tlp != tlp_filter:
                continue
            writer.writerow([i.value, i.type.value if hasattr(i.type, 'value') else str(i.type), i.confidence, i.tlp, i.source, i.kill_chain_phase, ";".join(i.tags)])
        return output.getvalue()

    def generate_threat_brief(self) -> str:
        analytics = ThreatIntelAnalytics(self.ti)
        lines = ["=== Daily Threat Intelligence Brief ===", f"Generated: {datetime.utcnow().isoformat()}", f"Total IoCs: {len(self.ti.iocs)}", f"Active Feeds: {analytics.feed_health_summary().get('active', 0)}", f"Total Matches: {len(self.ti.matches)}", f"Blocklist Entries: {len(self.ti.blocklist)}", "", "Top Indicators:"]
        for t in analytics.top_indicators_by_risk(5):
            lines.append(f"  [{t['type']}] {t['value']} (confidence: {t['confidence']})")
        lines.append("\nIoC Type Distribution:")
        for t, c in analytics.ioc_type_distribution().items():
            lines.append(f"  {t}: {c}")
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
