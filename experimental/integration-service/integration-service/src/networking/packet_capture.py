import asyncio
import json
import logging
import os
import uuid
import struct
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

PROTOCOL_MAP = {
    1: 'ICMP', 6: 'TCP', 17: 'UDP',
    2: 'IGMP', 8: 'EGP', 89: 'OSPF',
    132: 'SCTP', 33: 'DCCP', 4: 'IPIP',
}

@dataclass
class CaptureSession:
    id: str
    interface_name: str
    interface_description: str
    filter: str
    status: str
    packet_count: int
    bytes_captured: int
    duration_seconds: int
    file_path: str
    file_size_bytes: int
    started_at: str
    stopped_at: str
    created_by: str

@dataclass
class CapturedPacket:
    id: str
    session_id: str
    timestamp: str
    length: int
    protocol: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    src_mac: str
    dst_mac: str
    summary: str
    hex_dump: str
    decoded_fields: Dict[str, Any]

class PacketCaptureManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.sessions_file = os.path.join(self.data_path, 'capture_sessions.json')
        self.packets_file = os.path.join(self.data_path, 'capture_packets.json')
        self.pcap_dir = os.path.join(self.data_path, 'pcaps')
        self.sessions: Dict[str, CaptureSession] = {}
        self.packets: Dict[str, CapturedPacket] = {}
        self._active_sessions: Dict[str, asyncio.Task] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.pcap_dir, exist_ok=True)
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    sess = CaptureSession(**item)
                    self.sessions[sess.id] = sess
        except Exception as e:
            logger.warning(f"Failed to load sessions: {e}")
        try:
            if os.path.exists(self.packets_file):
                with open(self.packets_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    pkt = CapturedPacket(**item)
                    self.packets[pkt.id] = pkt
        except Exception as e:
            logger.warning(f"Failed to load packets: {e}")

    def _save_data(self):
        for file_key, attr in [(self.sessions_file, 'sessions'), (self.packets_file, 'packets')]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("PacketCaptureManager initialized")

    async def close(self):
        for session_id, task in self._active_sessions.items():
            task.cancel()
        self._save_data()

    async def list_interfaces(self) -> List[Dict[str, Any]]:
        import socket
        import subprocess
        interfaces = []
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            for line in lines:
                if ':' in line and '<' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        name = parts[1].strip().split('@')[0].strip()
                        if name and name != 'lo':
                            interfaces.append({'name': name, 'description': f'Interface {name}', 'type': 'physical'})
        except:
            pass
        if not interfaces:
            interfaces = [
                {'name': 'eth0', 'description': 'Primary Ethernet', 'type': 'physical'},
                {'name': 'eth1', 'description': 'Secondary Ethernet', 'type': 'physical'},
                {'name': 'wlan0', 'description': 'Wireless LAN', 'type': 'wireless'},
                {'name': 'wwan0', 'description': 'Cellular Modem', 'type': 'cellular'},
                {'name': 'docker0', 'description': 'Docker Bridge', 'type': 'virtual'},
                {'name': 'tun0', 'description': 'VPN Tunnel', 'type': 'virtual'},
            ]
        return interfaces

    async def start_capture(self, data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        session = CaptureSession(
            id=session_id,
            interface_name=data['interface'],
            interface_description=data.get('interface_description', ''),
            filter=data.get('filter', ''),
            status='running',
            packet_count=0,
            bytes_captured=0,
            duration_seconds=0,
            file_path=os.path.join(self.pcap_dir, f'{session_id}.pcap'),
            file_size_bytes=0,
            started_at=now.isoformat(),
            stopped_at='',
            created_by=data.get('created_by', 'system'),
        )
        self.sessions[session.id] = session
        self._save_data()
        self._active_sessions[session.id] = asyncio.create_task(self._simulate_capture(session.id, data.get('duration', 30)))
        return asdict(session)

    async def _simulate_capture(self, session_id: str, duration: int):
        import random
        session = self.sessions.get(session_id)
        if not session:
            return
        start_time = time.time()
        protocols = ['TCP', 'UDP', 'ICMP', 'DNS', 'HTTP', 'TLS', 'ARP']
        ips = ['192.168.1.1', '10.0.0.1', '172.16.0.1', '8.8.8.8', '1.1.1.1', '203.0.113.5', '198.51.100.10']
        ports = [80, 443, 53, 22, 8080, 8443, 3306, 5432, 6379, 25, 993, 5222]
        while time.time() - start_time < duration:
            if session.status != 'running':
                break
            pkt_count = random.randint(5, 50)
            for _ in range(pkt_count):
                await self._generate_fake_packet(session_id, protocols, ips, ports)
            session.packet_count += pkt_count
            session.duration_seconds = int(time.time() - start_time)
            session.bytes_captured += pkt_count * random.randint(40, 1500)
            self._save_data()
            await asyncio.sleep(1)
        session.status = 'completed'
        session.stopped_at = datetime.now().isoformat()
        session.duration_seconds = int(time.time() - start_time)
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        self._save_data()

    async def _generate_fake_packet(self, session_id: str, protocols: List[str], ips: List[str], ports: List[int]):
        import random
        import hashlib
        proto = random.choice(protocols)
        src_ip = random.choice(ips)
        dst_ip = random.choice(ips)
        src_port = random.choice(ports)
        dst_port = random.choice(ports)
        length = random.randint(40, 1500)
        timestamp = datetime.now().isoformat()
        packet_id = str(uuid.uuid4())

        if proto == 'DNS':
            summary = f'Standard query A example.com'
            decoded = {'query': 'example.com', 'type': 'A', 'response': False}
        elif proto == 'HTTP':
            summary = f'GET /index.html HTTP/1.1'
            decoded = {'method': 'GET', 'path': '/index.html', 'version': '1.1', 'host': 'example.com'}
        elif proto == 'TLS':
            summary = f'Client Hello (SNI: example.com)'
            decoded = {'handshake_type': 'client_hello', 'sni': 'example.com', 'version': 'TLS 1.3'}
        elif proto == 'ARP':
            summary = f'Who has {dst_ip}? Tell {src_ip}'
            decoded = {'opcode': 'request', 'sender_ip': src_ip, 'target_ip': dst_ip}
        else:
            summary = f'{src_ip}:{src_port} > {dst_ip}:{dst_port} [{proto.upper()}]'
            decoded = {'flags': 'ACK', 'seq': random.randint(1000, 99999), 'ack': random.randint(1000, 99999), 'window': 65535}

        hex_payload = hashlib.sha256(f'{packet_id}-{timestamp}'.encode()).hexdigest()[:64]
        hex_dump = ' '.join(hex_payload[i:i+2] for i in range(0, len(hex_payload), 2))

        packet = CapturedPacket(
            id=packet_id,
            session_id=session_id,
            timestamp=timestamp,
            length=length,
            protocol=proto,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port if proto in ('TCP', 'UDP') else 0,
            dst_port=dst_port if proto in ('TCP', 'UDP') else 0,
            src_mac=f'02:00:00:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}',
            dst_mac=f'02:00:00:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}',
            summary=summary,
            hex_dump=hex_dump[:120],
            decoded_fields=decoded,
        )
        self.packets[packet.id] = packet
        if len(self.packets) > 50000:
            old_ids = sorted(self.packets.keys(), key=lambda pid: self.packets[pid].timestamp)[:10000]
            for oid in old_ids:
                del self.packets[oid]

    async def stop_capture(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.status = 'stopped'
        session.stopped_at = datetime.now().isoformat()
        if session_id in self._active_sessions:
            self._active_sessions[session_id].cancel()
            del self._active_sessions[session_id]
        self._save_data()
        return asdict(session)

    async def pause_capture(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.status = 'paused'
        self._save_data()
        return asdict(session)

    async def resume_capture(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.status = 'running'
        self._save_data()
        return asdict(session)

    async def list_sessions(self) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self.sessions.values()]

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        return asdict(session) if session else None

    async def get_packets(self, session_id: str, offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        session_packets = sorted(
            [p for p in self.packets.values() if p.session_id == session_id],
            key=lambda p: p.timestamp
        )
        return [asdict(p) for p in session_packets[offset:offset+limit]]

    async def get_statistics(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {}
        session_packets = [p for p in self.packets.values() if p.session_id == session_id]
        proto_counts: Dict[str, int] = {}
        for pkt in session_packets:
            proto_counts[pkt.protocol] = proto_counts.get(pkt.protocol, 0) + 1
        top_src = {}
        top_dst = {}
        for pkt in session_packets:
            top_src[pkt.src_ip] = top_src.get(pkt.src_ip, 0) + 1
            top_dst[pkt.dst_ip] = top_dst.get(pkt.dst_ip, 0) + 1
        return {
            'session_id': session_id,
            'total_packets': len(session_packets),
            'packets_per_second': round(len(session_packets) / max(session.duration_seconds, 1), 2),
            'total_bytes': session.bytes_captured,
            'protocol_breakdown': dict(sorted(proto_counts.items(), key=lambda x: -x[1])),
            'top_source_ips': dict(sorted(top_src.items(), key=lambda x: -x[1])[:10]),
            'top_destination_ips': dict(sorted(top_dst.items(), key=lambda x: -x[1])[:10]),
            'duration_seconds': session.duration_seconds,
        }

    async def get_pcap_download_path(self, session_id: str) -> Optional[str]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        if not os.path.exists(session.file_path):
            pcap_data = self._generate_pcap_data(session_id)
            with open(session.file_path, 'wb') as f:
                f.write(pcap_data)
            session.file_size_bytes = os.path.getsize(session.file_path)
            self._save_data()
        return session.file_path

    def _generate_pcap_data(self, session_id: str) -> bytes:
        import struct
        pcap_header = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
        data = bytearray(pcap_header)
        session_packets = sorted([p for p in self.packets.values() if p.session_id == session_id], key=lambda p: p.timestamp)
        for pkt in session_packets:
            payload = bytes(pkt.hex_dump.replace(' ', ''), 'utf-8')[:pkt.length]
            pkt_header = struct.pack('<IIII', int(time.time()), 0, len(payload), len(payload))
            data.extend(pkt_header)
            data.extend(payload)
        return bytes(data)

    async def get_packet_stream(self, session_id: str) -> Optional[asyncio.Queue]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        queue: asyncio.Queue = asyncio.Queue()
        return queue

    async def add_packet_to_stream(self, session_id: str, packet_data: Dict[str, Any]):
        pass
