# Feature 63: Session Manager

## Overview
Centralized session management with device fingerprinting, active session viewing, and remote revocation capabilities.

## Components
- `session_manager.py` - Session lifecycle management
- `device_fingerprint.py` - Device fingerprint generation
- `session_routes.py` - Session management API
- `SessionManager` - Manager class

## Features
- View all active sessions per user
- Device fingerprinting (browser, OS, screen resolution, installed fonts, canvas fingerprint)
- Remote session revocation
- Geographic location detection
- Session expiry and refresh
- Concurrent session limits
- Suspicious login detection

## API Endpoints
- `GET /auth/sessions` - List active sessions
- `GET /auth/sessions/current` - Get current session details
- `DELETE /auth/sessions/{id}` - Revoke specific session
- `DELETE /auth/sessions` - Revoke all sessions except current
- `GET /auth/sessions/activity` - Session activity log

## Session Data Model
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "device_fingerprint": {
    "user_agent": "Mozilla/5.0...",
    "platform": "Windows",
    "screen_resolution": "1920x1080",
    "timezone": "Europe/Berlin",
    "language": "de-DE",
    "canvas_hash": "abc123",
    "installed_fonts": ["Arial", "Helvetica"],
    "ip_address": "203.0.113.1"
  },
  "location": {
    "country": "DE",
    "city": "Berlin",
    "lat": 52.52,
    "lon": 13.405
  },
  "created_at": "2025-01-01T00:00:00Z",
  "last_activity": "2025-01-01T01:00:00Z",
  "expires_at": "2025-01-02T00:00:00Z",
  "is_current": true
}
```

## Suspicious Detection Rules
- New device from unrecognized location
- Multiple sessions from different geographic regions
- Impossible travel detection
- Brute force attempt indicators
