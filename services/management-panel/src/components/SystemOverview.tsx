import { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

interface AggregatedMetrics {
  totalApps: number;
  totalPlayers: number;
  avgCpu: number;
  avgMemory: number;
  serverCount: number;
}

const formatPercent = (value: number) => `${Math.round(value)}%`;

export const SystemOverview = () => {
  const [metrics, setMetrics] = useState<AggregatedMetrics | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await apiClient.getAggregatedMetrics();
        if (active) {
          setMetrics(data);
          setUnavailable(false);
        }
      } catch {
        if (active) setUnavailable(true);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold tracking-tight text-white">System Overview</h3>

      {!metrics ? (
        <div className="card p-6 text-center">
          <p className="text-white/55">
            {unavailable ? 'Aggregated metrics unavailable.' : 'Loading system metrics…'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          <div className="card p-6">
            <p className="mb-1 text-sm text-white/45">Avg CPU</p>
            <p className="text-2xl font-semibold text-white">{Math.round(metrics.avgCpu)}%</p>
          </div>
          <div className="card p-6">
            <p className="mb-1 text-sm text-white/45">Avg Memory</p>
            <p className="text-2xl font-semibold text-white">{formatPercent(metrics.avgMemory)}</p>
          </div>
          <div className="card p-6">
            <p className="mb-1 text-sm text-white/45">Servers</p>
            <p className="text-2xl font-semibold text-white">{metrics.serverCount}</p>
          </div>
        </div>
      )}
    </div>
  );
};
