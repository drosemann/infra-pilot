# Feature 82: Threat Intelligence Platform

## Overview
Crowd-sourced and commercial threat intelligence aggregation, enrichment, and analysis platform.

## Components
- **IoCs**: Indicators of Compromise (IPs, Domains, URLs, Hashes)
- **Feeds**: 12 connected threat intelligence feeds (AlienVault OTX, VirusTotal, AbuseIPDB, etc.)
- **Actors**: 8 tracked threat actor groups with TTPs
- **Enrichment**: Automated IOC enrichment via VirusTotal, AbuseIPDB, GreyNoise, Shodan

## Data Models
- IOC: id, type, value, confidence, severity, source, first_seen, last_seen
- Feed: id, name, type, status, url, api_key (encrypted), last_fetch
- Actor: id, name, aliases, motivation, sectors_targeted, ttps

## API Endpoints
- GET /api/soc/ti/iocs - List IoCs
- POST /api/soc/ti/iocs - Add IOC
- GET /api/soc/ti/iocs/:id - Get IOC details
- DELETE /api/soc/ti/iocs/:id - Delete IOC
- GET /api/soc/ti/feeds - List feeds
- POST /api/soc/ti/feeds - Add feed
- POST /api/soc/ti/enrich - Enrich IOC
- GET /api/soc/ti/actors - List actors

## Metrics
- Total IoCs: 1,247
- New IoCs (24h): 35
- Feeds: 12 (10 active)
- Enrichment Match Rate: 62%
- Avg Enrich Time: 1.3s

## Discord Commands
- /tip - View threat intel summary
- /tip iocs - List IoCs
- /tip feeds - List feeds
- /tip actors - List actors
- /tip enrich - Enrich an IOC
- /tip stats - Platform statistics
