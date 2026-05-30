# Feature 86: Dependency Graph Viewer

## Overview
Interactive force-directed graph visualization of service dependencies with health status, impact analysis, and relationship exploration.

## Components
- Canvas-based force-directed layout
- Zoom, pan, and search/filter
- Node status indicators (healthy/warning/error/unknown)
- Edge type coloring (HTTP, gRPC, DB, messaging)
- Impact analysis: highlight affected downstream services
- Legend for node/edge type reference
- PNG export of current view

## Backend API
- `GET /api/v3/dependencies/graph` - full dependency graph
- `GET /api/v3/dependencies/impact/:nodeId` - impact analysis
- `POST /api/v3/dependencies/discover` - auto-discover dependencies
