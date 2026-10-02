import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { BackupArtifact } from '../lib/types';

const formatSize = (bytes: number) => {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(0)} KB`;
  return `${bytes} B`;
};

const formatAge = (mtimeMs: number) => {
  const mins = Math.max(0, Math.round((Date.now() - mtimeMs) / 60000));
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
};

// Read-only list of db-backup.sh artifacts. No restore, no scheduler.
export const BackupArtifacts = () => {
  const [artifacts, setArtifacts] = useState<BackupArtifact[]>([]);
  const [lastSuccess, setLastSuccess] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .getBackupArtifacts()
      .then((res) => {
        setArtifacts(res.artifacts);
        setLastSuccess(res.last_success_epoch);
      })
      .catch(() => setArtifacts([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-slate-400 py-4">Loading backup files...</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-md font-semibold text-white">Backup Files</h4>
        <span className="text-xs text-slate-400">
          {lastSuccess
            ? `Last success: ${new Date(lastSuccess * 1000).toLocaleString()}`
            : 'No successful backup yet'}
        </span>
      </div>
      {artifacts.length === 0 ? (
        <p className="text-slate-500 text-sm">No backup files found</p>
      ) : (
        <div className="space-y-1">
          {artifacts.slice(0, 10).map((a) => (
            <div
              key={a.name}
              className="flex items-center justify-between text-xs bg-slate-800 border border-slate-700 rounded-lg px-3 py-2"
            >
              <span className="text-slate-200 truncate mr-3">{a.name}</span>
              <span className="text-slate-500 whitespace-nowrap">
                {formatSize(a.size_bytes)} · {formatAge(a.mtime_ms)} · sha256{' '}
                {a.sha256_present ? '✓' : '—'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BackupArtifacts;
