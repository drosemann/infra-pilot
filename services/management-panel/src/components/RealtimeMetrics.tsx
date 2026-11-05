import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../lib/api';

interface MetricPoint {
  timestamp: string;
  value: number;
}

interface RealtimeData {
  cpu: { current: number; cores: number; unit: string };
  memory: { current: number; total: number; unit: string; percent: number };
  disk: { current: number; total: number; unit: string; percent: number };
  network: { rx: number; tx: number; unit: string };
  timestamp: string;
}

interface HistoryData {
  data: Array<{ timestamp: string; cpu: number; memory: number; tps: number; players: number }>;
  period: string;
  resolution: string;
}

function SparklineChart({ data, color, height, width }: {
  data: MetricPoint[];
  color: string;
  height: number;
  width: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length < 2) return;
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvasRef.current.width = width * dpr;
    canvasRef.current.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    const values = data.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';

    data.forEach((point, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((point.value - min) / range) * (height - 4) - 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });

    ctx.stroke();

    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = color + '20';
    ctx.fill();
  }, [data, color, height, width]);

  return <canvas ref={canvasRef} style={{ width, height }} />;
}

function Gauge({ value, max, label, unit, color }: {
  value: number;
  max: number;
  label: string;
  unit: string;
  color: string;
}) {
  const percent = Math.min((value / max) * 100, 100);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div style={{ textAlign: 'center', padding: '12px' }}>
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
        <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 50 50)" strokeLinecap="round" />
        <text x="50" y="50" textAnchor="middle" dominantBaseline="central"
          fontSize="20" fontWeight="bold" fill="#e9f0ff">
          {Math.round(value)}{unit === '%' ? '%' : ''}
        </text>
      </svg>
      <div style={{ marginTop: '4px', fontSize: '12px', color: 'rgba(245,245,247,0.45)' }}>
        {label} (max: {max}{unit})
      </div>
    </div>
  );
}

function MetricCard({ title, value, unit, trend, color }: {
  title: string;
  value: string | number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  color: string;
}) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      borderRadius: '10px',
      padding: '16px',
      border: '1px solid rgba(255,255,255,0.09)',
    }}>
      <div style={{ fontSize: '12px', color: 'rgba(245,245,247,0.45)', marginBottom: '8px' }}>{title}</div>
      <div style={{ fontSize: '28px', fontWeight: '600', color: '#f5f5f7' }}>
        {value}<span style={{ fontSize: '14px', color: 'rgba(245,245,247,0.45)', marginLeft: '4px' }}>{unit}</span>
      </div>
      {trend && (
        <div style={{ fontSize: '12px', color: trend === 'up' ? '#4bd37b' : trend === 'down' ? '#f44336' : '#8b95a5', marginTop: '4px' }}>
          {trend === 'up' ? '\u2191' : trend === 'down' ? '\u2193' : '\u2192'} {trend}
        </div>
      )}
    </div>
  );
}

export default function RealtimeMetrics({ appId }: { appId?: string }) {
  const [realtime, setRealtime] = useState<RealtimeData | null>(null);
  const [history, setHistory] = useState<MetricPoint[]>([]);
  const [period, setPeriod] = useState('1h');
  const [grafanaUrl, setGrafanaUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await apiClient.getRealtimeMetrics(appId);
        setRealtime(data);
      } catch {
        /* keep last known values */
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [appId]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data: HistoryData = await apiClient.getMetricsHistory(appId, period, '5m');
        if (data.data) {
          setHistory(data.data.map((d) => ({
            timestamp: d.timestamp,
            value: d.cpu || 0,
          })));
        }
      } catch {
        setHistory([]);
      }
    };
    fetchHistory();
  }, [period, appId]);

  useEffect(() => {
    apiClient.getGrafanaUrl()
      .then(data => {
        if (data.url) setGrafanaUrl(data.url);
      })
      .catch(() => {});
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {['1h', '6h', '24h', '7d'].map(p => (
          <button key={p} onClick={() => setPeriod(p)}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              border: 'none',
              background: period === p ? '#f5f5f7' : 'rgba(255,255,255,0.06)',
              color: period === p ? '#1d1d1f' : '#f5f5f7',
              cursor: 'pointer',
              fontWeight: period === p ? '600' : '400',
            }}>
            {p}
          </button>
        ))}
      </div>

      {realtime && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '16px' }}>
          <MetricCard title="CPU Usage" value={realtime.cpu.current} unit="%" color="#4ea8ff" />
          <MetricCard title="Memory" value={Math.round(realtime.memory.percent)} unit="%" color="#7bd389" />
          <MetricCard title="Disk" value={Math.round(realtime.disk.percent)} unit="%" color="#f2c14e" />
          <MetricCard title="Network RX" value={realtime.network.rx} unit="Mbps" color="#58a6ff" />
        </div>
      )}

      {realtime && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px', marginBottom: '16px' }}>
          <Gauge value={realtime.cpu.current} max={100} label="CPU" unit="%" color="#4ea8ff" />
          <Gauge value={realtime.memory.percent} max={100} label="Memory" unit="%" color="#7bd389" />
          <Gauge value={realtime.memory.current} max={realtime.memory.total}
            label="RAM Used" unit="MB" color="#f2c14e" />
        </div>
      )}

      <div style={{
        background: 'rgba(255,255,255,0.04)',
        borderRadius: '10px',
        padding: '16px',
        border: '1px solid rgba(255,255,255,0.09)',
        marginBottom: '16px',
      }}>
        <div style={{ fontSize: '14px', fontWeight: '600', color: '#f5f5f7', marginBottom: '12px' }}>
          CPU Usage &mdash; Last {period}
        </div>
        <SparklineChart data={history} color="#4ea8ff" height={120} width={600} />
      </div>

      {grafanaUrl && (
        <div style={{
          background: 'rgba(255,255,255,0.04)',
          borderRadius: '10px',
          padding: '16px',
          border: '1px solid rgba(255,255,255,0.09)',
        }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#f5f5f7', marginBottom: '12px' }}>
            Grafana Dashboard
          </div>
          <iframe src={grafanaUrl} style={{
            width: '100%', height: '400px',
            border: 'none', borderRadius: '6px',
          }} title="Grafana Dashboard" />
        </div>
      )}
    </div>
  );
}
