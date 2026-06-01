# Feature 27: Packet Capture Studio

## Overview
Web-based tcpdump/Wireshark interface for network packet capture. Start capture on any interface, live-stream packets to browser via WebSocket, apply display filters, and download PCAP files.

## Components

### Integration Service: `networking/packet_capture.py`
- `PacketCaptureManager` - Core packet capture management
  - Capture session lifecycle (start/stop/pause/resume)
  - Interface discovery (available network interfaces)
  - Capture filter management (BPF syntax)
  - PCAP file storage and retrieval
  - WebSocket live streaming of packets
  - Protocol dissection (basic layer 2/3/4)
  - Capture statistics (packets/sec, bytes/sec)

### Management Panel: `pages/networking/PacketCapturePage.tsx`
- Interface selection and status
- Capture control panel (start/stop/pause)
- Live packet stream viewer
- BPF filter input with syntax validation
- Protocol breakdown pie chart
- Packet detail inspector
- PCAP download and export
- Capture history and saved captures

### CLI Commands
- `ipilot capture start --interface eth0 --filter "tcp port 80"`
- `ipilot capture list`
- `ipilot capture stop <capture_id>`
- `ipilot capture download <capture_id>`

## API Endpoints
- `GET /api/networking/capture/interfaces` - List interfaces
- `POST /api/networking/capture/sessions` - Start capture
- `GET /api/networking/capture/sessions` - List sessions
- `GET /api/networking/capture/sessions/{id}` - Get session details
- `POST /api/networking/capture/sessions/{id}/stop` - Stop capture
- `POST /api/networking/capture/sessions/{id}/pause` - Pause capture
- `POST /api/networking/capture/sessions/{id}/resume` - Resume capture
- `GET /api/networking/capture/sessions/{id}/download` - Download PCAP
- `GET /api/networking/capture/sessions/{id}/packets` - Get packet list
- `GET /api/networking/capture/sessions/{id}/stream` - WebSocket stream
- `GET /api/networking/capture/sessions/{id}/statistics` - Capture stats

## Data Models

### CaptureSession
- id, interface_name, interface_description
- filter (BPF syntax), status (running/paused/stopped/completed)
- packet_count, bytes_captured, duration_seconds
- file_path (PCAP storage), file_size_bytes
- started_at, stopped_at, created_by

### CapturedPacket
- id, session_id, timestamp (nanosecond precision)
- length, protocol (TCP/UDP/ICMP/ARP/DNS/HTTP/TLS)
- src_ip, dst_ip, src_port, dst_port
- src_mac, dst_mac
- summary (one-line description)
- hex_dump (hexadecimal + ASCII representation)
- decoded_fields (JSON of parsed protocol fields)

## Implementation Details
- tcpdump/libpcap backend for capture
- Python pcapy/Scapy for programmatic capture
- WebSocket streaming with binary framing
- BPF filter validation before capture start
- PCAPNG format for stored captures
- Ring buffer capture to limit disk usage
- Protocol dissection: Ethernet, IPv4, IPv6, TCP, UDP, ICMP, ARP, DNS, HTTP, TLS
- WireShark-compatible output format
- Capture statistics every second
- Auto-stop on configurable size/duration limits

## Testing
- Capture session lifecycle
- BPF filter validation
- Protocol dissection accuracy
- WebSocket streaming
- PCAP file format compliance
- Concurrent capture sessions
- Ring buffer overflow handling
