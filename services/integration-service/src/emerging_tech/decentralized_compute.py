"""Decentralized Compute Network — peer-to-peer compute marketplace."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    TPU = "tpu"


class ComputeProviderStatus(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    DEGRADED = "degraded"
    BANNED = "banned"


class OrderStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class SettlementMethod(Enum):
    TOKEN = "token"
    FIAT = "fiat"
    CRYPTO = "crypto"
    CREDIT = "credit"


class ComputeProvider:
    def __init__(self, provider_id: str, name: str, wallet_address: str):
        self.provider_id = provider_id
        self.name = name
        self.wallet_address = wallet_address
        self.status = ComputeProviderStatus.OFFLINE
        self.total_cpu_cores = 0
        self.total_gpu_count = 0
        self.total_memory_mb = 0
        self.total_storage_gb = 0
        self.available_cpu_cores = 0
        self.available_gpu_count = 0
        self.available_memory_mb = 0
        self.available_storage_gb = 0
        self.gpu_models: list[str] = []
        self.cpu_model = ""
        self.region = ""
        self.price_per_cpu_hour = 0.0
        self.price_per_gpu_hour = 0.0
        self.price_per_gb_hour = 0.0
        self.price_per_gb_storage = 0.0
        self.reputation_score = 1.0
        self.total_jobs_completed = 0
        self.total_earned = 0.0
        self.uptime_pct = 0.0
        self.network_latency_ms = 0
        self.bandwidth_mbps = 0
        self.tags: list[str] = []
        self.joined_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id, "name": self.name,
            "wallet_address": self.wallet_address, "status": self.status.value,
            "total_cpu_cores": self.total_cpu_cores, "total_gpu_count": self.total_gpu_count,
            "total_memory_mb": self.total_memory_mb, "total_storage_gb": self.total_storage_gb,
            "available_cpu_cores": self.available_cpu_cores,
            "available_gpu_count": self.available_gpu_count,
            "available_memory_mb": self.available_memory_mb,
            "available_storage_gb": self.available_storage_gb,
            "gpu_models": self.gpu_models, "cpu_model": self.cpu_model, "region": self.region,
            "price_per_cpu_hour": self.price_per_cpu_hour,
            "price_per_gpu_hour": self.price_per_gpu_hour,
            "price_per_gb_hour": self.price_per_gb_hour,
            "price_per_gb_storage": self.price_per_gb_storage,
            "reputation_score": self.reputation_score,
            "total_jobs_completed": self.total_jobs_completed,
            "total_earned": self.total_earned, "uptime_pct": self.uptime_pct,
            "network_latency_ms": self.network_latency_ms,
            "bandwidth_mbps": self.bandwidth_mbps, "tags": self.tags,
            "joined_at": self.joined_at.isoformat(),
        }


class ComputeOrder:
    def __init__(self, order_id: str, name: str, consumer_wallet: str):
        self.order_id = order_id
        self.name = name
        self.consumer_wallet = consumer_wallet
        self.status = OrderStatus.PENDING
        self.provider_id = ""
        self.resource_type = ResourceType.CPU
        self.cpu_cores = 1
        self.gpu_count = 0
        self.memory_mb = 1024
        self.storage_gb = 10
        self.duration_hours = 1
        self.total_cost = 0.0
        self.settlement_method = SettlementMethod.CRYPTO
        self.token_amount = 0.0
        self.image = ""
        self.command = ""
        self.container_id = ""
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result_hash = ""
        self.logs: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id, "name": self.name,
            "consumer_wallet": self.consumer_wallet, "status": self.status.value,
            "provider_id": self.provider_id, "resource_type": self.resource_type.value,
            "cpu_cores": self.cpu_cores, "gpu_count": self.gpu_count,
            "memory_mb": self.memory_mb, "storage_gb": self.storage_gb,
            "duration_hours": self.duration_hours, "total_cost": self.total_cost,
            "settlement_method": self.settlement_method.value,
            "token_amount": self.token_amount, "image": self.image,
            "container_id": self.container_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_hash": self.result_hash,
        }


class ProviderRating:
    def __init__(self, rating_id: str, provider_id: str, consumer_wallet: str):
        self.rating_id = rating_id
        self.provider_id = provider_id
        self.consumer_wallet = consumer_wallet
        self.score = 5
        self.reliability = 5
        self.speed = 5
        self.communication = 5
        self.comment = ""
        self.order_id = ""
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rating_id": self.rating_id, "provider_id": self.provider_id,
            "consumer_wallet": self.consumer_wallet, "score": self.score,
            "reliability": self.reliability, "speed": self.speed,
            "communication": self.communication, "comment": self.comment,
            "order_id": self.order_id, "created_at": self.created_at.isoformat(),
        }


class DecentralizedComputeNetwork:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.providers: dict[str, ComputeProvider] = {}
        self.orders: dict[str, ComputeOrder] = {}
        self.ratings: dict[str, ProviderRating] = {}
        self.storage_path = config.get("storage_path", "data/decentralized_compute.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for p_data in data.get("providers", []):
                    p = ComputeProvider(p_data["provider_id"], p_data["name"], p_data["wallet_address"])
                    p.status = ComputeProviderStatus(p_data.get("status", "offline"))
                    p.total_cpu_cores = p_data.get("total_cpu_cores", 0)
                    p.total_gpu_count = p_data.get("total_gpu_count", 0)
                    p.total_memory_mb = p_data.get("total_memory_mb", 0)
                    p.total_storage_gb = p_data.get("total_storage_gb", 0)
                    p.region = p_data.get("region", "")
                    p.price_per_cpu_hour = p_data.get("price_per_cpu_hour", 0.0)
                    p.price_per_gpu_hour = p_data.get("price_per_gpu_hour", 0.0)
                    p.reputation_score = p_data.get("reputation_score", 1.0)
                    p.total_jobs_completed = p_data.get("total_jobs_completed", 0)
                    p.uptime_pct = p_data.get("uptime_pct", 0.0)
                    p.gpu_models = p_data.get("gpu_models", [])
                    self.providers[p.provider_id] = p
                for o_data in data.get("orders", []):
                    o = ComputeOrder(o_data["order_id"], o_data["name"], o_data["consumer_wallet"])
                    o.status = OrderStatus(o_data.get("status", "pending"))
                    o.provider_id = o_data.get("provider_id", "")
                    o.cpu_cores = o_data.get("cpu_cores", 1)
                    o.gpu_count = o_data.get("gpu_count", 0)
                    o.memory_mb = o_data.get("memory_mb", 1024)
                    o.duration_hours = o_data.get("duration_hours", 1)
                    o.total_cost = o_data.get("total_cost", 0.0)
                    o.image = o_data.get("image", "")
                    self.orders[o.order_id] = o
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized DecentralizedComputeNetwork with %d providers, %d orders", len(self.providers), len(self.orders))

    async def close(self):
        self._save()

    def _save(self):
        data = {"providers": [p.to_dict() for p in self.providers.values()], "orders": [o.to_dict() for o in self.orders.values()], "ratings": [r.to_dict() for r in self.ratings.values()]}
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    async def register_provider(self, name: str, wallet_address: str, region: str = "auto") -> ComputeProvider:
        provider_id = str(uuid.uuid4())
        provider = ComputeProvider(provider_id, name, wallet_address)
        provider.region = region
        provider.status = ComputeProviderStatus.ONLINE
        provider.total_cpu_cores = 16
        provider.total_memory_mb = 32768
        provider.total_storage_gb = 500
        provider.available_cpu_cores = 16
        provider.available_memory_mb = 32768
        provider.available_storage_gb = 500
        provider.price_per_cpu_hour = 0.05
        provider.price_per_gb_hour = 0.002
        provider.uptime_pct = 99.5
        self.providers[provider_id] = provider
        self._save()
        return provider

    def get_provider(self, provider_id: str) -> Optional[ComputeProvider]:
        return self.providers.get(provider_id)

    def list_providers(self, status: Optional[ComputeProviderStatus] = None) -> list[ComputeProvider]:
        if status:
            return [p for p in self.providers.values() if p.status == status]
        return list(self.providers.values())

    async def update_provider_resources(self, provider_id: str, resources: dict[str, Any]) -> bool:
        provider = self.providers.get(provider_id)
        if not provider:
            return False
        for key, value in resources.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        self._save()
        return True

    async def create_order(self, name: str, consumer_wallet: str, cpu_cores: int = 1, memory_mb: int = 1024, duration_hours: int = 1, gpu_count: int = 0) -> ComputeOrder:
        order_id = str(uuid.uuid4())
        order = ComputeOrder(order_id, name, consumer_wallet)
        order.cpu_cores = cpu_cores
        order.memory_mb = memory_mb
        order.duration_hours = duration_hours
        order.gpu_count = gpu_count
        order.total_cost = self._calculate_cost(cpu_cores, memory_mb, duration_hours, gpu_count)
        self.orders[order_id] = order
        self._save()
        asyncio.create_task(self._match_order(order_id))
        return order

    def _calculate_cost(self, cpu_cores: int, memory_mb: int, duration_hours: int, gpu_count: int = 0) -> float:
        cpu_cost = cpu_cores * 0.05 * duration_hours
        mem_cost = (memory_mb / 1024) * 0.002 * duration_hours
        gpu_cost = gpu_count * 0.50 * duration_hours
        return round(cpu_cost + mem_cost + gpu_cost, 4)

    async def _match_order(self, order_id: str):
        await asyncio.sleep(1)
        order = self.orders.get(order_id)
        if not order or order.status != OrderStatus.PENDING:
            return
        available = [p for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE and p.available_cpu_cores >= order.cpu_cores]
        if not available:
            order.status = OrderStatus.CANCELLED
            self._save()
            return
        provider = max(available, key=lambda p: p.reputation_score)
        order.status = OrderStatus.ACTIVE
        order.provider_id = provider.provider_id
        order.started_at = datetime.utcnow()
        provider.available_cpu_cores -= order.cpu_cores
        provider.available_memory_mb -= order.memory_mb
        self._save()
        asyncio.create_task(self._simulate_compute(order_id))

    async def _simulate_compute(self, order_id: str):
        await asyncio.sleep(3)
        order = self.orders.get(order_id)
        if not order:
            return
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
        order.result_hash = f"result-{uuid.uuid4().hex[:32]}"
        provider = self.providers.get(order.provider_id)
        if provider:
            provider.available_cpu_cores += order.cpu_cores
            provider.available_memory_mb += order.memory_mb
            provider.total_jobs_completed += 1
            provider.total_earned += order.total_cost
        self._save()

    def get_order(self, order_id: str) -> Optional[ComputeOrder]:
        return self.orders.get(order_id)

    def list_orders(self, status: Optional[OrderStatus] = None) -> list[ComputeOrder]:
        if status:
            return [o for o in self.orders.values() if o.status == status]
        return list(self.orders.values())

    async def cancel_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.status in (OrderStatus.PENDING, OrderStatus.ACTIVE):
            order.status = OrderStatus.CANCELLED
            provider = self.providers.get(order.provider_id)
            if provider:
                provider.available_cpu_cores += order.cpu_cores
                provider.available_memory_mb += order.memory_mb
            self._save()
            return True
        return False

    async def rate_provider(self, provider_id: str, consumer_wallet: str, score: int, order_id: str = "") -> ProviderRating:
        rating_id = str(uuid.uuid4())
        rating = ProviderRating(rating_id, provider_id, consumer_wallet)
        rating.score = min(5, max(1, score))
        rating.order_id = order_id
        self.ratings[rating_id] = rating
        provider = self.providers.get(provider_id)
        if provider:
            all_scores = [r.score for r in self.ratings.values() if r.provider_id == provider_id]
            provider.reputation_score = sum(all_scores) / len(all_scores)
        self._save()
        return rating

    def find_optimal_provider(self, cpu_cores: int = 1, memory_mb: int = 1024, gpu_count: int = 0, max_price_per_hour: float = 1.0) -> list[ComputeProvider]:
        candidates = [p for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE and p.available_cpu_cores >= cpu_cores and p.available_memory_mb >= memory_mb and p.available_gpu_count >= gpu_count and p.price_per_cpu_hour <= max_price_per_hour]
        return sorted(candidates, key=lambda p: (-p.reputation_score, p.price_per_cpu_hour))

    def get_market_stats(self) -> dict[str, Any]:
        active_orders = [o for o in self.orders.values() if o.status == OrderStatus.ACTIVE]
        completed_orders = [o for o in self.orders.values() if o.status == OrderStatus.COMPLETED]
        return {
            "total_providers": len(self.providers),
            "online_providers": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE),
            "total_orders": len(self.orders),
            "active_orders": len(active_orders),
            "completed_orders": len(completed_orders),
            "total_spent": sum(o.total_cost for o in completed_orders),
            "total_provider_earnings": sum(p.total_earned for p in self.providers.values()),
            "available_cpu_cores": sum(p.available_cpu_cores for p in self.providers.values()),
            "available_gpu_count": sum(p.available_gpu_count for p in self.providers.values()),
            "available_memory_gb": sum(p.available_memory_mb for p in self.providers.values()) / 1024,
            "avg_price_per_cpu_hour": sum(p.price_per_cpu_hour for p in self.providers.values()) / len(self.providers) if self.providers else 0,
        }

    # === Export ===
    def export_providers_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["provider_id", "name", "wallet_address", "status", "region", "cpu_cores", "gpu_count", "memory_mb", "reputation", "uptime_pct", "price_per_cpu_hour", "joined_at"])
        for p in self.providers.values():
            writer.writerow([p.provider_id, p.name, p.wallet_address, p.status.value, p.region, p.total_cpu_cores, p.total_gpu_count, p.total_memory_mb, p.reputation_score, p.uptime_pct, p.price_per_cpu_hour, p.joined_at.isoformat()])
        return output.getvalue()

    def export_orders_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["order_id", "name", "consumer_wallet", "status", "provider_id", "resource_type", "cpu_cores", "gpu_count", "memory_mb", "duration_hours", "total_cost", "created_at"])
        for o in self.orders.values():
            writer.writerow([o.order_id, o.name, o.consumer_wallet, o.status.value, o.provider_id, o.resource_type.value, o.cpu_cores, o.gpu_count, o.memory_mb, o.duration_hours, o.total_cost, o.created_at.isoformat()])
        return output.getvalue()

    def export_providers_json(self) -> str:
        return json.dumps({"providers": [p.to_dict() for p in self.providers.values()], "orders": [o.to_dict() for o in self.orders.values()]}, indent=2, default=str)

    # === Import ===
    def import_providers_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("providers", data if isinstance(data, list) else []):
            p = ComputeProvider(item.get("provider_id", str(uuid.uuid4())), item.get("name", "Imported Provider"), item.get("wallet_address", "0x0"))
            p.status = ComputeProviderStatus(item.get("status", "offline"))
            p.region = item.get("region", "")
            p.total_cpu_cores = item.get("total_cpu_cores", 0)
            p.total_gpu_count = item.get("total_gpu_count", 0)
            p.total_memory_mb = item.get("total_memory_mb", 0)
            p.total_storage_gb = item.get("total_storage_gb", 0)
            p.price_per_cpu_hour = item.get("price_per_cpu_hour", 0.0)
            p.reputation_score = item.get("reputation_score", 1.0)
            p.uptime_pct = item.get("uptime_pct", 0.0)
            self.providers[p.provider_id] = p
            count += 1
        return count

    # === Notification ===
    async def notify_order_status(self, order_id: str) -> dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        return {
            "order_id": order.order_id,
            "name": order.name,
            "consumer_wallet": order.consumer_wallet,
            "status": order.status.value,
            "message": f"Compute order {order.name} status: {order.status.value}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_completed_orders(self) -> list[dict[str, Any]]:
        results = []
        for o in self.orders.values():
            if o.status == OrderStatus.COMPLETED:
                results.append(await self.notify_order_status(o.order_id))
        return results

    # === State Machine ===
    def transition_order_status(self, order_id: str, target_status: str) -> Optional[ComputeOrder]:
        order = self.orders.get(order_id)
        if not order:
            return None
        valid = {
            OrderStatus.PENDING: [OrderStatus.ACTIVE, OrderStatus.CANCELLED],
            OrderStatus.ACTIVE: [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.DISPUTED],
            OrderStatus.COMPLETED: [OrderStatus.DISPUTED],
            OrderStatus.DISPUTED: [OrderStatus.CANCELLED, OrderStatus.COMPLETED],
            OrderStatus.CANCELLED: [],
        }
        new_status = OrderStatus(target_status)
        if new_status in valid.get(order.status, []):
            order.status = new_status
            self._save()
            return order
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("storage_path"):
            warnings.append("No storage path configured")
        if config.get("default_price_per_cpu_hour", 0.05) > 1.0:
            warnings.append("Default CPU price is high (>1.0)")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_providers": len(self.providers),
            "online": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE),
            "busy": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.BUSY),
            "total_orders": len(self.orders),
            "active_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE),
            "completed_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.COMPLETED),
            "total_revenue": sum(o.total_cost for o in self.orders.values() if o.status == OrderStatus.COMPLETED),
            "avg_rating": sum(r.score for r in self.ratings.values()) / len(self.ratings) if self.ratings else 0,
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        online = sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE)
        return {
            "total_providers": len(self.providers),
            "online": online,
            "active_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE),
            "health_pct": round(online / max(len(self.providers), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_update_provider_status(self, provider_ids: list[str], status: ComputeProviderStatus) -> int:
        count = 0
        for pid in provider_ids:
            p = self.providers.get(pid)
            if p:
                p.status = status
                count += 1
        self._save()
        return count

    async def bulk_cancel_orders(self, order_ids: list[str]) -> int:
        count = 0
        for oid in order_ids:
            o = self.orders.get(oid)
            if o and o.status in (OrderStatus.PENDING, OrderStatus.ACTIVE):
                o.status = OrderStatus.CANCELLED
                count += 1
        self._save()
        return count

    # === Tag Management ===
    def add_provider_tags(self, provider_ids: list[str], tags: list[str]) -> int:
        count = 0
        for pid in provider_ids:
            p = self.providers.get(pid)
            if p:
                for t in tags:
                    if t not in p.tags:
                        p.tags.append(t)
                count += 1
        self._save()
        return count

    def remove_provider_tags(self, provider_ids: list[str], tags: list[str]) -> int:
        count = 0
        for pid in provider_ids:
            p = self.providers.get(pid)
            if p:
                p.tags = [t for t in p.tags if t not in tags]
                count += 1
        self._save()
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "decentralized_compute",
            "providers": len(self.providers),
            "orders": len(self.orders),
            "online": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE),
            "active_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE),
            "status": "healthy",
        }

    # === Reputation Scoring ===
    def calculate_provider_reputation(self, provider_id: str) -> dict[str, Any]:
        provider = self.providers.get(provider_id)
        if not provider:
            return {"error": "Provider not found"}
        completed = sum(1 for o in self.orders.values() if o.provider_id == provider_id and o.status == OrderStatus.COMPLETED)
        failed = sum(1 for o in self.orders.values() if o.provider_id == provider_id and o.status == OrderStatus.FAILED)
        total = completed + failed
        success_rate = round(completed / max(total, 1) * 100, 1) if total > 0 else 0
        ratings = [r.score for r in self.ratings.values() if r.provider_id == provider_id]
        avg_rating = round(sum(ratings) / max(len(ratings), 1), 1)
        reliability = round(success_rate * 0.6 + avg_rating * 20 * 0.4, 1)
        return {"provider_id": provider_id, "name": provider.name, "success_rate": success_rate,
                "avg_rating": avg_rating, "completed_orders": completed, "failed_orders": failed,
                "reliability_score": reliability}

    def get_provider_rankings(self) -> list[dict[str, Any]]:
        rankings = []
        for pid in self.providers:
            rankings.append(self.calculate_provider_reputation(pid))
        rankings.sort(key=lambda x: x.get("reliability_score", 0), reverse=True)
        return rankings

    # === SLA Management ===
    def set_sla(self, provider_id: str, uptime_guarantee_pct: float = 99.9,
                max_response_time_ms: int = 5000, penalty_per_violation: float = 10.0) -> dict[str, Any]:
        provider = self.providers.get(provider_id)
        if not provider:
            return {"error": "Provider not found"}
        sla_id = str(uuid.uuid4())
        sla = {"sla_id": sla_id, "provider_id": provider_id, "uptime_guarantee_pct": uptime_guarantee_pct,
               "max_response_time_ms": max_response_time_ms, "penalty_per_violation": penalty_per_violation,
               "status": "active", "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_slas"):
            self._slas: dict[str, dict[str, Any]] = {}
        self._slas[sla_id] = sla
        return sla

    def get_slas(self, provider_id: str = "") -> list[dict[str, Any]]:
        slas = list(getattr(self, "_slas", {}).values())
        if provider_id:
            return [s for s in slas if s["provider_id"] == provider_id]
        return slas

    def check_sla_compliance(self, sla_id: str) -> dict[str, Any]:
        slas = getattr(self, "_slas", {})
        sla = slas.get(sla_id)
        if not sla:
            return {"error": "SLA not found"}
        orders = [o for o in self.orders.values() if o.provider_id == sla["provider_id"]]
        total = len(orders)
        violations = sum(1 for o in orders if o.status == OrderStatus.FAILED)
        return {"sla_id": sla_id, "provider_id": sla["provider_id"], "total_orders": total,
                "violations": violations, "compliance_pct": round((1 - violations / max(total, 1)) * 100, 1),
                "penalty_due": violations * sla["penalty_per_violation"]}

    # === Dispute Resolution ===
    def create_dispute(self, order_id: str, raised_by: str, reason: str) -> dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        dispute_id = str(uuid.uuid4())
        dispute = {"dispute_id": dispute_id, "order_id": order_id, "raised_by": raised_by,
                   "reason": reason, "status": "open", "created_at": datetime.utcnow().isoformat(),
                   "resolved_at": None, "resolution": None}
        if not hasattr(self, "_disputes"):
            self._disputes: dict[str, dict[str, Any]] = {}
        self._disputes[dispute_id] = dispute
        order.status = OrderStatus.DISPUTED
        self._save()
        return dispute

    def resolve_dispute(self, dispute_id: str, resolution: str, in_favor: str) -> dict[str, Any]:
        disputes = getattr(self, "_disputes", {})
        dispute = disputes.get(dispute_id)
        if not dispute:
            return {"error": "Dispute not found"}
        dispute["status"] = "resolved"
        dispute["resolution"] = resolution
        dispute["resolved_at"] = datetime.utcnow().isoformat()
        order = self.orders.get(dispute["order_id"])
        if order:
            order.status = OrderStatus.COMPLETED if in_favor == "consumer" else OrderStatus.FAILED
        self._save()
        return dispute

    def get_disputes(self, status: str = "") -> list[dict[str, Any]]:
        disputes = list(getattr(self, "_disputes", {}).values())
        if status:
            return [d for d in disputes if d["status"] == status]
        return disputes

    # === Reporting ===
    def generate_report(self, report_type: str = "summary") -> dict[str, Any]:
        if report_type == "summary":
            return {"providers": len(self.providers), "online": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE),
                    "orders": len(self.orders), "active_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE),
                    "completed_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.COMPLETED),
                    "total_revenue": sum(o.total_cost for o in self.orders.values() if o.status == OrderStatus.COMPLETED),
                    "avg_rating": sum(r.score for r in self.ratings.values()) / len(self.ratings) if self.ratings else 0}
        elif report_type == "providers":
            return {"providers": [{"id": pid, "name": p.name, "status": p.status.value, "rating": self.calculate_provider_reputation(pid).get("reliability_score", 0)} for pid, p in self.providers.items()]}
        return {}

    def export_orders(self, format: str = "json") -> Any:
        if format == "csv":
            lines = ["order_id,provider_id,cpu_hours,gpu_hours,memory_gb,status,total_cost,created_at"]
            for o in self.orders.values():
                lines.append(f"{o.order_id},{o.provider_id},{o.cpu_hours},{o.gpu_hours},{o.memory_gb},{o.status.value},{o.total_cost},{o.created_at.isoformat()}")
            return "\n".join(lines)
        return {"orders": [o.to_dict() for o in self.orders.values()]}

    # === Dashboard ===
    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "provider_count": len(self.providers),
            "online_count": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE),
            "order_count": len(self.orders),
            "active_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE),
            "total_revenue": sum(o.total_cost for o in self.orders.values() if o.status == OrderStatus.COMPLETED),
            "avg_rating": sum(r.score for r in self.ratings.values()) / len(self.ratings) if self.ratings else 0,
            "dispute_count": len(getattr(self, "_disputes", {})),
            "sla_count": len(getattr(self, "_slas", {})),
        }

    # === Scheduling ===
    def schedule_order_audit(self, interval_hours: int = 168) -> dict[str, Any]:
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

    def get_marketplace_stats(self) -> dict[str, Any]:
        total_cpu = sum(o.cpu_hours for o in self.orders.values() if o.status == OrderStatus.ACTIVE)
        total_gpu = sum(o.gpu_hours for o in self.orders.values() if o.status == OrderStatus.ACTIVE)
        return {"active_providers": sum(1 for p in self.providers.values() if p.status == ComputeProviderStatus.ONLINE),
                "active_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE),
                "total_cpu_hours": total_cpu, "total_gpu_hours": total_gpu,
                "avg_price_per_cpu_hour": round(sum(o.total_cost / max(o.cpu_hours, 1) for o in self.orders.values()) / max(len(self.orders), 1), 4)}

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
