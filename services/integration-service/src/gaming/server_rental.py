"""Server Rental integration module."""
import asyncio, json, logging, time, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
logger = logging.getLogger(__name__)
class RentalStatus(Enum): ACTIVE = "active"; PENDING = "pending"; EXPIRED = "expired"; CANCELLED = "cancelled"; MAINTENANCE = "maintenance"
@dataclass
class RentalListing:
    listing_id: str; name: str; game: str; player_slots: int; price_hourly: float; price_daily: float
    region: str; ram_gb: int; cpu_cores: int; storage_gb: int; status: RentalStatus; owner: str
    rating: float; total_rentals: int; available: bool; created_at: str; tags: List[str]; description: str
    def to_dict(self) -> Dict[str, Any]: return {
        "listing_id": self.listing_id, "name": self.name, "game": self.game,
        "player_slots": self.player_slots, "price_hourly": self.price_hourly, "price_daily": self.price_daily,
        "region": self.region, "ram_gb": self.ram_gb, "cpu_cores": self.cpu_cores,
        "storage_gb": self.storage_gb, "status": self.status.value, "owner": self.owner,
        "rating": self.rating, "total_rentals": self.total_rentals, "available": self.available,
        "created_at": self.created_at, "tags": self.tags, "description": self.description,
    }
@dataclass
class RentalAgreement:
    agreement_id: str; listing_id: str; renter: str; start_time: str; end_time: Optional[str]; cost: float
    status: RentalStatus; hourly_rate: float; duration_hours: int; auto_renew: bool; notes: str
    def to_dict(self) -> Dict[str, Any]: return {
        "agreement_id": self.agreement_id, "listing_id": self.listing_id, "renter": self.renter,
        "start_time": self.start_time, "end_time": self.end_time, "cost": self.cost,
        "status": self.status.value, "hourly_rate": self.hourly_rate, "duration_hours": self.duration_hours,
        "auto_renew": self.auto_renew, "notes": self.notes,
    }
class ServerRentalMarketplace:
    def __init__(self, config: Dict[str, Any]):
        self.config = config; self.listings: Dict[str, RentalListing] = {}; self.agreements: Dict[str, RentalAgreement] = {}
        self._running = False; self._total_revenue = 0.0; self._total_rentals = 0
    async def initialize(self) -> None: self._running = True; logger.info("Server Rental Marketplace initialized")
    async def close(self) -> None: self._running = False; logger.info("Server Rental Marketplace shut down")
    async def create_listing(self, name: str, game: str = "minecraft", player_slots: int = 20, price_hourly: float = 0.99, price_daily: float = 9.99, region: str = "NA-East", ram_gb: int = 4, cpu_cores: int = 2, storage_gb: int = 20, owner: str = "admin", tags: Optional[List[str]] = None, description: str = "") -> RentalListing:
        listing = RentalListing(listing_id=f"rent-{uuid.uuid4().hex[:8]}", name=name, game=game, player_slots=player_slots, price_hourly=price_hourly, price_daily=price_daily, region=region, ram_gb=ram_gb, cpu_cores=cpu_cores, storage_gb=storage_gb, status=RentalStatus.ACTIVE, owner=owner, rating=5.0, total_rentals=0, available=True, created_at=datetime.utcnow().isoformat(), tags=tags or [], description=description)
        self.listings[listing.listing_id] = listing; return listing
    async def rent_server(self, listing_id: str, renter: str, duration_hours: int = 1, auto_renew: bool = False) -> RentalAgreement:
        listing = self.listings.get(listing_id)
        if not listing: raise ValueError(f"Listing '{listing_id}' not found")
        if not listing.available: raise ValueError("Server not available")
        cost = listing.price_hourly * duration_hours
        agreement = RentalAgreement(agreement_id=f"agree-{uuid.uuid4().hex[:8]}", listing_id=listing_id, renter=renter, start_time=datetime.utcnow().isoformat(), end_time=(datetime.utcnow() + timedelta(hours=duration_hours)).isoformat(), cost=cost, status=RentalStatus.ACTIVE, hourly_rate=listing.price_hourly, duration_hours=duration_hours, auto_renew=auto_renew, notes="")
        self.agreements[agreement.agreement_id] = agreement
        listing.total_rentals += 1; listing.available = False; self._total_rentals += 1; self._total_revenue += cost
        return agreement
    async def end_rental(self, agreement_id: str) -> bool:
        a = self.agreements.get(agreement_id)
        if not a: return False
        a.status = RentalStatus.EXPIRED; a.end_time = datetime.utcnow().isoformat()
        listing = self.listings.get(a.listing_id)
        if listing: listing.available = True
        return True
    async def list_available(self, game: Optional[str] = None, region: Optional[str] = None) -> List[Dict[str, Any]]:
        results = [l for l in self.listings.values() if l.available]
        if game: results = [r for r in results if r.game == game]
        if region: results = [r for r in results if r.region == region]
        return [r.to_dict() for r in results]
    async def get_stats(self) -> Dict[str, Any]:
        return {"total_listings": len(self.listings), "available": sum(1 for l in self.listings.values() if l.available), "active_rentals": sum(1 for a in self.agreements.values() if a.status == RentalStatus.ACTIVE), "total_revenue": round(self._total_revenue, 2), "total_rentals": self._total_rentals, "avg_rating": round(sum(l.rating for l in self.listings.values()) / max(len(self.listings), 1), 1)}
    async def health_check(self) -> Dict[str, Any]: return {"status": "healthy" if self._running else "unhealthy", "listings": len(self.listings)}
