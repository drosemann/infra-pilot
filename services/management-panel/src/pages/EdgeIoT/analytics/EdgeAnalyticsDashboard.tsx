import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { AlertTriangle, Activity, Cpu, HardDrive, MemoryStick, Wifi, TrendingUp, BarChart3, Download, RefreshCw, Search, Filter, Clock, Zap, Thermometer, Gauge, PieChart, LineChart, Table } from 'lucide-react';

interface MetricPoint {
  timestamp: string;
  value: number;
  label?: string;
}

interface MetricSummary {
  avg: number;
  max: number;
  min: number;
  p95: number;
  p99: number;
  samples: number;
}

interface AnalyticsReport {
  generated_at: string;
  time_range: { start: string; end: string };
  metrics_summary: Record<string, MetricSummary>;
  overall_status: string;
  alerts: string[];
}

const METRIC_CATEGORIES: Record<string, { icon: React.ReactNode; color: string }> = {
  'iot.temperature': { icon: <Thermometer className="h-4 w-4" />, color: 'text-red-500' },
  'iot.humidity': { icon: <Activity className="h-4 w-4" />, color: 'text-blue-500' },
  'iot.power_consumption': { icon: <Zap className="h-4 w-4" />, color: 'text-yellow-500' },
  'edge.cpu_usage': { icon: <Cpu className="h-4 w-4" />, color: 'text-purple-500' },
  'edge.memory_usage': { icon: <MemoryStick className="h-4 w-4" />, color: 'text-green-500' },
  'edge.disk_usage': { icon: <HardDrive className="h-4 w-4" />, color: 'text-orange-500' },
  'edge.network_throughput': { icon: <Wifi className="h-4 w-4" />, color: 'text-cyan-500' },
  'edge.response_time': { icon: <Clock className="h-4 w-4" />, color: 'text-pink-500' },
  'edge.error_rate': { icon: <AlertTriangle className="h-4 w-4" />, color: 'text-red-600' },
};

const dummyMetrics: Record<string, MetricPoint[]> = {
  'edge.cpu_usage': Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    value: 30 + Math.random() * 60,
  })),
  'edge.memory_usage': Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    value: 40 + Math.random() * 50,
  })),
  'edge.network_throughput': Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    value: 200 + Math.random() * 800,
  })),
  'iot.temperature': Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    value: 18 + Math.random() * 15,
  })),
};

const dummyReport: AnalyticsReport = {
  generated_at: new Date().toISOString(),
  time_range: { start: new Date(Date.now() - 86400000).toISOString(), end: new Date().toISOString() },
  metrics_summary: {
    'edge.cpu_usage': { avg: 45.2, max: 92.1, min: 12.3, p95: 85.4, p99: 90.1, samples: 1440 },
    'edge.memory_usage': { avg: 62.8, max: 95.5, min: 30.1, p95: 88.2, p99: 93.7, samples: 1440 },
    'edge.disk_usage': { avg: 55.3, max: 78.9, min: 42.1, p95: 72.4, p99: 76.8, samples: 1440 },
    'edge.network_throughput': { avg: 456.7, max: 985.2, min: 102.3, p95: 876.5, p99: 945.1, samples: 1440 },
    'edge.response_time': { avg: 125.4, max: 890.2, min: 15.3, p95: 450.2, p99: 720.5, samples: 1440 },
    'edge.error_rate': { avg: 0.8, max: 5.2, min: 0.0, p95: 2.8, p99: 4.1, samples: 1440 },
    'iot.temperature': { avg: 24.5, max: 38.2, min: 18.1, p95: 32.5, p99: 35.8, samples: 1440 },
    'iot.humidity': { avg: 58.3, max: 82.1, min: 35.2, p95: 75.4, p99: 79.8, samples: 1440 },
    'iot.power_consumption': { avg: 125.6, max: 245.3, min: 45.2, p95: 210.5, p99: 230.1, samples: 1440 },
    'iot.signal_strength': { avg: -62.3, max: -45.1, min: -85.2, p95: -48.5, p99: -46.2, samples: 1440 },
  },
  overall_status: 'healthy',
  alerts: [],
};

const MiniSparkline: React.FC<{ data: MetricPoint[]; width?: number; height?: number; color?: string }> = ({ data, width = 120, height = 30, color = '#10b981' }) => {
  if (!data.length) return null;
  const max = Math.max(...data.map(d => d.value));
  const min = Math.min(...data.map(d => d.value));
  const range = max - min || 1;
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d.value - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  });
  return (
    <svg width={width} height={height} className="inline-block">
      <polyline points={points.join(' ')} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
};

const StatCard: React.FC<{ title: string; value: string; subtitle?: string; icon: React.ReactNode; trend?: 'up' | 'down' | 'stable'; color?: string }> = ({ title, value, subtitle, icon, trend, color }) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <div className={color || 'text-muted-foreground'}>{icon}</div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      {trend && (
        <Badge variant={trend === 'up' ? 'destructive' : trend === 'down' ? 'secondary' : 'outline'} className="mt-2">
          {trend === 'up' ? '↑ Increasing' : trend === 'down' ? '↓ Decreasing' : '→ Stable'}
        </Badge>
      )}
    </CardContent>
  </Card>
);

const MetricBar: React.FC<{ name: string; metric: MetricSummary }> = ({ name, metric }) => {
  const meta = METRIC_CATEGORIES[name] || { icon: <Activity className="h-4 w-4" />, color: 'text-gray-500' };
  const avgPct = Math.min(100, (metric.avg / 100) * 100);
  const barColor = avgPct > 80 ? 'bg-red-500' : avgPct > 60 ? 'bg-yellow-500' : 'bg-green-500';
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={meta.color}>{meta.icon}</span>
          <span className="text-sm font-medium">{name}</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <MiniSparkline data={dummyMetrics[name] || []} />
          <span>avg {metric.avg.toFixed(1)}</span>
          <span>p95 {metric.p95.toFixed(1)}</span>
          <span>p99 {metric.p99.toFixed(1)}</span>
        </div>
      </div>
      <div className="w-full bg-secondary rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${barColor}`} style={{ width: `${avgPct}%` }} />
      </div>
    </div>
  );
};

interface AlertBannerProps {
  report: AnalyticsReport;
  onDismiss: () => void;
}

const AlertBanner: React.FC<AlertBannerProps> = ({ report, onDismiss }) => {
  if (report.overall_status === 'healthy' && !report.alerts.length) return null;
  const isWarning = report.overall_status === 'degraded';
  return (
    <div className={`p-4 rounded-lg mb-6 flex items-start gap-3 ${isWarning ? 'bg-yellow-50 border border-yellow-200' : 'bg-red-50 border border-red-200'}`}>
      <AlertTriangle className={`h-5 w-5 mt-0.5 ${isWarning ? 'text-yellow-600' : 'text-red-600'}`} />
      <div className="flex-1">
        <p className={`font-medium ${isWarning ? 'text-yellow-800' : 'text-red-800'}`}>
          System {isWarning ? 'Degraded' : 'Alerts'}
        </p>
        {report.alerts.slice(0, 3).map((alert, i) => (
          <p key={i} className={`text-sm mt-1 ${isWarning ? 'text-yellow-700' : 'text-red-700'}`}>{alert}</p>
        ))}
      </div>
      <Button variant="ghost" size="sm" onClick={onDismiss}>Dismiss</Button>
    </div>
  );
};

export default function EdgeAnalyticsDashboard() {
  const [report, setReport] = useState<AnalyticsReport>(dummyReport);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const filteredMetrics = Object.entries(report.metrics_summary).filter(([name]) =>
    name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => {
      setReport(prev => ({
        ...prev,
        generated_at: new Date().toISOString(),
        metrics_summary: Object.fromEntries(
          Object.entries(prev.metrics_summary).map(([k, v]) => [k, { ...v, avg: v.avg * (0.9 + Math.random() * 0.2) }])
        ),
      }));
      setRefreshing(false);
    }, 1000);
  }, []);

  const handleExport = useCallback((format: string) => {
    const data = format === 'csv'
      ? ['metric,avg,max,min,p95,p99,samples', ...Object.entries(report.metrics_summary).map(([k, v]) => `${k},${v.avg},${v.max},${v.min},${v.p95},${v.p99},${v.samples}`)].join('\n')
      : JSON.stringify(report, null, 2);
    const blob = new Blob([data], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `edge-analytics-${Date.now()}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [report]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Edge & IoT Analytics</h1>
          <p className="text-muted-foreground mt-1">Real-time monitoring and analysis of edge devices and IoT sensor networks</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Time Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="6h">Last 6 Hours</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => handleExport('csv')}><Download className="h-4 w-4 mr-2" />CSV</Button>
          <Button variant="outline" onClick={() => handleExport('json')}><Download className="h-4 w-4 mr-2" />JSON</Button>
          <Button onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </div>

      <AlertBanner report={report} onDismiss={() => setReport(prev => ({ ...prev, alerts: [], overall_status: 'healthy' }))} />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Devices" value="1,247" subtitle="Active edge nodes" icon={<Cpu className="h-4 w-4" />} trend="up" color="text-purple-500" />
        <StatCard title="Avg CPU Usage" value={`${report.metrics_summary['edge.cpu_usage']?.avg.toFixed(1) || 'N/A'}%`} subtitle="Across all nodes" icon={<Activity className="h-4 w-4" />} trend="stable" color="text-blue-500" />
        <StatCard title="Avg Response Time" value={`${report.metrics_summary['edge.response_time']?.avg.toFixed(0) || 'N/A'}ms`} subtitle="P95: ${report.metrics_summary['edge.response_time']?.p95.toFixed(0)}ms" icon={<Clock className="h-4 w-4" />} color="text-pink-500" />
        <StatCard title="Error Rate" value={`${report.metrics_summary['edge.error_rate']?.avg.toFixed(2) || 'N/A'}%`} subtitle="P99: ${report.metrics_summary['edge.error_rate']?.p99.toFixed(2)}%" icon={<AlertTriangle className="h-4 w-4" />} trend={report.metrics_summary['edge.error_rate']?.avg > 1 ? 'up' : 'down'} color="text-red-500" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="IoT Devices" value="3,892" subtitle="Sensors & actuators" icon={<Wifi className="h-4 w-4" />} trend="up" color="text-cyan-500" />
        <StatCard title="Avg Temperature" value={`${report.metrics_summary['iot.temperature']?.avg.toFixed(1) || 'N/A'}°C`} subtitle="Max: ${report.metrics_summary['iot.temperature']?.max.toFixed(1)}°C" icon={<Thermometer className="h-4 w-4" />} color="text-red-500" />
        <StatCard title="Avg Humidity" value={`${report.metrics_summary['iot.humidity']?.avg.toFixed(0) || 'N/A'}%`} subtitle="Min: ${report.metrics_summary['iot.humidity']?.min.toFixed(0)}%" icon={<Activity className="h-4 w-4" />} color="text-blue-500" />
        <StatCard title="Total Power" value={`${report.metrics_summary['iot.power_consumption']?.avg.toFixed(0) || 'N/A'}W`} subtitle="Peak: ${report.metrics_summary['iot.power_consumption']?.max.toFixed(0)}W" icon={<Zap className="h-4 w-4" />} color="text-yellow-500" />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview"><BarChart3 className="h-4 w-4 mr-2" />Overview</TabsTrigger>
          <TabsTrigger value="edge"><Cpu className="h-4 w-4 mr-2" />Edge Metrics</TabsTrigger>
          <TabsTrigger value="iot"><Wifi className="h-4 w-4 mr-2" />IoT Metrics</TabsTrigger>
          <TabsTrigger value="anomalies"><AlertTriangle className="h-4 w-4 mr-2" />Anomalies</TabsTrigger>
          <TabsTrigger value="trends"><TrendingUp className="h-4 w-4 mr-2" />Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>All Metrics</CardTitle>
                  <CardDescription>Aggregated metrics from all edge and IoT sources</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input placeholder="Search metrics..." className="pl-8 w-64" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                  </div>
                  <Button variant="ghost" size="sm"><Filter className="h-4 w-4" /></Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {filteredMetrics.map(([name, metric]) => (
                <MetricBar key={name} name={name} metric={metric} />
              ))}
              {filteredMetrics.length === 0 && (
                <p className="text-center text-muted-foreground py-8">No metrics found matching "{searchQuery}"</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="edge" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Edge Computing Metrics</CardTitle>
              <CardDescription>CPU, memory, disk, network, and application performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {['edge.cpu_usage', 'edge.memory_usage', 'edge.disk_usage', 'edge.network_throughput', 'edge.response_time', 'edge.error_rate'].map(name => {
                  const metric = report.metrics_summary[name];
                  if (!metric) return null;
                  return <MetricBar key={name} name={name} metric={metric} />;
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="iot" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>IoT Sensor Metrics</CardTitle>
              <CardDescription>Temperature, humidity, power, signal strength, and more</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {['iot.temperature', 'iot.humidity', 'iot.pressure', 'iot.vibration', 'iot.power_consumption', 'iot.signal_strength', 'iot.data_rate', 'iot.packet_loss', 'iot.latency', 'iot.battery_level'].map(name => {
                  const metric = report.metrics_summary[name];
                  if (!metric) return null;
                  return <MetricBar key={name} name={name} metric={metric} />;
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="anomalies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Anomaly Detection</CardTitle>
              <CardDescription>Metrics that exceed normal thresholds and require attention</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {report.alerts.length === 0 && (
                  <div className="text-center py-8">
                    <Activity className="h-12 w-12 mx-auto text-green-500 mb-3" />
                    <p className="text-lg font-medium text-green-600">No Anomalies Detected</p>
                    <p className="text-sm text-muted-foreground mt-1">All metrics are operating within normal parameters</p>
                  </div>
                )}
                {report.alerts.map((alert, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                    <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    <span className="text-sm text-yellow-800">{alert}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Metric Trends</CardTitle>
              <CardDescription>24-hour trend lines for key performance indicators</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {Object.entries(dummyMetrics).map(([name, points]) => (
                <div key={name} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{name}</span>
                      {METRIC_CATEGORIES[name] && <span className={METRIC_CATEGORIES[name].color}>{METRIC_CATEGORIES[name].icon}</span>}
                    </div>
                    <Badge variant="outline">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      {points.length} data points
                    </Badge>
                  </div>
                  <div className="w-full h-32 bg-secondary/30 rounded-lg p-2">
                    <svg viewBox="0 0 240 60" className="w-full h-full">
                      <polyline
                        points={points.map((p, i) => {
                          const max = Math.max(...points.map(x => x.value));
                          const min = Math.min(...points.map(x => x.value));
                          const range = max - min || 1;
                          return `${(i / (points.length - 1)) * 240},${60 - ((p.value - min) / range) * 56}`;
                        }).join(' ')}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        className="text-primary"
                      />
                    </svg>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common analytics tasks</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={() => handleExport('csv')}><Download className="h-4 w-4 mr-2" /> Export Report (CSV)</Button>
          <Button variant="outline" onClick={() => handleExport('json')}><Download className="h-4 w-4 mr-2" /> Export Report (JSON)</Button>
          <Button variant="outline" onClick={handleRefresh}><RefreshCw className="h-4 w-4 mr-2" /> Refresh Data</Button>
          <Button variant="outline" onClick={() => window.print()}><BarChart3 className="h-4 w-4 mr-2" /> Print Dashboard</Button>
          <Button variant="outline" onClick={() => setSelectedTimeRange('7d')}><Clock className="h-4 w-4 mr-2" /> Last 7 Days</Button>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">
        Last updated: {new Date(report.generated_at).toLocaleString()} | Time range: {selectedTimeRange} | Overall status: {report.overall_status}
      </p>
    </div>
  );
}
