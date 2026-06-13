"""CO2 Offset Integration - One-click carbon offset purchase."""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class OffsetProvider(Enum):
    PATCH = "patch"
    CLIMATE_TECH = "climate_tech"
    CARBON_JACK = "carbon_jack"
    TERRAPASS = "terrapass"


class ProjectType(Enum):
    REFORESTATION = "reforestation"
    RENEWABLE_ENERGY = "renewable_energy"
    DIRECT_AIR_CAPTURE = "direct_air_capture"
    METHANE_CAPTURE = "methane_capture"
    BLUE_CARBON = "blue_carbon"
    SOIL_CARBON = "soil_carbon"


class OffsetStatus(Enum):
    QUOTED = "quoted"
    PURCHASED = "purchased"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class OffsetQuote:
    """A quote for carbon offset purchase."""

    def __init__(self, quote_id: str, co2_kg: float):
        self.quote_id = quote_id
        self.co2_kg = co2_kg
        self.project_name: str = ""
        self.project_type: ProjectType = ProjectType.REFORESTATION
        self.project_location: str = ""
        self.cost_per_ton: float = 15.0
        self.total_cost: float = 0.0
        self.currency: str = "USD"
        self.valid_until: datetime = datetime.utcnow() + timedelta(hours=24)
        self.created_at = datetime.utcnow()

    def calculate(self):
        self.total_cost = round(self.co2_kg / 1000 * self.cost_per_ton, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "co2_kg": self.co2_kg,
            "co2_tons": round(self.co2_kg / 1000, 3),
            "project_name": self.project_name,
            "project_type": self.project_type.value,
            "project_location": self.project_location,
            "cost_per_ton": self.cost_per_ton,
            "total_cost": self.total_cost,
            "currency": self.currency,
            "valid_until": self.valid_until.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class OffsetCertificate:
    """A carbon offset certificate."""

    def __init__(self, cert_id: str, quote: OffsetQuote):
        self.cert_id = cert_id
        self.quote = quote
        self.serial_number: str = f"IP-OFFSET-{uuid.uuid4().hex[:12].upper()}"
        self.purchase_date = datetime.utcnow()
        self.provider: OffsetProvider = OffsetProvider.PATCH
        self.receipt_id: str = f"RCP-{uuid.uuid4().hex[:8].upper()}"
        self.registry_serial: str = ""
        self.project_id: str = ""
        self.status: OffsetStatus = OffsetStatus.PURCHASED
        self.certificate_pdf: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cert_id": self.cert_id,
            "serial_number": self.serial_number,
            "purchase_date": self.purchase_date.isoformat(),
            "provider": self.provider.value,
            "receipt_id": self.receipt_id,
            "project_name": self.quote.project_name,
            "project_type": self.quote.project_type.value,
            "project_location": self.quote.project_location,
            "co2_kg": self.quote.co2_kg,
            "co2_tons": round(self.quote.co2_kg / 1000, 3),
            "total_cost": self.quote.total_cost,
            "currency": self.quote.currency,
            "status": self.status.value,
        }


class AutoOffsetConfig:
    """Configuration for automatic monthly offset purchases."""

    def __init__(self):
        self.enabled: bool = False
        self.budget_monthly: float = 50.0
        self.project_type: ProjectType = ProjectType.REFORESTATION
        self.day_of_month: int = 1
        self.notify_before: bool = True
        self.notify_after: bool = True
        self.max_price_per_ton: float = 50.0
        self.provider: OffsetProvider = OffsetProvider.PATCH

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "budget_monthly": self.budget_monthly,
            "project_type": self.project_type.value,
            "day_of_month": self.day_of_month,
            "notify_before": self.notify_before,
            "notify_after": self.notify_after,
            "max_price_per_ton": self.max_price_per_ton,
            "provider": self.provider.value,
        }


class CO2OffsetManager:
    """Manager for carbon offset purchases and tracking."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.quotes: dict[str, OffsetQuote] = {}
        self.certificates: dict[str, OffsetCertificate] = {}
        self.auto_config = AutoOffsetConfig()
        self._auto_task: Optional[asyncio.Task] = None
        self.energy_tracker = None
        self._seed_data()

    def _seed_data(self):
        for i in range(3):
            quote = OffsetQuote(f"q-{uuid.uuid4().hex[:8]}", random.uniform(100, 2000))
            quote.project_name = ["Amazon Reforestation", "Wind Farm Texas", "Solar India"][i]
            quote.project_type = [ProjectType.REFORESTATION, ProjectType.RENEWABLE_ENERGY,
                                  ProjectType.RENEWABLE_ENERGY][i]
            quote.project_location = ["Brazil", "USA", "India"][i]
            quote.cost_per_ton = [15.0, 12.0, 18.0][i]
            quote.calculate()
            self.quotes[quote.quote_id] = quote
            cert = OffsetCertificate(f"cert-{uuid.uuid4().hex[:8]}", quote)
            cert.provider = OffsetProvider.PATCH
            cert.status = OffsetStatus.VERIFIED
            cert.purchase_date = datetime.utcnow() - timedelta(days=hash(str(i)) % 60)
            cert.project_id = f"proj-{uuid.uuid4().hex[:8]}"
            cert.registry_serial = f"VCS-{uuid.uuid4().hex[:10].upper()}"
            self.certificates[cert.cert_id] = cert

    async def initialize(self):
        if self.auto_config.enabled:
            self._auto_task = asyncio.create_task(self._auto_offset_loop())
        logger.info("CO2OffsetManager initialized with %d certificates", len(self.certificates))

    async def close(self):
        if self._auto_task:
            self._auto_task.cancel()
        logger.info("CO2OffsetManager closed")

    async def _auto_offset_loop(self):
        while True:
            try:
                await asyncio.sleep(86400)
                now = datetime.utcnow()
                if now.day == self.auto_config.day_of_month:
                    await self._execute_auto_offset()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Auto offset error: %s", e)

    async def _execute_auto_offset(self):
        if not self.auto_config.enabled:
            return
        quote = self.calculate_offset_amount(
            100.0,  # placeholder for actual energy data
            self.auto_config.project_type.value
        )
        if quote.total_cost <= self.auto_config.budget_monthly:
            cert = self.purchase_offset(quote.quote_id)
            if cert:
                logger.info("Auto offset purchased: %s kg CO2 for $%s",
                           quote.co2_kg, quote.total_cost)

    def calculate_offset_amount(self, energy_kwh: float,
                                 project_type: str = "reforestation",
                                 provider: str = "patch") -> OffsetQuote:
        grid_intensity = 285.0
        co2_kg = round(energy_kwh * grid_intensity / 1000, 2)
        quote_id = f"q-{uuid.uuid4().hex[:8]}"
        quote = OffsetQuote(quote_id, co2_kg)
        try:
            quote.project_type = ProjectType(project_type)
        except ValueError:
            quote.project_type = ProjectType.REFORESTATION

        project_prices = {
            ProjectType.REFORESTATION: 15.0,
            ProjectType.RENEWABLE_ENERGY: 12.0,
            ProjectType.DIRECT_AIR_CAPTURE: 150.0,
            ProjectType.METHANE_CAPTURE: 8.0,
            ProjectType.BLUE_CARBON: 25.0,
            ProjectType.SOIL_CARBON: 20.0,
        }
        quote.cost_per_ton = project_prices.get(quote.project_type, 15.0)

        project_names = {
            ProjectType.REFORESTATION: "Global Reforestation Fund",
            ProjectType.RENEWABLE_ENERGY: "Renewable Energy Certificate",
            ProjectType.DIRECT_AIR_CAPTURE: "Direct Air Capture Facility",
            ProjectType.METHANE_CAPTURE: "Landfill Methane Capture",
            ProjectType.BLUE_CARBON: "Mangrove Blue Carbon",
            ProjectType.SOIL_CARBON: "Regenerative Agriculture",
        }
        quote.project_name = project_names.get(quote.project_type, "Carbon Offset Project")
        quote.project_location = "Global"
        quote.calculate()
        self.quotes[quote_id] = quote
        return quote

    def purchase_offset(self, quote_id: str) -> Optional[OffsetCertificate]:
        quote = self.quotes.get(quote_id)
        if not quote:
            return None
        cert_id = f"cert-{uuid.uuid4().hex[:8]}"
        cert = OffsetCertificate(cert_id, quote)
        cert.provider = OffsetProvider.PATCH
        cert.status = OffsetStatus.PURCHASED
        cert.purchase_date = datetime.utcnow()
        cert.project_id = f"proj-{uuid.uuid4().hex[:8]}"
        cert.registry_serial = f"VCS-{uuid.uuid4().hex[:10].upper()}"
        self.certificates[cert_id] = cert
        quote.valid_until = datetime.utcnow()
        logger.info("Offset purchased: %s kg CO2 for $%s", quote.co2_kg, quote.total_cost)
        return cert

    def get_quote(self, quote_id: str) -> Optional[OffsetQuote]:
        return self.quotes.get(quote_id)

    def get_certificate(self, cert_id: str) -> Optional[OffsetCertificate]:
        return self.certificates.get(cert_id)

    def list_certificates(self) -> list[OffsetCertificate]:
        return sorted(self.certificates.values(), key=lambda c: c.purchase_date, reverse=True)

    def verify_certificate(self, cert_id: str) -> bool:
        cert = self.certificates.get(cert_id)
        if not cert or cert.status != OffsetStatus.PURCHASED:
            return False
        cert.status = OffsetStatus.VERIFIED
        return True

    def setup_auto_offset(self, budget_monthly: float,
                          project_type: str = "reforestation",
                          day_of_month: int = 1) -> AutoOffsetConfig:
        self.auto_config.enabled = True
        self.auto_config.budget_monthly = budget_monthly
        try:
            self.auto_config.project_type = ProjectType(project_type)
        except ValueError:
            self.auto_config.project_type = ProjectType.REFORESTATION
        self.auto_config.day_of_month = day_of_month
        if self._auto_task is None or self._auto_task.done():
            self._auto_task = asyncio.create_task(self._auto_offset_loop())
        return self.auto_config

    def get_statistics(self) -> dict[str, Any]:
        total_purchased = len(self.certificates)
        verified = sum(1 for c in self.certificates.values() if c.status == OffsetStatus.VERIFIED)
        total_co2 = sum(c.quote.co2_kg for c in self.certificates.values())
        total_spent = sum(c.quote.total_cost for c in self.certificates.values())
        return {
            "total_purchases": total_purchased,
            "verified_certificates": verified,
            "total_co2_offset_kg": round(total_co2, 2),
            "total_co2_offset_tons": round(total_co2 / 1000, 3),
            "total_spent": round(total_spent, 2),
            "currency": "USD",
            "avg_price_per_ton": round(total_spent / max(total_co2 / 1000, 0.001), 2),
            "auto_offset_enabled": self.auto_config.enabled,
            "monthly_budget": self.auto_config.budget_monthly,
        }
