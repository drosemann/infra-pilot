# Feature 26: Network Segmentation Designer

## Overview
Drag-and-drop VLAN/subnet designer with automatic firewall rule generation from topology diagrams. Compliance checks for PCI segment isolation and other regulatory requirements.

## Components

### Integration Service: `networking/segmentation.py`
- `NetworkSegmentationManager` - Core segmentation management
  - VLAN CRUD with 802.1Q tagging
  - Subnet design and CIDR allocation
  - Topology graph management (nodes, edges, segments)
  - Automatic firewall rule generation
  - Compliance checking (PCI, HIPAA, SOC2)
  - IP address management (IPAM)
  - Segment isolation validation

### Management Panel: `pages/networking/SegmentationPage.tsx`
- Drag-and-drop topology canvas (React Flow)
- VLAN/subnet creation sidebar
- Firewall rule preview and editor
- Compliance check results panel
- IPAM table with usage stats
- Export to NetBox/Infoblox format

### CLI Commands
- `ipilot network segment create --name <name> --cidr <cidr>`
- `ipilot network segment list`
- `ipilot network segment connect <seg1> <seg2> --firewall <rules>`

## API Endpoints
- `GET /api/networking/segments` - List segments
- `POST /api/networking/segments` - Create segment
- `GET /api/networking/segments/{id}` - Get segment details
- `PUT /api/networking/segments/{id}` - Update segment
- `DELETE /api/networking/segments/{id}` - Delete segment
- `GET /api/networking/segments/{id}/topology` - Get topology
- `PUT /api/networking/segments/{id}/topology` - Update topology
- `POST /api/networking/segments/{id}/connect` - Connect segments
- `POST /api/networking/segments/{id}/disconnect` - Disconnect segments
- `GET /api/networking/segments/{id}/firewall-rules` - Generated firewall rules
- `POST /api/networking/segments/{id}/compliance-check` - Check compliance
- `GET /api/networking/ipam` - IP address management
- `POST /api/networking/ipam/reserve` - Reserve IP address

## Data Models

### NetworkSegment
- id, name, description, vlan_id (1-4094)
- cidr, gateway, netmask
- segment_type (public/private/dmz/management/iot/pci)
- color (for topology visualization), tags
- parent_segment_id (for hierarchical segments)
- dhcp_range_start, dhcp_range_end

### TopologyNode
- id, segment_id, type (segment/router/firewall/server)
- label, position_x, position_y
- config (JSON)

### TopologyEdge
- id, source_node, target_node
- type (trunk/access/routed), firewall_rules (JSON)
- bandwidth, latency

### FirewallRule
- id, segment_pair_id, direction (ingress/egress)
- protocol (tcp/udp/icmp/any), source_cidr, dest_cidr
- port_range, action (allow/deny/reject)
- log, description

## Implementation Details
- React Flow for drag-and-drop canvas
- CIDR calculator for subnet validation
- Firewall rule generation from topology
- Compliance templates for PCI DSS v4.0, HIPAA, SOC 2
- VLAN assignment via SNMP/netlink
- IPAM with subnet allocation tracking
- Export formats: NetBox JSON, Infoblox CSV
- Integration with firewall backends (iptables, nftables, pfSense)

## Testing
- Topology CRUD operations
- Firewall rule generation accuracy
- Compliance check scenarios
- VLAN ID collision detection
- IPAM allocation correctness
- Export format validation
