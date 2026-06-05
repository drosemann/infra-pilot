# Feature 45: File Sharing & Sync

## Overview
Nextcloud/Seafile integration. Share links with expiry, password protection, upload-only folders, and cross-server sync.

## Components
- **Integration Service Module**: `advanced-storage/file_sharing.py` - File sharing API
- **Management Panel Page**: `advanced-storage/FileSharing.tsx` - File sharing UI
- **CLI Commands**: `ipilot storage share`

## Features
- Nextcloud/Seafile/ownCloud integration
- Share link generation with expiry
- Password-protected shares
- Upload-only drop folders
- Cross-server file sync
- File versioning
- Conflict resolution
- Bandwidth throttling
- Audit logging
- Virus scanning integration
