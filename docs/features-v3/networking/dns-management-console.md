# Feature 23: DNS Management Console

## Overview
Full DNS zone editor supporting A, AAAA, CNAME, MX, TXT, SRV, NS, PTR records. DNSSEC management, secondary DNS zones, and DDNS client configuration.

## Components

### Integration Service: `networking/dns_manager.py`
- `DNSZoneManager` - Core DNS management
  - Zone CRUD (primary, secondary, reverse)
  - Record CRUD for all standard types
  - DNSSEC key management and signing
  - Zone transfer (AXFR/IXFR)
  - DDNS update handling
  - Template zones for quick deployment

### Orchestrator Agent: `cogs/dns_console.py`
- Discord commands:
  - `/dns zone create` - Create DNS zone
  - `/dns zone list` - List zones
  - `/dns record add` - Add DNS record
  - `/dns record remove` - Remove DNS record
  - `/dns record list` - List records in zone
  - `/dns dnssec status` - Check DNSSEC status
  - `/dns dnssec sign` - Sign zone with DNSSEC

### Management Panel: `pages/networking/DNSPage.tsx`
- Zone editor with visual record management
- DNSSEC status dashboard
- Zone transfer configuration
- DDNS client setup
- Import/export zone files (BIND format)
- Search across all zones/records

### Mobile: `app/networking/dns.tsx`
- Zone list with record counts
- Quick record operations
- DNSSEC status check

### CLI Commands
- `ipilot dns zone create <domain>`
- `ipilot dns zone list`
- `ipilot dns record add <zone> <name> <type> <value>`
- `ipilot dns record list <zone>`

## API Endpoints
- `GET /api/networking/dns/zones` - List zones
- `POST /api/networking/dns/zones` - Create zone
- `GET /api/networking/dns/zones/{id}` - Get zone
- `PUT /api/networking/dns/zones/{id}` - Update zone
- `DELETE /api/networking/dns/zones/{id}` - Delete zone
- `GET /api/networking/dns/zones/{id}/records` - List records
- `POST /api/networking/dns/zones/{id}/records` - Create record
- `PUT /api/networking/dns/zones/{id}/records/{record_id}` - Update record
- `DELETE /api/networking/dns/zones/{id}/records/{record_id}` - Delete record
- `POST /api/networking/dns/zones/{id}/dnssec/sign` - Sign zone
- `GET /api/networking/dns/zones/{id}/dnssec/status` - DNSSEC status
- `POST /api/networking/dns/zones/{id}/transfer` - Trigger zone transfer

## Data Models

### DNSZone
- id, domain, type (primary/secondary/reverse)
- master_servers (for secondary), allowed_transfers
- serial, refresh, retry, expire, ttl
- dnssec_status (unsigned/signing/signed/error)
- dnskey_record, ds_record
- soa_record (embedded)
- nameservers list

### DNSRecord
- id, zone_id, name, type (A/AAAA/CNAME/MX/TXT/SRV/NS/PTR)
- value, priority (MX), weight (SRV), port (SRV)
- ttl, enabled, notes
- created_at, updated_at

## Implementation Details
- PowerDNS or BIND backend integration
- DNSSEC via dnssec-keygen/dnssec-signzone
- Zone file format: BIND-compatible
- REST API with PowerDNS API compatibility
- Rate limiting on DDNS updates
- Audit logging for all zone changes
- Validation of DNS record values
- TTL sanity checking

## Testing
- Zone CRUD operations
- Record validation tests
- DNSSEC signing and verification
- Zone transfer simulation
- DDNS update handling
- Large zone performance tests
