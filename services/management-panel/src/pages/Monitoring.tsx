import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { DockerApp } from '../lib/types';
import { MetricsOverview } from '../components/MetricsOverview';
import { PerformanceChart } from '../components/PerformanceChart';
import { PlayerCountChart } from '../components/PlayerCountChart';
import { ResourceMonitor } from '../components/ResourceMonitor';
import { HealthCheckDashboard } from '../components/HealthCheckDashboard';
import RealtimeMetrics from '../components/RealtimeMetrics';
import { PageHeader } from '../components/PageHeader';

export const Monitoring = () => {
  const [apps, setApps] = useState<DockerApp[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [tpsData, setTpsData] = useState<number[]>([]);
  const [playerData, setPlayerData] = useState<Array<{ time: string; count: number }>>([]);
  const [timeRange, setTimeRange] = useState<'5m' | '30m' | '1h'>('30m');
  const [showHealth, setShowHealth] = useState(false);
  const [showRealtime, setShowRealtime] = useState(false);
  const [hasMetrics, setHasMetrics] = useState(false);

  useEffect(() => {
    apiClient.listApps().then(setApps).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedApp) return;
    const loadMetrics = async () => {
      try {
        const metrics = await apiClient.getServerMetrics(selectedApp, timeRange);
        setTpsData(metrics.map((m) => m.tps || 0));
        setPlayerData(
          metrics.map((m) => ({
            time: new Date(m.recorded_at).toLocaleTimeString(),
            count: m.player_count,
          }))
        );
        setHasMetrics(metrics.length > 0);
      } catch {
        setTpsData([]);
        setPlayerData([]);
        setHasMetrics(false);
      }
    };
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, [selectedApp, timeRange]);

  return (
    <div className="mx-auto max-w-5xl space-y-12 px-2 py-8">
      <PageHeader
        eyebrow="Observe"
        actions={
          <div className="flex items-center gap-3">
            <select
              value={selectedApp}
              onChange={(e) => setSelectedApp(e.target.value)}
              className="input-field w-auto text-sm"
              aria-label="Select server"
            >
              <option value="">All servers</option>
              {apps.map((app) => (
                <option key={app.id} value={app.id}>{app.name}</option>
              ))}
            </select>
            <button
              onClick={() => { setShowRealtime(!showRealtime); setShowHealth(false); }}
              className={showRealtime ? "primary-button" : "secondary-button"}
            >
              Realtime
            </button>
            <button
              onClick={() => { setShowHealth(!showHealth); setShowRealtime(false); }}
              className={showHealth ? "primary-button" : "secondary-button"}
            >
              Health Checks
            </button>
          </div>
        }
      >
        <h1 className="text-4xl font-semibold tracking-tight text-white">Monitoring</h1>
        <p className="mt-2 text-white/55">Server performance and health.</p>
      </PageHeader>

      {showRealtime ? (
        <div className="card p-6">
          <RealtimeMetrics appId={selectedApp || undefined} />
        </div>
      ) : showHealth ? (
        <HealthCheckDashboard />
      ) : (
        <>
          <MetricsOverview />

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold tracking-tight text-white">
                {selectedApp ? 'Server Performance' : 'Resource Overview'}
              </h2>
              <div className="flex gap-2">
                {(['5m', '30m', '1h'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                      timeRange === range
                        ? 'bg-white text-black'
                        : 'text-white/55 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>

            {!selectedApp ? (
              <p className="text-sm text-white/45">Select a server above to see performance charts.</p>
            ) : !hasMetrics ? (
              <div className="card p-12 text-center">
                <p className="text-white/55">No metrics yet for this server.</p>
                <p className="mt-2 text-sm text-white/35">Charts appear once the agent reports data.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <PerformanceChart
                  data={tpsData}
                  label="TPS"
                  value={tpsData.length > 0 ? String(Math.round(tpsData[tpsData.length - 1])) : '0'}
                />
                <PlayerCountChart data={playerData} />
              </div>
            )}
          </div>

          <ResourceMonitor />
        </>
      )}
    </div>
  );
};

export default Monitoring;
