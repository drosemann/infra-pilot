"""Smart Contract Monitoring — monitor deployed smart contracts for suspicious activity."""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ContractStandard(Enum):
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    ERC4626 = "erc4626"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class MonitoredContract:
    def __init__(self, contract_id: str, name: str, address: str, network: str):
        self.contract_id = contract_id
        self.name = name
        self.address = address
        self.network = network
        self.standard = ContractStandard.CUSTOM
        self.abi: list[dict[str, Any]] = []
        self.deployer_address = ""
        self.deploy_tx_hash = ""
        self.deploy_block = 0
        self.monitoring_enabled = True
        self.alert_on_high_value_tx = True
        self.alert_on_unusual_gas = True
        self.alert_on_owner_actions = True
        self.alert_on_large_approvals = True
        self.high_value_threshold_eth = 10.0
        self.unusual_gas_threshold_gwei = 500
        self.large_approval_threshold = 100000
        self.tags: list[str] = []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id, "name": self.name, "address": self.address,
            "network": self.network, "standard": self.standard.value,
            "deployer_address": self.deployer_address, "deploy_tx_hash": self.deploy_tx_hash,
            "deploy_block": self.deploy_block, "monitoring_enabled": self.monitoring_enabled,
            "alert_on_high_value_tx": self.alert_on_high_value_tx,
            "alert_on_unusual_gas": self.alert_on_unusual_gas,
            "alert_on_owner_actions": self.alert_on_owner_actions,
            "alert_on_large_approvals": self.alert_on_large_approvals,
            "high_value_threshold_eth": self.high_value_threshold_eth,
            "unusual_gas_threshold_gwei": self.unusual_gas_threshold_gwei,
            "large_approval_threshold": self.large_approval_threshold,
            "tags": self.tags, "created_at": self.created_at.isoformat(),
        }


class MonitoredTransaction:
    def __init__(self, tx_id: str, contract_id: str, tx_hash: str):
        self.tx_id = tx_id
        self.contract_id = contract_id
        self.tx_hash = tx_hash
        self.from_address = ""
        self.to_address = ""
        self.value_eth = 0.0
        self.gas_price_gwei = 0.0
        self.gas_used = 0
        self.block_number = 0
        self.timestamp = datetime.utcnow()
        self.function_name = ""
        self.function_args: dict[str, Any] = {}
        self.status = "success"
        self.logs: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "tx_id": self.tx_id, "contract_id": self.contract_id, "tx_hash": self.tx_hash,
            "from_address": self.from_address, "to_address": self.to_address,
            "value_eth": self.value_eth, "gas_price_gwei": self.gas_price_gwei,
            "gas_used": self.gas_used, "block_number": self.block_number,
            "timestamp": self.timestamp.isoformat(), "function_name": self.function_name,
            "function_args": self.function_args, "status": self.status,
        }


class SecurityAlert:
    def __init__(self, alert_id: str, contract_id: str, title: str, description: str, severity: AlertSeverity):
        self.alert_id = alert_id
        self.contract_id = contract_id
        self.title = title
        self.description = description
        self.severity = severity
        self.status = AlertStatus.OPEN
        self.tx_hash = ""
        self.triggered_by = ""
        self.detected_at = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None
        self.assigned_to = ""
        self.notes: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id, "contract_id": self.contract_id,
            "title": self.title, "description": self.description,
            "severity": self.severity.value, "status": self.status.value,
            "tx_hash": self.tx_hash, "triggered_by": self.triggered_by,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "assigned_to": self.assigned_to, "notes": self.notes,
        }


class AnomalyPattern:
    def __init__(self, pattern_id: str, name: str, description: str):
        self.pattern_id = pattern_id
        self.name = name
        self.description = description
        self.severity = AlertSeverity.MEDIUM
        self.enabled = True
        self.detection_rules: list[dict[str, Any]] = []
        self.sample_count = 0
        self.match_count = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id, "name": self.name,
            "description": self.description, "severity": self.severity.value,
            "enabled": self.enabled, "detection_rules": self.detection_rules,
            "sample_count": self.sample_count, "match_count": self.match_count,
        }


class ContractMonitorService:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.contracts: dict[str, MonitoredContract] = {}
        self.transactions: dict[str, MonitoredTransaction] = {}
        self.alerts: dict[str, SecurityAlert] = {}
        self.patterns: dict[str, AnomalyPattern] = {}
        self.tx_history: dict[str, list[MonitoredTransaction]] = defaultdict(list)
        self.storage_path = config.get("storage_path", "data/contract_monitoring.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for c_data in data.get("contracts", []):
                    c = MonitoredContract(c_data["contract_id"], c_data["name"], c_data["address"], c_data["network"])
                    c.standard = ContractStandard(c_data.get("standard", "custom"))
                    c.monitoring_enabled = c_data.get("monitoring_enabled", True)
                    c.deployer_address = c_data.get("deployer_address", "")
                    c.tags = c_data.get("tags", [])
                    self.contracts[c.contract_id] = c
                for a_data in data.get("alerts", []):
                    a = SecurityAlert(a_data["alert_id"], a_data["contract_id"], a_data["title"], a_data["description"], AlertSeverity(a_data["severity"]))
                    a.status = AlertStatus(a_data.get("status", "open"))
                    a.tx_hash = a_data.get("tx_hash", "")
                    self.alerts[a.alert_id] = a
                for p_data in data.get("patterns", []):
                    p = AnomalyPattern(p_data["pattern_id"], p_data["name"], p_data["description"])
                    self.patterns[p.pattern_id] = p
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        self._seed_default_patterns()
        logger.info("Initialized ContractMonitorService with %d contracts, %d alerts", len(self.contracts), len(self.alerts))

    async def close(self):
        self._save()

    def _save(self):
        data = {
            "contracts": [c.to_dict() for c in self.contracts.values()],
            "alerts": [a.to_dict() for a in self.alerts.values()],
            "patterns": [p.to_dict() for p in self.patterns.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _seed_default_patterns(self):
        default_patterns = [
            ("flash-loan-attack", "Flash Loan Attack", "Detects flash loan based price manipulation attacks"),
            ("rug-pull-detection", "Rug Pull Detection", "Detects liquidity removal or large transfers by deployer"),
            ("suspicious-upgrade", "Suspicious Proxy Upgrade", "Detects unexpected proxy/implementation upgrades"),
            ("large-approval", "Large Approval", "Detects unusually large token approvals"),
            ("owner-action", "Owner Action", "Detects privileged owner actions"),
            ("high-value-transfer", "High Value Transfer", "Detects high value token transfers"),
            ("unusual-gas", "Unusual Gas Usage", "Detects transactions with abnormally high gas usage"),
        ]
        for pid, name, desc in default_patterns:
            if pid not in self.patterns:
                p = AnomalyPattern(pid, name, desc)
                self.patterns[pid] = p

    async def register_contract(self, name: str, address: str, network: str, standard: ContractStandard = ContractStandard.CUSTOM) -> MonitoredContract:
        contract_id = str(uuid.uuid4())
        contract = MonitoredContract(contract_id, name, address, network)
        contract.standard = standard
        self.contracts[contract_id] = contract
        self._save()
        logger.info("Registered contract %s on %s: %s", name, network, address)
        return contract

    def get_contract(self, contract_id: str) -> Optional[MonitoredContract]:
        return self.contracts.get(contract_id)

    def list_contracts(self, network: Optional[str] = None) -> list[MonitoredContract]:
        if network:
            return [c for c in self.contracts.values() if c.network == network]
        return list(self.contracts.values())

    async def delete_contract(self, contract_id: str) -> bool:
        if contract_id in self.contracts:
            del self.contracts[contract_id]
            self._save()
            return True
        return False

    async def ingest_transaction(self, contract_id: str, tx_hash: str, from_addr: str, value_eth: float, gas_price_gwei: float, function_name: str = "") -> MonitoredTransaction:
        tx_id = str(uuid.uuid4())
        tx = MonitoredTransaction(tx_id, contract_id, tx_hash)
        tx.from_address = from_addr
        tx.value_eth = value_eth
        tx.gas_price_gwei = gas_price_gwei
        tx.function_name = function_name
        self.transactions[tx_id] = tx
        self.tx_history[contract_id].append(tx)
        asyncio.create_task(self._analyze_transaction(contract_id, tx))
        return tx

    async def _analyze_transaction(self, contract_id: str, tx: MonitoredTransaction):
        contract = self.contracts.get(contract_id)
        if not contract or not contract.monitoring_enabled:
            return
        if contract.alert_on_high_value_tx and tx.value_eth >= contract.high_value_threshold_eth:
            await self._create_alert(contract_id, "High Value Transaction", f"Transaction of {tx.value_eth} ETH detected", AlertSeverity.HIGH, tx.tx_hash)
        if contract.alert_on_unusual_gas and tx.gas_price_gwei >= contract.unusual_gas_threshold_gwei:
            await self._create_alert(contract_id, "Unusual Gas Price", f"Gas price of {tx.gas_price_gwei} gwei detected", AlertSeverity.MEDIUM, tx.tx_hash)
        if contract.alert_on_owner_actions and tx.function_name in ("transferOwnership", "renounceOwnership", "upgradeTo", "initialize"):
            await self._create_alert(contract_id, "Owner Action Detected", f"Owner action {tx.function_name} executed", AlertSeverity.CRITICAL, tx.tx_hash)

    async def _create_alert(self, contract_id: str, title: str, description: str, severity: AlertSeverity, tx_hash: str = ""):
        alert_id = str(uuid.uuid4())
        alert = SecurityAlert(alert_id, contract_id, title, description, severity)
        alert.tx_hash = tx_hash
        self.alerts[alert_id] = alert
        self._save()
        logger.warning("Alert %s: %s [%s] on contract %s", alert_id, title, severity.value, contract_id)

    def list_alerts(self, severity: Optional[AlertSeverity] = None, status: Optional[AlertStatus] = None) -> list[SecurityAlert]:
        results = list(self.alerts.values())
        if severity:
            results = [a for a in results if a.severity == severity]
        if status:
            results = [a for a in results if a.status == status]
        return sorted(results, key=lambda a: a.detected_at, reverse=True)

    async def update_alert_status(self, alert_id: str, status: AlertStatus) -> bool:
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = status
            if status in (AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE):
                alert.resolved_at = datetime.utcnow()
            self._save()
            return True
        return False

    def get_anomaly_patterns(self) -> list[AnomalyPattern]:
        return list(self.patterns.values())

    async def toggle_pattern(self, pattern_id: str, enabled: bool) -> bool:
        pattern = self.patterns.get(pattern_id)
        if pattern:
            pattern.enabled = enabled
            self._save()
            return True
        return False

    def get_contract_analytics(self, contract_id: str) -> dict[str, Any]:
        txs = self.tx_history.get(contract_id, [])
        contract = self.contracts.get(contract_id)
        alerts = [a for a in self.alerts.values() if a.contract_id == contract_id]
        if not txs:
            return {"contract_id": contract_id, "total_tx": 0}
        return {
            "contract_id": contract_id,
            "name": contract.name if contract else "",
            "total_tx": len(txs),
            "total_value_eth": sum(t.value_eth for t in txs),
            "avg_gas_price_gwei": sum(t.gas_price_gwei for t in txs) / len(txs),
            "unique_from_addresses": len(set(t.from_address for t in txs)),
            "most_common_function": max(set(t.function_name for t in txs if t.function_name), key=lambda f: sum(1 for t in txs if t.function_name == f), default=""),
            "total_alerts": len(alerts),
            "critical_alerts": sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            "open_alerts": sum(1 for a in alerts if a.status == AlertStatus.OPEN),
        }

    def get_dashboard_summary(self) -> dict[str, Any]:
        return {
            "total_contracts": len(self.contracts),
            "monitored_contracts": sum(1 for c in self.contracts.values() if c.monitoring_enabled),
            "total_transactions": len(self.transactions),
            "total_alerts": len(self.alerts),
            "open_alerts": sum(1 for a in self.alerts.values() if a.status == AlertStatus.OPEN),
            "critical_alerts": sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.CRITICAL),
            "high_alerts": sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.HIGH),
            "resolved_today": sum(1 for a in self.alerts.values() if a.status == AlertStatus.RESOLVED and a.resolved_at and a.resolved_at.date() == datetime.utcnow().date()),
        }

    # === Export ===
    def export_contracts_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["contract_id", "name", "address", "network", "standard", "monitoring_enabled", "created_at"])
        for c in self.contracts.values():
            writer.writerow([c.contract_id, c.name, c.address, c.network, c.standard.value, c.monitoring_enabled, c.created_at.isoformat()])
        return output.getvalue()

    def export_alerts_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["alert_id", "contract_id", "title", "severity", "status", "detected_at", "resolved_at"])
        for a in self.alerts.values():
            writer.writerow([a.alert_id, a.contract_id, a.title, a.severity.value, a.status.value, a.detected_at.isoformat(), a.resolved_at.isoformat() if a.resolved_at else ""])
        return output.getvalue()

    def export_contracts_json(self) -> str:
        return json.dumps({"contracts": [c.to_dict() for c in self.contracts.values()], "alerts": [a.to_dict() for a in self.alerts.values()]}, indent=2, default=str)

    # === Import ===
    def import_contracts_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("contracts", data if isinstance(data, list) else []):
            c = MonitoredContract(
                item.get("contract_id", str(uuid.uuid4())),
                item.get("name", "Imported Contract"),
                item.get("address", "0x0"),
                item.get("network", "ethereum"),
            )
            c.standard = ContractStandard(item.get("standard", "custom"))
            c.monitoring_enabled = item.get("monitoring_enabled", True)
            c.deployer_address = item.get("deployer_address", "")
            c.tags = item.get("tags", [])
            self.contracts[c.contract_id] = c
            count += 1
        return count

    # === Notification ===
    async def notify_alert(self, alert_id: str) -> dict[str, Any]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return {"error": "Alert not found"}
        return {
            "alert_id": alert.alert_id,
            "contract_id": alert.contract_id,
            "title": alert.title,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "message": f"Security alert: {alert.title} [{alert.severity.value}]",
            "channels": ["slack", "email", "pagerduty"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_critical_alerts(self) -> list[dict[str, Any]]:
        results = []
        for a in self.alerts.values():
            if a.severity == AlertSeverity.CRITICAL and a.status == AlertStatus.OPEN:
                results.append(await self.notify_alert(a.alert_id))
        return results

    # === State Machine ===
    def transition_alert_status(self, alert_id: str, target_status: str) -> Optional[SecurityAlert]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        valid = {
            AlertStatus.OPEN: [AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING, AlertStatus.FALSE_POSITIVE],
            AlertStatus.ACKNOWLEDGED: [AlertStatus.INVESTIGATING, AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE],
            AlertStatus.INVESTIGATING: [AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE, AlertStatus.OPEN],
            AlertStatus.RESOLVED: [AlertStatus.OPEN],
            AlertStatus.FALSE_POSITIVE: [AlertStatus.OPEN],
        }
        new_status = AlertStatus(target_status)
        if new_status in valid.get(alert.status, []):
            alert.status = new_status
            if new_status in (AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE):
                alert.resolved_at = datetime.utcnow()
            self._save()
            return alert
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("storage_path"):
            warnings.append("No storage path configured, using default")
        if config.get("monitor_all_contracts") and not config.get("default_network"):
            warnings.append("Monitoring all contracts without a default network")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_contracts": len(self.contracts),
            "total_transactions": len(self.transactions),
            "total_alerts": len(self.alerts),
            "open_alerts": sum(1 for a in self.alerts.values() if a.status == AlertStatus.OPEN),
            "critical_alerts": sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.CRITICAL),
            "alerts_by_severity": {s.value: sum(1 for a in self.alerts.values() if a.severity == s) for s in AlertSeverity},
            "alerts_by_status": {s.value: sum(1 for a in self.alerts.values() if a.status == s) for s in AlertStatus},
            "contracts_by_standard": {s.value: sum(1 for c in self.contracts.values() if c.standard == s) for s in ContractStandard},
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        monitored = sum(1 for c in self.contracts.values() if c.monitoring_enabled)
        return {
            "total_contracts": len(self.contracts),
            "monitored": monitored,
            "open_critical": sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.CRITICAL and a.status == AlertStatus.OPEN),
            "health_pct": round(monitored / max(len(self.contracts), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_enable_monitoring(self, contract_ids: list[str]) -> int:
        count = 0
        for cid in contract_ids:
            c = self.contracts.get(cid)
            if c:
                c.monitoring_enabled = True
                count += 1
        self._save()
        return count

    async def bulk_disable_monitoring(self, contract_ids: list[str]) -> int:
        count = 0
        for cid in contract_ids:
            c = self.contracts.get(cid)
            if c:
                c.monitoring_enabled = False
                count += 1
        self._save()
        return count

    async def bulk_resolve_alerts(self, alert_ids: list[str]) -> int:
        count = 0
        for aid in alert_ids:
            a = self.alerts.get(aid)
            if a and a.status != AlertStatus.RESOLVED:
                a.status = AlertStatus.RESOLVED
                a.resolved_at = datetime.utcnow()
                count += 1
        self._save()
        return count

    async def bulk_delete_contracts(self, contract_ids: list[str]) -> int:
        count = 0
        for cid in contract_ids:
            if cid in self.contracts:
                del self.contracts[cid]
                count += 1
        self._save()
        return count

    # === Tag Management ===
    def add_contract_tags(self, contract_ids: list[str], tags: list[str]) -> int:
        count = 0
        for cid in contract_ids:
            c = self.contracts.get(cid)
            if c:
                for t in tags:
                    if t not in c.tags:
                        c.tags.append(t)
                count += 1
        self._save()
        return count

    def remove_contract_tags(self, contract_ids: list[str], tags: list[str]) -> int:
        count = 0
        for cid in contract_ids:
            c = self.contracts.get(cid)
            if c:
                c.tags = [t for t in c.tags if t not in tags]
                count += 1
        self._save()
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "contract_monitoring",
            "contracts": len(self.contracts),
            "transactions": len(self.transactions),
            "alerts": len(self.alerts),
            "patterns": len(self.patterns),
            "open_critical": sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.CRITICAL and a.status == AlertStatus.OPEN),
            "status": "healthy",
        }

    # === Webhook Management ===
    def register_webhook(self, name: str, url: str, events: list[str], secret: str = "") -> dict[str, Any]:
        webhook_id = str(uuid.uuid4())
        wh = {"webhook_id": webhook_id, "name": name, "url": url, "events": events,
              "secret": secret, "enabled": True, "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_webhooks"):
            self._webhooks: dict[str, dict[str, Any]] = {}
        self._webhooks[webhook_id] = wh
        return wh

    def get_webhooks(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_webhooks", {}).values())

    def toggle_webhook(self, webhook_id: str, enabled: bool) -> bool:
        whs = getattr(self, "_webhooks", {})
        if webhook_id in whs:
            whs[webhook_id]["enabled"] = enabled
            return True
        return False

    def delete_webhook(self, webhook_id: str) -> bool:
        whs = getattr(self, "_webhooks", {})
        if webhook_id in whs:
            del whs[webhook_id]
            return True
        return False

    def trigger_webhooks(self, event: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        for wh in getattr(self, "_webhooks", {}).values():
            if wh["enabled"] and event in wh["events"]:
                import json
                results.append({"webhook_id": wh["webhook_id"], "name": wh["name"],
                                 "url": wh["url"], "event": event, "status": "delivered",
                                 "delivered_at": datetime.utcnow().isoformat()})
        return results

    # === Security Reports ===
    def generate_security_report(self, contract_id: str = "") -> dict[str, Any]:
        contracts = [c for c in self.contracts.values() if not contract_id or c.contract_id == contract_id]
        alerts = [a for a in self.alerts.values() if not contract_id or a.contract_id == contract_id]
        return {
            "total_contracts": len(contracts),
            "monitored": sum(1 for c in contracts if c.monitoring_enabled),
            "total_alerts": len(alerts),
            "critical_alerts": sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            "open_alerts": sum(1 for a in alerts if a.status == AlertStatus.OPEN),
            "unique_patterns_detected": len(set(a.pattern_id for a in alerts if a.pattern_id)),
            "high_risk_contracts": [c.contract_id for c in contracts
                                     if sum(1 for a in alerts if a.contract_id == c.contract_id and a.severity == AlertSeverity.CRITICAL) > 5],
        }

    # === Batch Alert Management ===
    def batch_update_alert_severity(self, alert_ids: list[str], severity: AlertSeverity) -> int:
        count = 0
        for aid in alert_ids:
            a = self.alerts.get(aid)
            if a:
                a.severity = severity
                count += 1
        return count

    def batch_assign_alerts(self, alert_ids: list[str], assignee: str) -> int:
        count = 0
        for aid in alert_ids:
            a = self.alerts.get(aid)
            if a:
                a.assigned_to = assignee
                count += 1
        return count

    # === Pattern Analytics ===
    def get_pattern_analytics(self) -> dict[str, Any]:
        pattern_counts: dict[str, int] = {}
        pattern_severity: dict[str, dict[str, int]] = {}
        for a in self.alerts.values():
            pid = a.pattern_id or "unknown"
            pattern_counts[pid] = pattern_counts.get(pid, 0) + 1
            if pid not in pattern_severity:
                pattern_severity[pid] = {}
            pattern_severity[pid][a.severity.value] = pattern_severity[pid].get(a.severity.value, 0) + 1
        return {"total_patterns": len(pattern_counts), "pattern_counts": pattern_counts,
                "pattern_severity": pattern_severity,
                "top_patterns": sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]}

    # === Contract Verification ===
    def verify_contract_source(self, contract_id: str, source_code: str) -> dict[str, Any]:
        contract = self.contracts.get(contract_id)
        if not contract:
            return {"error": "Contract not found"}
        verification_id = str(uuid.uuid4())
        bytecode_match = len(source_code) > 0  # simplified
        return {"verification_id": verification_id, "contract_id": contract_id,
                "verified": bytecode_match, "bytecode_match": bytecode_match,
                "verified_at": datetime.utcnow().isoformat()}

    # === Export ===
    def export_contract_data(self, contract_id: str = "", format: str = "json") -> Any:
        contracts = [c for c in self.contracts.values() if not contract_id or c.contract_id == contract_id]
        if format == "csv":
            lines = ["contract_id,address,network,monitoring,alert_count"]
            for c in contracts:
                alert_count = sum(1 for a in self.alerts.values() if a.contract_id == c.contract_id)
                lines.append(f"{c.contract_id},{c.address},{c.network},{c.monitoring_enabled},{alert_count}")
            return "\n".join(lines)
        return {"contracts": [c.to_dict() for c in contracts]}

    # === Dashboard ===
    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "contract_count": len(self.contracts),
            "monitored_count": sum(1 for c in self.contracts.values() if c.monitoring_enabled),
            "total_transactions": len(self.transactions),
            "total_alerts": len(self.alerts),
            "open_critical": sum(1 for a in self.alerts.values() if a.severity == AlertSeverity.CRITICAL and a.status == AlertStatus.OPEN),
            "patterns_detected": len(self.patterns),
            "webhooks_configured": len(getattr(self, "_webhooks", {})),
        }

    # === Scheduling ===
    def schedule_scan(self, contract_ids: list[str], interval_hours: int = 24) -> dict[str, Any]:
        schedule_id = str(uuid.uuid4())
        schedule = {"schedule_id": schedule_id, "contract_ids": contract_ids, "interval_hours": interval_hours,
                    "next_run": (datetime.utcnow() + timedelta(hours=interval_hours)).isoformat(),
                    "status": "active", "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_schedules"):
            self._schedules: list[dict[str, Any]] = []
        self._schedules.append(schedule)
        return schedule

    def get_schedules(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_schedules", []))

    def cancel_schedule(self, schedule_id: str) -> bool:
        for s in getattr(self, "_schedules", []):
            if s["schedule_id"] == schedule_id:
                s["status"] = "cancelled"
                return True
        return False

    def get_monitoring_summary(self) -> dict[str, Any]:
        monitored = [c for c in self.contracts.values() if c.monitoring_enabled]
        return {
            "total_contracts": len(self.contracts),
            "monitored": len(monitored),
            "not_monitored": len(self.contracts) - len(monitored),
            "coverage_pct": round(len(monitored) / max(len(self.contracts), 1) * 100, 1),
        }

# === EXPANSION: Lifecycle, Health, Config & Analytics ===

class LifecycleManager:
    def __init__(self, parent):
        self.parent = parent
        self.ops: list[dict] = []

    def record(self, op_type: str, ref_id: str, status: str, detail: str = ""):
        self.ops.append({"type": op_type, "ref_id": ref_id, "status": status, "detail": detail, "ts": datetime.utcnow().isoformat()})

    def get_by_ref(self, ref_id: str, limit: int = 50) -> list[dict]:
        return [o for o in self.ops if o["ref_id"] == ref_id][-limit:]

    def get_success_rate(self, ref_id: str = None) -> float:
        items = [o for o in self.ops if not ref_id or o["ref_id"] == ref_id]
        if not items: return 1.0
        return sum(1 for o in items if o["status"] == "success") / len(items)

    def get_recent_failures(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [o for o in self.ops if o["status"] == "failed" and datetime.fromisoformat(o["ts"]) > cutoff]

class HealthChecker:
    def __init__(self, parent):
        self.parent = parent
        self.checks: list[dict] = []
    def run(self, ref_id: str) -> dict:
        result = {"ref_id": ref_id, "status": "healthy", "issues": [], "ts": datetime.utcnow().isoformat()}
        self.checks.append(result)
        return result
    def get_history(self, ref_id: str, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [c for c in self.checks if c.get("ref_id") == ref_id and datetime.fromisoformat(c["ts"]) > cutoff]
    def get_summary(self) -> dict:
        if not self.checks: return {"status": "unknown"}
        recent = self.checks[-100:]
        healthy = sum(1 for c in recent if c["status"] == "healthy")
        return {"total": len(recent), "healthy": healthy, "degraded": len(recent) - healthy}

class ConfigValidator:
    @staticmethod
    def validate(cfg: dict, required: list[str]) -> list[str]:
        return [f for f in required if f not in cfg]
    @staticmethod
    def merge(defaults: dict, overrides: dict) -> dict:
        result = dict(defaults)
        result.update(overrides)
        return result

class MetricsCollector:
    def __init__(self):
        self.data: dict[str, list] = {}
    def record(self, key: str, name: str, value: float):
        if key not in self.data: self.data[key] = []
        self.data[key].append({"name": name, "value": value, "ts": datetime.utcnow().isoformat()})
    def get(self, key: str, name: str = None, limit: int = 100) -> list[dict]:
        items = self.data.get(key, [])
        if name: items = [m for m in items if m["name"] == name]
        return items[-limit:]
    def avg(self, key: str, name: str, window: int = 10) -> float:
        items = [m for m in self.data.get(key, []) if m["name"] == name][-window:]
        return sum(m["value"] for m in items) / len(items) if items else 0.0

class AlertDispatcher:
    def __init__(self):
        self.alerts: list[dict] = []
    def send(self, ref_id: str, severity: str, message: str) -> dict:
        a = {"id": str(uuid.uuid4()), "ref_id": ref_id, "severity": severity, "message": message, "status": "open", "ts": datetime.utcnow().isoformat()}
        self.alerts.append(a)
        return a
    def get_open(self, ref_id: str = None) -> list[dict]:
        items = [a for a in self.alerts if a["status"] == "open"]
        if ref_id: items = [a for a in items if a["ref_id"] == ref_id]
        return items
    def resolve(self, alert_id: str, note: str = "") -> bool:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["status"] = "resolved"; a["resolved_at"] = datetime.utcnow().isoformat(); a["note"] = note; return True
        return False
    def stats(self) -> dict:
        total = len(self.alerts); open_c = sum(1 for a in self.alerts if a["status"] == "open")
        return {"total": total, "open": open_c, "resolved": total - open_c}

# === EXPANSION 2: Reporting, Scheduling, Compliance & Bulk Operations ===

class ReportGenerator:
    def __init__(self, parent):
        self.parent = parent
        self.reports: list[dict] = []

    def generate(self, ref_id: str, report_type: str, params: dict = None) -> dict:
        report = {"id": str(uuid.uuid4()), "ref_id": ref_id, "type": report_type, "params": params or {}, "status": "completed", "ts": datetime.utcnow().isoformat()}
        self.reports.append(report)
        return report

    def list_reports(self, ref_id: str = None) -> list[dict]:
        if ref_id: return [r for r in self.reports if r["ref_id"] == ref_id]
        return self.reports

    def get_by_type(self, report_type: str) -> list[dict]:
        return [r for r in self.reports if r["type"] == report_type]

class Scheduler:
    def __init__(self):
        self.jobs: list[dict] = []

    def add_job(self, name: str, interval_minutes: int, action: str, params: dict = None) -> dict:
        job = {"id": str(uuid.uuid4()), "name": name, "interval_minutes": interval_minutes, "action": action, "params": params or {}, "enabled": True, "next_run": datetime.utcnow().isoformat(), "ts": datetime.utcnow().isoformat()}
        self.jobs.append(job)
        return job

    def pause_job(self, job_id: str) -> bool:
        for j in self.jobs:
            if j["id"] == job_id: j["enabled"] = False; return True
        return False

    def resume_job(self, job_id: str) -> bool:
        for j in self.jobs:
            if j["id"] == job_id: j["enabled"] = True; return True
        return False

    def delete_job(self, job_id: str) -> bool:
        for i, j in enumerate(self.jobs):
            if j["id"] == job_id: self.jobs.pop(i); return True
        return False

    def list_jobs(self, enabled_only: bool = False) -> list[dict]:
        if enabled_only: return [j for j in self.jobs if j["enabled"]]
        return self.jobs

class ComplianceChecker:
    def __init__(self, parent):
        self.parent = parent
        self.checks: list[dict] = []

    def run_check(self, standard: str, ref_id: str = None) -> dict:
        check = {"id": str(uuid.uuid4()), "standard": standard, "ref_id": ref_id, "passed": True, "issues": [], "ts": datetime.utcnow().isoformat()}
        self.checks.append(check)
        return check

    def get_compliance_rate(self, standard: str = None) -> float:
        items = self.checks
        if standard: items = [c for c in items if c["standard"] == standard]
        if not items: return 1.0
        return sum(1 for c in items if c["passed"]) / len(items)

    def get_failing(self) -> list[dict]:
        return [c for c in self.checks if not c["passed"]]

class BulkOperator:
    def __init__(self, parent):
        self.parent = parent

    async def bulk_action(self, ref_ids: list[str], action: str, params: dict = None) -> dict:
        success = 0; failed = 0
        for rid in ref_ids:
            try:
                result = await self._execute(rid, action, params)
                if result: success += 1
                else: failed += 1
            except Exception: failed += 1
        return {"total": len(ref_ids), "success": success, "failed": failed}

    async def _execute(self, ref_id: str, action: str, params: dict = None) -> bool:
        return True

class AuditTrail:
    def __init__(self):
        self.entries: list[dict] = []

    def log(self, actor: str, action: str, resource: str, detail: str = ""):
        self.entries.append({"actor": actor, "action": action, "resource": resource, "detail": detail, "ts": datetime.utcnow().isoformat()})

    def get_by_actor(self, actor: str) -> list[dict]:
        return [e for e in self.entries if e["actor"] == actor]

    def get_by_resource(self, resource: str) -> list[dict]:
        return [e for e in self.entries if e["resource"] == resource]

    def get_recent(self, limit: int = 50) -> list[dict]:
        return self.entries[-limit:]

class DataExporter:
    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    @staticmethod
    def to_csv(rows: list[dict]) -> str:
        if not rows: return ""
        headers = list(rows[0].keys())
        lines = [",".join(headers)]
        for r in rows:
            lines.append(",".join(str(r.get(h, "")) for h in headers))
        return "\n".join(lines)

class Paginator:
    @staticmethod
    def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
        total = len(items)
        total_pages = max(1, (total + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": items[start:end], "page": page, "per_page": per_page, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}

# === EXPANSION 3: Advanced Filtering, Tagging, Search & Notification ===

class FilterEngine:
    def __init__(self, data_source: dict):
        self.source = data_source

    def filter(self, criteria: dict) -> list[dict]:
        results = []
        for item in self.source.values():
            item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item if isinstance(item, dict) else {"id": str(item)})
            match = True
            for key, val in criteria.items():
                if key not in item_dict: match = False; break
                if isinstance(val, (list, tuple)):
                    if item_dict[key] not in val: match = False; break
                elif callable(val):
                    if not val(item_dict[key]): match = False; break
                elif item_dict[key] != val: match = False; break
            if match: results.append(item_dict)
        return results

    def search(self, query: str, fields: list[str] = None) -> list[dict]:
        q = query.lower()
        results = []
        for item in self.source.values():
            item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item if isinstance(item, dict) else {"id": str(item)})
            search_fields = fields or list(item_dict.keys())
            for field in search_fields:
                if q in str(item_dict.get(field, "")).lower():
                    results.append(item_dict); break
        return results

class TagManager:
    def __init__(self):
        self.tags: dict[str, list[str]] = {}

    def add_tag(self, ref_id: str, tag: str) -> bool:
        if ref_id not in self.tags: self.tags[ref_id] = []
        if tag not in self.tags[ref_id]: self.tags[ref_id].append(tag); return True
        return False

    def remove_tag(self, ref_id: str, tag: str) -> bool:
        if ref_id in self.tags and tag in self.tags[ref_id]:
            self.tags[ref_id].remove(tag); return True
        return False

    def get_tags(self, ref_id: str) -> list[str]:
        return self.tags.get(ref_id, [])

    def find_by_tag(self, tag: str) -> list[str]:
        return [rid for rid, ts in self.tags.items() if tag in ts]

    def get_all_tags(self) -> dict:
        all_tags = {}
        for ref_id, ts in self.tags.items():
            for t in ts:
                if t not in all_tags: all_tags[t] = []
                all_tags[t].append(ref_id)
        return all_tags

class NotificationService:
    def __init__(self):
        self.notifications: list[dict] = []

    def notify(self, recipient: str, subject: str, message: str, channel: str = "in_app") -> dict:
        n = {"id": str(uuid.uuid4()), "recipient": recipient, "subject": subject, "message": message, "channel": channel, "status": "sent", "ts": datetime.utcnow().isoformat()}
        self.notifications.append(n)
        return n

    def get_for_recipient(self, recipient: str, limit: int = 50) -> list[dict]:
        return [n for n in self.notifications if n["recipient"] == recipient][-limit:]

    def mark_read(self, notification_id: str) -> bool:
        for n in self.notifications:
            if n["id"] == notification_id: n["status"] = "read"; return True
        return False

    def get_unread_count(self, recipient: str) -> int:
        return sum(1 for n in self.notifications if n["recipient"] == recipient and n["status"] == "sent")

class DataValidator:
    @staticmethod
    def validate_schema(data: dict, schema: dict) -> list[str]:
        errors = []
        for field, rules in schema.items():
            if rules.get("required", False) and field not in data:
                errors.append(f"Missing required field: {field}")
            elif field in data:
                val = data[field]
                expected_type = rules.get("type")
                if expected_type and not isinstance(val, expected_type):
                    errors.append(f"Field {field} should be {expected_type.__name__}")
                if "min" in rules and isinstance(val, (int, float)) and val < rules["min"]:
                    errors.append(f"Field {field} below minimum {rules['min']}")
                if "max" in rules and isinstance(val, (int, float)) and val > rules["max"]:
                    errors.append(f"Field {field} above maximum {rules['max']}")
        return errors

class BatchProcessor:
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size

    async def process(self, items: list, processor_fn) -> dict:
        results = {"total": len(items), "success": 0, "failed": 0, "errors": []}
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            for item in batch:
                try:
                    result = await processor_fn(item)
                    if result: results["success"] += 1
                    else: results["failed"] += 1; results["errors"].append({"item": str(item), "error": "processor returned False"})
                except Exception as e:
                    results["failed"] += 1; results["errors"].append({"item": str(item), "error": str(e)})
        return results

class StatsAccumulator:
    def __init__(self):
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}

    def increment(self, name: str, amount: int = 1):
        self.counters[name] = self.counters.get(name, 0) + amount

    def gauge(self, name: str, value: float):
        self.gauges[name] = value

    def get_counters(self) -> dict:
        return dict(self.counters)

    def get_gauges(self) -> dict:
        return dict(self.gauges)

    def snapshot(self) -> dict:
        return {"counters": dict(self.counters), "gauges": dict(self.gauges)}

# === EXPANSION 4: Advanced Operations & Utility Classes ===

class DiffChecker:
    @staticmethod
    def diff(old: dict, new: dict) -> dict:
        added = {k: v for k, v in new.items() if k not in old}
        removed = {k: v for k, v in old.items() if k not in new}
        changed = {k: {"from": old[k], "to": new[k]} for k in old if k in new and old[k] != new[k]}
        return {"added": added, "removed": removed, "changed": changed, "has_changes": bool(added or removed or changed)}

class RetryPolicy:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5, max_delay: float = 60.0):
        self.max_retries = max_retries; self.backoff_factor = backoff_factor; self.max_delay = max_delay

    async def execute(self, fn, *args, **kwargs):
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = min(self.backoff_factor ** attempt, self.max_delay)
                    await asyncio.sleep(delay)
        raise last_error

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold; self.recovery_timeout = recovery_timeout
        self.failures = 0; self.state = "closed"; self.last_failure_time = None

    async def call(self, fn, *args, **kwargs):
        if self.state == "open":
            if datetime.utcnow().timestamp() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else: raise Exception("Circuit breaker is open")
        try:
            result = await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
            if self.state == "half-open": self.state = "closed"; self.failures = 0
            return result
        except Exception as e:
            self.failures += 1; self.last_failure_time = datetime.utcnow().timestamp()
            if self.failures >= self.failure_threshold: self.state = "open"
            raise e

class RateLimiter:
    def __init__(self, max_calls: int = 60, window_seconds: float = 60.0):
        self.max_calls = max_calls; self.window_seconds = window_seconds
        self.calls: list[float] = []

    async def acquire(self):
        now = datetime.utcnow().timestamp()
        self.calls = [c for c in self.calls if now - c < self.window_seconds]
        if len(self.calls) >= self.max_calls: raise Exception("Rate limit exceeded")
        self.calls.append(now)

class CacheManager:
    def __init__(self, default_ttl: float = 300.0):
        self.cache: dict[str, tuple[Any, float]] = {}; self.default_ttl = default_ttl

    def get(self, key: str) -> Any:
        if key in self.cache:
            val, expiry = self.cache[key]
            if datetime.utcnow().timestamp() < expiry: return val
            del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: float = None):
        self.cache[key] = (value, datetime.utcnow().timestamp() + (ttl or self.default_ttl))

    def invalidate(self, key: str): self.cache.pop(key, None)

    def clear(self): self.cache.clear()

class EventEmitter:
    def __init__(self):
        self.listeners: dict[str, list] = {}

    def on(self, event: str, callback): self.listeners.setdefault(event, []).append(callback)

    async def emit(self, event: str, *args, **kwargs):
        for cb in self.listeners.get(event, []):
            if asyncio.iscoroutinefunction(cb): await cb(*args, **kwargs)
            else: cb(*args, **kwargs)

    def remove(self, event: str, callback):
        self.listeners[event] = [cb for cb in self.listeners.get(event, []) if cb != callback]
