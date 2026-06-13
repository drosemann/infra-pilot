import json
import logging
import os
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class ResourceListing:
    id: str
    seller_id: str
    resource_type: str
    quantity: int
    unit: str
    price_per_unit_hour: float
    total_available: int
    available_now: int
    location: str
    provider: str
    server_id: str
    min_duration_hours: int
    max_duration_hours: int
    status: str
    tags: List[str]
    description: str
    created_at: str
    expires_at: str

@dataclass
class TradeOrder:
    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    quantity: int
    duration_hours: int
    total_price: float
    status: str
    escrow_status: str
    dispute_reason: str
    dispute_evidence: str
    created_at: str
    completed_at: str

@dataclass
class ReputationScore:
    user_id: str
    overall_score: float
    total_trades: int
    completed_trades: int
    cancelled_trades: int
    disputed_trades: int
    response_time_avg: int
    fulfillment_rate: float
    recent_reviews: List[Dict[str, Any]]

class ResourceTradingManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.listings_file = os.path.join(self.data_path, 'trading_listings.json')
        self.orders_file = os.path.join(self.data_path, 'trading_orders.json')
        self.reputation_file = os.path.join(self.data_path, 'trading_reputation.json')
        self.listings: Dict[str, ResourceListing] = {}
        self.orders: Dict[str, TradeOrder] = {}
        self.reputations: Dict[str, ReputationScore] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.listings_file, 'listings', ResourceListing),
            (self.orders_file, 'orders', TradeOrder),
        ]:
            try:
                if os.path.exists(file_key):
                    with open(file_key, 'r') as f:
                        data = json.load(f)
                    storage = getattr(self, attr)
                    storage.clear()
                    for item in data:
                        storage[item['id']] = cls(**item)
            except Exception as e:
                logger.warning(f"Failed to load {attr}: {e}")
        try:
            if os.path.exists(self.reputation_file):
                with open(self.reputation_file, 'r') as f:
                    raw = json.load(f)
                for item in raw:
                    rep = ReputationScore(**item)
                    self.reputations[rep.user_id] = rep
        except Exception as e:
            logger.warning(f"Failed to load reputations: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.listings_file, 'listings'),
            (self.orders_file, 'orders'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")
        try:
            with open(self.reputation_file, 'w') as f:
                json.dump([asdict(v) for v in self.reputations.values()], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save reputations: {e}")

    async def initialize(self):
        logger.info("ResourceTradingManager initialized")

    async def close(self):
        self._save_data()

    async def search_listings(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = [l for l in self.listings.values() if l.status == 'active']
        if query:
            if 'resource_type' in query:
                results = [r for r in results if r.resource_type == query['resource_type']]
            if 'min_quantity' in query:
                results = [r for r in results if r.available_now >= query['min_quantity']]
            if 'max_price' in query:
                results = [r for r in results if r.price_per_unit_hour <= query['max_price']]
            if 'location' in query:
                results = [r for r in results if query['location'].lower() in r.location.lower()]
            if 'tags' in query:
                query_tags = set(t.lower() for t in query['tags'])
                results = [r for r in results if query_tags & set(t.lower() for t in r.tags)]
        results.sort(key=lambda r: r.price_per_unit_hour)
        return [asdict(r) for r in results]

    async def create_listing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        listing_id = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(days=data.get('duration_days', 7))
        listing = ResourceListing(
            id=listing_id,
            seller_id=data['seller_id'],
            resource_type=data['resource_type'],
            quantity=data['quantity'],
            unit=data.get('unit', 'unit'),
            price_per_unit_hour=data['price_per_unit_hour'],
            total_available=data['quantity'],
            available_now=data['quantity'],
            location=data.get('location', 'Any'),
            provider=data.get('provider', ''),
            server_id=data.get('server_id', ''),
            min_duration_hours=data.get('min_duration_hours', 1),
            max_duration_hours=data.get('max_duration_hours', 720),
            status=data.get('status', 'active'),
            tags=data.get('tags', []),
            description=data.get('description', ''),
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )
        self.listings[listing.id] = listing
        self._save_data()
        return asdict(listing)

    async def update_listing(self, listing_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        listing = self.listings.get(listing_id)
        if not listing:
            return None
        for key in ['price_per_unit_hour', 'available_now', 'status', 'tags', 'description', 'min_duration_hours', 'max_duration_hours']:
            if key in data:
                setattr(listing, key, data[key])
        self._save_data()
        return asdict(listing)

    async def delete_listing(self, listing_id: str) -> bool:
        if listing_id in self.listings:
            self.listings[listing_id].status = 'cancelled'
            self._save_data()
            return True
        return False

    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        listing = self.listings.get(listing_id)
        return asdict(listing) if listing else None

    async def create_order(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        listing = self.listings.get(data['listing_id'])
        if not listing or listing.status != 'active':
            return None
        quantity = data.get('quantity', 1)
        if quantity > listing.available_now:
            return None
        duration = data.get('duration_hours', 1)
        if duration < listing.min_duration_hours or duration > listing.max_duration_hours:
            return None
        total_price = quantity * listing.price_per_unit_hour * duration
        order = TradeOrder(
            id=str(uuid.uuid4()),
            listing_id=data['listing_id'],
            buyer_id=data['buyer_id'],
            seller_id=listing.seller_id,
            quantity=quantity,
            duration_hours=duration,
            total_price=round(total_price, 6),
            status='pending',
            escrow_status='funded',
            dispute_reason='',
            dispute_evidence='',
            created_at=datetime.now().isoformat(),
            completed_at='',
        )
        self.orders[order.id] = order
        listing.available_now -= quantity
        self._save_data()
        return asdict(order)

    async def get_orders(self, user_id: str) -> List[Dict[str, Any]]:
        user_orders = [o for o in self.orders.values() if o.buyer_id == user_id or o.seller_id == user_id]
        return [asdict(o) for o in sorted(user_orders, key=lambda x: x.created_at, reverse=True)]

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)
        return asdict(order) if order else None

    async def fulfill_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)
        if not order or order.status != 'pending':
            return None
        order.status = 'active'
        self._save_data()
        return asdict(order)

    async def dispute_order(self, order_id: str, reason: str, evidence: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)
        if not order:
            return None
        order.status = 'dispute'
        order.dispute_reason = reason
        order.dispute_evidence = evidence
        order.escrow_status = 'held'
        self._save_data()
        return asdict(order)

    async def complete_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)
        if not order:
            return None
        order.status = 'completed'
        order.completed_at = datetime.now().isoformat()
        order.escrow_status = 'released'
        await self._update_reputation(order.seller_id, True)
        await self._update_reputation(order.buyer_id, True)
        self._save_data()
        return asdict(order)

    async def _update_reputation(self, user_id: str, successful: bool):
        rep = self.reputations.get(user_id)
        if not rep:
            rep = ReputationScore(user_id=user_id, overall_score=5.0, total_trades=0, completed_trades=0, cancelled_trades=0, disputed_trades=0, response_time_avg=0, fulfillment_rate=1.0, recent_reviews=[])
            self.reputations[user_id] = rep
        rep.total_trades += 1
        if successful:
            rep.completed_trades += 1
        else:
            rep.cancelled_trades += 1
        rep.fulfillment_rate = rep.completed_trades / max(rep.total_trades, 1)
        rep.overall_score = round(1 + (rep.fulfillment_rate * 4), 1)

    async def get_reputation(self, user_id: str) -> Dict[str, Any]:
        rep = self.reputations.get(user_id)
        if not rep:
            return {'user_id': user_id, 'overall_score': 5.0, 'total_trades': 0, 'completed_trades': 0, 'fulfillment_rate': 1.0}
        return asdict(rep)

    async def get_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        txns = []
        for order in self.orders.values():
            if order.buyer_id == user_id or order.seller_id == user_id:
                txns.append({
                    'order_id': order.id,
                    'type': 'purchase' if order.buyer_id == user_id else 'sale',
                    'counterparty': order.seller_id if order.buyer_id == user_id else order.buyer_id,
                    'amount': order.total_price,
                    'status': order.status,
                    'timestamp': order.created_at,
                })
        return sorted(txns, key=lambda t: t['timestamp'], reverse=True)

    async def get_pricing_suggestions(self, resource_type: str) -> Dict[str, Any]:
        active = [l for l in self.listings.values() if l.resource_type == resource_type and l.status == 'active']
        if not active:
            return {'resource_type': resource_type, 'average_price': 0.05, 'price_range': [0.01, 0.10], 'suggested_price': 0.03}
        prices = [l.price_per_unit_hour for l in active]
        avg = sum(prices) / len(prices)
        sorted_prices = sorted(prices)
        return {
            'resource_type': resource_type,
            'active_listings': len(active),
            'average_price': round(avg, 6),
            'min_price': round(min(prices), 6),
            'max_price': round(max(prices), 6),
            'median_price': round(sorted_prices[len(sorted_prices)//2], 6),
            'suggested_price': round(avg * 0.95, 6),
        }
