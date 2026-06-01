import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class Reseller:
    id: str
    name: str
    email: str
    status: str
    custom_domain: str
    panel_branding: Dict[str, Any]
    base_margin_pct: float
    commission_tier: str
    total_customers: int
    total_revenue: float
    lifetime_value: float
    api_key: str
    created_at: str

@dataclass
class ResellerProduct:
    id: str
    reseller_id: str
    product_name: str
    base_price: float
    margin_pct: float
    final_price: float
    product_type: str
    min_commitment: int
    max_qty: int

@dataclass
class SubAdmin:
    id: str
    reseller_id: str
    email: str
    name: str
    role: str
    permissions: List[str]
    status: str
    created_at: str
    last_login: str

class ResellerManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.resellers_file = os.path.join(self.data_path, 'resellers.json')
        self.products_file = os.path.join(self.data_path, 'reseller_products.json')
        self.subadmins_file = os.path.join(self.data_path, 'reseller_subadmins.json')
        self.resellers: Dict[str, Reseller] = {}
        self.products: Dict[str, ResellerProduct] = {}
        self.subadmins: Dict[str, SubAdmin] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.resellers_file, 'resellers', Reseller),
            (self.products_file, 'products', ResellerProduct),
            (self.subadmins_file, 'subadmins', SubAdmin),
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

    def _save_data(self):
        for file_key, attr in [
            (self.resellers_file, 'resellers'),
            (self.products_file, 'products'),
            (self.subadmins_file, 'subadmins'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("ResellerManager initialized")

    async def close(self):
        self._save_data()

    async def list_resellers(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.resellers.values()]

    async def create_reseller(self, data: Dict[str, Any]) -> Dict[str, Any]:
        reseller_id = str(uuid.uuid4())
        import hashlib
        api_key = hashlib.sha256(f"{reseller_id}-{data['email']}-{datetime.now().isoformat()}".encode()).hexdigest()[:32]
        now = datetime.now()
        reseller = Reseller(
            id=reseller_id, name=data['name'], email=data['email'],
            status='active',
            custom_domain=data.get('custom_domain', ''),
            panel_branding=data.get('branding', {'logo': '', 'primary_color': '#6366f1', 'accent_color': '#8b5cf6', 'custom_css': ''}),
            base_margin_pct=data.get('base_margin_pct', 15.0),
            commission_tier='bronze',
            total_customers=0, total_revenue=0.0, lifetime_value=0.0,
            api_key=api_key, created_at=now.isoformat(),
        )
        self.resellers[reseller.id] = reseller
        self._save_data()
        return asdict(reseller)

    async def get_reseller(self, reseller_id: str) -> Optional[Dict[str, Any]]:
        reseller = self.resellers.get(reseller_id)
        return asdict(reseller) if reseller else None

    async def update_reseller(self, reseller_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reseller = self.resellers.get(reseller_id)
        if not reseller:
            return None
        for key in ['name', 'email', 'status', 'custom_domain', 'panel_branding', 'base_margin_pct']:
            if key in data:
                setattr(reseller, key, data[key])
        self._save_data()
        return asdict(reseller)

    async def get_customers(self, reseller_id: str) -> List[Dict[str, Any]]:
        return [{'id': str(uuid.uuid4()), 'email': f'customer{i}@example.com', 'name': f'Customer {i}', 'plan': 'starter', 'status': 'active', 'created_at': (datetime.now() - timedelta(days=i*30)).isoformat(), 'total_spent': round(100 + i * 25, 2)} for i in range(1, 6)]

    async def get_revenue(self, reseller_id: str) -> Dict[str, Any]:
        reseller = self.resellers.get(reseller_id)
        if not reseller:
            return {}
        return {
            'reseller_id': reseller_id,
            'total_revenue': reseller.total_revenue,
            'monthly_recurring': reseller.total_revenue / max((datetime.now() - datetime.fromisoformat(reseller.created_at)).days / 30, 1),
            'commission_tier': reseller.commission_tier,
            'base_margin_pct': reseller.base_margin_pct,
            'total_customers': reseller.total_customers,
            'lifetime_value': reseller.lifetime_value,
            'estimated_payout': round(reseller.total_revenue * reseller.base_margin_pct / 100, 2),
        }

    async def update_branding(self, reseller_id: str, branding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reseller = self.resellers.get(reseller_id)
        if not reseller:
            return None
        current = reseller.panel_branding.copy() if isinstance(reseller.panel_branding, dict) else {}
        current.update(branding)
        reseller.panel_branding = current
        self._save_data()
        return asdict(reseller)

    async def update_margins(self, reseller_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reseller = self.resellers.get(reseller_id)
        if not reseller:
            return None
        if 'base_margin_pct' in data:
            reseller.base_margin_pct = data['base_margin_pct']
        if 'product_margins' in data:
            for pm in data['product_margins']:
                product = next((p for p in self.products.values() if p.reseller_id == reseller_id and p.product_name == pm.get('product_name', '')), None)
                if product:
                    product.margin_pct = pm.get('margin_pct', product.margin_pct)
                    product.final_price = round(product.base_price * (1 + product.margin_pct / 100), 6)
        self._save_data()
        return asdict(reseller)

    async def create_sub_admin(self, reseller_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reseller = self.resellers.get(reseller_id)
        if not reseller:
            return None
        admin_id = str(uuid.uuid4())
        admin = SubAdmin(
            id=admin_id, reseller_id=reseller_id, email=data['email'],
            name=data.get('name', ''), role=data.get('role', 'admin'),
            permissions=data.get('permissions', ['customers.view', 'services.view']),
            status='active', created_at=datetime.now().isoformat(), last_login='',
        )
        self.subadmins[admin.id] = admin
        self._save_data()
        return asdict(admin)

    async def list_sub_admins(self, reseller_id: str) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self.subadmins.values() if a.reseller_id == reseller_id]

    async def remove_sub_admin(self, reseller_id: str, admin_id: str) -> bool:
        admin = self.subadmins.get(admin_id)
        if not admin or admin.reseller_id != reseller_id:
            return False
        del self.subadmins[admin_id]
        self._save_data()
        return True

    async def get_products(self, reseller_id: str) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.products.values() if p.reseller_id == reseller_id]
