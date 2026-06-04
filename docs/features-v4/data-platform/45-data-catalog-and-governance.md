# Feature 45: Data Catalog & Governance

## Overview
Enterprise data catalog with automated metadata harvesting, search, certification workflows, and lineage tracking for governed data discovery.

## Components
- `data_catalog.py` - Catalog asset management with search and harvesting
- `cog_data_catalog.py` - Discord bot commands for catalog operations

## Data Models
- CatalogAsset - Asset with name, type (table/view/report/dashboard), schema, owner, tags, certified flag
- HarvestRun - Harvest operation with assets found, columns found, duration
- LineageNode - Asset lineage with upstream/downstream dependencies

## API Endpoints
- `GET /api/v4/data/catalog/assets` - List assets
- `POST /api/v4/data/catalog/assets` - Register asset
- `GET /api/v4/data/catalog/search` - Search assets
- `POST /api/v4/data/catalog/harvest` - Trigger metadata harvest
- `POST /api/v4/data/catalog/assets/:id/certify` - Certify asset

## Metrics
- Total cataloged assets
- Certified vs uncertified ratio
- Search usage frequency

## Discord Commands
- `/catalog list` - List catalog assets
- `/catalog search` - Search assets
- `/catalog register` - Register new asset
- `/catalog harvest` - Trigger metadata harvest
- `/catalog certify` - Certify an asset
