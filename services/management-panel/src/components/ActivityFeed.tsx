import { useState } from 'react';
import { Filter, Download, Clock, User, AlertTriangle, Info, AlertCircle } from 'lucide-react';
import { apiClient } from '../lib/api';
import { apiClientEffect, useEffectful } from '../lib/effect';
import type { ActivityEvent } from '../lib/types';

const severityIcons = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
};

const severityColors = {
  info: 'text-blue-400 bg-blue-500/10',
  warning: 'text-amber-400 bg-amber-500/10',
  error: 'text-red-400 bg-red-500/10',
};

const eventTypeLabels: Record<string, string> = {
  'app:create': 'App Created',
  'app:update': 'App Updated',
  'app:delete': 'App Deleted',
  'app:start': 'App Started',
  'app:stop': 'App Stopped',
  'app:restart': 'App Restarted',
  'backup:create': 'Backup Created',
  'backup:update': 'Backup Updated',
  'backup:delete': 'Backup Deleted',
  'config:update': 'Config Updated',
  deployment: 'Deployment',
  alert: 'Alert Triggered',
  maintenance: 'Maintenance',
  'user:login': 'User Login',
  'user:logout': 'User Logout',
  'database:create': 'Database Created',
  'database:delete': 'Database Deleted',
  'knowledge_base:create': 'KB Article Created',
  'knowledge_base:update': 'KB Article Updated',
  'knowledge_base:delete': 'KB Article Deleted',
};

interface ActivityFeedProps {
  limit?: number;
  compact?: boolean;
}

export function ActivityFeed({ limit = 50, compact = false }: ActivityFeedProps) {
  const [offset, setOffset] = useState(0);
  const [typeFilter, setTypeFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const { data, loading, refresh } = useEffectful(
    () => apiClientEffect.getActivityFeed({
      limit,
      offset,
      type: typeFilter || undefined,
      from: dateFrom || undefined,
      to: dateTo || undefined,
    }),
    [limit, offset, typeFilter, dateFrom, dateTo]
  );

  const events = data?.events ?? [];
  const total = data?.total ?? 0;
  const hasMore = offset + limit < total;

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const blob = await apiClient.exportActivity({
        format,
        type: typeFilter || undefined,
        from: dateFrom || undefined,
        to: dateTo || undefined,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `activity-export.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      console.error('Export failed');
    }
  };

  const loadMore = () => setOffset(o => o + limit);

  return (
    <div className="space-y-4">
      {!compact && (
        <div className="card flex flex-wrap items-center gap-3 p-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-white/40" />
            <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="input-field w-auto text-sm">
              <option value="">All Events</option>
              {Object.entries(eventTypeLabels).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input-field w-auto text-sm" />
            <span className="text-xs text-white/40">to</span>
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input-field w-auto text-sm" />
          </div>
          <div className="flex items-center gap-1 ml-auto">
            <button onClick={() => handleExport('csv')} className="secondary-button">
              <Download className="w-3 h-3" /> CSV
            </button>
            <button onClick={() => handleExport('json')} className="secondary-button">
              <Download className="w-3 h-3" /> JSON
            </button>
          </div>
        </div>
      )}

      <div className="card divide-y divide-white/5">
        {loading && events.length === 0 ? (
          <div className="py-8 text-center text-white/45">Loading...</div>
        ) : events.length === 0 ? (
          <div className="py-8 text-center text-white/45">No activity events found</div>
        ) : events.map(event => {
          const SevIcon = severityIcons[event.severity];
          return (
            <div key={event.id} className="flex items-start gap-3 p-4">
              <div className={`p-1.5 rounded-full ${severityColors[event.severity]}`}>
                <SevIcon className="w-3.5 h-3.5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                    event.severity === 'error' ? 'bg-red-500/10 text-red-400' :
                    event.severity === 'warning' ? 'bg-amber-500/10 text-amber-400' :
                    'bg-blue-500/10 text-blue-400'
                  }`}>
                    {eventTypeLabels[event.type] || event.type}
                  </span>
                  {event.userName && (
                    <span className="flex items-center gap-1 text-xs text-white/40">
                      <User className="w-3 h-3" />
                      {event.userName}
                    </span>
                  )}
                </div>
                <p className="text-sm text-white/70">{event.description}</p>
                <span className="flex items-center gap-1 text-xs text-white/40 mt-1">
                  <Clock className="w-3 h-3" />
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {hasMore && (
        <div className="text-center">
          <button onClick={loadMore} className="secondary-button">
            Load More ({total - offset - limit} remaining)
          </button>
        </div>
      )}
    </div>
  );
}
