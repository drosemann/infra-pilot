import { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

export const ResourceDistribution = () => {
  const [shares, setShares] = useState<Array<{ name: string; value: number; color: string }> | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const stats = await apiClient.getRealtimeMetrics();
        if (!active) return;
        setShares([
          { name: 'CPU', value: Math.round(stats.cpu.current), color: '#3b82f6' },
          { name: 'Memory', value: Math.round(stats.memory.percent), color: '#a855f7' },
          { name: 'Disk', value: Math.round(stats.disk.percent), color: '#06b6d4' },
        ]);
        setUnavailable(false);
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

  if (!shares) {
    return (
      <div className="space-y-4">
        <h3 className="text-xl font-semibold tracking-tight text-white">Resource Distribution</h3>
        <div className="card p-6 text-center">
          <p className="text-white/55">
            {unavailable ? 'Host metrics unavailable.' : 'Loading…'}
          </p>
        </div>
      </div>
    );
  }

  const total = shares.reduce((sum, r) => sum + r.value, 0) || 1;
  let currentAngle = -90; // Start from top

  const segments = shares.map((resource) => {
    const sliceAngle = (resource.value / total) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + sliceAngle;

    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const x1 = 50 + 45 * Math.cos(startRad);
    const y1 = 50 + 45 * Math.sin(startRad);
    const x2 = 50 + 45 * Math.cos(endRad);
    const y2 = 50 + 45 * Math.sin(endRad);

    const largeArc = sliceAngle > 180 ? 1 : 0;

    const path = [
      `M 50 50`,
      `L ${x1} ${y1}`,
      `A 45 45 0 ${largeArc} 1 ${x2} ${y2}`,
      'Z',
    ].join(' ');

    currentAngle = endAngle;

    return { ...resource, path };
  });

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold tracking-tight text-white">Resource Distribution</h3>

      <div className="grid grid-cols-2 gap-6">
        <div className="card flex items-center justify-center p-6">
          <svg width="160" height="160" viewBox="0 0 100 100">
            {segments.map((segment) => (
              <path
                key={segment.name}
                d={segment.path}
                fill={segment.color}
                opacity="0.85"
              />
            ))}
            <circle cx="50" cy="50" r="25" fill="#101014" />
          </svg>
        </div>

        <div className="space-y-3">
          {shares.map((resource) => (
            <div key={resource.name} className="card flex items-center justify-between p-3">
              <div className="flex items-center gap-3">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: resource.color }}
                />
                <span className="text-sm text-white/60">{resource.name}</span>
              </div>
              <span className="text-sm font-semibold text-white">{resource.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
