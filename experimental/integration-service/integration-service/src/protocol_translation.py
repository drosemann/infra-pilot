"""IoT protocol translation and connectivity layer.

This module provides protocol translation between IoT device protocols
(MQTT, CoAP, HTTP, LoRaWAN) and the internal data pipeline.
"""

import json
import logging
import time
import struct
import base64
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    MQTT = "mqtt"
    COAP = "coap"
    HTTP = "http"
    LORAWAN = "lorawan"
    MODBUS = "modbus"
    BACNET = "bacnet"
    ZIGBEE = "zigbee"
    BLE = "ble"
    WEBSOCKET = "websocket"


class EncodingFormat(Enum):
    JSON = "json"
    CBOR = "cbor"
    PROTOBUF = "protobuf"
    MSGPACK = "msgpack"
    BINARY = "binary"
    BASE64 = "base64"
    XML = "xml"
    CSV = "csv"


@dataclass
class ProtocolMessage:
    message_id: str
    protocol: ProtocolType
    device_id: str
    payload: Dict[str, Any]
    raw_bytes: Optional[bytes] = None
    encoding: EncodingFormat = EncodingFormat.JSON
    received_at: datetime = field(default_factory=datetime.utcnow)
    rssi_dbm: Optional[int] = None
    snr_db: Optional[float] = None
    gateway_id: Optional[str] = None
    port: Optional[int] = None
    acknowledged: bool = False


class MQTTTranslator:
    """Translates MQTT messages to internal format."""

    def __init__(self):
        self.topic_patterns: Dict[str, str] = {}

    def register_topic(self, pattern: str, device_type: str):
        self.topic_patterns[pattern] = device_type

    def parse_topic(self, topic: str) -> Tuple[Optional[str], Optional[str]]:
        for pattern, device_type in self.topic_patterns.items():
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")
            if len(pattern_parts) != len(topic_parts):
                continue
            match = True
            extracted = {}
            for p, t in zip(pattern_parts, topic_parts):
                if p.startswith("{"):
                    extracted[p[1:-1]] = t
                elif p != t:
                    match = False
                    break
            if match:
                return extracted.get("device_id"), device_type
        return None, None

    def translate(self, topic: str, payload: bytes) -> Optional[ProtocolMessage]:
        try:
            device_id, device_type = self.parse_topic(topic)
            if not device_id:
                device_id = f"mqtt-{hashlib.md5(topic.encode()).hexdigest()[:8]}"
            payload_str = payload.decode("utf-8")
            try:
                data = json.loads(payload_str)
            except json.JSONDecodeError:
                data = {"raw": payload_str}
            msg = ProtocolMessage(
                message_id=str(uuid.uuid4()),
                protocol=ProtocolType.MQTT,
                device_id=device_id,
                payload=data,
                raw_bytes=payload,
                encoding=EncodingFormat.JSON,
            )
            return msg
        except Exception as e:
            logger.error(f"MQTT translation error: {e}")
            return None


class CoAPTranslator:
    """Translates CoAP messages to internal format."""

    def translate(self, uri_path: str, payload: bytes,
                  content_format: int = 50) -> Optional[ProtocolMessage]:
        try:
            device_id = uri_path.strip("/").split("/")[0] if uri_path else "coap-device"
            data = {}
            if content_format == 50:
                try:
                    data = json.loads(payload.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    data = {"raw": base64.b64encode(payload).decode()}
            elif content_format == 42:
                data = {"encoding": "cbor", "raw": base64.b64encode(payload).decode()}
            else:
                data = {"encoding": "unknown", "size": len(payload)}
            msg = ProtocolMessage(
                message_id=str(uuid.uuid4()),
                protocol=ProtocolType.COAP,
                device_id=device_id,
                payload=data,
                raw_bytes=payload,
                encoding=EncodingFormat.JSON if content_format == 50 else EncodingFormat.BINARY,
            )
            return msg
        except Exception as e:
            logger.error(f"CoAP translation error: {e}")
            return None


class LoRaWANPayloadDecoder:
    """Decodes LoRaWAN payloads using a device-specific payload format."""

    def __init__(self):
        self.decoders: Dict[str, callable] = {}

    def register_decoder(self, device_type: str, decoder_func: callable):
        self.decoders[device_type] = decoder_func

    def decode_temperature_humidity(self, payload: bytes) -> Dict[str, Any]:
        if len(payload) < 4:
            return {"error": "payload_too_short"}
        temp_raw = struct.unpack(">h", payload[0:2])[0]
        humidity_raw = struct.unpack(">h", payload[2:4])[0]
        return {
            "temperature_celsius": round(temp_raw / 100.0, 2),
            "humidity_pct": round(humidity_raw / 100.0, 2),
        }

    def decode_power_meter(self, payload: bytes) -> Dict[str, Any]:
        if len(payload) < 8:
            return {"error": "payload_too_short"}
        voltage = struct.unpack(">H", payload[0:2])[0]
        current_raw = struct.unpack(">H", payload[2:4])[0]
        power = struct.unpack(">I", payload[4:8])[0]
        return {
            "voltage_v": round(voltage / 10.0, 1),
            "current_a": round(current_raw / 100.0, 2),
            "power_w": power,
        }

    def decode_gps(self, payload: bytes) -> Dict[str, Any]:
        if len(payload) < 6:
            return {"error": "payload_too_short"}
        lat_raw = struct.unpack(">I", payload[0:3] + b"\x00")[0] >> 8
        lng_raw = struct.unpack(">I", payload[3:6] + b"\x00")[0] >> 8
        lat = (lat_raw / 10000.0) - 90.0
        lng = (lng_raw / 10000.0) - 180.0
        return {"latitude": round(lat, 6), "longitude": round(lng, 6)}

    def decode_generic_sensor(self, payload: bytes) -> Dict[str, Any]:
        result = {}
        if len(payload) >= 1:
            result["flags"] = payload[0]
        if len(payload) >= 3:
            result["value_1"] = struct.unpack(">H", payload[1:3])[0]
        if len(payload) >= 5:
            result["value_2"] = struct.unpack(">H", payload[3:5])[0]
        if len(payload) >= 7:
            result["value_3"] = struct.unpack(">H", payload[5:7])[0]
        return result

    def decode(self, device_type: str, payload: bytes) -> Dict[str, Any]:
        decoder = self.decoders.get(device_type)
        if decoder:
            return decoder(payload)
        built_in_decoders = {
            "temperature_humidity": self.decode_temperature_humidity,
            "power_meter": self.decode_power_meter,
            "gps_tracker": self.decode_gps,
            "generic_sensor": self.decode_generic_sensor,
        }
        decoder = built_in_decoders.get(device_type)
        if decoder:
            return decoder(payload)
        return {"raw_hex": payload.hex(), "length": len(payload)}

    def encode_downlink(self, device_type: str, command: Dict[str, Any]) -> bytes:
        if device_type == "relay_control":
            channel = command.get("channel", 1)
            state = command.get("state", False)
            return bytes([channel, 1 if state else 0])
        elif device_type == "setpoint":
            value = command.get("value", 0)
            return struct.pack(">h", int(value * 100))
        elif device_type == "led_config":
            mode = command.get("mode", 0)
            brightness = command.get("brightness", 128)
            color = command.get("color", 0xFFFFFF)
            return bytes([mode, brightness]) + struct.pack(">I", color)[1:4]
        return b"\x00"


class ProtocolGateway:
    """Unified gateway that handles multiple IoT protocols."""

    def __init__(self):
        self.mqtt = MQTTTranslator()
        self.coap = CoAPTranslator()
        self.lorawan = LoRaWANPayloadDecoder()
        self.translators = {
            ProtocolType.MQTT: self.mqtt,
            ProtocolType.COAP: self.coap,
        }

    def ingest(self, protocol: ProtocolType, source: str, payload: bytes,
               metadata: Optional[Dict[str, Any]] = None) -> Optional[ProtocolMessage]:
        translator = self.translators.get(protocol)
        if not translator:
            logger.warning(f"No translator for protocol: {protocol}")
            return None
        if protocol == ProtocolType.MQTT:
            return self.mqtt.translate(source, payload)
        elif protocol == ProtocolType.COAP:
            content_format = (metadata or {}).get("content_format", 50)
            return self.coap.translate(source, payload, content_format)
        elif protocol == ProtocolType.LORAWAN:
            device_type = (metadata or {}).get("device_type", "generic_sensor")
            decoded = self.lorawan.decode(device_type, payload)
            msg = ProtocolMessage(
                message_id=str(uuid.uuid4()),
                protocol=ProtocolType.LORAWAN,
                device_id=(metadata or {}).get("device_id", "lorawan-device"),
                payload=decoded,
                raw_bytes=payload,
                encoding=EncodingFormat.BINARY,
                rssi_dbm=(metadata or {}).get("rssi"),
                snr_db=(metadata or {}).get("snr"),
                gateway_id=(metadata or {}).get("gateway_id"),
                port=(metadata or {}).get("port"),
            )
            return msg
        return None


class ConnectionManager:
    """Manages device connections and sessions."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = 10000

    def create_session(self, device_id: str, protocol: ProtocolType,
                       remote_addr: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "device_id": device_id,
            "protocol": protocol.value,
            "remote_addr": remote_addr,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "message_count": 0,
            "is_active": True,
        }
        if len(self.sessions) > self.max_sessions:
            self._cleanup_old_sessions()
        return session_id

    def update_activity(self, session_id: str):
        session = self.sessions.get(session_id)
        if session:
            session["last_activity"] = datetime.utcnow().isoformat()
            session["message_count"] += 1

    def close_session(self, session_id: str):
        session = self.sessions.get(session_id)
        if session:
            session["is_active"] = False

    def get_active_devices(self) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        active = []
        for session_id, session in self.sessions.items():
            last = datetime.fromisoformat(session["last_activity"])
            if session["is_active"] and last > cutoff:
                active.append({"session_id": session_id, **session})
        return active

    def _cleanup_old_sessions(self):
        cutoff = datetime.utcnow() - timedelta(hours=24)
        keys_to_delete = []
        for session_id, session in self.sessions.items():
            last = datetime.fromisoformat(session["last_activity"])
            if last < cutoff:
                keys_to_delete.append(session_id)
        for key in keys_to_delete:
            del self.sessions[key]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.sessions)
        active = len(self.get_active_devices())
        protocols = {}
        for session in self.sessions.values():
            proto = session["protocol"]
            protocols[proto] = protocols.get(proto, 0) + 1
        return {
            "total_sessions": total,
            "active_sessions": active,
            "protocols": protocols,
        }
