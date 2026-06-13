import json
import logging
import os
import uuid
import math
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

CRYPTO_CURRENCIES = ['BTC', 'ETH', 'SOL', 'USDC_ETH', 'USDC_SOL']

@dataclass
class CryptoWallet:
    id: str
    user_id: str
    currency: str
    address: str
    address_type: str
    label: str
    is_default: bool
    balance_confirmed: float
    balance_unconfirmed: float
    total_received: float
    total_sent: float
    created_at: str

@dataclass
class CryptoInvoice:
    id: str
    user_id: str
    fiat_amount: float
    fiat_currency: str
    crypto_amount: float
    crypto_currency: str
    wallet_address: str
    payment_uri: str
    status: str
    required_confirmations: int
    current_confirmations: int
    tx_hash: str
    block_number: int
    created_at: str
    expires_at: str
    paid_at: str

@dataclass
class CryptoTransaction:
    id: str
    invoice_id: str
    currency: str
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    fee: float
    confirmations: int
    status: str
    block_number: int
    block_timestamp: str
    explorer_url: str

class CryptoPaymentManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.wallets_file = os.path.join(self.data_path, 'crypto_wallets.json')
        self.invoices_file = os.path.join(self.data_path, 'crypto_invoices.json')
        self.transactions_file = os.path.join(self.data_path, 'crypto_transactions.json')
        self.wallets: Dict[str, CryptoWallet] = {}
        self.invoices: Dict[str, CryptoInvoice] = {}
        self.transactions: Dict[str, CryptoTransaction] = {}
        self._rates_cache: Dict[str, float] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.wallets_file, 'wallets', CryptoWallet),
            (self.invoices_file, 'invoices', CryptoInvoice),
            (self.transactions_file, 'transactions', CryptoTransaction),
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
            (self.wallets_file, 'wallets'),
            (self.invoices_file, 'invoices'),
            (self.transactions_file, 'transactions'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("CryptoPaymentManager initialized")

    async def close(self):
        self._save_data()

    def _generate_address(self, currency: str) -> tuple:
        raw = hashlib.sha256(f"{currency}-{uuid.uuid4()}-{datetime.now().isoformat()}".encode()).digest()
        if currency == 'BTC':
            addr = f"1{hashlib.sha256(raw).hexdigest()[:33]}"
            return addr, 'p2pkh'
        elif currency == 'ETH':
            addr = f"0x{hashlib.sha256(raw).hexdigest()[:40]}"
            return addr, 'eoa'
        elif currency == 'SOL':
            addr = hashlib.sha256(raw).hexdigest()[:44]
            return addr, 'ed25519'
        elif currency in ('USDC_ETH', 'USDC_SOL'):
            addr = f"0x{hashlib.sha256(raw).hexdigest()[:40]}"
            return addr, 'eoa'
        return hashlib.sha256(raw).hexdigest()[:34], 'p2pkh'

    def _get_explorer_url(self, currency: str, tx_hash: str) -> str:
        explorers = {
            'BTC': f'https://blockstream.info/tx/{tx_hash}',
            'ETH': f'https://etherscan.io/tx/{tx_hash}',
            'SOL': f'https://solscan.io/tx/{tx_hash}',
            'USDC_ETH': f'https://etherscan.io/tx/{tx_hash}',
            'USDC_SOL': f'https://solscan.io/tx/{tx_hash}',
        }
        return explorers.get(currency, '')

    def _get_rate(self, currency: str) -> float:
        rates = {
            'BTC': 67500.0, 'ETH': 3450.0, 'SOL': 145.0,
            'USDC_ETH': 1.0, 'USDC_SOL': 1.0,
        }
        return rates.get(currency, 1.0)

    async def list_wallets(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(w) for w in self.wallets.values() if w.user_id == user_id]

    async def create_wallet(self, data: Dict[str, Any]) -> Dict[str, Any]:
        currency = data['currency']
        if currency not in CRYPTO_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}. Supported: {CRYPTO_CURRENCIES}")
        wallet_id = str(uuid.uuid4())
        addr, addr_type = self._generate_address(currency)
        wallet = CryptoWallet(
            id=wallet_id, user_id=data.get('user_id', ''),
            currency=currency, address=addr, address_type=addr_type,
            label=data.get('label', f'{currency} Wallet'),
            is_default=data.get('is_default', False),
            balance_confirmed=0.0, balance_unconfirmed=0.0,
            total_received=0.0, total_sent=0.0,
            created_at=datetime.now().isoformat(),
        )
        self.wallets[wallet.id] = wallet
        self._save_data()
        return asdict(wallet)

    async def get_wallet_balance(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        wallet = self.wallets.get(wallet_id)
        if not wallet:
            return None
        return {
            'wallet_id': wallet_id,
            'address': wallet.address,
            'currency': wallet.currency,
            'confirmed': wallet.balance_confirmed,
            'unconfirmed': wallet.balance_unconfirmed,
            'total_received': wallet.total_received,
            'total_sent': wallet.total_sent,
            'usd_value': round((wallet.balance_confirmed + wallet.balance_unconfirmed) * self._get_rate(wallet.currency), 2),
        }

    async def get_rates(self) -> Dict[str, float]:
        return self._rates_cache if self._rates_cache else {c: self._get_rate(c) for c in CRYPTO_CURRENCIES}

    async def create_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        fiat_amount = data['amount']
        fiat_currency = data.get('currency', 'USD')
        crypto_currency = data.get('crypto_currency', 'BTC')
        if crypto_currency not in CRYPTO_CURRENCIES:
            raise ValueError(f"Unsupported crypto currency: {crypto_currency}")
        rate = self._get_rate(crypto_currency)
        crypto_amount = fiat_amount / rate if rate > 0 else 0
        user_wallets = [w for w in self.wallets.values() if w.user_id == data.get('user_id', '') and w.currency == crypto_currency]
        wallet = user_wallets[0] if user_wallets else None
        if not wallet:
            wallet_data = await self.create_wallet({'user_id': data.get('user_id', ''), 'currency': crypto_currency, 'label': f'Invoice Wallet {crypto_currency}', 'is_default': True})
            wallet_data_obj = CryptoWallet(**wallet_data)
            self.wallets[wallet_data_obj.id] = wallet_data_obj
            wallet = wallet_data_obj
        invoice_id = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(hours=1)
        payment_uri = ''
        if crypto_currency == 'BTC':
            payment_uri = f'bitcoin:{wallet.address}?amount={crypto_amount:.8f}'
        elif crypto_currency in ('ETH', 'USDC_ETH'):
            payment_uri = f'ethereum:{wallet.address}?value={int(crypto_amount * 1e18)}'
        elif crypto_currency == 'SOL':
            payment_uri = f'solana:{wallet.address}?amount={crypto_amount:.9f}'
        invoice = CryptoInvoice(
            id=invoice_id, user_id=data.get('user_id', ''),
            fiat_amount=fiat_amount, fiat_currency=fiat_currency,
            crypto_amount=round(crypto_amount, 8), crypto_currency=crypto_currency,
            wallet_address=wallet.address, payment_uri=payment_uri,
            status='pending', required_confirmations=2, current_confirmations=0,
            tx_hash='', block_number=0, created_at=now.isoformat(),
            expires_at=expires.isoformat(), paid_at='',
        )
        self.invoices[invoice.id] = invoice
        self._save_data()
        return asdict(invoice)

    async def list_invoices(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(i) for i in self.invoices.values() if i.user_id == user_id]

    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        invoice = self.invoices.get(invoice_id)
        return asdict(invoice) if invoice else None

    async def verify_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        tx = self.transactions.get(transaction_id)
        if not tx:
            return None
        tx.confirmations += 1
        if tx.confirmations >= 3:
            tx.status = 'confirmed'
            invoice = self.invoices.get(tx.invoice_id)
            if invoice:
                invoice.current_confirmations = tx.confirmations
                if invoice.status == 'pending' and tx.confirmations >= invoice.required_confirmations:
                    invoice.status = 'confirmed'
                    invoice.paid_at = datetime.now().isoformat()
                    wallet = next((w for w in self.wallets.values() if w.address == tx.to_address), None)
                    if wallet:
                        wallet.balance_confirmed += tx.amount
                        wallet.total_received += tx.amount
        self._save_data()
        return asdict(tx)

    async def get_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        user_invoices = [i.id for i in self.invoices.values() if i.user_id == user_id]
        return [asdict(t) for t in self.transactions.values() if t.invoice_id in user_invoices]

    async def simulate_payment(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            return None
        import hashlib as hl, random
        tx_hash = hl.sha256(f"{invoice_id}-{random.random()}".encode()).hexdigest()
        tx = CryptoTransaction(
            id=str(uuid.uuid4()), invoice_id=invoice_id,
            currency=invoice.crypto_currency, tx_hash=tx_hash,
            from_address=self._generate_address(invoice.crypto_currency)[0],
            to_address=invoice.wallet_address, amount=invoice.crypto_amount,
            fee=invoice.crypto_amount * 0.001, confirmations=1,
            status='pending', block_number=random.randint(1000000, 9999999),
            block_timestamp=datetime.now().isoformat(),
            explorer_url=self._get_explorer_url(invoice.crypto_currency, tx_hash),
        )
        self.transactions[tx.id] = tx
        invoice.tx_hash = tx_hash
        self._save_data()
        result = await self.verify_transaction(tx.id)
        return result
