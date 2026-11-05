import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { AlertHistoryEntry } from '../lib/types';

export const AlertHistory = () => {
  const [alerts, setAlerts] = useState<AlertHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setAlerts(await apiClient.getAlertHistory());
      } catch {
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (id: number) => {
    try {
      await apiClient.acknowledgeAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
    } catch {
      // silent
    }
  };

  if (loading) {
    return <div className="py-4 text-white/45">Loading alert history…</div>;
  }

  if (alerts.length === 0) {
    return (
      <div className="card p-6 text-center">
        <p className="text-white/55">No alerts triggered yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
            alert.acknowledged
              ? 'border-white/5 bg-white/[0.02]'
              : 'border-red-500/30 bg-white/[0.02]'
          }`}
        >
          <div className="flex items-center gap-3">
            <span className={`w-2 h-2 rounded-full ${alert.acknowledged ? 'bg-white/30' : 'bg-red-500 animate-pulse'}`} />
            <div>
              <p className="text-sm text-white">
                {alert.metric_type} was {alert.metric_value} ({alert.operator} {alert.threshold})
              </p>
              <p className="text-xs text-white/40">
                {new Date(alert.triggered_at).toLocaleString()}
              </p>
            </div>
          </div>
          {!alert.acknowledged && (
            <button
              onClick={() => handleAcknowledge(alert.id)}
              className="primary-button"
            >
              Acknowledge
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

export default AlertHistory;
