"""Hardware Lifecycle Tracker - Track server hardware age, warranty, e-waste."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, date
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class HardwareType(Enum):
    SERVER = "server"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"
    UPS = "ups"
    OTHER = "other"


class AssetStatus(Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"
    DISPOSED = "disposed"


class DepreciationMethod(Enum):
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS = "sum_of_years"


class HardwareAsset:
    """A hardware asset tracked in the lifecycle system."""

    def __init__(self, asset_id: str, asset_type: HardwareType,
                 manufacturer: str, model: str, serial_number: str):
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.manufacturer = manufacturer
        self.model = model
        self.serial_number = serial_number
        self.purchase_date: date = date.today()
        self.purchase_price: float = 0.0
        self.warranty_months: int = 36
        self.warranty_expiry: date = date.today()
        self.expected_lifespan_months: int = 60
        self.end_of_life_date: Optional[date] = None
        self.location: str = ""
        self.rack: str = ""
        self.rack_position: str = ""
        self.owner: str = ""
        self.status: AssetStatus = AssetStatus.ACTIVE
        self.decommission_date: Optional[date] = None
        self.disposal_method: Optional[str] = None
        self.recycling_partner: Optional[str] = None
        self.last_maintenance_date: Optional[date] = None
        self.next_maintenance_date: Optional[date] = None
        self.maintenance_interval_days: int = 180
        self.depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
        self.salvage_value: float = 0.0
        self.tags: list[str] = []
        self.notes: str = ""
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def age_months(self) -> float:
        delta = date.today() - self.purchase_date
        return delta.days / 30.44

    @property
    def warranty_remaining_days(self) -> int:
        delta = self.warranty_expiry - date.today()
        return max(0, delta.days)

    @property
    def is_warranty_expired(self) -> bool:
        return self.warranty_expiry < date.today()

    @property
    def is_lifespan_exceeded(self) -> bool:
        return self.age_months > self.expected_lifespan_months

    @property
    def current_value(self) -> float:
        if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
            monthly_dep = (self.purchase_price - self.salvage_value) / self.expected_lifespan_months
            age = min(self.age_months, self.expected_lifespan_months)
            return max(self.salvage_value, self.purchase_price - monthly_dep * age)
        return self.purchase_price

    @property
    def maintenance_overdue(self) -> bool:
        if not self.next_maintenance_date:
            return False
        return self.next_maintenance_date < date.today()

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type.value,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "purchase_date": self.purchase_date.isoformat(),
            "purchase_price": self.purchase_price,
            "warranty_months": self.warranty_months,
            "warranty_expiry": self.warranty_expiry.isoformat(),
            "warranty_remaining_days": self.warranty_remaining_days,
            "expected_lifespan_months": self.expected_lifespan_months,
            "age_months": round(self.age_months, 1),
            "end_of_life_date": self.end_of_life_date.isoformat() if self.end_of_life_date else None,
            "location": self.location,
            "rack": self.rack,
            "owner": self.owner,
            "status": self.status.value,
            "decommission_date": self.decommission_date.isoformat() if self.decommission_date else None,
            "disposal_method": self.disposal_method,
            "recycling_partner": self.recycling_partner,
            "last_maintenance": self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
            "next_maintenance": self.next_maintenance_date.isoformat() if self.next_maintenance_date else None,
            "maintenance_overdue": self.maintenance_overdue,
            "current_value": round(self.current_value, 2),
            "is_warranty_expired": self.is_warranty_expired,
            "is_lifespan_exceeded": self.is_lifespan_exceeded,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class HardwareLifecycleTracker:
    """Track hardware lifecycle, warranty, and e-waste."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.assets: dict[str, HardwareAsset] = {}
        self._seed_data()

    def _seed_data(self):
        demo_assets = [
            ("ast-001", HardwareType.SERVER, "Dell", "PowerEdge R740", "DELL-001-2023",
             date(2023, 1, 15), 8500.00, 36, 60, "DC1-R01-U01"),
            ("ast-002", HardwareType.SERVER, "Dell", "PowerEdge R740", "DELL-002-2023",
             date(2023, 3, 20), 8500.00, 36, 60, "DC1-R01-U05"),
            ("ast-003", HardwareType.SERVER, "HPE", "ProLiant DL380", "HPE-001-2022",
             date(2022, 6, 10), 9200.00, 36, 60, "DC1-R02-U10"),
            ("ast-004", HardwareType.STORAGE, "Synology", "RS3617RPxs", "SYN-001-2023",
             date(2023, 2, 1), 3500.00, 24, 48, "DC1-R03-U01"),
            ("ast-005", HardwareType.NETWORK, "Cisco", "Catalyst 9300", "CISCO-001-2022",
             date(2022, 11, 15), 6500.00, 60, 84, "DC1-R01-U40"),
            ("ast-006", HardwareType.GPU, "NVIDIA", "A100 80GB", "NVDA-001-2024",
             date(2024, 1, 10), 15000.00, 36, 48, "DC1-R01-U03"),
            ("ast-007", HardwareType.SERVER, "Supermicro", "AS-4124GO", "SUPER-001-2024",
             date(2024, 2, 20), 12000.00, 36, 60, "DC1-R02-U15"),
            ("ast-008", HardwareType.UPS, "APC", "SMT3000RM2U", "APC-001-2022",
             date(2022, 5, 1), 1800.00, 24, 36, "DC1-R00-U00"),
            ("ast-009", HardwareType.SERVER, "Dell", "PowerEdge R650", "DELL-003-2024",
             date(2024, 4, 5), 11000.00, 36, 60, "DC1-R01-U08"),
            ("ast-010", HardwareType.STORAGE, "NetApp", "AFF A250", "NETAPP-001-2023",
             date(2023, 8, 1), 45000.00, 36, 60, "DC1-R03-U05"),
        ]
        for aid, atype, mfr, model, sn, pu_date, price, wmonths, lifespan, loc in demo_assets:
            asset = HardwareAsset(aid, atype, mfr, model, sn)
            asset.purchase_date = pu_date
            asset.purchase_price = price
            asset.warranty_months = wmonths
            asset.warranty_expiry = date(pu_date.year + wmonths // 12,
                                         pu_date.month + wmonths % 12,
                                         min(pu_date.day, 28))
            asset.expected_lifespan_months = lifespan
            asset.end_of_life_date = date(pu_date.year + lifespan // 12,
                                          pu_date.month + lifespan % 12,
                                          min(pu_date.day, 28))
            asset.location = loc
            asset.owner = "infrastructure-team"
            asset.last_maintenance_date = date.today() - timedelta(days=hash(aid) % 120)
            asset.next_maintenance_date = asset.last_maintenance_date + timedelta(days=180)
            self.assets[aid] = asset

    async def initialize(self):
        logger.info("HardwareLifecycleTracker initialized with %d assets", len(self.assets))

    async def close(self):
        logger.info("HardwareLifecycleTracker closed")

    def add_asset(self, asset_type: str, manufacturer: str, model: str,
                  serial_number: str, purchase_date: str, purchase_price: float,
                  warranty_months: int = 36, lifespan_months: int = 60) -> HardwareAsset:
        asset_id = f"ast-{uuid.uuid4().hex[:8]}"
        try:
            atype = HardwareType(asset_type)
        except ValueError:
            atype = HardwareType.OTHER
        asset = HardwareAsset(asset_id, atype, manufacturer, model, serial_number)
        asset.purchase_date = date.fromisoformat(purchase_date)
        asset.purchase_price = purchase_price
        asset.warranty_months = warranty_months
        asset.warranty_expiry = date(
            asset.purchase_date.year + warranty_months // 12,
            asset.purchase_date.month + warranty_months % 12,
            min(asset.purchase_date.day, 28)
        )
        asset.expected_lifespan_months = lifespan_months
        asset.end_of_life_date = date(
            asset.purchase_date.year + lifespan_months // 12,
            asset.purchase_date.month + lifespan_months % 12,
            min(asset.purchase_date.day, 28)
        )
        self.assets[asset_id] = asset
        return asset

    def get_asset(self, asset_id: str) -> Optional[HardwareAsset]:
        return self.assets.get(asset_id)

    def list_assets(self, asset_type: Optional[str] = None,
                    status: Optional[str] = None,
                    manufacturer: Optional[str] = None) -> list[HardwareAsset]:
        result = list(self.assets.values())
        if asset_type:
            result = [a for a in result if a.asset_type.value == asset_type]
        if status:
            result = [a for a in result if a.status.value == status]
        if manufacturer:
            result = [a for a in result if a.manufacturer.lower() == manufacturer.lower()]
        return result

    def update_asset(self, asset_id: str, updates: dict) -> Optional[HardwareAsset]:
        asset = self.assets.get(asset_id)
        if not asset:
            return None
        if "location" in updates:
            asset.location = updates["location"]
        if "owner" in updates:
            asset.owner = updates["owner"]
        if "status" in updates:
            try:
                asset.status = AssetStatus(updates["status"])
            except ValueError:
                pass
        if "notes" in updates:
            asset.notes = updates["notes"]
        if "tags" in updates:
            asset.tags = updates["tags"]
        asset.updated_at = datetime.utcnow()
        return asset

    def decommission_asset(self, asset_id: str, method: str,
                           partner: Optional[str] = None) -> bool:
        asset = self.assets.get(asset_id)
        if not asset:
            return False
        asset.status = AssetStatus.DECOMMISSIONED
        asset.decommission_date = date.today()
        asset.disposal_method = method
        asset.recycling_partner = partner
        asset.updated_at = datetime.utcnow()
        return True

    def dispose_asset(self, asset_id: str) -> bool:
        asset = self.assets.get(asset_id)
        if not asset:
            return False
        asset.status = AssetStatus.DISPOSED
        asset.decommission_date = date.today()
        asset.updated_at = datetime.utcnow()
        return True

    def record_maintenance(self, asset_id: str) -> bool:
        asset = self.assets.get(asset_id)
        if not asset:
            return False
        asset.last_maintenance_date = date.today()
        asset.next_maintenance_date = date.today() + timedelta(days=asset.maintenance_interval_days)
        asset.updated_at = datetime.utcnow()
        return True

    def get_warranty_alerts(self) -> list[HardwareAsset]:
        thirty_days = date.today() + timedelta(days=30)
        return [a for a in self.assets.values()
                if a.status == AssetStatus.ACTIVE
                and not a.is_warranty_expired
                and a.warranty_expiry <= thirty_days]

    def get_eol_alerts(self) -> list[HardwareAsset]:
        ninety_days = date.today() + timedelta(days=90)
        return [a for a in self.assets.values()
                if a.status == AssetStatus.ACTIVE
                and a.end_of_life_date
                and a.end_of_life_date <= ninety_days]

    def get_lifespan_exceeded(self) -> list[HardwareAsset]:
        return [a for a in self.assets.values()
                if a.status == AssetStatus.ACTIVE and a.is_lifespan_exceeded]

    def get_maintenance_due(self) -> list[HardwareAsset]:
        seven_days = date.today() + timedelta(days=7)
        return [a for a in self.assets.values()
                if a.status == AssetStatus.ACTIVE
                and a.next_maintenance_date
                and a.next_maintenance_date <= seven_days]

    def get_statistics(self) -> dict[str, Any]:
        total = len(self.assets)
        active = sum(1 for a in self.assets.values() if a.status == AssetStatus.ACTIVE)
        decommissioned = sum(1 for a in self.assets.values() if a.status == AssetStatus.DECOMMISSIONED)
        disposed = sum(1 for a in self.assets.values() if a.status == AssetStatus.DISPOSED)
        warranty_expired = sum(1 for a in self.assets.values() if a.is_warranty_expired)
        lifespan_exceeded = sum(1 for a in self.assets.values() if a.is_lifespan_exceeded)
        total_value = sum(a.current_value for a in self.assets.values())
        total_purchase = sum(a.purchase_price for a in self.assets.values())
        return {
            "total_assets": total,
            "active_assets": active,
            "decommissioned": decommissioned,
            "disposed": disposed,
            "warranty_expired": warranty_expired,
            "lifespan_exceeded": lifespan_exceeded,
            "maintenance_overdue": sum(1 for a in self.assets.values() if a.maintenance_overdue),
            "total_purchase_value": round(total_purchase, 2),
            "total_current_value": round(total_value, 2),
            "depreciation": round(total_purchase - total_value, 2),
            "assets_by_type": {
                t.value: sum(1 for a in self.assets.values() if a.asset_type == t)
                for t in HardwareType
            },
        }

    def generate_report(self) -> dict[str, Any]:
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "statistics": self.get_statistics(),
            "warranty_expiring_soon": [a.to_dict() for a in self.get_warranty_alerts()],
            "eol_approaching": [a.to_dict() for a in self.get_eol_alerts()],
            "lifespan_exceeded": [a.to_dict() for a in self.get_lifespan_exceeded()],
            "maintenance_due": [a.to_dict() for a in self.get_maintenance_due()],
        }
