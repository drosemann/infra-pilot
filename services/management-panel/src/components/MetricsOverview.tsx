import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { MetricCard } from './MetricCard';

export const MetricsOverview = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiClient.getAggregatedMetrics();
        setMetrics(data);
      } catch {
        setMetrics(null);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card animate-pulse p-6">
            <div className="mb-4 h-4 w-24 rounded bg-white/10" />
            <div className="h-8 w-16 rounded bg-white/10" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        icon="ðŸ–¥ï¸"
        label="Total Servers"
        value={metrics?.serverCount || 0}
        hint="Across all apps"
      />
      <MetricCard
        icon="ðŸ‘¥"
        label="Total Players"
        value={metrics?.totalPlayers || 0}
        hint="Across all apps"
      />
      <MetricCard
        icon="âš¡"
        label="Avg CPU"
        value={`${metrics?.avgCpu || 0}%`}
        hint="Across all apps"
      />
      <MetricCard
        icon="ðŸ’¾"
        label="Avg Memory"
        value={`${metrics?.avgMemory || 0}%`}
        hint="Across all apps"
      />
    </div>
  );
};

export default MetricsOverview;
