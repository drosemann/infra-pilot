# Feature 64: Privileged Access Management (PAM)

## Overview
Just-In-Time (JIT) elevated access management with session recording, approval workflows, and privilege escalation controls.

## Components
- `pam_manager.py` - Core PAM logic
- `jit_access.py` - Just-In-Time elevation management
- `session_recorder.py` - Terminal session recording
- `pam_routes.py` - API endpoints
- `approval_workflow.py` - Approval request handling

## JIT Access Flow
1. User requests elevated access (role, duration, reason)
2. Optional: Approval request sent to authorized approvers
3. Upon approval, temporary role is granted
4. Session is recorded
5. Access auto-expires after configured duration
6. Session recording is stored for audit

## Privilege Levels
- `viewer` - Read-only access
- `operator` - Basic operations
- `admin` - Administrative tasks
- `break_glass` - Emergency super-admin (requires post-hoc justification)

## API Endpoints
- `POST /auth/pam/request` - Request elevated access
- `POST /auth/pam/approve/{request_id}` - Approve request
- `POST /auth/pam/deny/{request_id}` - Deny request
- `GET /auth/pam/requests` - List pending requests
- `GET /auth/pam/requests/history` - Access request history
- `POST /auth/pam/break-glass` - Emergency access
- `GET /auth/pam/sessions/recordings` - Session recordings

## Session Recording
- Terminal I/O capture via asciicast format
- Metadata: user, start time, end time, actions performed
- Searchable by user, time range, command patterns
- Playback via web-based terminal player
