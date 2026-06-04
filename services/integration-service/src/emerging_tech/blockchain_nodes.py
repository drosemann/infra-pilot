"""Blockchain Node Manager — one-click ethereum/solana/polygon/avalanche node deployment."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BlockchainNetwork(Enum):
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"


class NodeRole(Enum):
    FULL = "full"
    ARCHIVE = "archive"
    VALIDATOR = "validator"
    LIGHT = "light"
    RPC = "rpc"


class NodeStatus(Enum):
    PROVISIONING = "provisioning"
    SYNCING = "syncing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    SYNCED = "synced"


class StakingStatus(Enum):
    NONE = "none"
    ACTIVE = "active"
    PENDING = "pending"
    UNBONDING = "unbonding"
    SLASHED = "slashed"


class BlockchainNode:
    def __init__(self, node_id: str, name: str, network: BlockchainNetwork, role: NodeRole):
        self.node_id = node_id
        self.name = name
        self.network = network
        self.role = role
        self.status = NodeStatus.PROVISIONING
        self.endpoint = ""
        self.p2p_port = 30303
        self.rpc_port = 8545
        self.ws_port = 8546
        self.network_id = 1
        self.chain_id = 1
        self.sync_progress = 0.0
        self.current_block = 0
        self.target_block = 0
        self.peer_count = 0
        self.disk_usage_gb = 0.0
        self.memory_usage_mb = 0.0
        self.cpu_usage_pct = 0.0
        self.staking_status = StakingStatus.NONE
        self.staked_amount = 0.0
        self.validator_address = ""
        self.validator_commission = 0.0
        self.rewards_earned = 0.0
        self.uptime_pct = 0.0
        self.container_id = ""
        self.node_key = ""
        self.enode_url = ""
        self.tags: list[str] = []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "network": self.network.value,
            "role": self.role.value,
            "status": self.status.value,
            "endpoint": self.endpoint,
            "p2p_port": self.p2p_port,
            "rpc_port": self.rpc_port,
            "ws_port": self.ws_port,
            "network_id": self.network_id,
            "chain_id": self.chain_id,
            "sync_progress": self.sync_progress,
            "current_block": self.current_block,
            "target_block": self.target_block,
            "peer_count": self.peer_count,
            "disk_usage_gb": self.disk_usage_gb,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_pct": self.cpu_usage_pct,
            "staking_status": self.staking_status.value,
            "staked_amount": self.staked_amount,
            "validator_address": self.validator_address,
            "validator_commission": self.validator_commission,
            "rewards_earned": self.rewards_earned,
            "uptime_pct": self.uptime_pct,
            "container_id": self.container_id,
            "enode_url": self.enode_url,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlockchainNode":
        node = cls(
            data["node_id"], data["name"],
            BlockchainNetwork(data["network"]),
            NodeRole(data["role"]),
        )
        node.status = NodeStatus(data.get("status", "provisioning"))
        node.endpoint = data.get("endpoint", "")
        node.p2p_port = data.get("p2p_port", 30303)
        node.rpc_port = data.get("rpc_port", 8545)
        node.ws_port = data.get("ws_port", 8546)
        node.network_id = data.get("network_id", 1)
        node.chain_id = data.get("chain_id", 1)
        node.sync_progress = data.get("sync_progress", 0.0)
        node.current_block = data.get("current_block", 0)
        node.target_block = data.get("target_block", 0)
        node.peer_count = data.get("peer_count", 0)
        node.disk_usage_gb = data.get("disk_usage_gb", 0.0)
        node.memory_usage_mb = data.get("memory_usage_mb", 0.0)
        node.cpu_usage_pct = data.get("cpu_usage_pct", 0.0)
        node.staking_status = StakingStatus(data.get("staking_status", "none"))
        node.staked_amount = data.get("staked_amount", 0.0)
        node.validator_address = data.get("validator_address", "")
        node.validator_commission = data.get("validator_commission", 0.0)
        node.rewards_earned = data.get("rewards_earned", 0.0)
        node.uptime_pct = data.get("uptime_pct", 0.0)
        node.container_id = data.get("container_id", "")
        node.enode_url = data.get("enode_url", "")
        node.tags = data.get("tags", [])
        return node


class DeploymentConfig:
    def __init__(self, network: BlockchainNetwork, role: NodeRole):
        self.network = network
        self.role = role
        self.volume_size_gb = 500
        self.cpu_cores = 4
        self.memory_mb = 8192
        self.region = "auto"
        self.snapshot_url = ""
        self.extra_flags: list[str] = []
        self.monitoring_enabled = True
        self.auto_update = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "network": self.network.value,
            "role": self.role.value,
            "volume_size_gb": self.volume_size_gb,
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "region": self.region,
            "snapshot_url": self.snapshot_url,
            "extra_flags": self.extra_flags,
            "monitoring_enabled": self.monitoring_enabled,
            "auto_update": self.auto_update,
        }


class ValidatorInfo:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.public_key = ""
        self.withdrawal_address = ""
        self.fee_recipient = ""
        self.balance = 0.0
        self.effective_balance = 0.0
        self.attestation_hit_rate = 0.0
        self.proposal_count = 0
        self.missed_proposals = 0
        self.last_proposed_slot = 0
        self.penalty_count = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "public_key": self.public_key,
            "withdrawal_address": self.withdrawal_address,
            "fee_recipient": self.fee_recipient,
            "balance": self.balance,
            "effective_balance": self.effective_balance,
            "attestation_hit_rate": self.attestation_hit_rate,
            "proposal_count": self.proposal_count,
            "missed_proposals": self.missed_proposals,
            "last_proposed_slot": self.last_proposed_slot,
            "penalty_count": self.penalty_count,
        }


class BlockchainNodeManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.nodes: dict[str, BlockchainNode] = {}
        self.validators: dict[str, ValidatorInfo] = {}
        self.storage_path = config.get("storage_path", "data/blockchain_nodes.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for node_data in data.get("nodes", []):
                    node = BlockchainNode.from_dict(node_data)
                    self.nodes[node.node_id] = node
                for val_data in data.get("validators", []):
                    val = ValidatorInfo(val_data["node_id"])
                    val.public_key = val_data.get("public_key", "")
                    val.balance = val_data.get("balance", 0.0)
                    self.validators[val.node_id] = val
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized BlockchainNodeManager with %d nodes", len(self.nodes))

    async def close(self):
        self._save()

    def _save(self):
        data = {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "validators": [v.to_dict() for v in self.validators.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    async def deploy_node(self, name: str, network: BlockchainNetwork, role: NodeRole, config: Optional[DeploymentConfig] = None) -> BlockchainNode:
        node_id = str(uuid.uuid4())
        node = BlockchainNode(node_id, name, network, role)
        if config:
            node.network_id = self._network_id(network)
            node.chain_id = self._chain_id(network)
        self.nodes[node_id] = node
        self._save()
        asyncio.create_task(self._simulate_deployment(node_id))
        logger.info("Deploying %s %s node: %s", network.value, role.value, name)
        return node

    def _network_id(self, network: BlockchainNetwork) -> int:
        return {BlockchainNetwork.ETHEREUM: 1, BlockchainNetwork.SOLANA: 101, BlockchainNetwork.POLYGON: 137, BlockchainNetwork.AVALANCHE: 43114}.get(network, 1)

    def _chain_id(self, network: BlockchainNetwork) -> int:
        return self._network_id(network)

    async def _simulate_deployment(self, node_id: str):
        node = self.nodes.get(node_id)
        if not node:
            return
        await asyncio.sleep(2)
        node.status = NodeStatus.SYNCING
        node.sync_progress = 5.0
        for i in range(20):
            await asyncio.sleep(1)
            if node_id not in self.nodes:
                return
            node.sync_progress = min(100.0, node.sync_progress + 4.75)
            node.current_block = int(node.target_block * node.sync_progress / 100)
            node.peer_count = 8 + (i % 5)
        node.status = NodeStatus.SYNCED

    def get_node(self, node_id: str) -> Optional[BlockchainNode]:
        return self.nodes.get(node_id)

    def list_nodes(self, network: Optional[BlockchainNetwork] = None) -> list[BlockchainNode]:
        if network:
            return [n for n in self.nodes.values() if n.network == network]
        return list(self.nodes.values())

    async def delete_node(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.STOPPED
            del self.nodes[node_id]
            if node_id in self.validators:
                del self.validators[node_id]
            self._save()
            return True
        return False

    async def start_node(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node and node.status in (NodeStatus.STOPPED, NodeStatus.ERROR):
            node.status = NodeStatus.SYNCING
            self._save()
            return True
        return False

    async def stop_node(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node and node.status == NodeStatus.RUNNING:
            node.status = NodeStatus.STOPPED
            self._save()
            return True
        return False

    async def get_node_metrics(self, node_id: str) -> dict[str, Any]:
        node = self.nodes.get(node_id)
        if not node:
            return {}
        return {
            "node_id": node.node_id,
            "sync_progress": node.sync_progress,
            "current_block": node.current_block,
            "peer_count": node.peer_count,
            "disk_usage_gb": node.disk_usage_gb,
            "memory_usage_mb": node.memory_usage_mb,
            "cpu_usage_pct": node.cpu_usage_pct,
            "uptime_pct": node.uptime_pct,
        }

    async def stake(self, node_id: str, amount: float, withdrawal_address: str) -> bool:
        node = self.nodes.get(node_id)
        if not node or node.role != NodeRole.VALIDATOR:
            return False
        node.staking_status = StakingStatus.PENDING
        node.staked_amount = amount
        val = ValidatorInfo(node_id)
        val.withdrawal_address = withdrawal_address
        val.balance = amount
        val.effective_balance = amount
        self.validators[node_id] = val
        self._save()
        asyncio.create_task(self._simulate_staking(node_id))
        return True

    async def _simulate_staking(self, node_id: str):
        await asyncio.sleep(3)
        node = self.nodes.get(node_id)
        if not node:
            return
        node.staking_status = StakingStatus.ACTIVE
        val = self.validators.get(node_id)
        if val:
            val.attestation_hit_rate = 0.98
            val.proposal_count = 5
        self._save()

    async def unstake(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node:
            node.staking_status = StakingStatus.UNBONDING
            self._save()
            return True
        return False

    async def claim_rewards(self, node_id: str) -> float:
        node = self.nodes.get(node_id)
        if node and node.staking_status == StakingStatus.ACTIVE:
            rewards = node.rewards_earned
            node.rewards_earned = 0.0
            self._save()
            return rewards
        return 0.0

    def get_network_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for network in BlockchainNetwork:
            nodes = [n for n in self.nodes.values() if n.network == network]
            summary[network.value] = {
                "total": len(nodes),
                "running": sum(1 for n in nodes if n.status == NodeStatus.RUNNING),
                "syncing": sum(1 for n in nodes if n.status == NodeStatus.SYNCING),
                "validators": sum(1 for n in nodes if n.role == NodeRole.VALIDATOR),
                "total_staked": sum(n.staked_amount for n in nodes),
            }
        return summary

    def get_network_defaults(self, network: str) -> dict[str, Any]:
        defaults = {
            "ethereum": {"p2p_port": 30303, "rpc_port": 8545, "ws_port": 8546, "volume_gb": 2000},
            "solana": {"p2p_port": 8000, "rpc_port": 8899, "ws_port": 8900, "volume_gb": 500},
            "polygon": {"p2p_port": 30303, "rpc_port": 8545, "ws_port": 8546, "volume_gb": 1000},
            "avalanche": {"p2p_port": 9651, "rpc_port": 9650, "ws_port": 9650, "volume_gb": 500},
        }
        return defaults.get(network, defaults["ethereum"])

    # === Export ===
    def export_nodes_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "network", "role", "status", "version", "staked", "peers", "uptime_pct", "created_at"])
        for n in self.nodes.values():
            writer.writerow([n.id, n.name, n.network.value, n.role.value, n.status.value, n.version, n.staked_amount, n.peer_count, n.uptime_percentage, n.created_at.isoformat()])
        return output.getvalue()

    def export_nodes_json(self) -> str:
        return json.dumps([n.to_dict() for n in self.nodes.values()], indent=2, default=str)

    # === Import ===
    def import_nodes_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            node = BlockchainNode(
                id=item.get("id", str(uuid.uuid4())),
                name=item.get("name", "Imported Node"),
                network=BlockchainNetwork(item.get("network", "ethereum")),
                role=NodeRole(item.get("role", "full_node")),
                status=NodeStatus(item.get("status", "stopped")),
                version=item.get("version", "latest"),
                staked_amount=item.get("staked_amount", 0.0),
                peer_count=item.get("peer_count", 0),
                uptime_percentage=item.get("uptime_percentage", 0.0),
            )
            self.nodes[node.id] = node
            count += 1
        return count

    # === Notification ===
    async def notify_node_status(self, node_id: str) -> Dict[str, Any]:
        node = self.nodes.get(node_id)
        if not node:
            return {"error": "Node not found"}
        return {
            "node_id": node.id,
            "name": node.name,
            "network": node.network.value,
            "status": node.status.value,
            "message": f"Blockchain node {node.name} ({node.network.value}) status: {node.status.value}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_synced_nodes(self) -> List[Dict]:
        results = []
        for n in self.nodes.values():
            if n.status == NodeStatus.SYNCING:
                results.append(await self.notify_node_status(n.id))
        return results

    # === State Machine ===
    def transition_node_status(self, node_id: str, target_status: str) -> Optional[BlockchainNode]:
        node = self.nodes.get(node_id)
        if not node:
            return None
        valid = {
            NodeStatus.STOPPED: [NodeStatus.STARTING, NodeStatus.STOPPED],
            NodeStatus.STARTING: [NodeStatus.RUNNING, NodeStatus.STOPPED],
            NodeStatus.RUNNING: [NodeStatus.STOPPING, NodeStatus.SYNCING],
            NodeStatus.SYNCING: [NodeStatus.RUNNING, NodeStatus.STOPPED],
            NodeStatus.STOPPING: [NodeStatus.STOPPED],
            NodeStatus.ERROR: [NodeStatus.STOPPED, NodeStatus.STARTING],
        }
        new_status = NodeStatus(target_status)
        if new_status in valid.get(node.status, []):
            node.status = new_status
            return node
        return None

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("network"):
            errors.append("Network is required")
        if config.get("network") and config["network"] not in [n.value for n in BlockchainNetwork]:
            errors.append(f"Unknown network: {config.get('network')}")
        if config.get("volume_gb", 100) > 5000:
            warnings.append("Volume size exceeds 5TB, may impact cost")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_node_analytics(self) -> Dict:
        total_uptime = sum(n.uptime_percentage for n in self.nodes.values())
        node_count = len(self.nodes)
        return {
            "avg_uptime": round(total_uptime / node_count, 1) if node_count else 0,
            "total_staked": sum(n.staked_amount for n in self.nodes.values()),
            "total_peers": sum(n.peer_count for n in self.nodes.values()),
            "by_network": self.get_network_summary(),
            "by_role": {r.value: sum(1 for n in self.nodes.values() if n.role == r) for r in NodeRole},
        }

    def get_staking_apy(self, network: str) -> float:
        rates = {"ethereum": 3.5, "solana": 6.2, "polygon": 4.8, "avalanche": 7.1, "near": 5.0}
        return rates.get(network, 0.0)

    def get_health_snapshot(self) -> Dict:
        running = sum(1 for n in self.nodes.values() if n.status == NodeStatus.RUNNING)
        errored = sum(1 for n in self.nodes.values() if n.status == NodeStatus.ERROR)
        return {
            "total": len(self.nodes),
            "operational": running,
            "degraded": errored,
            "health_pct": round(running / len(self.nodes) * 100, 1) if self.nodes else 0,
        }

    # === Bulk Operations ===
    async def bulk_start_nodes(self, node_ids: List[str]) -> int:
        count = 0
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node and node.status == NodeStatus.STOPPED:
                node.status = NodeStatus.STARTING
                node.status = NodeStatus.RUNNING
                count += 1
        return count

    async def bulk_stop_nodes(self, node_ids: List[str]) -> int:
        count = 0
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node and node.status == NodeStatus.RUNNING:
                node.status = NodeStatus.STOPPING
                node.status = NodeStatus.STOPPED
                count += 1
        return count

    async def bulk_update_version(self, node_ids: List[str], version: str) -> int:
        count = 0
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node:
                node.version = version
                count += 1
        return count

    # === Tag Management ===
    def add_node_tags(self, node_ids: List[str], tags: List[str]) -> int:
        count = 0
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node:
                for t in tags:
                    if t not in node.tags:
                        node.tags.append(t)
                count += 1
        return count

    def remove_node_tags(self, node_ids: List[str], tags: List[str]) -> int:
        count = 0
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node:
                node.tags = [t for t in node.tags if t not in tags]
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "blockchain_nodes",
            "initialized": self._initialized,
            "nodes": len(self.nodes),
            "running": sum(1 for n in self.nodes.values() if n.status == NodeStatus.RUNNING),
            "syncing": sum(1 for n in self.nodes.values() if n.status == NodeStatus.SYNCING),
            "errored": sum(1 for n in self.nodes.values() if n.status == NodeStatus.ERROR),
            "networks": list(set(n.network.value for n in self.nodes.values())),
            "status": "healthy" if self._initialized else "not_initialized",
        }

    # === Alert Management ===
    def create_alert_rule(self, name: str, network: str, metric: str, threshold: float, severity: str = "warning") -> dict[str, Any]:
        rule_id = str(uuid.uuid4())
        rule = {"rule_id": rule_id, "name": name, "network": network, "metric": metric,
                "threshold": threshold, "severity": severity, "enabled": True, "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_alert_rules"):
            self._alert_rules: dict[str, dict[str, Any]] = {}
        self._alert_rules[rule_id] = rule
        return rule

    def get_alert_rules(self, network: str = "") -> list[dict[str, Any]]:
        rules = list(getattr(self, "_alert_rules", {}).values())
        if network:
            return [r for r in rules if r["network"] == network]
        return rules

    def toggle_alert_rule(self, rule_id: str, enabled: bool) -> bool:
        rules = getattr(self, "_alert_rules", {})
        if rule_id in rules:
            rules[rule_id]["enabled"] = enabled
            return True
        return False

    def delete_alert_rule(self, rule_id: str) -> bool:
        rules = getattr(self, "_alert_rules", {})
        if rule_id in rules:
            del rules[rule_id]
            return True
        return False

    def evaluate_alert_rules(self) -> list[dict[str, Any]]:
        triggered = []
        for rule in getattr(self, "_alert_rules", {}).values():
            if not rule["enabled"]:
                continue
            nodes = [n for n in self.nodes.values() if n.network.value == rule["network"]]
            if rule["metric"] == "uptime":
                value = round(sum(n.uptime_percentage for n in nodes) / max(len(nodes), 1), 1)
            elif rule["metric"] == "peer_count":
                value = sum(n.peer_count for n in nodes) / max(len(nodes), 1)
            elif rule["metric"] == "node_count":
                value = len(nodes)
            else:
                continue
            if value < rule["threshold"]:
                triggered.append({"rule_id": rule["rule_id"], "name": rule["name"],
                                  "metric": rule["metric"], "current_value": value,
                                  "threshold": rule["threshold"], "severity": rule["severity"],
                                  "triggered_at": datetime.utcnow().isoformat()})
        return triggered

    # === Backup & Restore ===
    def backup_node_config(self, node_id: str) -> dict[str, Any] | None:
        node = self.nodes.get(node_id)
        if not node:
            return None
        backup_id = str(uuid.uuid4())
        backup = {"backup_id": backup_id, "node_id": node_id, "config": node.client_config,
                  "version": node.version, "tags": list(node.tags), "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_backups"):
            self._backups: dict[str, list[dict[str, Any]]] = {}
        if node_id not in self._backups:
            self._backups[node_id] = []
        self._backups[node_id].append(backup)
        return backup

    def restore_node_config(self, backup_id: str) -> dict[str, Any] | None:
        backups = getattr(self, "_backups", {})
        for nid, bk_list in backups.items():
            for bk in bk_list:
                if bk["backup_id"] == backup_id:
                    node = self.nodes.get(nid)
                    if node:
                        node.client_config = bk["config"]
                        node.version = bk["version"]
                        return {"node_id": nid, "restored_from": backup_id, "status": "restored"}
        return None

    def list_backups(self, node_id: str = "") -> list[dict[str, Any]]:
        backups = getattr(self, "_backups", {})
        if node_id:
            return backups.get(node_id, [])
        result = []
        for bk_list in backups.values():
            result.extend(bk_list)
        return result

    # === Reporting ===
    def generate_report(self, network: str = "", report_type: str = "summary") -> dict[str, Any]:
        nodes = [n for n in self.nodes.values() if not network or n.network.value == network]
        if report_type == "summary":
            return {"network": network or "all", "node_count": len(nodes),
                    "running": sum(1 for n in nodes if n.status == NodeStatus.RUNNING),
                    "avg_uptime": round(sum(n.uptime_percentage for n in nodes) / max(len(nodes), 1), 1),
                    "total_staked": sum(n.staked_amount for n in nodes)}
        elif report_type == "cost":
            return {"network": network or "all", "estimated_monthly_cost": sum(n.staked_amount for n in nodes) * 0.01,
                    "nodes": len(nodes), "avg_staked": round(sum(n.staked_amount for n in nodes) / max(len(nodes), 1), 2)}
        return {}

    def export_node_data(self, network: str = "", format: str = "json") -> Any:
        nodes = [n for n in self.nodes.values() if not network or n.network.value == network]
        if format == "csv":
            lines = ["id,name,network,role,status,version,uptime,staked,peers"]
            for n in nodes:
                lines.append(f"{n.node_id},{n.name},{n.network.value},{n.role.value},{n.status.value},{n.version},{n.uptime_percentage},{n.staked_amount},{n.peer_count}")
            return "\n".join(lines)
        return {"network": network or "all", "nodes": [n.to_dict() for n in nodes]}

    # === Scheduling ===
    def schedule_backup(self, node_ids: list[str], interval_hours: int = 24) -> dict[str, Any]:
        schedule_id = str(uuid.uuid4())
        schedule = {"schedule_id": schedule_id, "node_ids": node_ids, "interval_hours": interval_hours,
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

    # === Dashboard ===
    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "running_count": sum(1 for n in self.nodes.values() if n.status == NodeStatus.RUNNING),
            "total_staked": sum(n.staked_amount for n in self.nodes.values()),
            "networks": self.get_network_summary(),
            "health_snapshot": self.get_health_snapshot(),
            "recent_events": [],  # placeholder for event log
            "alert_rules": len(getattr(self, "_alert_rules", {})),
            "avg_uptime": round(sum(n.uptime_percentage for n in self.nodes.values()) / max(len(self.nodes), 1), 1),
        }

    # === Comparison ===
    def compare_nodes(self, node_id_a: str, node_id_b: str) -> dict[str, Any]:
        a = self.nodes.get(node_id_a)
        b = self.nodes.get(node_id_b)
        if not a or not b:
            return {"error": "One or both nodes not found"}
        return {
            "name": {"a": a.name, "b": b.name},
            "network": {"a": a.network.value, "b": b.network.value},
            "role": {"a": a.role.value, "b": b.role.value},
            "status": {"a": a.status.value, "b": b.status.value},
            "version": {"a": a.version, "b": b.version},
            "uptime": {"a": a.uptime_percentage, "b": b.uptime_percentage},
            "staked": {"a": a.staked_amount, "b": b.staked_amount},
            "peers": {"a": a.peer_count, "b": b.peer_count},
        }

    # === Node Discovery ===
    def discover_peers(self, node_id: str) -> list[dict[str, Any]]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        discovered = []
        for other in self.nodes.values():
            if other.node_id != node_id and other.network == node.network and other.status == NodeStatus.RUNNING:
                discovered.append({"node_id": other.node_id, "name": other.name,
                                   "address": f"{other.host}:{other.port}", "peers": other.peer_count})
        return discovered

    def suggest_node_upgrades(self, node_id: str) -> list[dict[str, Any]]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        suggestions = []
        network_nodes = [n for n in self.nodes.values() if n.network == node.network and n.node_id != node_id]
        if network_nodes:
            avg_version = sum(float(n.version) for n in network_nodes if n.version.replace('.', '', 1).isdigit()) / len(network_nodes)
            if avg_version > float(node.version):
                suggestions.append({"type": "version_upgrade", "current": node.version, "recommended": f"{avg_version:.1f}"})
        if node.uptime_percentage < 90:
            suggestions.append({"type": "uptime_improvement", "current": node.uptime_percentage, "target": 99.5})
        return suggestions


# === EXPANSION: Node Lifecycle, Health, Config & Alerts ===

class NodeLifecycleManager:
    def __init__(self, manager):
        self.manager = manager
        self.operations: list[dict] = []

    def record_operation(self, op_type: str, node_id: str, status: str, detail: str = ""):
        self.operations.append({"type": op_type, "node_id": node_id, "status": status, "detail": detail, "timestamp": datetime.utcnow().isoformat()})

    def get_node_ops(self, node_id: str, limit: int = 50) -> list[dict]:
        return [o for o in self.operations if o["node_id"] == node_id][-limit:]

    def get_success_rate(self, node_id: str = None) -> float:
        ops = self.operations
        if node_id:
            ops = [o for o in ops if o["node_id"] == node_id]
        if not ops:
            return 1.0
        return sum(1 for o in ops if o["status"] == "success") / len(ops)

    def get_failure_trend(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [o for o in self.operations if datetime.fromisoformat(o["timestamp"]) > cutoff]
        by_hour = defaultdict(int)
        for o in recent:
            if o["status"] == "failed":
                by_hour[o["timestamp"][:13]] += 1
        return [{"hour": h, "count": c} for h, c in sorted(by_hour.items())]


class NodeConfigValidator:
    @staticmethod
    def validate_deployment(config: dict) -> list[str]:
        errors = []
        if not config.get("chain"):
            errors.append("Chain is required")
        if config.get("network") not in ("mainnet", "testnet", "devnet"):
            errors.append("Invalid network")
        if config.get("node_type") not in ("full", "archive", "validator", "light", "rpc"):
            errors.append("Invalid node type")
        if config.get("rpc_port") and not (1024 < int(config["rpc_port"]) < 65535):
            errors.append("RPC port out of range")
        return errors

    @staticmethod
    def suggest_defaults(chain: str) -> dict:
        defaults = {
            "ethereum": {"network": "mainnet", "node_type": "full", "rpc_port": 8545, "p2p_port": 30303},
            "solana": {"network": "mainnet", "node_type": "rpc", "rpc_port": 8899, "p2p_port": 8001},
            "polygon": {"network": "mainnet", "node_type": "full", "rpc_port": 8545, "p2p_port": 30303},
            "avalanche": {"network": "mainnet", "node_type": "full", "rpc_port": 9650, "p2p_port": 9651},
        }
        return defaults.get(chain, {"network": "testnet", "node_type": "full", "rpc_port": 8545, "p2p_port": 30303})


class NodeMetricsCollector:
    def __init__(self):
        self.metrics: dict[str, list] = {}

    def record_metric(self, node_id: str, name: str, value: float):
        if node_id not in self.metrics:
            self.metrics[node_id] = []
        self.metrics[node_id].append({"name": name, "value": value, "timestamp": datetime.utcnow().isoformat()})

    def get_metrics(self, node_id: str, name: str = None, limit: int = 100) -> list[dict]:
        items = self.metrics.get(node_id, [])
        if name:
            items = [m for m in items if m["name"] == name]
        return items[-limit:]

    def get_average(self, node_id: str, name: str, window: int = 10) -> float:
        items = [m for m in self.metrics.get(node_id, []) if m["name"] == name][-window:]
        if not items:
            return 0.0
        return sum(m["value"] for m in items) / len(items)

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
