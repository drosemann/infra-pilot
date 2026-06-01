# Feature 47: Data Migration Wizard

## Overview
Guided migration between storage backends. rsync/rclone-based with progress, checksum verification, rollback on failure.

## Components
- **Management Panel Page**: `advanced-storage/DataMigrationWizard.tsx` - Migration wizard UI
- **Integration Service Module**: `advanced-storage/data_migration.py` - Migration engine

## Features
- Step-by-step guided migration
- Source/destination selection (S3, local, B2, etc.)
- rsync and rclone backends
- Real-time progress tracking
- Checksum verification
- Automatic rollback on failure
- Bandwidth throttling
- Incremental sync
- Email notification on completion
- Migration report
