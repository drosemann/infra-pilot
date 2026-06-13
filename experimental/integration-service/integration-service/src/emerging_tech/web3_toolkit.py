"""Web3 Developer Toolkit — blockchain explorer, transaction builder, faucet manager."""

import asyncio
import aiofiles
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NetworkType(Enum):
    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"
    LOCAL = "local"


class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"
    DROPPED = "dropped"


class FaucetStatus(Enum):
    ACTIVE = "active"
    DEPLETED = "depleted"
    PAUSED = "paused"


class BlockExplorer:
    def __init__(self, explorer_id: str, name: str, network: str):
        self.explorer_id = explorer_id
        self.name = name
        self.network = network
        self.base_url = ""
        self.api_url = ""
        self.chain_id = 1
        self.network_type = NetworkType.MAINNET
        self.supported_modules: list[str] = ["blocks", "transactions", "accounts", "tokens", "contracts"]
        self.block_count = 0
        self.last_scanned_block = 0
        self.sync_status = "synced"
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "explorer_id": self.explorer_id, "name": self.name, "network": self.network,
            "base_url": self.base_url, "api_url": self.api_url, "chain_id": self.chain_id,
            "network_type": self.network_type.value,
            "supported_modules": self.supported_modules,
            "block_count": self.block_count, "last_scanned_block": self.last_scanned_block,
            "sync_status": self.sync_status, "created_at": self.created_at.isoformat(),
        }


class TransactionTemplate:
    def __init__(self, template_id: str, name: str, network: str):
        self.template_id = template_id
        self.name = name
        self.network = network
        self.from_address = ""
        self.to_address = ""
        self.value_eth = 0.0
        self.data_hex = ""
        self.gas_limit = 21000
        self.gas_price_gwei = 20
        self.nonce = 0
        self.chain_id = 1
        self.contract_interaction = False
        self.contract_abi: list[dict[str, Any]] = []
        self.function_name = ""
        self.function_args: list[Any] = []
        self.signed_tx = ""
        self.tx_hash = ""
        self.status = TransactionStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id, "name": self.name, "network": self.network,
            "from_address": self.from_address, "to_address": self.to_address,
            "value_eth": self.value_eth, "data_hex": self.data_hex[:64] + "..." if len(self.data_hex) > 64 else self.data_hex,
            "gas_limit": self.gas_limit, "gas_price_gwei": self.gas_price_gwei,
            "nonce": self.nonce, "chain_id": self.chain_id,
            "contract_interaction": self.contract_interaction,
            "function_name": self.function_name, "function_args": self.function_args,
            "signed_tx": self.signed_tx[:32] + "..." if len(self.signed_tx) > 32 else self.signed_tx,
            "tx_hash": self.tx_hash, "status": self.status.value,
        }


class Faucet:
    def __init__(self, faucet_id: str, name: str, network: str, token_symbol: str):
        self.faucet_id = faucet_id
        self.name = name
        self.network = network
        self.token_symbol = token_symbol
        self.status = FaucetStatus.ACTIVE
        self.drip_amount = 1.0
        self.cooldown_seconds = 86400
        self.max_daily_drips = 5
        self.total_drips = 0
        self.total_tokens_distributed = 0.0
        self.balance = 1000.0
        self.min_balance_warning = 100.0
        self.contract_address = ""
        self.faucet_private_key = ""
        self.captcha_required = True
        self.allowed_networks: list[str] = []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "faucet_id": self.faucet_id, "name": self.name, "network": self.network,
            "token_symbol": self.token_symbol, "status": self.status.value,
            "drip_amount": self.drip_amount, "cooldown_seconds": self.cooldown_seconds,
            "max_daily_drips": self.max_daily_drips, "total_drips": self.total_drips,
            "total_tokens_distributed": self.total_tokens_distributed,
            "balance": self.balance, "min_balance_warning": self.min_balance_warning,
            "contract_address": self.contract_address,
            "captcha_required": self.captcha_required,
            "allowed_networks": self.allowed_networks,
            "created_at": self.created_at.isoformat(),
        }


class FaucetDrip:
    def __init__(self, drip_id: str, faucet_id: str, recipient_address: str):
        self.drip_id = drip_id
        self.faucet_id = faucet_id
        self.recipient_address = recipient_address
        self.amount = 0.0
        self.tx_hash = ""
        self.status = "pending"
        self.requested_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "drip_id": self.drip_id, "faucet_id": self.faucet_id,
            "recipient_address": self.recipient_address, "amount": self.amount,
            "tx_hash": self.tx_hash, "status": self.status,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class GasPriceTracker:
    def __init__(self):
        self.network = "ethereum"
        self.slow_gwei = 10.0
        self.standard_gwei = 20.0
        self.fast_gwei = 50.0
        self.instant_gwei = 100.0
        self.base_fee_gwei = 15.0
        self.priority_fee_gwei = 2.0
        self.updated_at = datetime.utcnow()
        self.historical: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "network": self.network, "slow_gwei": self.slow_gwei,
            "standard_gwei": self.standard_gwei, "fast_gwei": self.fast_gwei,
            "instant_gwei": self.instant_gwei, "base_fee_gwei": self.base_fee_gwei,
            "priority_fee_gwei": self.priority_fee_gwei,
            "updated_at": self.updated_at.isoformat(),
        }


class Web3ToolkitService:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.explorers: dict[str, BlockExplorer] = {}
        self.tx_templates: dict[str, TransactionTemplate] = {}
        self.faucets: dict[str, Faucet] = {}
        self.drips: dict[str, FaucetDrip] = {}
        self.gas_trackers: dict[str, GasPriceTracker] = {}
        self.contract_verification_queue: list[dict[str, Any]] = []
        self.storage_path = config.get("storage_path", "data/web3_toolkit.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for e_data in data.get("explorers", []):
                    e = BlockExplorer(e_data["explorer_id"], e_data["name"], e_data["network"])
                    e.base_url = e_data.get("base_url", "")
                    e.api_url = e_data.get("api_url", "")
                    e.chain_id = e_data.get("chain_id", 1)
                    e.block_count = e_data.get("block_count", 0)
                    self.explorers[e.explorer_id] = e
                for f_data in data.get("faucets", []):
                    f = Faucet(f_data["faucet_id"], f_data["name"], f_data["network"], f_data["token_symbol"])
                    f.status = FaucetStatus(f_data.get("status", "active"))
                    f.drip_amount = f_data.get("drip_amount", 1.0)
                    f.cooldown_seconds = f_data.get("cooldown_seconds", 86400)
                    f.total_drips = f_data.get("total_drips", 0)
                    f.total_tokens_distributed = f_data.get("total_tokens_distributed", 0.0)
                    f.balance = f_data.get("balance", 1000.0)
                    self.faucets[f.faucet_id] = f
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        self._seed_default_networks()
        logger.info("Initialized Web3ToolkitService with %d explorers, %d faucets", len(self.explorers), len(self.faucets))

    async def close(self):
        await self._save()

    async def _save(self):
        data = {
            "explorers": [e.to_dict() for e in self.explorers.values()],
            "faucets": [f.to_dict() for f in self.faucets.values()],
            "tx_templates": [t.to_dict() for t in self.tx_templates.values()],
        }
        async with aiofiles.open(self.storage_path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    def _seed_default_networks(self):
        default_networks = [
            ("eth-mainnet", "Ethereum Mainnet", "ethereum", "https://etherscan.io", "https://api.etherscan.io/api", 1, NetworkType.MAINNET),
            ("eth-goerli", "Ethereum Goerli", "ethereum", "https://goerli.etherscan.io", "https://api-goerli.etherscan.io/api", 5, NetworkType.TESTNET),
            ("eth-sepolia", "Ethereum Sepolia", "ethereum", "https://sepolia.etherscan.io", "https://api-sepolia.etherscan.io/api", 11155111, NetworkType.TESTNET),
            ("polygon-mainnet", "Polygon Mainnet", "polygon", "https://polygonscan.com", "https://api.polygonscan.com/api", 137, NetworkType.MAINNET),
            ("arbitrum-mainnet", "Arbitrum One", "arbitrum", "https://arbiscan.io", "https://api.arbiscan.io/api", 42161, NetworkType.MAINNET),
            ("optimism-mainnet", "Optimism", "optimism", "https://optimistic.etherscan.io", "https://api-optimistic.etherscan.io/api", 10, NetworkType.MAINNET),
            ("base-mainnet", "Base", "base", "https://basescan.org", "https://api.basescan.org/api", 8453, NetworkType.MAINNET),
            ("avalanche-mainnet", "Avalanche C-Chain", "avalanche", "https://snowtrace.io", "https://api.snowtrace.io/api", 43114, NetworkType.MAINNET),
        ]
        for eid, name, network, base_url, api_url, chain_id, net_type in default_networks:
            if eid not in self.explorers:
                e = BlockExplorer(eid, name, network)
                e.base_url = base_url
                e.api_url = api_url
                e.chain_id = chain_id
                e.network_type = net_type
                self.explorers[eid] = e

        default_faucets = [
            ("eth-sepolia-faucet", "Sepolia ETH Faucet", "sepolia", "ETH", "0xsepolia-faucet-address"),
            ("eth-goerli-faucet", "Goerli ETH Faucet", "goerli", "ETH", "0xgoerli-faucet-address"),
        ]
        for fid, name, network, symbol, addr in default_faucets:
            if fid not in self.faucets:
                f = Faucet(fid, name, network, symbol)
                f.contract_address = addr
                f.drip_amount = 0.1
                self.faucets[fid] = f

    def list_explorers(self, network: Optional[str] = None) -> list[BlockExplorer]:
        if network:
            return [e for e in self.explorers.values() if e.network == network]
        return list(self.explorers.values())

    def get_explorer(self, explorer_id: str) -> Optional[BlockExplorer]:
        return self.explorers.get(explorer_id)

    async def lookup_block(self, explorer_id: str, block_number: int) -> dict[str, Any]:
        explorer = self.explorers.get(explorer_id)
        if not explorer:
            return {}
        return {
            "explorer": explorer.name, "block_number": block_number,
            "hash": f"0x{block_number:064x}", "timestamp": datetime.utcnow().isoformat(),
            "transactions": 42, "gas_used": 8000000, "gas_limit": 15000000,
            "base_fee": 15.0, "miner": "0xabc...def",
        }

    async def lookup_transaction(self, explorer_id: str, tx_hash: str) -> dict[str, Any]:
        explorer = self.explorers.get(explorer_id)
        if not explorer:
            return {}
        return {
            "explorer": explorer.name, "hash": tx_hash,
            "from": "0xfrom...addr", "to": "0xto...addr",
            "value_eth": 0.5, "gas_price_gwei": 25.0,
            "gas_used": 21000, "status": "confirmed",
            "block_number": 15000000, "timestamp": datetime.utcnow().isoformat(),
        }

    async def lookup_address(self, explorer_id: str, address: str) -> dict[str, Any]:
        explorer = self.explorers.get(explorer_id)
        if not explorer:
            return {}
        return {
            "explorer": explorer.name, "address": address,
            "balance_eth": 10.5, "transaction_count": 150,
            "is_contract": address.endswith("c"),
            "token_holdings": [{"symbol": "USDC", "balance": 1000}, {"symbol": "LINK", "balance": 50}],
        }

    async def create_transaction(self, name: str, network: str, to_address: str, value_eth: float = 0.0) -> TransactionTemplate:
        template_id = str(uuid.uuid4())
        template = TransactionTemplate(template_id, name, network)
        template.to_address = to_address
        template.value_eth = value_eth
        self.tx_templates[template_id] = template
        return template

    def get_transaction(self, template_id: str) -> Optional[TransactionTemplate]:
        return self.tx_templates.get(template_id)

    def list_transactions(self) -> list[TransactionTemplate]:
        return list(self.tx_templates.values())

    async def sign_and_send(self, template_id: str, private_key: str) -> Optional[TransactionTemplate]:
        template = self.tx_templates.get(template_id)
        if not template:
            return None
        template.signed_tx = f"0x{uuid.uuid4().hex[:128]}"
        template.tx_hash = f"0x{uuid.uuid4().hex[:64]}"
        template.status = TransactionStatus.PENDING
        asyncio.create_task(self._simulate_confirmation(template_id))
        return template

    async def _simulate_confirmation(self, template_id: str):
        await asyncio.sleep(2)
        template = self.tx_templates.get(template_id)
        if template:
            template.status = TransactionStatus.CONFIRMED

    def get_gas_price(self, network: str = "ethereum") -> GasPriceTracker:
        if network not in self.gas_trackers:
            tracker = GasPriceTracker()
            tracker.network = network
            self.gas_trackers[network] = tracker
        return self.gas_trackers[network]

    async def create_faucet(self, name: str, network: str, token_symbol: str, drip_amount: float = 1.0) -> Faucet:
        faucet_id = str(uuid.uuid4())
        faucet = Faucet(faucet_id, name, network, token_symbol)
        faucet.drip_amount = drip_amount
        self.faucets[faucet_id] = faucet
        await self._save()
        return faucet

    def list_faucets(self) -> list[Faucet]:
        return list(self.faucets.values())

    def get_faucet(self, faucet_id: str) -> Optional[Faucet]:
        return self.faucets.get(faucet_id)

    async def request_drip(self, faucet_id: str, recipient_address: str) -> Optional[FaucetDrip]:
        faucet = self.faucets.get(faucet_id)
        if not faucet or faucet.status != FaucetStatus.ACTIVE or faucet.balance < faucet.drip_amount:
            return None
        drip_id = str(uuid.uuid4())
        drip = FaucetDrip(drip_id, faucet_id, recipient_address)
        drip.amount = faucet.drip_amount
        drip.status = "completed"
        drip.tx_hash = f"0x{uuid.uuid4().hex[:64]}"
        drip.completed_at = datetime.utcnow()
        faucet.total_drips += 1
        faucet.total_tokens_distributed += faucet.drip_amount
        faucet.balance -= faucet.drip_amount
        self.drips[drip_id] = drip
        await self._save()
        return drip

    async def fund_faucet(self, faucet_id: str, amount: float) -> bool:
        faucet = self.faucets.get(faucet_id)
        if faucet:
            faucet.balance += amount
            if faucet.status == FaucetStatus.DEPLETED and faucet.balance > faucet.min_balance_warning:
                faucet.status = FaucetStatus.ACTIVE
            await self._save()
            return True
        return False

    async def verify_contract(self, explorer_id: str, contract_address: str, source_code: str, compiler_version: str = "0.8.20") -> dict[str, Any]:
        verification_id = str(uuid.uuid4())
        entry = {
            "verification_id": verification_id, "explorer_id": explorer_id,
            "contract_address": contract_address, "compiler_version": compiler_version,
            "status": "pending", "submitted_at": datetime.utcnow().isoformat(),
        }
        self.contract_verification_queue.append(entry)
        asyncio.create_task(self._simulate_verification(verification_id))
        return entry

    async def _simulate_verification(self, verification_id: str):
        await asyncio.sleep(2)
        for entry in self.contract_verification_queue:
            if entry["verification_id"] == verification_id:
                entry["status"] = "verified"

    def get_verification_status(self, verification_id: str) -> Optional[dict[str, Any]]:
        for entry in self.contract_verification_queue:
            if entry["verification_id"] == verification_id:
                return entry
        return None

    def get_gas_price_history(self, network: str = "ethereum") -> list[dict[str, Any]]:
        tracker = self.gas_trackers.get(network)
        if tracker:
            return tracker.historical
        return []

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_explorers": len(self.explorers),
            "total_faucets": len(self.faucets),
            "active_faucets": sum(1 for f in self.faucets.values() if f.status == FaucetStatus.ACTIVE),
            "total_drips": sum(f.total_drips for f in self.faucets.values()),
            "total_tokens_distributed": sum(f.total_tokens_distributed for f in self.faucets.values()),
            "total_transactions": len(self.tx_templates),
            "pending_verifications": sum(1 for v in self.contract_verification_queue if v["status"] == "pending"),
        }

    # === Export ===
    def _export_csv_rows(self, headers: list, rows: list) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return output.getvalue()

    def export_faucets_csv(self) -> str:
        return self._export_csv_rows(
            ["faucet_id", "name", "network", "token_symbol", "status", "drip_amount", "cooldown_s", "max_daily", "total_drips", "total_distributed", "balance", "created_at"],
            [[f.faucet_id, f.name, f.network, f.token_symbol, f.status.value, f.drip_amount, f.cooldown_seconds, f.max_daily_drips, f.total_drips, f.total_tokens_distributed, f.balance, f.created_at.isoformat()] for f in self.faucets.values()]
        )

    def export_explorers_csv(self) -> str:
        return self._export_csv_rows(
            ["explorer_id", "name", "network", "chain_id", "network_type", "block_count", "last_scanned", "sync_status", "created_at"],
            [[e.explorer_id, e.name, e.network, e.chain_id, e.network_type.value, e.block_count, e.last_scanned_block, e.sync_status, e.created_at.isoformat()] for e in self.explorers.values()]
        )

    def export_faucets_json(self) -> str:
        return json.dumps({"faucets": [f.to_dict() for f in self.faucets.values()], "explorers": [e.to_dict() for e in self.explorers.values()], "templates": [t.to_dict() for t in self.tx_templates.values()]}, indent=2, default=str)

    # === Import ===
    def import_faucets_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("faucets", data if isinstance(data, list) else []):
            f = Faucet(item.get("faucet_id", str(uuid.uuid4())), item.get("name", "Imported Faucet"), item.get("network", "sepolia"), item.get("token_symbol", "ETH"))
            f.status = FaucetStatus(item.get("status", "active"))
            f.drip_amount = item.get("drip_amount", 0.1)
            f.cooldown_seconds = item.get("cooldown_seconds", 86400)
            f.total_drips = item.get("total_drips", 0)
            f.total_tokens_distributed = item.get("total_tokens_distributed", 0.0)
            f.balance = item.get("balance", 1000.0)
            self.faucets[f.faucet_id] = f
            count += 1
        return count

    # === Notification ===
    async def notify_faucet_status(self, faucet_id: str) -> dict[str, Any]:
        faucet = self.faucets.get(faucet_id)
        if not faucet:
            return {"error": "Faucet not found"}
        return {
            "faucet_id": faucet.faucet_id,
            "name": faucet.name,
            "network": faucet.network,
            "token_symbol": faucet.token_symbol,
            "status": faucet.status.value,
            "balance": faucet.balance,
            "message": f"Faucet {faucet.name} ({faucet.network}) status: {faucet.status.value}, balance: {faucet.balance}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_low_balance_faucets(self) -> list[dict[str, Any]]:
        results = []
        for f in self.faucets.values():
            if f.balance < f.min_balance_warning:
                results.append(await self.notify_faucet_status(f.faucet_id))
        return results

    # === State Machine ===
    async def transition_faucet_status(self, faucet_id: str, target_status: str) -> Optional[Faucet]:
        faucet = self.faucets.get(faucet_id)
        if not faucet:
            return None
        valid = {
            FaucetStatus.ACTIVE: [FaucetStatus.PAUSED, FaucetStatus.DEPLETED],
            FaucetStatus.PAUSED: [FaucetStatus.ACTIVE],
            FaucetStatus.DEPLETED: [FaucetStatus.PAUSED, FaucetStatus.ACTIVE],
        }
        new_status = FaucetStatus(target_status)
        if new_status in valid.get(faucet.status, []):
            faucet.status = new_status
            await self._save()
            return faucet
        return None

    def transition_tx_status(self, template_id: str, target_status: str) -> Optional[TransactionTemplate]:
        template = self.tx_templates.get(template_id)
        if not template:
            return None
        valid = {
            TransactionStatus.PENDING: [TransactionStatus.CONFIRMED, TransactionStatus.FAILED, TransactionStatus.DROPPED],
            TransactionStatus.CONFIRMED: [],
            TransactionStatus.FAILED: [TransactionStatus.PENDING],
            TransactionStatus.REVERTED: [TransactionStatus.PENDING],
            TransactionStatus.DROPPED: [TransactionStatus.PENDING],
        }
        new_status = TransactionStatus(target_status)
        if new_status in valid.get(template.status, []):
            template.status = new_status
            return template
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if config.get("max_file_size_mb", 1024) > 10240:
            warnings.append("Max file size exceeds 10GB")
        if config.get("default_gas_price_gwei", 20) > 500:
            warnings.append("Default gas price is very high")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_explorers": len(self.explorers),
            "total_faucets": len(self.faucets),
            "active_faucets": sum(1 for f in self.faucets.values() if f.status == FaucetStatus.ACTIVE),
            "total_drips": sum(f.total_drips for f in self.faucets.values()),
            "total_tokens_distributed": sum(f.total_tokens_distributed for f in self.faucets.values()),
            "total_transactions": len(self.tx_templates),
            "pending_tx": sum(1 for t in self.tx_templates.values() if t.status == TransactionStatus.PENDING),
            "confirmed_tx": sum(1 for t in self.tx_templates.values() if t.status == TransactionStatus.CONFIRMED),
            "pending_verifications": sum(1 for v in self.contract_verification_queue if v["status"] == "pending"),
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        active_faucets = sum(1 for f in self.faucets.values() if f.status == FaucetStatus.ACTIVE)
        depleted = sum(1 for f in self.faucets.values() if f.status == FaucetStatus.DEPLETED)
        return {
            "total_faucets": len(self.faucets),
            "active": active_faucets,
            "depleted": depleted,
            "total_explorers": len(self.explorers),
            "health_pct": round(active_faucets / max(len(self.faucets), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_pause_faucets(self, faucet_ids: list[str]) -> int:
        count = 0
        for fid in faucet_ids:
            f = self.faucets.get(fid)
            if f and f.status == FaucetStatus.ACTIVE:
                f.status = FaucetStatus.PAUSED
                count += 1
        await self._save()
        return count

    async def bulk_fund_faucets(self, faucet_ids: list[str], amount: float) -> int:
        count = 0
        for fid in faucet_ids:
            f = self.faucets.get(fid)
            if f:
                f.balance += amount
                if f.status == FaucetStatus.DEPLETED:
                    f.status = FaucetStatus.ACTIVE
                count += 1
        await self._save()
        return count

    # === Tag Management ===
    def add_explorer_tags(self, explorer_ids: list[str], tags: list[str]) -> int:
        count = 0
        for eid in explorer_ids:
            e = self.explorers.get(eid)
            if e:
                pass  # explorers don't have tags currently
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "web3_toolkit",
            "explorers": len(self.explorers),
            "faucets": len(self.faucets),
            "active_faucets": sum(1 for f in self.faucets.values() if f.status == FaucetStatus.ACTIVE),
            "total_drips": sum(f.total_drips for f in self.faucets.values()),
            "tx_templates": len(self.tx_templates),
            "pending_verifications": sum(1 for v in self.contract_verification_queue if v["status"] == "pending"),
            "status": "healthy",
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
