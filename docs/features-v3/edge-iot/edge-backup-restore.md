# Feature 10: Edge Backup & Restore

## Overview
Periodic backup of edge device state including configuration, local data, ML models, and application state. Restore to the same device or a replacement device.

## Capabilities
- Scheduled full and incremental backups
- Configuration backup (system config, application config, network settings)
- Data backup (local databases, file storage, container volumes)
- ML model backup (deployed models, training data, inference results)
- Restore to same device (rollback support)
- Restore to replacement device (hardware migration)
- Backup encryption (AES-256-GCM)
- Backup integrity verification (SHA-256 checksums)
- Cloud sync for off-site backup storage
- Retention policies with auto-cleanup
- Restore dry-run mode
- Backup reports and audit log

## Backup Types

| Type | Content | Frequency | Size |
|------|---------|-----------|------|
| Full | Complete device state | Weekly | Large |
| System Config | OS configs, network, packages | Daily | Small |
| Application Data | Docker volumes, databases | Hourly | Medium |
| ML Models | Deployed TFLite/ONNX models | On-update | Large |
| Certificate | Certs, keys (encrypted) | On-change | Tiny |

## Backup Flow

```python
class EdgeBackupManager:
    """Manage backups for edge devices."""
    
    async def create_backup(self, device_id: str, 
                            backup_type: BackupType) -> BackupResult:
        device = await self.device_store.get(device_id)
        
        # 1. Create backup manifest
        manifest = BackupManifest(
            device_id=device_id,
            backup_type=backup_type,
            timestamp=datetime.utcnow(),
            device_fingerprint=device.fingerprint,
            software_version=device.agent_version
        )
        
        # 2. Collect backup data based on type
        artifacts = []
        
        if backup_type in (BackupType.FULL, BackupType.SYSTEM_CONFIG):
            config_data = await self.collect_config(device)
            artifacts.append(await self.create_artifact("config.tar.gz", config_data))
        
        if backup_type in (BackupType.FULL, BackupType.APP_DATA):
            app_data = await self.collect_app_data(device)
            artifacts.append(await self.create_artifact("data.tar.gz", app_data))
        
        if backup_type in (BackupType.FULL, BackupType.ML_MODELS):
            model_data = await self.collect_models(device)
            artifacts.append(await self.create_artifact("models.tar.gz", model_data))
        
        # 3. Encrypt artifacts
        encrypted = []
        for artifact in artifacts:
            encrypted_data = await self.crypto.encrypt(
                artifact.data, 
                self.config.backup_encryption_key
            )
            encrypted.append(Artifact(artifact.name + ".enc", encrypted_data))
        
        # 4. Create checksum manifest
        checksums = {a.name: sha256(a.data) for a in encrypted}
        manifest.checksums = checksums
        
        # 5. Store backup
        backup_id = str(uuid4())
        for artifact in encrypted:
            await self.storage.store(
                f"backups/{device_id}/{backup_id}/{artifact.name}",
                artifact.data
            )
        
        # 6. Sync to cloud if configured
        if self.config.cloud_sync_enabled:
            asyncio.create_task(self.sync_to_cloud(device_id, backup_id))
        
        return BackupResult(
            backup_id=backup_id, 
            manifest=manifest,
            size_bytes=sum(len(a.data) for a in encrypted),
            artifact_count=len(encrypted)
        )
    
    async def restore(self, device_id: str, backup_id: str,
                      target_device_id: Optional[str] = None) -> RestoreResult:
        target = target_device_id or device_id
        device = await self.device_store.get(target)
        
        # Verify target device compatibility
        backup_manifest = await self.get_manifest(device_id, backup_id)
        if not await self._check_compatibility(device, backup_manifest):
            raise RestoreError("Device incompatible with backup")
        
        # Retrieve and decrypt artifacts
        artifacts = []
        for name in backup_manifest.checksums.keys():
            encrypted = await self.storage.retrieve(
                f"backups/{device_id}/{backup_id}/{name}"
            )
            decrypted = await self.crypto.decrypt(
                encrypted, self.config.backup_encryption_key
            )
            artifacts.append(Artifact(name.replace(".enc", ""), decrypted))
        
        # Verify checksums
        for artifact in artifacts:
            expected = backup_manifest.checksums.get(artifact.name + ".enc")
            if expected and sha256(artifact.data) != expected:
                raise RestoreError(f"Checksum mismatch for {artifact.name}")
        
        # Apply artifacts
        results = []
        for artifact in artifacts:
            result = await self._apply_artifact(device, artifact)
            results.append(result)
        
        return RestoreResult(
            backup_id=backup_id,
            target_device_id=target,
            restored_artifacts=len(results),
            success=all(r.success for r in results)
        )
```

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/edge_backup_restore.py`
- CLI commands for backup and restore operations
- Management panel UI for backup management
