# Feature 9: Digital Twin Viewer

## Overview
3D visualization of edge devices with real-time telemetry overlay. Three.js-based interactive viewer with click-to-inspect device details and live data streaming.

## Capabilities
- 3D rendering of edge device locations with Three.js
- Real-time telemetry overlay (CPU, memory, temperature, status)
- Click-to-inspect device details panel
- Device grouping and filtering by type/status/tags
- Geolocation-aware device placement on 3D map
- Animated data flow visualization between devices
- Timeline scrubber for historical telemetry replay
- Custom 3D models per device type
- Minimap for large deployments
- AR mode for on-site device visualization

## Viewer Architecture

```
Digital Twin Viewer
  ├── 3D Engine (Three.js)
  │   ├── Scene with lighting and shadows
  │   ├── Camera controls (orbit, zoom, pan)
  │   ├── Raycaster for click detection
  │   └── Animation loop for telemetry updates
  │
  ├── Device Models
  │   ├── Raspberry Pi 4/5 (custom GLTF)
  │   ├── Jetson Nano/Orin (custom GLTF)
  │   ├── RockPi 5 (custom GLTF)
  │   ├── Generic server (procedural geometry)
  │   └── Antenna/gateway (custom GLTF)
  │
  ├── Data Layer
  │   ├── WebSocket connection for live telemetry
  │   ├── REST API for historical data
  │   ├── Device state manager
  │   └── Color-coded status indicators
  │
  └── Interaction Layer
      ├── Hover tooltip with quick stats
      ├── Click selection with detail panel
      ├── Context menu for actions
      ├── Filter/Search bar
      └── Minimap navigation
```

## Telemetry Overlay

Real-time data shown on each device node:
- Status ring (green=online, yellow=degraded, red=offline)
- CPU usage bar (animated fill)
- Memory usage bar
- Temperature indicator (blue=cool, orange=warm, red=hot)
- Network activity pulses
- Alert badge (when active alerts exist)

## Component Structure

```tsx
// Main viewer component
<DigitalTwinViewer
  devices={devices}
  telemetryStream={telemetryWs}
  onDeviceSelect={(id) => handleSelect(id)}
  onDeviceAction={(id, action) => handleAction(id, action)}
/>

// Detail panel
<DeviceDetailPanel
  device={selectedDevice}
  telemetry={deviceTelemetry}
  metrics={historicalMetrics}
  onClose={() => setSelected(null)}
>
  <DeviceInfoSection device={selectedDevice} />
  <TelemetryChart metric="cpu" data={cpuHistory} />
  <TelemetryChart metric="memory" data={memHistory} />
  <TelemetryChart metric="temperature" data={tempHistory} />
  <DeviceActions device={selectedDevice} />
</DeviceDetailPanel>
```

## Implementation
- Primary service: Management Panel (React component)
- Module: `services/management-panel/src/pages/EdgeIoT/DigitalTwinViewer.tsx`
- WebSocket backend: integration-service for telemetry streaming
- Three.js for 3D rendering with React Three Fiber
