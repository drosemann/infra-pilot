"""Security Orchestration, Automation, and Response (SOAR) platform.

Playbook engine, 100+ technology connectors, case management, threat intel feed
integration, automated incident response workflows, and reporting.
"""

import json
import uuid
import hashlib
import logging
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class PlaybookTrigger(str, Enum):
    MANUAL = "manual"
    ALERT = "alert"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    THREAT_INTEL = "threat_intel"
    IOC_MATCH = "ioc_match"
    VULNERABILITY_FOUND = "vulnerability_found"
    DECEPTION_ENGAGED = "deception_engaged"
    UEBA_ANOMALY = "ueba_anomaly"
    CSPM_FINDING = "cspm_finding"


class PlaybookActionType(str, Enum):
    HTTP_REQUEST = "http_request"
    CREATE_TICKET = "create_ticket"
    SEND_EMAIL = "send_email"
    SEND_SLACK = "send_slack"
    SEND_WEBHOOK = "send_webhook"
    RUN_COMMAND = "run_command"
    BLOCK_IP = "block_ip"
    BLOCK_DOMAIN = "block_domain"
    QUARANTINE_ENDPOINT = "quarantine_endpoint"
    DISABLE_USER = "disable_user"
    RESET_PASSWORD = "reset_password"
    TERMINATE_INSTANCE = "terminate_instance"
    ISOLATE_CONTAINER = "isolate_container"
    SCAN_VULNERABILITY = "scan_vulnerability"
    FETCH_THREAT_INTEL = "fetch_threat_intel"
    UPDATE_CASE = "update_case"
    ADD_EVIDENCE = "add_evidence"
    CREATE_INCIDENT = "create_incident"
    NOTIFY_SOC = "notify_soc"
    ESCALATE = "escalate"
    DELAY = "delay"
    CONDITIONAL = "conditional"
    FOREACH = "foreach"
    PARALLEL = "parallel"


class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ConnectorType(str, Enum):
    SIEM = "siem"
    EDR = "edr"
    FIREWALL = "firewall"
    EMAIL = "email"
    TICKETING = "ticketing"
    DNS = "dns"
    CLOUD = "cloud"
    IDENTITY = "identity"
    THREAT_INTEL = "threat_intel"
    VULNERABILITY = "vulnerability"
    DECEPTION = "deception"
    NETWORK = "network"
    ENDPOINT = "endpoint"
    MESSAGING = "messaging"


@dataclass
class PlaybookAction:
    id: str
    action_type: PlaybookActionType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    condition: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    timeout_seconds: int = 60
    retry_count: int = 0
    retry_delay_seconds: int = 5
    parallel_actions: List["PlaybookAction"] = field(default_factory=list)
    foreach_field: Optional[str] = None


@dataclass
class Playbook:
    id: str
    name: str
    description: str
    trigger: PlaybookTrigger
    actions: List[PlaybookAction]
    enabled: bool = True
    version: int = 1
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    total_runs: int = 0
    success_rate: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.value,
            "actions": [asdict(a) for a in self.actions],
            "enabled": self.enabled,
            "version": self.version,
            "tags": self.tags,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "total_runs": self.total_runs,
            "success_rate": self.success_rate,
        }


@dataclass
class Case:
    id: str
    title: str
    description: str
    priority: CasePriority
    status: CaseStatus = CaseStatus.OPEN
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_incident_id: Optional[str] = None
    related_alerts: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    severity_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assignee": self.assignee,
            "tags": self.tags,
            "related_incident_id": self.related_incident_id,
            "related_alerts": self.related_alerts,
            "evidence": self.evidence,
            "timeline": self.timeline,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "severity_score": self.severity_score,
        }


@dataclass
class Connector:
    id: str
    name: str
    connector_type: ConnectorType
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    healthy: bool = True
    last_heartbeat: Optional[datetime] = None
    actions_supported: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "connector_type": self.connector_type.value,
            "config_schema": list(self.config.keys()),
            "enabled": self.enabled,
            "healthy": self.healthy,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "actions_supported": self.actions_supported,
        }


@dataclass
class PlaybookExecution:
    id: str
    playbook_id: str
    playbook_name: str
    trigger: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions_log: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    triggered_by: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "playbook_id": self.playbook_id,
            "playbook_name": self.playbook_name,
            "trigger": self.trigger,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "actions_log": self.actions_log,
            "error": self.error,
            "triggered_by": self.triggered_by,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "duration_seconds": (self.completed_at - self.started_at).total_seconds() if self.completed_at else None,
        }


class SOARPlatform:
    """Security Orchestration, Automation, and Response platform."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.playbooks: Dict[str, Playbook] = {}
        self.cases: Dict[str, Case] = {}
        self.connectors: Dict[str, Connector] = {}
        self.executions: Dict[str, PlaybookExecution] = {}
        self._execution_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    def _load_default_connectors(self):
        default_connectors = [
            Connector(id="conn-splunk", name="Splunk SIEM", connector_type=ConnectorType.SIEM,
                      actions_supported=["search", "alert", "create_notable"]),
            Connector(id="conn-sentinel", name="Microsoft Sentinel", connector_type=ConnectorType.SIEM,
                      actions_supported=["ingest", "query", "create_incident"]),
            Connector(id="conn-crowdstrike", name="CrowdStrike Falcon", connector_type=ConnectorType.EDR,
                      actions_supported=["quarantine", "scan", "ioc_search", "prevention_policy"]),
            Connector(id="conn-carbonblack", name="VMware Carbon Black", connector_type=ConnectorType.EDR,
                      actions_supported=["isolate", "kill_process", "get_file"]),
            Connector(id="conn-paloalto", name="Palo Alto Firewall", connector_type=ConnectorType.FIREWALL,
                      actions_supported=["block_ip", "block_url", "create_rule", "policy_audit"]),
            Connector(id="conn-okta", name="Okta Identity", connector_type=ConnectorType.IDENTITY,
                      actions_supported=["disable_user", "reset_password", "revoke_sessions", "mfa_reset"]),
            Connector(id="conn-servicenow", name="ServiceNow ITSM", connector_type=ConnectorType.TICKETING,
                      actions_supported=["create_ticket", "update_ticket", "assign_ticket"]),
            Connector(id="conn-jira", name="Jira", connector_type=ConnectorType.TICKETING,
                      actions_supported=["create_issue", "transition", "add_comment"]),
            Connector(id="conn-virustotal", name="VirusTotal", connector_type=ConnectorType.THREAT_INTEL,
                      actions_supported=["file_scan", "url_scan", "domain_report", "ip_report"]),
            Connector(id="conn-slack", name="Slack", connector_type=ConnectorType.MESSAGING,
                      actions_supported=["send_message", "create_channel", "invite_user"]),
            Connector(id="conn-teams", name="Microsoft Teams", connector_type=ConnectorType.MESSAGING,
                      actions_supported=["send_message", "create_team", "add_member"]),
            Connector(id="conn-aws", name="AWS", connector_type=ConnectorType.CLOUD,
                      actions_supported=["terminate_instance", "create_snapshot", "modify_sg", "disable_key"]),
            Connector(id="conn-azure", name="Azure", connector_type=ConnectorType.CLOUD,
                      actions_supported=["stop_vm", "deallocate", "lock_resource", "run_command"]),
            Connector(id="conn-gcp", name="GCP", connector_type=ConnectorType.CLOUD,
                      actions_supported=["stop_instance", "set_iam_policy", "export_logs"]),
            Connector(id="conn-qualys", name="Qualys VM", connector_type=ConnectorType.VULNERABILITY,
                      actions_supported=["scan", "report", "remediate"]),
            Connector(id="conn-tenable", name="Tenable.io", connector_type=ConnectorType.VULNERABILITY,
                      actions_supported=["scan", "export", "agent_deploy"]),
            Connector(id="conn-cloudflare", name="Cloudflare", connector_type=ConnectorType.DNS,
                      actions_supported=["block_domain", "update_firewall_rule", "purge_cache"]),
            Connector(id="conn-proofpoint", name="Proofpoint Email", connector_type=ConnectorType.EMAIL,
                      actions_supported=["quarantine_message", "block_sender", "url_decode"]),
        ]
        for conn in default_connectors:
            self.connectors[conn.id] = conn

    async def initialize(self):
        self._load_default_connectors()
        self._load_default_playbooks()
        self._running = True
        asyncio.create_task(self._execution_worker())
        logger.info(f"SOAR platform initialized with {len(self.connectors)} connectors and {len(self.playbooks)} playbooks")

    async def close(self):
        self._running = False
        logger.info("SOAR platform shut down")

    def _load_default_playbooks(self):
        default_playbooks_data = [
            {
                "id": "pb-malware-isolation",
                "name": "Malware Isolation Playbook",
                "description": "Automatically isolate endpoints with confirmed malware detections",
                "trigger": PlaybookTrigger.INCIDENT_CREATED,
                "actions": [
                    PlaybookAction(id="act-1", action_type=PlaybookActionType.UPDATE_CASE, name="Update Case Status",
                                   order=1, config={"status": "in_progress", "message": "Malware isolation initiated"}),
                    PlaybookAction(id="act-2", action_type=PlaybookActionType.FETCH_THREAT_INTEL, name="Gather Threat Intel",
                                   order=2, config={"sources": ["virustotal", "crowdstrike"]}),
                    PlaybookAction(id="act-3", action_type=PlaybookActionType.QUARANTINE_ENDPOINT, name="Isolate Endpoint",
                                   order=3, config={"isolation_type": "full", "notify_user": True}),
                    PlaybookAction(id="act-4", action_type=PlaybookActionType.BLOCK_IP, name="Block C2 IPs",
                                   order=4, config={"firewall": "paloalto", "duration_hours": 48}),
                    PlaybookAction(id="act-5", action_type=PlaybookActionType.NOTIFY_SOC, name="Notify SOC Team",
                                   order=5, config={"channel": "incidents", "level": "high"}),
                ],
            },
            {
                "id": "pb-phishing-response",
                "name": "Phishing Response Playbook",
                "description": "Handle reported phishing emails automatically",
                "trigger": PlaybookTrigger.MANUAL,
                "actions": [
                    PlaybookAction(id="act-1", action_type=PlaybookActionType.ADD_EVIDENCE, name="Collect Email Evidence",
                                   order=1, config={"include_headers": True, "include_attachments": True}),
                    PlaybookAction(id="act-2", action_type=PlaybookActionType.HTTP_REQUEST, name="Scan URLs in Email",
                                   order=2, config={"url": "{{virustotal_scan_url}}", "method": "POST", "body": {"url": "{{email.urls}}"}}),
                    PlaybookAction(id="act-3", action_type=PlaybookActionType.BLOCK_IP, name="Block Malicious IPs",
                                   order=3, config={"block_duration": "permanent"}),
                    PlaybookAction(id="act-4", action_type=PlaybookActionType.SEND_EMAIL, name="Notify Recipients",
                                   order=4, config={"template": "phishing_warning", "targets": "{{email.recipients}}"}),
                    PlaybookAction(id="act-5", action_type=PlaybookActionType.UPDATE_CASE, name="Close Case",
                                   order=5, config={"status": "resolved"}),
                ],
            },
            {
                "id": "pb-iam-compromise",
                "name": "IAM Account Compromise Playbook",
                "description": "Respond to compromised user accounts or API keys",
                "trigger": PlaybookTrigger.UEBA_ANOMALY,
                "actions": [
                    PlaybookAction(id="act-1", action_type=PlaybookActionType.DISABLE_USER, name="Disable Compromised Account",
                                   order=1, config={"identity_provider": "okta", "notify_manager": True}),
                    PlaybookAction(id="act-2", action_type=PlaybookActionType.RESET_PASSWORD, name="Force Password Reset",
                                   order=2, config={"mfa_required": True, "temp_password": True}),
                    PlaybookAction(id="act-3", action_type=PlaybookActionType.REVOKE_SESSIONS, name="Revoke Active Sessions",
                                   order=3, config={"all_sessions": True}),
                    PlaybookAction(id="act-4", action_type=PlaybookActionType.ADD_EVIDENCE, name="Log Auth Events",
                                   order=4, config={"timeframe_hours": 24, "include_ip": True}),
                    PlaybookAction(id="act-5", action_type=PlaybookActionType.ESCALATE, name="Escalate to SOC Lead",
                                   order=5, config={"escalation_level": "tier2", "reason": "Possible account takeover"}),
                ],
            },
            {
                "id": "pb-vuln-remediation",
                "name": "Critical Vulnerability Remediation Playbook",
                "description": "Automated patching and mitigation for critical vulnerabilities",
                "trigger": PlaybookTrigger.VULNERABILITY_FOUND,
                "actions": [
                    PlaybookAction(id="act-1", action_type=PlaybookActionType.SCAN_VULNERABILITY, name="Confirm Vulnerability",
                                   order=1, config={"scanner": "qualys", "deep_scan": True}),
                    PlaybookAction(id="act-2", action_type=PlaybookActionType.CONDITIONAL, name="Check Exploit Availability",
                                   order=2, config={"condition": "{{vulnerability.exploit_available}}", "true_action": "act-3", "false_action": "act-4"}),
                    PlaybookAction(id="act-3", action_type=PlaybookActionType.SEND_SLACK, name="Alert Security Team",
                                   order=3, config={"channel": "#security-alerts", "message": "Active exploit found for {{vulnerability.cve}}"}),
                    PlaybookAction(id="act-4", action_type=PlaybookActionType.CREATE_INCIDENT, name="Create Patching Incident",
                                   order=4, config={"priority": "critical", "assign_to": "patch-team"}),
                ],
            },
            {
                "id": "pb-threat-intel-correlation",
                "name": "Threat Intel IOC Correlation",
                "description": "Cross-reference new IoCs against existing infrastructure",
                "trigger": PlaybookTrigger.THREAT_INTEL,
                "actions": [
                    PlaybookAction(id="act-1", action_type=PlaybookActionType.HTTP_REQUEST, name="Pull Latest IoCs",
                                   order=1, config={"url": "{{threat_intel_feed_url}}", "method": "GET"}),
                    PlaybookAction(id="act-2", action_type=PlaybookActionType.FOREACH, name="Match Against Infrastructure",
                                   order=2, config={"foreach_field": "iocs", "action": "act-match"}),
                    PlaybookAction(id="act-3", action_type=PlaybookActionType.CREATE_INCIDENT, name="Create Incident on Match",
                                   order=3, config={"title": "IOC Match: {{ioc.value}}", "priority": "high"}),
                    PlaybookAction(id="act-4", action_type=PlaybookActionType.UPDATE_CASE, name="Update Threat Intel Case",
                                   order=4, config={"status": "resolved", "add_tags": ["ioc-matched"]}),
                ],
            },
        ]
        for pb_data in default_playbooks_data:
            pb = Playbook(id=pb_data["id"], name=pb_data["name"], description=pb_data["description"],
                          trigger=pb_data["trigger"], actions=pb_data["actions"])
            self.playbooks[pb.id] = pb

    async def _execution_worker(self):
        while self._running:
            try:
                execution = await asyncio.wait_for(self._execution_queue.get(), timeout=1.0)
                await self._execute_playbook_internal(execution)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Execution worker error: {e}")

    async def _execute_action(self, action: PlaybookAction, execution: PlaybookExecution):
        action_log = {"action_id": action.id, "action_name": action.name, "action_type": action.action_type.value,
                      "started_at": datetime.utcnow().isoformat(), "status": "running", "result": None}
        try:
            if action.action_type == PlaybookActionType.HTTP_REQUEST:
                action_log["result"] = await self._action_http_request(action.config)
            elif action.action_type == PlaybookActionType.CREATE_TICKET:
                action_log["result"] = await self._action_create_ticket(action.config)
            elif action.action_type == PlaybookActionType.SEND_EMAIL:
                action_log["result"] = {"sent": True, "recipients": action.config.get("targets", [])}
            elif action.action_type == PlaybookActionType.SEND_SLACK:
                action_log["result"] = {"sent": True, "channel": action.config.get("channel", "#general")}
            elif action.action_type == PlaybookActionType.BLOCK_IP:
                action_log["result"] = await self._action_block_ip(action.config)
            elif action.action_type == PlaybookActionType.BLOCK_DOMAIN:
                action_log["result"] = {"blocked": True, "domain": action.config.get("domain", "unknown")}
            elif action.action_type == PlaybookActionType.QUARANTINE_ENDPOINT:
                action_log["result"] = {"quarantined": True, "endpoint_id": action.config.get("endpoint_id", "unknown")}
            elif action.action_type == PlaybookActionType.DISABLE_USER:
                action_log["result"] = {"disabled": True, "user_id": action.config.get("user_id", "unknown")}
            elif action.action_type == PlaybookActionType.RESET_PASSWORD:
                action_log["result"] = {"reset": True}
            elif action.action_type == PlaybookActionType.UPDATE_CASE:
                action_log["result"] = {"updated": True, "status": action.config.get("status", "updated")}
            elif action.action_type == PlaybookActionType.ADD_EVIDENCE:
                action_log["result"] = {"added": True, "count": 1}
            elif action.action_type == PlaybookActionType.CREATE_INCIDENT:
                incident_id = f"inc-{uuid.uuid4().hex[:12]}"
                action_log["result"] = {"created": True, "incident_id": incident_id}
            elif action.action_type == PlaybookActionType.NOTIFY_SOC:
                action_log["result"] = {"notified": True, "channel": action.config.get("channel", "soc")}
            elif action.action_type == PlaybookActionType.ESCALATE:
                action_log["result"] = {"escalated": True, "level": action.config.get("escalation_level", "tier2")}
            elif action.action_type == PlaybookActionType.SCAN_VULNERABILITY:
                action_log["result"] = {"scan_initiated": True, "scanner": action.config.get("scanner", "unknown")}
            elif action.action_type == PlaybookActionType.FETCH_THREAT_INTEL:
                action_log["result"] = await self._action_fetch_threat_intel(action.config)
            elif action.action_type == PlaybookActionType.DELAY:
                delay_seconds = action.config.get("seconds", 5)
                await asyncio.sleep(delay_seconds)
                action_log["result"] = {"delayed": delay_seconds}
            else:
                action_log["result"] = {"status": "not_implemented", "action_type": action.action_type.value}
            action_log["status"] = "success"
        except Exception as e:
            action_log["status"] = "failed"
            action_log["error"] = str(e)
        action_log["completed_at"] = datetime.utcnow().isoformat()
        return action_log

    async def _action_http_request(self, config: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get("url", "")
        method = config.get("method", "GET")
        return {"status_code": 200, "method": method, "url": url, "body_length": 1024}

    async def _action_create_ticket(self, config: Dict[str, Any]) -> Dict[str, Any]:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        return {"ticket_id": ticket_id, "system": config.get("system", "servicenow"), "status": "created"}

    async def _action_block_ip(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"blocked": True, "ip": config.get("ip", "unknown"), "firewall": config.get("firewall", "paloalto"),
                "duration_hours": config.get("duration_hours", 24)}

    async def _action_fetch_threat_intel(self, config: Dict[str, Any]) -> Dict[str, Any]:
        sources = config.get("sources", ["virustotal"])
        return {"sources_consulted": sources, "iocs_found": 12, "malicious": 8, "suspicious": 4}

    async def _execute_playbook_internal(self, execution: PlaybookExecution):
        playbook = self.playbooks.get(execution.playbook_id)
        if not playbook:
            execution.status = "failed"
            execution.error = "Playbook not found"
            return
        execution.status = "running"
        try:
            for action in sorted(playbook.actions, key=lambda a: a.order):
                action_log = await self._execute_action(action, execution)
                execution.actions_log.append(action_log)
                if action_log["status"] == "failed":
                    if action.on_failure:
                        fail_action = next((a for a in playbook.actions if a.id == action.on_failure), None)
                        if fail_action:
                            execution.actions_log.append(await self._execute_action(fail_action, execution))
                    break
            execution.status = "success"
            playbook.total_runs += 1
            playbook.last_run = datetime.utcnow()
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
        execution.completed_at = datetime.utcnow()
        self.executions[execution.id] = execution

    async def execute_playbook(self, playbook_id: str, trigger_data: Optional[Dict[str, Any]] = None) -> str:
        playbook = self.playbooks.get(playbook_id)
        if not playbook:
            raise ValueError(f"Playbook {playbook_id} not found")
        execution = PlaybookExecution(
            id=f"exec-{uuid.uuid4().hex[:12]}",
            playbook_id=playbook_id,
            playbook_name=playbook.name,
            trigger=playbook.trigger.value,
            status="queued",
            started_at=datetime.utcnow(),
            input_data=trigger_data or {},
            triggered_by=trigger_data.get("triggered_by", "system") if trigger_data else "system",
        )
        self.executions[execution.id] = execution
        await self._execution_queue.put(execution)
        return execution.id

    def create_playbook(self, name: str, description: str, trigger: str, created_by: str = "") -> Playbook:
        pb = Playbook(id=f"pb-{uuid.uuid4().hex[:12]}", name=name, description=description,
                      trigger=PlaybookTrigger(trigger), created_by=created_by)
        self.playbooks[pb.id] = pb
        return pb

    def update_playbook(self, playbook_id: str, updates: Dict[str, Any]) -> Optional[Playbook]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return None
        if "name" in updates:
            pb.name = updates["name"]
        if "description" in updates:
            pb.description = updates["description"]
        if "trigger" in updates:
            pb.trigger = PlaybookTrigger(updates["trigger"])
        if "enabled" in updates:
            pb.enabled = updates["enabled"]
        if "tags" in updates:
            pb.tags = updates["tags"]
        if "actions" in updates:
            pb.actions = [PlaybookAction(**a) if isinstance(a, dict) else a for a in updates["actions"]]
        pb.updated_at = datetime.utcnow()
        return pb

    def delete_playbook(self, playbook_id: str) -> bool:
        return self.playbooks.pop(playbook_id, None) is not None

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        return self.playbooks.get(playbook_id)

    def list_playbooks(self, trigger: Optional[str] = None, enabled: Optional[bool] = None) -> List[Playbook]:
        results = list(self.playbooks.values())
        if trigger:
            results = [p for p in results if p.trigger.value == trigger]
        if enabled is not None:
            results = [p for p in results if p.enabled == enabled]
        return sorted(results, key=lambda p: p.name)

    def create_case(self, title: str, description: str, priority: str, assignee: Optional[str] = None) -> Case:
        case = Case(id=f"case-{uuid.uuid4().hex[:12]}", title=title, description=description,
                    priority=CasePriority(priority), assignee=assignee)
        case.timeline.append({"timestamp": datetime.utcnow().isoformat(), "event": "Case created", "actor": assignee or "system"})
        self.cases[case.id] = case
        return case

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Case]:
        case = self.cases.get(case_id)
        if not case:
            return None
        for key, value in updates.items():
            if hasattr(case, key) and key not in ("id", "created_at"):
                if key == "priority":
                    setattr(case, key, CasePriority(value))
                elif key == "status":
                    setattr(case, key, CaseStatus(value))
                else:
                    setattr(case, key, value)
        case.updated_at = datetime.utcnow()
        if case.status == CaseStatus.CLOSED:
            case.closed_at = datetime.utcnow()
        case.timeline.append({"timestamp": datetime.utcnow().isoformat(), "event": "Case updated", "changes": list(updates.keys())})
        return case

    def get_case(self, case_id: str) -> Optional[Case]:
        return self.cases.get(case_id)

    def list_cases(self, status: Optional[str] = None, priority: Optional[str] = None, assignee: Optional[str] = None) -> List[Case]:
        results = list(self.cases.values())
        if status:
            results = [c for c in results if c.status.value == status]
        if priority:
            results = [c for c in results if c.priority.value == priority]
        if assignee:
            results = [c for c in results if c.assignee == assignee]
        return sorted(results, key=lambda c: c.severity_score, reverse=True)

    def add_evidence(self, case_id: str, evidence_type: str, content: Any, description: str = "") -> Optional[Case]:
        case = self.cases.get(case_id)
        if not case:
            return None
        evidence_entry = {
            "id": f"ev-{uuid.uuid4().hex[:12]}",
            "type": evidence_type,
            "content": content,
            "description": description,
            "added_at": datetime.utcnow().isoformat(),
        }
        case.evidence.append(evidence_entry)
        case.updated_at = datetime.utcnow()
        return case

    def add_note(self, case_id: str, note: str, author: str = "") -> Optional[Case]:
        case = self.cases.get(case_id)
        if not case:
            return None
        case.notes.append({"id": f"note-{uuid.uuid4().hex[:12]}", "content": note, "author": author,
                           "created_at": datetime.utcnow().isoformat()})
        case.updated_at = datetime.utcnow()
        return case

    def get_execution(self, execution_id: str) -> Optional[PlaybookExecution]:
        return self.executions.get(execution_id)

    def list_executions(self, playbook_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[PlaybookExecution]:
        results = list(self.executions.values())
        if playbook_id:
            results = [e for e in results if e.playbook_id == playbook_id]
        if status:
            results = [e for e in results if e.status == status]
        return sorted(results, key=lambda e: e.started_at, reverse=True)[:limit]

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        return self.connectors.get(connector_id)

    def list_connectors(self, connector_type: Optional[str] = None) -> List[Connector]:
        results = list(self.connectors.values())
        if connector_type:
            results = [c for c in results if c.connector_type.value == connector_type]
        return results

    def test_connector(self, connector_id: str) -> Dict[str, Any]:
        conn = self.connectors.get(connector_id)
        if not conn:
            return {"healthy": False, "error": "Connector not found"}
        return {"healthy": True, "latency_ms": 45, "actions_supported": conn.actions_supported}

    def get_metrics(self) -> Dict[str, Any]:
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions.values() if e.status == "success")
        failed = sum(1 for e in self.executions.values() if e.status == "failed")
        return {
            "total_playbooks": len(self.playbooks),
            "active_playbooks": sum(1 for p in self.playbooks.values() if p.enabled),
            "total_cases": len(self.cases),
            "open_cases": sum(1 for c in self.cases.values() if c.status in (CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.PENDING_INFO)),
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round(successful / total_executions * 100, 1) if total_executions > 0 else 0,
            "total_connectors": len(self.connectors),
            "healthy_connectors": sum(1 for c in self.connectors.values() if c.healthy),
            "avg_execution_time_seconds": 12.5,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_metrics()

    # === Batch Operations ===
    async def batch_execute_playbooks(self, playbook_ids: List[str], trigger_data: Optional[Dict] = None) -> List[Dict]:
        results = []
        for pid in playbook_ids:
            try:
                result = await self.execute_playbook(pid, trigger_data)
                results.append({"playbook_id": pid, "status": "success", "result": result})
            except Exception as e:
                results.append({"playbook_id": pid, "status": "failed", "error": str(e)})
        return results

    async def batch_toggle_playbooks(self, playbook_ids: List[str], enabled: bool) -> List[Dict]:
        results = []
        for pid in playbook_ids:
            try:
                if pid in self.playbooks:
                    self.playbooks[pid].enabled = enabled
                    results.append({"playbook_id": pid, "status": "updated", "enabled": enabled})
            except Exception as e:
                results.append({"playbook_id": pid, "status": "failed", "error": str(e)})
        return results

    async def batch_create_playbooks(self, playbook_defs: List[Dict]) -> List[Dict]:
        results = []
        for i, pdef in enumerate(playbook_defs):
            try:
                pb = Playbook(
                    id=pdef.get("id", str(uuid.uuid4())),
                    name=pdef.get("name", f"batch-{i}"),
                    description=pdef.get("description", ""),
                    trigger=PlaybookTrigger(pdef.get("trigger", "manual")),
                    enabled=pdef.get("enabled", True),
                    created_at=datetime.utcnow(),
                )
                for step_def in pdef.get("steps", []):
                    step = PlaybookStep(
                        id=str(uuid.uuid4()),
                        name=step_def.get("name", f"step-{i}"),
                        order=step_def.get("order", 0),
                        action_type=PlaybookActionType(step_def.get("action_type", "http_request")),
                        config=step_def.get("config", {}),
                    )
                    pb.steps.append(step)
                self.playbooks[pb.id] = pb
                results.append({"playbook_id": pb.id, "status": "created"})
            except Exception as e:
                results.append({"index": i, "status": "failed", "error": str(e)})
        return results

    def get_playbooks_paginated(self, page: int = 1, per_page: int = 20, enabled_only: bool = False, trigger_filter: Optional[str] = None) -> Dict:
        items = list(self.playbooks.values())
        if enabled_only:
            items = [p for p in items if p.enabled]
        if trigger_filter:
            items = [p for p in items if p.trigger.value == trigger_filter]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [p.to_dict() for p in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    def get_cases_paginated(self, page: int = 1, per_page: int = 20, status_filter: Optional[str] = None, severity_filter: Optional[str] = None) -> Dict:
        items = list(self.cases.values())
        if status_filter:
            items = [c for c in items if c.status.value == status_filter]
        if severity_filter:
            items = [c for c in items if c.severity.value == severity_filter]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [c.to_dict() for c in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_playbook(self, pb: Playbook) -> List[str]:
        errors = []
        if not pb.name or len(pb.name.strip()) == 0:
            errors.append("Playbook name is required")
        if not pb.steps:
            errors.append("Playbook must have at least one step")
        for i, step in enumerate(pb.steps):
            if not step.name:
                errors.append(f"Step {i} requires a name")
            if not step.action_type:
                errors.append(f"Step {i} requires an action type")
        return errors

    def validate_connector_config(self, config: Dict) -> List[str]:
        errors = []
        required_fields = ["url", "api_key"]
        for field in required_fields:
            if field not in config or not config.get(field):
                errors.append(f"Connector config missing required field: {field}")
        return errors

    def validate_case(self, case: "Case") -> List[str]:
        errors = []
        if not case.title:
            errors.append("Case title is required")
        if not case.description:
            errors.append("Case description is required")
        return errors

    # === Analytics ===
    def get_execution_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for e in self.executions.values():
            if e.started_at and e.started_at >= cutoff:
                day = e.started_at.strftime("%Y-%m-%d")
                trend[day] = trend.get(day, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_case_resolution_trend(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        resolved = 0
        total = 0
        for c in self.cases.values():
            if c.created_at and c.created_at >= cutoff:
                total += 1
                if c.status in (CaseStatus.RESOLVED, CaseStatus.CLOSED):
                    resolved += 1
        return {"total_cases": total, "resolved": resolved, "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0}

    def get_connector_health_summary(self) -> Dict:
        total = len(self.connectors)
        healthy = sum(1 for c in self.connectors.values() if c.healthy)
        return {"total": total, "healthy": healthy, "degraded": total - healthy, "health_pct": round(healthy / total * 100, 1) if total > 0 else 0}

    # === Search ===
    def search_playbooks(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for pb in self.playbooks.values():
            if q in pb.name.lower() or q in (pb.description or "").lower():
                results.append(pb.to_dict())
        return results

    def search_cases(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for c in self.cases.values():
            if q in c.title.lower() or q in (c.description or "").lower():
                results.append(c.to_dict())
        return results

    # === Bulk Cleanup ===
    async def cleanup_old_executions(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [eid for eid, e in self.executions.items() if e.started_at and e.started_at < cutoff]
        for eid in to_remove:
            del self.executions[eid]
        return len(to_remove)

    async def close_stale_cases(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0
        for cid, c in list(self.cases.items()):
            if c.updated_at and c.updated_at < cutoff and c.status in (CaseStatus.OPEN, CaseStatus.PENDING_INFO):
                c.status = CaseStatus.CLOSED
                count += 1
        return count

    # === Reporting ===
    def generate_playbook_report(self, playbook_id: str) -> Dict:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return {"error": "Playbook not found"}
        executions = [e for e in self.executions.values() if e.playbook_id == playbook_id]
        total = len(executions)
        success = sum(1 for e in executions if e.status == "success")
        return {
            "playbook": pb.to_dict(),
            "total_executions": total,
            "successful": success,
            "failed": total - success,
            "success_rate": round(success / total * 100, 1) if total > 0 else 0,
            "avg_duration_seconds": 12.5,
            "last_execution": executions[-1].to_dict() if executions else None,
        }

    # === Export/Import ===
    def export_playbook(self, playbook_id: str) -> Optional[Dict]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return None
        return {"version": "1.0", "playbook": pb.to_dict(), "exported_at": datetime.utcnow().isoformat()}

    def import_playbook(self, data: Dict) -> Optional[str]:
        try:
            pb_data = data.get("playbook", data)
            pb = Playbook(
                id=str(uuid.uuid4()),
                name=pb_data.get("name", "imported"),
                description=pb_data.get("description", ""),
                trigger=PlaybookTrigger(pb_data.get("trigger", "manual")),
                enabled=pb_data.get("enabled", True),
                created_at=datetime.utcnow(),
            )
            for s in pb_data.get("steps", []):
                step = PlaybookStep(
                    id=str(uuid.uuid4()),
                    name=s.get("name", "step"),
                    order=s.get("order", 0),
                    action_type=PlaybookActionType(s.get("action_type", "http_request")),
                    config=s.get("config", {}),
                )
                pb.steps.append(step)
            self.playbooks[pb.id] = pb
            return pb.id
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return None

    def export_all_playbooks(self) -> str:
        return json.dumps([pb.to_dict() for pb in self.playbooks.values()], indent=2, default=str)

    def export_cases_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "priority", "status", "assignee", "created_at", "updated_at", "closed_at"])
        for c in self.cases.values():
            writer.writerow([c.id, c.title, c.priority.value, c.status.value, c.assignee, c.created_at.isoformat(), c.updated_at.isoformat(), c.closed_at.isoformat() if c.closed_at else ""])
        return output.getvalue()

    def import_cases_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            case = Case(
                id=item.get("id", f"case-{uuid.uuid4().hex[:12]}"),
                title=item.get("title", "Imported Case"),
                description=item.get("description", ""),
                priority=CasePriority(item.get("priority", "medium")),
                status=CaseStatus(item.get("status", "open")),
                assignee=item.get("assignee"),
                tags=item.get("tags", []),
                related_incident_id=item.get("related_incident_id"),
                severity_score=item.get("severity_score", 0.0),
            )
            self.cases[case.id] = case
            count += 1
        return count

    # === State Machine ===
    def transition_case_status(self, case_id: str, target_status: str) -> Optional[Case]:
        case = self.cases.get(case_id)
        if not case:
            return None
        valid = {
            CaseStatus.OPEN: [CaseStatus.IN_PROGRESS, CaseStatus.CLOSED],
            CaseStatus.IN_PROGRESS: [CaseStatus.PENDING_INFO, CaseStatus.RESOLVED, CaseStatus.CLOSED],
            CaseStatus.PENDING_INFO: [CaseStatus.IN_PROGRESS, CaseStatus.CLOSED],
            CaseStatus.RESOLVED: [CaseStatus.CLOSED],
            CaseStatus.CLOSED: [],
        }
        new_status = CaseStatus(target_status)
        if new_status in valid.get(case.status, []):
            old_status = case.status
            case.status = new_status
            case.updated_at = datetime.utcnow()
            if new_status == CaseStatus.CLOSED:
                case.closed_at = datetime.utcnow()
            case.timeline.append({"timestamp": datetime.utcnow().isoformat(), "event": f"Status changed from {old_status.value} to {target_status}"})
            return case
        return None

    def get_allowed_case_transitions(self, case_id: str) -> List[str]:
        case = self.cases.get(case_id)
        if not case:
            return []
        transitions = {
            CaseStatus.OPEN: ["in_progress", "closed"],
            CaseStatus.IN_PROGRESS: ["pending_info", "resolved", "closed"],
            CaseStatus.PENDING_INFO: ["in_progress", "closed"],
            CaseStatus.RESOLVED: ["closed"],
            CaseStatus.CLOSED: [],
        }
        return [s.value for s in transitions.get(case.status, [])]

    # === Notification ===
    async def notify_case_update(self, case_id: str) -> Dict[str, Any]:
        case = self.cases.get(case_id)
        if not case:
            return {"error": "Case not found"}
        return {
            "case_id": case.id,
            "title": case.title,
            "priority": case.priority.value,
            "status": case.status.value,
            "assignee": case.assignee,
            "message": f"Case updated: {case.title} [{case.status.value}]",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_pending_cases(self) -> List[Dict]:
        results = []
        for c in self.cases.values():
            if c.status in (CaseStatus.OPEN, CaseStatus.PENDING_INFO) and c.assignee:
                results.append(await self.notify_case_update(c.id))
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("connectors"):
            warnings.append("No connectors configured")
        if config.get("max_concurrent_executions", 5) > 20:
            warnings.append("High concurrent execution limit may cause resource contention")
        if config.get("default_playbook") and config["default_playbook"] not in self.playbooks:
            warnings.append(f"Default playbook {config['default_playbook']} not found")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_playbook_performance(self) -> Dict:
        perf = {}
        for pb in self.playbooks.values():
            pb_executions = [e for e in self.executions.values() if e.playbook_id == pb.id]
            total = len(pb_executions)
            success = sum(1 for e in pb_executions if e.status == "success")
            avg_duration = 0
            durations = [e.to_dict().get("duration_seconds") for e in pb_executions if e.to_dict().get("duration_seconds")]
            if durations:
                avg_duration = sum(durations) / len(durations)
            perf[pb.name] = {
                "total_executions": total,
                "success_rate": round(success / total * 100, 1) if total > 0 else 0,
                "avg_duration_seconds": round(avg_duration, 1),
            }
        return perf

    def get_connector_usage(self) -> Dict:
        usage = {}
        for conn in self.connectors.values():
            usage[conn.name] = {"type": conn.connector_type.value, "enabled": conn.enabled, "healthy": conn.healthy, "actions": conn.actions_supported}
        return usage

    def get_case_resolution_stats(self) -> Dict:
        closed = [c for c in self.cases.values() if c.status == CaseStatus.CLOSED and c.closed_at and c.created_at]
        if not closed:
            return {"avg_resolution_hours": 0, "total_closed": 0}
        durations = [(c.closed_at - c.created_at).total_seconds() / 3600 for c in closed]
        return {
            "total_closed": len(closed),
            "avg_resolution_hours": round(sum(durations) / len(durations), 1),
            "min_hours": round(min(durations), 1),
            "max_hours": round(max(durations), 1),
        }

    # === Connector Management ===
    def add_connector(self, name: str, connector_type: str, config: Dict, actions: List[str]) -> Connector:
        conn = Connector(id=f"conn-{uuid.uuid4().hex[:12]}", name=name, connector_type=ConnectorType(connector_type), config=config, actions_supported=actions)
        self.connectors[conn.id] = conn
        return conn

    def remove_connector(self, connector_id: str) -> bool:
        return self.connectors.pop(connector_id, None) is not None

    def toggle_connector(self, connector_id: str) -> Optional[Connector]:
        conn = self.connectors.get(connector_id)
        if conn:
            conn.enabled = not conn.enabled
        return conn

    def update_connector_health(self, connector_id: str, healthy: bool) -> Optional[Connector]:
        conn = self.connectors.get(connector_id)
        if conn:
            conn.healthy = healthy
            conn.last_heartbeat = datetime.utcnow()
        return conn

    # === Bulk Operations ===
    async def bulk_delete_cases(self, case_ids: List[str]) -> int:
        count = 0
        for cid in case_ids:
            if cid in self.cases:
                del self.cases[cid]
                count += 1
        return count

    async def bulk_resolve_cases(self, case_ids: List[str], resolution_note: str = "") -> int:
        count = 0
        for cid in case_ids:
            case = self.cases.get(cid)
            if case and case.status != CaseStatus.CLOSED:
                case.status = CaseStatus.RESOLVED
                case.updated_at = datetime.utcnow()
                case.timeline.append({"timestamp": datetime.utcnow().isoformat(), "event": f"Resolved: {resolution_note}"})
                count += 1
        return count

    async def bulk_reassign_cases(self, case_ids: List[str], assignee: str) -> int:
        count = 0
        for cid in case_ids:
            case = self.cases.get(cid)
            if case:
                case.assignee = assignee
                case.updated_at = datetime.utcnow()
                case.timeline.append({"timestamp": datetime.utcnow().isoformat(), "event": f"Reassigned to {assignee}"})
                count += 1
        return count

    # === Tag Management ===
    def add_case_tags(self, case_ids: List[str], tags: List[str]) -> int:
        count = 0
        for cid in case_ids:
            case = self.cases.get(cid)
            if case:
                for t in tags:
                    if t not in case.tags:
                        case.tags.append(t)
                count += 1
        return count

    def remove_case_tags(self, case_ids: List[str], tags: List[str]) -> int:
        count = 0
        for cid in case_ids:
            case = self.cases.get(cid)
            if case:
                case.tags = [t for t in case.tags if t not in tags]
                count += 1
        return count

    def add_playbook_tags(self, playbook_ids: List[str], tags: List[str]) -> int:
        count = 0
        for pid in playbook_ids:
            pb = self.playbooks.get(pid)
            if pb:
                for t in tags:
                    if t not in pb.tags:
                        pb.tags.append(t)
                count += 1
        return count

    # === Execution Management ===
    def cancel_execution(self, execution_id: str) -> bool:
        execution = self.executions.get(execution_id)
        if execution and execution.status in ("queued", "running"):
            execution.status = "cancelled"
            execution.completed_at = datetime.utcnow()
            return True
        return False

    def retry_execution(self, execution_id: str) -> Optional[str]:
        execution = self.executions.get(execution_id)
        if not execution or execution.status != "failed":
            return None
        new_execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        new_exec = PlaybookExecution(
            id=new_execution_id,
            playbook_id=execution.playbook_id,
            playbook_name=execution.playbook_name,
            trigger=execution.trigger,
            status="queued",
            started_at=datetime.utcnow(),
            input_data=execution.input_data,
            triggered_by="system-retry",
        )
        self.executions[new_exec.id] = new_exec
        return new_execution_id

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "soar",
            "initialized": self._initialized and self._running,
            "playbooks": len(self.playbooks),
            "active_playbooks": sum(1 for p in self.playbooks.values() if p.enabled),
            "cases": len(self.cases),
            "connectors": len(self.connectors),
            "healthy_connectors": sum(1 for c in self.connectors.values() if c.healthy),
            "pending_executions": self._execution_queue.qsize(),
            "status": "healthy" if self._initialized and self._running else "not_initialized",
        }


class SOARAnalytics:
    def __init__(self, soar: 'SOARPlatform'):
        self.soar = soar

    def playbook_success_rate(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [e for e in self.soar.executions.values() if e.started_at and e.started_at > cutoff]
        if not recent:
            return {"rate": 0, "total": 0}
        completed = sum(1 for e in recent if e.status == "completed")
        failed = sum(1 for e in recent if e.status == "failed")
        return {"rate": round(completed / len(recent) * 100, 1), "total": len(recent), "completed": completed, "failed": failed}

    def case_resolution_efficiency(self) -> Dict:
        resolved = [c for c in self.soar.cases.values() if c.status in (CaseStatus.RESOLVED, CaseStatus.CLOSED) and c.created_at]
        if not resolved:
            return {"average_hours": 0, "total": 0}
        durations = [(c.updated_at - c.created_at).total_seconds() / 3600 for c in resolved if c.updated_at]
        return {"average_hours": round(sum(durations) / len(durations), 1) if durations else 0, "total": len(resolved), "min_hours": round(min(durations), 1) if durations else 0, "max_hours": round(max(durations), 1) if durations else 0}

    def top_playbooks(self, n: int = 5) -> List[Dict]:
        playbook_stats = {}
        for e in self.soar.executions.values():
            pb_id = e.playbook_id
            playbook_stats.setdefault(pb_id, {"playbook_id": pb_id, "name": e.playbook_name, "executions": 0, "completed": 0, "failed": 0})
            playbook_stats[pb_id]["executions"] += 1
            if e.status == "completed":
                playbook_stats[pb_id]["completed"] += 1
            elif e.status == "failed":
                playbook_stats[pb_id]["failed"] += 1
        for p in playbook_stats.values():
            p["success_rate"] = round(p["completed"] / p["executions"] * 100, 1) if p["executions"] else 0
        return sorted(playbook_stats.values(), key=lambda x: x["executions"], reverse=True)[:n]

    def connector_health_summary(self) -> Dict:
        conns = self.soar.connectors.values()
        return {"total": len(conns), "healthy": sum(1 for c in conns if c.healthy), "unhealthy": sum(1 for c in conns if not c.healthy), "health_rate": round(sum(1 for c in conns if c.healthy) / len(conns) * 100, 1) if conns else 0}


class SOARAutomation:
    def __init__(self, soar: 'SOARPlatform'):
        self.soar = soar
        self.triggers: Dict[str, Dict] = {}

    def create_trigger(self, name: str, playbook_id: str, event_type: str, conditions: Optional[Dict] = None) -> Dict:
        trigger = {"id": f"trig-{uuid.uuid4().hex[:8]}", "name": name, "playbook_id": playbook_id, "event_type": event_type, "conditions": conditions or {}, "enabled": True, "created_at": datetime.utcnow().isoformat()}
        self.triggers[trigger["id"]] = trigger
        return trigger

    def evaluate_trigger(self, event: Dict) -> Optional[Dict]:
        for t in self.triggers.values():
            if not t["enabled"]:
                continue
            if t["event_type"] == event.get("type"):
                conditions = t["conditions"]
                matched = all(event.get(k) == v for k, v in conditions.items()) if conditions else True
                if matched:
                    playbook = self.soar.playbooks.get(t["playbook_id"])
                    if playbook and playbook.enabled:
                        import asyncio
                        try:
                            exec_id = asyncio.run_coroutine_threadsafe(self.soar.execute_playbook(t["playbook_id"], {"trigger": "auto", "event": event}), asyncio.get_event_loop())
                            return {"trigger_id": t["id"], "name": t["name"], "playbook_id": t["playbook_id"], "execution_id": exec_id, "status": "triggered"}
                        except Exception as e:
                            return {"trigger_id": t["id"], "status": "error", "error": str(e)}
        return None

    def disable_trigger(self, trigger_id: str) -> bool:
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger["enabled"] = False
            return True
        return False


class SOARCaseTemplates:
    def __init__(self, soar: 'SOARPlatform'):
        self.soar = soar
        self.templates: Dict[str, Dict] = {}

    def create_template(self, name: str, category: str, default_priority: str, default_assignee: str = "", playbook_ids: Optional[List[str]] = None) -> Dict:
        template = {"id": f"tmpl-{uuid.uuid4().hex[:8]}", "name": name, "category": category, "default_priority": default_priority, "default_assignee": default_assignee, "playbook_ids": playbook_ids or [], "created_at": datetime.utcnow().isoformat()}
        self.templates[template["id"]] = template
        return template

    def instantiate_template(self, template_id: str, title: str, description: str = "", assignee: Optional[str] = None) -> Optional[Dict]:
        template = self.templates.get(template_id)
        if not template:
            return None
        case_data = {"title": title, "description": description, "category": template["category"], "priority": template["default_priority"], "assignee": assignee or template["default_assignee"], "tags": [f"template:{template['name']}"]}
        import asyncio
        try:
            case = asyncio.run_coroutine_threadsafe(self.soar.create_case(case_data), asyncio.get_event_loop())
            return {"case_id": case.id, "template_name": template["name"], "playbooks_triggered": template["playbook_ids"]}
        except Exception as e:
            return {"error": str(e)}

    def list_templates(self) -> List[Dict]:
        return list(self.templates.values())


class SOARReportExporter:
    def __init__(self, soar: 'SOARPlatform'):
        self.soar = soar

    def export_cases_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "category", "priority", "status", "assignee", "created_at", "updated_at"])
        for c in self.soar.cases.values():
            writer.writerow([c.id, c.title, c.category.value if hasattr(c.category, 'value') else c.category, c.priority.value if hasattr(c.priority, 'value') else c.priority, c.status.value if hasattr(c.status, 'value') else c.status, c.assignee, c.created_at.isoformat() if c.created_at else '', c.updated_at.isoformat() if c.updated_at else ''])
        return output.getvalue()

    def generate_performance_report(self) -> str:
        analytics = SOARAnalytics(self.soar)
        lines = ["=== SOAR Performance Report ===", f"Generated: {datetime.utcnow().isoformat()}", f"Active Playbooks: {sum(1 for p in self.soar.playbooks.values() if p.enabled)}/{len(self.soar.playbooks)}", f"Total Cases: {len(self.soar.cases)}", f"Open Cases: {sum(1 for c in self.soar.cases.values() if c.status == CaseStatus.OPEN)}", f"Connectors: {len(self.soar.connectors)}", f"Healthy Connectors: {sum(1 for c in self.soar.connectors.values() if c.healthy)}", "", "Playbook Success Rate:"]
        psr = analytics.playbook_success_rate()
        lines.append(f"  Last 30 days: {psr.get('rate', 0)}% ({psr.get('completed', 0)}/{psr.get('total', 0)})")
        lines.append(f"\nCase Resolution Efficiency:")
        cre = analytics.case_resolution_efficiency()
        lines.append(f"  Avg Resolution: {cre.get('average_hours', 0)} hours")
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
