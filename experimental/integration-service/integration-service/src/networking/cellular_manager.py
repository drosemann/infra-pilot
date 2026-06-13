import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class CellularModem:
    id: str
    name: str
    manufacturer: str
    model: str
    firmware_version: str
    interface_name: str
    protocol: str
    imei: str
    imsi: str
    iccid: str
    operator_name: str
    connection_status: str
    rssi_dbm: int
    rsrp_dbm: int
    rsrq_db: float
    sinr_db: float
    cell_id: str
    tac: str
    band: str
    carrier_aggregation: bool
    ipv4_address: str
    ipv6_address: str
    data_used_gb: float
    data_cap_gb: float
    temperature_celsius: float

@dataclass
class APNConfig:
    id: str
    modem_id: str
    apn: str
    username: str
    password_encrypted: str
    authentication: str
    ip_type: str
    roaming_enabled: bool
    is_primary: bool

@dataclass
class SMSMessage:
    id: str
    modem_id: str
    direction: str
    sender: str
    recipient: str
    message: str
    status: str
    received_at: str

@dataclass
class FailoverConfig:
    id: str
    primary_uplink_id: str
    cellular_uplink_id: str
    failover_threshold_latency_ms: int
    failover_threshold_loss_pct: float
    auto_failback: bool
    failback_after_seconds: int
    data_saver_mode: str

class CellularManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.modems_file = os.path.join(self.data_path, 'cellular_modems.json')
        self.apns_file = os.path.join(self.data_path, 'cellular_apns.json')
        self.sms_file = os.path.join(self.data_path, 'cellular_sms.json')
        self.failover_file = os.path.join(self.data_path, 'cellular_failover.json')
        self.modems: Dict[str, CellularModem] = {}
        self.apns: Dict[str, APNConfig] = {}
        self.sms_messages: Dict[str, SMSMessage] = {}
        self.failover_config: Optional[FailoverConfig] = None
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.modems_file, 'modems', CellularModem),
            (self.apns_file, 'apns', APNConfig),
            (self.sms_file, 'sms_messages', SMSMessage),
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
            if os.path.exists(self.failover_file):
                with open(self.failover_file, 'r') as f:
                    data = json.load(f)
                self.failover_config = FailoverConfig(**data)
        except Exception as e:
            logger.warning(f"Failed to load failover config: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.modems_file, 'modems'),
            (self.apns_file, 'apns'),
            (self.sms_file, 'sms_messages'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")
        if self.failover_config:
            try:
                with open(self.failover_file, 'w') as f:
                    json.dump(asdict(self.failover_config), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save failover config: {e}")

    async def initialize(self):
        logger.info("CellularManager initialized")
        if not self.modems:
            await self._seed_default_modem()

    async def close(self):
        self._save_data()

    async def _seed_default_modem(self):
        modem = CellularModem(
            id=str(uuid.uuid4()),
            name='Primary LTE Modem',
            manufacturer='Quectel',
            model='EG25-G',
            firmware_version='EG25GGBR07A08M2G',
            interface_name='wwan0',
            protocol='qmi',
            imei='359123456789012',
            imsi='310150123456789',
            iccid='89014103211118516720',
            operator_name='Verizon',
            connection_status='connected',
            rssi_dbm=-75,
            rsrp_dbm=-95,
            rsrq_db=-12.5,
            sinr_db=8.3,
            cell_id='12345678',
            tac='12345',
            band='B13',
            carrier_aggregation=False,
            ipv4_address='10.0.0.2',
            ipv6_address='',
            data_used_gb=15.3,
            data_cap_gb=50.0,
            temperature_celsius=42.5,
        )
        self.modems[modem.id] = modem
        apn = APNConfig(
            id=str(uuid.uuid4()),
            modem_id=modem.id,
            apn='internet',
            username='',
            password_encrypted='',
            authentication='none',
            ip_type='ipv4',
            roaming_enabled=False,
            is_primary=True,
        )
        self.apns[apn.id] = apn
        self._save_data()

    async def list_modems(self) -> List[Dict[str, Any]]:
        return [asdict(m) for m in self.modems.values()]

    async def get_modem(self, modem_id: str) -> Optional[Dict[str, Any]]:
        modem = self.modems.get(modem_id)
        return asdict(modem) if modem else None

    async def get_signal(self, modem_id: str) -> Optional[Dict[str, Any]]:
        modem = self.modems.get(modem_id)
        if not modem:
            return None
        signal_quality = 'excellent'
        if modem.rsrp_dbm < -120:
            signal_quality = 'poor'
        elif modem.rsrp_dbm < -105:
            signal_quality = 'fair'
        elif modem.rsrp_dbm < -95:
            signal_quality = 'good'
        return {
            'modem_id': modem_id,
            'rssi_dbm': modem.rssi_dbm,
            'rsrp_dbm': modem.rsrp_dbm,
            'rsrq_db': modem.rsrq_db,
            'sinr_db': modem.sinr_db,
            'signal_quality': signal_quality,
            'band': modem.band,
            'carrier_aggregation': modem.carrier_aggregation,
            'cell_id': modem.cell_id,
            'operator': modem.operator_name,
            'timestamp': datetime.now().isoformat(),
        }

    async def get_usage(self, modem_id: str) -> Optional[Dict[str, Any]]:
        modem = self.modems.get(modem_id)
        if not modem:
            return None
        return {
            'modem_id': modem_id,
            'data_used_gb': modem.data_used_gb,
            'data_cap_gb': modem.data_cap_gb,
            'usage_pct': round(modem.data_used_gb / modem.data_cap_gb * 100, 2) if modem.data_cap_gb > 0 else 0,
            'data_remaining_gb': round(max(0, modem.data_cap_gb - modem.data_used_gb), 2),
            'billing_period': 'current_month',
        }

    async def set_apn(self, modem_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        modem = self.modems.get(modem_id)
        if not modem:
            return None
        apn_id = str(uuid.uuid4())
        apn = APNConfig(
            id=apn_id,
            modem_id=modem_id,
            apn=data['apn'],
            username=data.get('username', ''),
            password_encrypted=self._encrypt(data.get('password', '')),
            authentication=data.get('authentication', 'none'),
            ip_type=data.get('ip_type', 'ipv4'),
            roaming_enabled=data.get('roaming_enabled', False),
            is_primary=data.get('is_primary', True),
        )
        self.apns[apn.id] = apn
        self._save_data()
        return asdict(apn)

    def _encrypt(self, value: str) -> str:
        import base64
        return base64.b64encode(value.encode()).decode('ascii')

    async def get_apn(self, modem_id: str) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self.apns.values() if a.modem_id == modem_id]

    async def send_sms(self, modem_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        modem = self.modems.get(modem_id)
        if not modem:
            return None
        sms = SMSMessage(
            id=str(uuid.uuid4()),
            modem_id=modem_id,
            direction='outgoing',
            sender=modem.ipv4_address or modem.imei,
            recipient=data['to'],
            message=data['message'],
            status='sent',
            received_at=datetime.now().isoformat(),
        )
        self.sms_messages[sms.id] = sms
        self._save_data()
        return asdict(sms)

    async def list_sms(self, modem_id: str) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self.sms_messages.values() if s.modem_id == modem_id]

    async def reset_modem(self, modem_id: str) -> Optional[Dict[str, Any]]:
        modem = self.modems.get(modem_id)
        if not modem:
            return None
        modem.connection_status = 'disconnected'
        modem.ipv4_address = ''
        modem.ipv6_address = ''
        self._save_data()
        modem.connection_status = 'connected'
        modem.ipv4_address = '10.0.0.2'
        self._save_data()
        return asdict(modem)

    async def get_failover_status(self) -> Optional[Dict[str, Any]]:
        if not self.failover_config:
            self.failover_config = FailoverConfig(
                id=str(uuid.uuid4()),
                primary_uplink_id='uplink_fiber_001',
                cellular_uplink_id=list(self.modems.keys())[0] if self.modems else '',
                failover_threshold_latency_ms=150,
                failover_threshold_loss_pct=5.0,
                auto_failback=True,
                failback_after_seconds=300,
                data_saver_mode='medium',
            )
            self._save_data()
        return asdict(self.failover_config)

    async def update_failover(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.failover_config:
            self.failover_config = FailoverConfig(id=str(uuid.uuid4()), primary_uplink_id='', cellular_uplink_id='', failover_threshold_latency_ms=150, failover_threshold_loss_pct=5.0, auto_failback=True, failback_after_seconds=300, data_saver_mode='medium')
        for key in ['primary_uplink_id', 'cellular_uplink_id', 'failover_threshold_latency_ms', 'failover_threshold_loss_pct', 'auto_failback', 'failback_after_seconds', 'data_saver_mode']:
            if key in data:
                setattr(self.failover_config, key, data[key])
        self._save_data()
        return asdict(self.failover_config)

    async def receive_sms(self, modem_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        sms = SMSMessage(
            id=str(uuid.uuid4()),
            modem_id=modem_id,
            direction='incoming',
            sender=data['from'],
            recipient=data.get('to', ''),
            message=data['message'],
            status='received',
            received_at=datetime.now().isoformat(),
        )
        self.sms_messages[sms.id] = sms
        self._save_data()
        return asdict(sms)
