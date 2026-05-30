# Feature 89: Geolocation Heatmap

## Overview
Map-based visualization of user/request geographic distribution with heatmap overlay and drill-down.

## Components
- Leaflet/Mapbox world map
- Heatmap overlay (density-based)
- Individual marker mode for pinpoint accuracy
- Country/region aggregation
- Time-series playback (see distribution change over time)
- Filter by: date range, service, response time, error rate
- City-level drill-down
- Color-coded regions by metric

## Data Points
- Request origin (geo-IP lookup)
- User connection location
- API call distribution
- Error distribution by region
- Latency heatmap by region
- Active users by location

## Backend API
- `POST /api/geo/ingest` - ingest geo event
- `GET /api/geo/heatmap` - get heatmap data
- `GET /api/geo/regions` - region aggregation
- `GET /api/geo/top-cities` - top N cities
- `GET /api/geo/timelapse` - time-series data
- `GET /api/geo/filter-options` - available filters
