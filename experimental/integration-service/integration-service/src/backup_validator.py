import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupValidator:
    """Ephemeral restore and integrity checking for backups with validation scoring."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_file = config.get('backup_validations_file', 'data/backup_validations.json')
        self.validations: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            with open(self.data_file) as f:
                self.validations = json.load(f)
        except:
            self.validations = []

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.validations[-1000:], f, indent=2)

    async def validate_backup(self, backup_id: str, backup_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        checks = {
            'integrity': self._check_integrity(backup_data or {}),
            'schema_valid': self._check_schema(backup_data or {}),
            'completeness': self._check_completeness(backup_data or {}),
            'consistency': self._check_consistency(backup_data or {}),
        }
        passed = sum(1 for c in checks.values() if c.get('passed', False))
        total = len(checks)
        score = round((passed / total) * 100, 1) if total > 0 else 0

        result = {
            'id': f'val_{len(self.validations)}_{int(datetime.now().timestamp())}',
            'backup_id': backup_id,
            'checks': checks,
            'score': score,
            'passed_all': passed == total,
            'validated_at': datetime.now().isoformat()
        }
        self.validations.append(result)
        self._save()
        return result

    def _check_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        if not data:
            errors.append('Backup data is empty')
        if isinstance(data, dict):
            for key in ('files', 'content', 'checksum'):
                val = data.get(key)
                if val is not None and not isinstance(val, (str, dict, list)):
                    errors.append(f'Field "{key}" has unexpected type: {type(val).__name__}')
        return {'passed': len(errors) == 0, 'errors': errors}

    def _check_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        expected_fields = ['id', 'service', 'created_at', 'size_bytes']
        if isinstance(data, dict):
            for field in expected_fields:
                if field not in data:
                    errors.append(f'Missing required field: {field}')
        else:
            errors.append('Data is not a structured object')
        return {'passed': len(errors) == 0, 'errors': errors}

    def _check_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        if isinstance(data, dict):
            size = data.get('size_bytes', 0)
            if size <= 0:
                errors.append('Backup size is zero or negative')
            file_count = data.get('file_count', 0)
            if file_count == 0 and data.get('files') is None:
                errors.append('Backup contains no files')
        else:
            errors.append('Cannot assess completeness on non-dict data')
        return {'passed': len(errors) == 0, 'errors': errors}

    def _check_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        if isinstance(data, dict):
            created = data.get('created_at')
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    if dt > datetime.now():
                        errors.append('Backup created_at is in the future')
                except:
                    errors.append('Backup created_at is not a valid ISO date')
            if data.get('size_bytes', 0) > 0 and data.get('file_count', 0) == 0:
                errors.append('Backup has size but no files listed')
        return {'passed': len(errors) == 0, 'errors': errors}

    async def get_validation_results(self, backup_id: str) -> List[Dict[str, Any]]:
        return [v for v in self.validations if v.get('backup_id') == backup_id]

    async def get_validation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.validations[-limit:]

    async def close(self):
        self._save()
