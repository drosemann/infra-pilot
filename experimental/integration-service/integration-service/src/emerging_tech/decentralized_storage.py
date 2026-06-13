"""Decentralized Storage Gateway — IPFS/Arweave/Filecoin integration gateway."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class StorageProtocol(Enum):
    IPFS = "ipfs"
    ARWEAVE = "arweave"
    FILECOIN = "filecoin"


class StorageTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


class PinningStatus(Enum):
    PINNING = "pinning"
    PINNED = "pinned"
    UNPINNING = "unpinning"
    UNPINNED = "unpinned"
    FAILED = "failed"


class ContentItem:
    def __init__(self, content_id: str, name: str, protocol: StorageProtocol, cid: str):
        self.content_id = content_id
        self.name = name
        self.protocol = protocol
        self.cid = cid
        self.size_bytes = 0
        self.mime_type = ""
        self.tier = StorageTier.HOT
        self.pinning_status = PinningStatus.PINNING
        self.replication_factor = 3
        self.checksum = ""
        self.storage_nodes: list[str] = []
        self.tags: list[str] = []
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count = 0
        self.gateway_url = ""
        self.metadata: dict[str, Any] = {}
        self.encrypted = False
        self.encryption_key_id = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            "name": self.name,
            "protocol": self.protocol.value,
            "cid": self.cid,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "tier": self.tier.value,
            "pinning_status": self.pinning_status.value,
            "replication_factor": self.replication_factor,
            "checksum": self.checksum,
            "storage_nodes": self.storage_nodes,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "gateway_url": self.gateway_url,
            "metadata": self.metadata,
            "encrypted": self.encrypted,
            "encryption_key_id": self.encryption_key_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentItem":
        item = cls(data["content_id"], data["name"], StorageProtocol(data["protocol"]), data["cid"])
        item.size_bytes = data.get("size_bytes", 0)
        item.mime_type = data.get("mime_type", "")
        item.tier = StorageTier(data.get("tier", "hot"))
        item.pinning_status = PinningStatus(data.get("pinning_status", "pinned"))
        item.replication_factor = data.get("replication_factor", 3)
        item.checksum = data.get("checksum", "")
        item.storage_nodes = data.get("storage_nodes", [])
        item.tags = data.get("tags", [])
        item.access_count = data.get("access_count", 0)
        item.gateway_url = data.get("gateway_url", "")
        item.metadata = data.get("metadata", {})
        item.encrypted = data.get("encrypted", False)
        item.encryption_key_id = data.get("encryption_key_id", "")
        return item


class PinningService:
    def __init__(self, name: str, endpoint: str):
        self.name = name
        self.endpoint = endpoint
        self.api_key = ""
        self.total_pinned = 0
        self.storage_used_gb = 0.0
        self.healthy = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "total_pinned": self.total_pinned,
            "storage_used_gb": self.storage_used_gb,
            "healthy": self.healthy,
        }


class StorageGatewayConfig:
    def __init__(self):
        self.ipfs_gateway = "https://ipfs.io"
        self.arweave_gateway = "https://arweave.net"
        self.filecoin_api = ""
        self.pinning_services: list[PinningService] = []
        self.default_replication = 3
        self.auto_pin = True
        self.hybrid_mode = True
        self.cold_storage_provider = "s3"
        self.cold_storage_bucket = ""
        self.warm_threshold_days = 30
        self.cold_threshold_days = 90
        self.max_file_size_mb = 1024

    def to_dict(self) -> dict[str, Any]:
        return {
            "ipfs_gateway": self.ipfs_gateway,
            "arweave_gateway": self.arweave_gateway,
            "filecoin_api": self.filecoin_api,
            "pinning_services": [p.to_dict() for p in self.pinning_services],
            "default_replication": self.default_replication,
            "auto_pin": self.auto_pin,
            "hybrid_mode": self.hybrid_mode,
            "cold_storage_provider": self.cold_storage_provider,
            "cold_storage_bucket": self.cold_storage_bucket,
            "warm_threshold_days": self.warm_threshold_days,
            "cold_threshold_days": self.cold_threshold_days,
            "max_file_size_mb": self.max_file_size_mb,
        }


class DecentralizedStorageGateway:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.gateway_config = StorageGatewayConfig()
        self.items: dict[str, ContentItem] = {}
        self.storage_path = config.get("storage_path", "data/decentralized_storage.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for item_data in data.get("items", []):
                    item = ContentItem.from_dict(item_data)
                    self.items[item.content_id] = item
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized DecentralizedStorageGateway with %d items", len(self.items))

    async def close(self):
        self._save()

    def _save(self):
        data = {"items": [i.to_dict() for i in self.items.values()]}
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    async def upload_content(self, name: str, data_bytes: bytes, protocol: StorageProtocol, mime_type: str = "") -> ContentItem:
        content_id = str(uuid.uuid4())
        cid = self._generate_cid(data_bytes, protocol)
        item = ContentItem(content_id, name, protocol, cid)
        item.size_bytes = len(data_bytes)
        item.mime_type = mime_type or "application/octet-stream"
        item.gateway_url = self._gateway_url(protocol, cid)
        self.items[content_id] = item
        self._save()
        asyncio.create_task(self._simulate_pinning(content_id))
        logger.info("Uploaded content %s via %s: %s (%d bytes)", content_id, protocol.value, name, len(data_bytes))
        return item

    def _generate_cid(self, data: bytes, protocol: StorageProtocol) -> str:
        import hashlib
        h = hashlib.sha256(data).hexdigest()
        prefix = {"ipfs": "Qm", "arweave": "a", "filecoin": "bafy"}.get(protocol, "Qm")
        return f"{prefix}{h[:44]}"

    def _gateway_url(self, protocol: StorageProtocol, cid: str) -> str:
        urls = {
            StorageProtocol.IPFS: f"{self.gateway_config.ipfs_gateway}/ipfs/{cid}",
            StorageProtocol.ARWEAVE: f"{self.gateway_config.arweave_gateway}/{cid}",
            StorageProtocol.FILECOIN: f"{self.gateway_config.filecoin_api}/retrieve/{cid}",
        }
        return urls.get(protocol, "")

    async def _simulate_pinning(self, content_id: str):
        item = self.items.get(content_id)
        if not item:
            return
        await asyncio.sleep(1)
        item.pinning_status = PinningStatus.PINNED
        item.storage_nodes = [f"node-{i}" for i in range(item.replication_factor)]
        self._save()

    def get_content(self, content_id: str) -> Optional[ContentItem]:
        item = self.items.get(content_id)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.utcnow()
        return item

    def list_content(self, protocol: Optional[StorageProtocol] = None) -> list[ContentItem]:
        if protocol:
            return [i for i in self.items.values() if i.protocol == protocol]
        return list(self.items.values())

    async def delete_content(self, content_id: str) -> bool:
        item = self.items.get(content_id)
        if item:
            item.pinning_status = PinningStatus.UNPINNING
            await asyncio.sleep(1)
            del self.items[content_id]
            self._save()
            return True
        return False

    async def pin_content(self, content_id: str) -> bool:
        item = self.items.get(content_id)
        if item and item.pinning_status != PinningStatus.PINNED:
            item.pinning_status = PinningStatus.PINNING
            self._save()
            asyncio.create_task(self._simulate_pinning(content_id))
            return True
        return False

    async def unpin_content(self, content_id: str) -> bool:
        item = self.items.get(content_id)
        if item and item.pinning_status == PinningStatus.PINNED:
            item.pinning_status = PinningStatus.UNPINNING
            self._save()
            await asyncio.sleep(1)
            item.pinning_status = PinningStatus.UNPINNED
            self._save()
            return True
        return False

    async def set_storage_tier(self, content_id: str, tier: StorageTier) -> bool:
        item = self.items.get(content_id)
        if item:
            item.tier = tier
            self._save()
            return True
        return False

    async def replicate_content(self, content_id: str, replication_factor: int) -> bool:
        item = self.items.get(content_id)
        if item:
            item.replication_factor = max(1, min(10, replication_factor))
            self._save()
            return True
        return False

    def search_content(self, query: str) -> list[ContentItem]:
        q = query.lower()
        return [i for i in self.items.values() if q in i.name.lower() or q in i.cid.lower() or q in ",".join(i.tags)]

    def get_storage_stats(self) -> dict[str, Any]:
        total_bytes = sum(i.size_bytes for i in self.items.values())
        stats: dict[str, Any] = {"total_items": len(self.items), "total_bytes": total_bytes, "total_gb": round(total_bytes / (1024**3), 2)}
        for protocol in StorageProtocol:
            items = [i for i in self.items.values() if i.protocol == protocol]
            stats[protocol.value] = {"count": len(items), "bytes": sum(i.size_bytes for i in items)}
        for tier in StorageTier:
            items = [i for i in self.items.values() if i.tier == tier]
            stats[f"tier_{tier.value}"] = {"count": len(items), "bytes": sum(i.size_bytes for i in items)}
        return stats

    def update_gateway_config(self, updates: dict[str, Any]):
        for key, value in updates.items():
            if hasattr(self.gateway_config, key):
                setattr(self.gateway_config, key, value)
        self._save()

    async def pin_by_cid(self, cid: str, protocol: StorageProtocol) -> ContentItem:
        content_id = str(uuid.uuid4())
        item = ContentItem(content_id, f"pinned-{cid[:16]}", protocol, cid)
        item.pinning_status = PinningStatus.PINNING
        item.gateway_url = self._gateway_url(protocol, cid)
        self.items[content_id] = item
        self._save()
        asyncio.create_task(self._simulate_pinning(content_id))
        return item

    # === Export ===
    def export_content_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["content_id", "name", "protocol", "cid", "size_bytes", "mime_type", "tier", "pinning_status", "replication", "encrypted", "access_count", "created_at"])
        for i in self.items.values():
            writer.writerow([i.content_id, i.name, i.protocol.value, i.cid, i.size_bytes, i.mime_type, i.tier.value, i.pinning_status.value, i.replication_factor, i.encrypted, i.access_count, i.created_at.isoformat()])
        return output.getvalue()

    def export_content_json(self) -> str:
        return json.dumps([i.to_dict() for i in self.items.values()], indent=2, default=str)

    # === Import ===
    def import_content_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item_data in data if isinstance(data, list) else data.get("items", []):
            item = ContentItem(
                item_data.get("content_id", str(uuid.uuid4())),
                item_data.get("name", "Imported Item"),
                StorageProtocol(item_data.get("protocol", "ipfs")),
                item_data.get("cid", "Qmimport"),
            )
            item.size_bytes = item_data.get("size_bytes", 0)
            item.mime_type = item_data.get("mime_type", "")
            item.tier = StorageTier(item_data.get("tier", "hot"))
            item.pinning_status = PinningStatus.PINNED
            item.replication_factor = item_data.get("replication_factor", 3)
            item.tags = item_data.get("tags", [])
            self.items[item.content_id] = item
            count += 1
        self._save()
        return count

    # === Notification ===
    async def notify_content_status(self, content_id: str) -> dict[str, Any]:
        item = self.items.get(content_id)
        if not item:
            return {"error": "Content not found"}
        return {
            "content_id": item.content_id,
            "name": item.name,
            "protocol": item.protocol.value,
            "cid": item.cid,
            "pinning_status": item.pinning_status.value,
            "message": f"Content {item.name} ({item.protocol.value}) status: {item.pinning_status.value}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_failed_pins(self) -> list[dict[str, Any]]:
        results = []
        for i in self.items.values():
            if i.pinning_status == PinningStatus.FAILED:
                results.append(await self.notify_content_status(i.content_id))
        return results

    # === State Machine ===
    def transition_pinning_status(self, content_id: str, target_status: str) -> Optional[ContentItem]:
        item = self.items.get(content_id)
        if not item:
            return None
        valid = {
            PinningStatus.PINNING: [PinningStatus.PINNED, PinningStatus.FAILED],
            PinningStatus.PINNED: [PinningStatus.UNPINNING],
            PinningStatus.UNPINNING: [PinningStatus.UNPINNED, PinningStatus.FAILED],
            PinningStatus.UNPINNED: [PinningStatus.PINNING],
            PinningStatus.FAILED: [PinningStatus.PINNING],
        }
        new_status = PinningStatus(target_status)
        if new_status in valid.get(item.pinning_status, []):
            item.pinning_status = new_status
            self._save()
            return item
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if config.get("max_file_size_mb", 1024) > 10240:
            warnings.append("Max file size exceeds 10GB")
        if not config.get("ipfs_gateway"):
            warnings.append("No IPFS gateway configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        total_bytes = sum(i.size_bytes for i in self.items.values())
        return {
            "total_items": len(self.items),
            "total_gb": round(total_bytes / (1024**3), 2),
            "by_protocol": {p.value: sum(1 for i in self.items.values() if i.protocol == p) for p in StorageProtocol},
            "by_tier": {t.value: sum(1 for i in self.items.values() if i.tier == t) for t in StorageTier},
            "total_accesses": sum(i.access_count for i in self.items.values()),
            "encrypted_count": sum(1 for i in self.items.values() if i.encrypted),
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        pinned = sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNED)
        failed = sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.FAILED)
        return {
            "total": len(self.items),
            "pinned": pinned,
            "failed": failed,
            "health_pct": round(pinned / max(len(self.items), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_pin_content(self, content_ids: list[str]) -> int:
        count = 0
        for cid in content_ids:
            i = self.items.get(cid)
            if i and i.pinning_status not in (PinningStatus.PINNED, PinningStatus.PINNING):
                i.pinning_status = PinningStatus.PINNING
                count += 1
        self._save()
        return count

    async def bulk_unpin_content(self, content_ids: list[str]) -> int:
        count = 0
        for cid in content_ids:
            i = self.items.get(cid)
            if i and i.pinning_status == PinningStatus.PINNED:
                i.pinning_status = PinningStatus.UNPINNING
                count += 1
        self._save()
        return count

    async def bulk_set_tier(self, content_ids: list[str], tier: StorageTier) -> int:
        count = 0
        for cid in content_ids:
            i = self.items.get(cid)
            if i:
                i.tier = tier
                count += 1
        self._save()
        return count

    async def bulk_delete_content(self, content_ids: list[str]) -> int:
        count = 0
        for cid in content_ids:
            if cid in self.items:
                del self.items[cid]
                count += 1
        self._save()
        return count

    # === Tag Management ===
    def add_content_tags(self, content_ids: list[str], tags: list[str]) -> int:
        count = 0
        for cid in content_ids:
            i = self.items.get(cid)
            if i:
                for t in tags:
                    if t not in i.tags:
                        i.tags.append(t)
                count += 1
        self._save()
        return count

    def remove_content_tags(self, content_ids: list[str], tags: list[str]) -> int:
        count = 0
        for cid in content_ids:
            i = self.items.get(cid)
            if i:
                i.tags = [t for t in i.tags if t not in tags]
                count += 1
        self._save()
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "decentralized_storage",
            "items": len(self.items),
            "pinned": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNED),
            "pinning": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNING),
            "failed": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.FAILED),
            "total_gb": round(sum(i.size_bytes for i in self.items.values()) / (1024**3), 2),
            "status": "healthy",
        }

    # === Replication Policies ===
    def set_replication_policy(self, name: str, min_replicas: int = 3, max_replicas: int = 10,
                                 regions: list[str] | None = None) -> dict[str, Any]:
        policy_id = str(uuid.uuid4())
        policy = {"policy_id": policy_id, "name": name, "min_replicas": min_replicas,
                  "max_replicas": max_replicas, "regions": regions or ["auto"],
                  "status": "active", "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_replication_policies"):
            self._replication_policies: dict[str, dict[str, Any]] = {}
        self._replication_policies[policy_id] = policy
        return policy

    def get_replication_policies(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_replication_policies", {}).values())

    def apply_replication_policy(self, content_ids: list[str], policy_id: str) -> int:
        policy = getattr(self, "_replication_policies", {}).get(policy_id)
        if not policy:
            return 0
        count = 0
        for cid in content_ids:
            item = self.items.get(cid)
            if item:
                item.replication_count = policy["min_replicas"]
                item.metadata["replication_policy"] = policy_id
                count += 1
        self._save()
        return count

    # === Cost Tracking ===
    def track_storage_cost(self, content_id: str, cost_per_gb_month: float = 0.05) -> dict[str, Any]:
        item = self.items.get(content_id)
        if not item:
            return {"error": "Content not found"}
        size_gb = item.size_bytes / (1024**3)
        monthly_cost = size_gb * cost_per_gb_month * (item.replication_count or 1)
        cost_entry = {"content_id": content_id, "size_gb": round(size_gb, 4), "replicas": item.replication_count or 1,
                      "cost_per_gb": cost_per_gb_month, "monthly_cost": round(monthly_cost, 4),
                      "calculated_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_cost_entries"):
            self._cost_entries: list[dict[str, Any]] = []
        self._cost_entries.append(cost_entry)
        return cost_entry

    def get_cost_summary(self) -> dict[str, Any]:
        entries = getattr(self, "_cost_entries", [])
        total = round(sum(e["monthly_cost"] for e in entries), 2)
        return {"total_monthly_cost": total, "entries": len(entries),
                "avg_cost_per_item": round(total / max(len(entries), 1), 4)}

    # === File Management ===
    def list_content_by_type(self, mime_type: str = "") -> list[dict[str, Any]]:
        items = [i for i in self.items.values() if not mime_type or i.mime_type == mime_type]
        return [i.to_dict() for i in items]

    def get_storage_usage_by_tier(self) -> dict[str, Any]:
        usage: dict[str, dict[str, Any]] = {}
        for tier in StorageTier:
            items = [i for i in self.items.values() if i.tier == tier]
            total_bytes = sum(i.size_bytes for i in items)
            usage[tier.value] = {"count": len(items), "total_bytes": total_bytes,
                                  "total_gb": round(total_bytes / (1024**3), 2)}
        return usage

    def search_content(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [i.to_dict() for i in self.items.values()
                if q in i.name.lower() or q in (i.cid or "").lower() or q in str(i.tags).lower()]

    # === Reporting ===
    def generate_report(self, report_type: str = "summary") -> dict[str, Any]:
        if report_type == "summary":
            return {"items": len(self.items), "pinned": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNED),
                    "total_gb": round(sum(i.size_bytes for i in self.items.values()) / (1024**3), 2),
                    "by_tier": self.get_storage_usage_by_tier(),
                    "encrypted_count": sum(1 for i in self.items.values() if i.encrypted)}
        elif report_type == "pinning":
            return {"pinned": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNED),
                    "pinning": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNING),
                    "unpinning": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.UNPINNING),
                    "failed": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.FAILED)}
        return {}

    def export_content_data(self, format: str = "json") -> Any:
        if format == "csv":
            lines = ["cid,name,mime_type,size_bytes,tier,pinning_status,encrypted,created_at"]
            for i in self.items.values():
                lines.append(f"{i.cid},{i.name},{i.mime_type},{i.size_bytes},{i.tier.value},{i.pinning_status.value},{i.encrypted},{i.created_at.isoformat()}")
            return "\n".join(lines)
        return {"items": [i.to_dict() for i in self.items.values()]}

    # === Dashboard ===
    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "item_count": len(self.items),
            "pinned_count": sum(1 for i in self.items.values() if i.pinning_status == PinningStatus.PINNED),
            "total_gb": round(sum(i.size_bytes for i in self.items.values()) / (1024**3), 2),
            "encrypted_count": sum(1 for i in self.items.values() if i.encrypted),
            "usage_by_tier": self.get_storage_usage_by_tier(),
            "replication_policies": len(getattr(self, "_replication_policies", {})),
            "monthly_cost": self.get_cost_summary().get("total_monthly_cost", 0),
        }

    # === Scheduling ===
    def schedule_pinning_check(self, interval_hours: int = 24) -> dict[str, Any]:
        schedule_id = str(uuid.uuid4())
        schedule = {"schedule_id": schedule_id, "interval_hours": interval_hours,
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

    # === Content Lifecycle ===
    def set_retention_policy(self, name: str, retention_days: int = 365, action: str = "archive") -> dict[str, Any]:
        policy_id = str(uuid.uuid4())
        policy = {"policy_id": policy_id, "name": name, "retention_days": retention_days,
                  "action": action, "status": "active", "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_retention_policies"):
            self._retention_policies: dict[str, dict[str, Any]] = {}
        self._retention_policies[policy_id] = policy
        return policy

    def get_retention_policies(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_retention_policies", {}).values())

    def apply_retention_policies(self) -> dict[str, Any]:
        archived = 0
        deleted = 0
        for policy in getattr(self, "_retention_policies", {}).values():
            if policy["status"] != "active":
                continue
            cutoff = datetime.utcnow() - timedelta(days=policy["retention_days"])
            for i in self.items.values():
                if i.created_at < cutoff:
                    if policy["action"] == "delete":
                        if i.cid in self.items:
                            del self.items[i.cid]
                            deleted += 1
                    elif policy["action"] == "archive":
                        archived += 1
        self._save()
        return {"archived": archived, "deleted": deleted}

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
