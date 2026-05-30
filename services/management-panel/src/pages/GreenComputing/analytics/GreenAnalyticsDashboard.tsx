import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { AlertTriangle, Activity, Zap, Cloud, DollarSign, Thermometer, Droplets, Recycle, BarChart3, Download, RefreshCw, Search, Filter, Leaf, TreePine, Wind, Sun, TrendingUp, PieChart, Target, Award, Gauge, LineChart } from 'lucide-react';

interface MetricSummary {
  avg: number;
  max: number;
  min: number;
  p95: number;
  p99: number;
  samples: number;
}

interface GreenReport {
  generated_at: string;
  time_range: { start: string; end: string };
  metrics_summary: Record<string, MetricSummary>;
  overall_status: string;
  alerts: string[];
  sustainability_score: number;
  carbon_saved: number;
  energy_saved: number;
  cost_saved: number;
}

const greenMetricsMeta: Record<string, { icon: React.ReactNode; color: string; unit: string }> = {
  'green.power_usage': { icon: <Zap className="h-4 w-4" />, color: 'text-yellow-500', unit: 'kW' },
  'green.carbon_emission': { icon: <Cloud className="h-4 w-4" />, color: 'text-gray-500', unit: 'kg CO₂' },
  'green.pue': { icon: <BarChart3 className="h-4 w-4" />, color: 'text-blue-500', unit: '' },
  'green.energy_cost': { icon: <DollarSign className="h-4 w-4" />, color: 'text-green-500', unit: '$' },
  'green.renewable_percentage': { icon: <Sun className="h-4 w-4" />, color: 'text-amber-500', unit: '%' },
  'green.cooling_efficiency': { icon: <Thermometer className="h-4 w-4" />, color: 'text-cyan-500', unit: '' },
  'green.server_utilization': { icon: <Activity className="h-4 w-4" />, color: 'text-purple-500', unit: '%' },
  'green.water_usage': { icon: <Droplets className="h-4 w-4" />, color: 'text-blue-600', unit: 'L' },
  'green.recycling_rate': { icon: <Recycle className="h-4 w-4" />, color: 'text-emerald-500', unit: '%' },
  'green.sustainability_score': { icon: <Leaf className="h-4 w-4" />, color: 'text-green-600', unit: '' },
};

const dummyGreenReport: GreenReport = {
  generated_at: new Date().toISOString(),
  time_range: { start: new Date(Date.now() - 86400000).toISOString(), end: new Date().toISOString() },
  metrics_summary: {
    'green.power_usage': { avg: 342.5, max: 512.3, min: 201.2, p95: 478.9, p99: 498.2, samples: 1440 },
    'green.carbon_emission': { avg: 145.2, max: 235.1, min: 82.3, p95: 210.5, p99: 225.8, samples: 1440 },
    'green.pue': { avg: 1.42, max: 1.68, min: 1.28, p95: 1.58, p99: 1.62, samples: 1440 },
    'green.energy_cost': { avg: 1150.75, max: 1875.30, min: 675.20, p95: 1650.40, p99: 1780.90, samples: 1440 },
    'green.renewable_percentage': { avg: 48.3, max: 72.1, min: 25.4, p95: 65.8, p99: 70.2, samples: 1440 },
    'green.cooling_efficiency': { avg: 0.78, max: 0.92, min: 0.55, p95: 0.88, p99: 0.90, samples: 1440 },
    'green.server_utilization': { avg: 62.5, max: 88.2, min: 35.1, p95: 82.4, p99: 86.1, samples: 1440 },
    'green.water_usage': { avg: 485.2, max: 720.5, min: 310.8, p95: 650.3, p99: 690.7, samples: 1440 },
    'green.recycling_rate': { avg: 58.7, max: 75.2, min: 42.1, p95: 70.5, p99: 73.8, samples: 1440 },
    'green.sustainability_score': { avg: 71.4, max: 88.5, min: 55.2, p95: 82.5, p99: 85.9, samples: 1440 },
  },
  overall_status: 'healthy',
  alerts: [],
  sustainability_score: 71.4,
  carbon_saved: 12500,
  energy_saved: 45000,
  cost_saved: 32500,
};

const SustainabilityGauge: React.FC<{ score: number; size?: number }> = ({ score, size = 180 }) => {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="12" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold" style={{ color }}>{score.toFixed(0)}</span>
        <span className="text-xs text-muted-foreground">/100</span>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ name: string; metric: MetricSummary }> = ({ name, metric }) => {
  const meta = greenMetricsMeta[name] || { icon: <Activity className="h-4 w-4" />, color: 'text-gray-500', unit: '' };
  const barPct = Math.min(100, (metric.avg / 100) * 100);
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={meta.color}>{meta.icon}</span>
            <CardTitle className="text-sm font-medium">{name.replace('green.', '')}</CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">{metric.samples} samples</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{metric.avg.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">{meta.unit}</span></div>
        <div className="flex justify-between text-xs text-muted-foreground mt-2">
          <span>Min: {metric.min.toFixed(1)}</span>
          <span>Max: {metric.max.toFixed(1)}</span>
        </div>
        <div className="w-full bg-secondary rounded-full h-1.5 mt-2">
          <div className="h-1.5 rounded-full transition-all bg-primary" style={{ width: `${barPct}%` }} />
        </div>
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>P95: {metric.p95.toFixed(1)}</span>
          <span>P99: {metric.p99.toFixed(1)}</span>
        </div>
      </CardContent>
    </Card>
  );
};

const ImpactCard: React.FC<{ title: string; value: string; subtitle: string; icon: React.ReactNode; color: string }> = ({ title, value, subtitle, icon, color }) => (
  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        </div>
        <div className={`p-3 rounded-full ${color}`}>{icon}</div>
      </div>
    </CardContent>
  </Card>
);

interface AlertBannerProps {
  report: GreenReport;
  onDismiss: () => void;
}

const AlertBanner: React.FC<AlertBannerProps> = ({ report, onDismiss }) => {
  if (report.overall_status === 'healthy' && !report.alerts.length) return null;
  return (
    <div className="p-4 rounded-lg mb-6 flex items-start gap-3 bg-yellow-50 border border-yellow-200">
      <AlertTriangle className="h-5 w-5 mt-0.5 text-yellow-600" />
      <div className="flex-1">
        <p className="font-medium text-yellow-800">Sustainability Alerts</p>
        {report.alerts.slice(0, 3).map((a, i) => <p key={i} className="text-sm text-yellow-700 mt-1">{a}</p>)}
      </div>
      <Button variant="ghost" size="sm" onClick={onDismiss}>Dismiss</Button>
    </div>
  );
};

export default function GreenAnalyticsDashboard() {
  const [report, setReport] = useState<GreenReport>(dummyGreenReport);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('24h');
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
          Object.entries(prev.metrics_summary).map(([k, v]) => [k, { ...v, avg: v.avg * (0.95 + Math.random() * 0.1) }])
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
    a.download = `green-analytics-${Date.now()}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [report]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Green Computing Analytics</h1>
          <p className="text-muted-foreground mt-1">Sustainability metrics, carbon tracking, and environmental impact analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
              <SelectItem value="1y">Last Year</SelectItem>
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

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="flex items-center justify-center">
          <div className="text-center">
            <SustainabilityGauge score={report.sustainability_score} />
            <p className="text-sm font-medium mt-2">Sustainability Score</p>
            <Badge variant={report.sustainability_score >= 70 ? 'default' : 'secondary'} className="mt-1">
              {report.sustainability_score >= 80 ? 'Excellent' : report.sustainability_score >= 60 ? 'Good' : 'Needs Improvement'}
            </Badge>
          </div>
        </div>
        <ImpactCard title="Carbon Saved" value={`${(report.carbon_saved / 1000).toFixed(1)}t`} subtitle="CO₂ equivalent this period" icon={<Cloud className="h-6 w-6 text-white" />} color="bg-green-500" />
        <ImpactCard title="Energy Saved" value={`${(report.energy_saved / 1000).toFixed(1)}MWh`} subtitle="Reduced consumption" icon={<Zap className="h-6 w-6 text-white" />} color="bg-yellow-500" />
        <ImpactCard title="Cost Savings" value={`$${(report.cost_saved / 1000).toFixed(1)}K`} subtitle="Operational cost reduction" icon={<DollarSign className="h-6 w-6 text-white" />} color="bg-blue-500" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <ImpactCard title="Avg PUE" value={report.metrics_summary['green.pue']?.avg.toFixed(2) || 'N/A'} subtitle="Power Usage Effectiveness" icon={<BarChart3 className="h-6 w-6 text-white" />} color="bg-purple-500" />
        <ImpactCard title="Renewable Energy" value={`${report.metrics_summary['green.renewable_percentage']?.avg.toFixed(0) || 'N/A'}%`} subtitle="Of total energy mix" icon={<Sun className="h-6 w-6 text-white" />} color="bg-amber-500" />
        <ImpactCard title="Cooling Efficiency" value={report.metrics_summary['green.cooling_efficiency']?.avg.toFixed(2) || 'N/A'} subtitle="Cooling load ratio" icon={<Wind className="h-6 w-6 text-white" />} color="bg-cyan-500" />
        <ImpactCard title="Server Utilization" value={`${report.metrics_summary['green.server_utilization']?.avg.toFixed(0) || 'N/A'}%`} subtitle="Average server usage" icon={<Activity className="h-6 w-6 text-white" />} color="bg-indigo-500" />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview"><PieChart className="h-4 w-4 mr-2" />Overview</TabsTrigger>
          <TabsTrigger value="energy"><Zap className="h-4 w-4 mr-2" />Energy</TabsTrigger>
          <TabsTrigger value="carbon"><Cloud className="h-4 w-4 mr-2" />Carbon</TabsTrigger>
          <TabsTrigger value="efficiency"><Target className="h-4 w-4 mr-2" />Efficiency</TabsTrigger>
          <TabsTrigger value="sustainability"><Leaf className="h-4 w-4 mr-2" />Sustainability</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>All Green Metrics</CardTitle>
                  <CardDescription>Comprehensive sustainability and efficiency metrics</CardDescription>
                </div>
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search metrics..." className="pl-8 w-64" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {filteredMetrics.map(([name, metric]) => (
                  <MetricCard key={name} name={name} metric={metric} />
                ))}
                {filteredMetrics.length === 0 && <p className="text-center text-muted-foreground col-span-2 py-8">No metrics found</p>}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="energy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Energy Metrics</CardTitle>
              <CardDescription>Power usage, energy cost, and renewable energy tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <MetricCard name="green.power_usage" metric={report.metrics_summary['green.power_usage']} />
                <MetricCard name="green.energy_cost" metric={report.metrics_summary['green.energy_cost']} />
                <MetricCard name="green.renewable_percentage" metric={report.metrics_summary['green.renewable_percentage']} />
                <MetricCard name="green.pue" metric={report.metrics_summary['green.pue']} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="carbon" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Carbon Emissions</CardTitle>
              <CardDescription>Carbon footprint tracking and reduction metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <MetricCard name="green.carbon_emission" metric={report.metrics_summary['green.carbon_emission']} />
                <MetricCard name="green.sustainability_score" metric={report.metrics_summary['green.sustainability_score']} />
              </div>
              <div className="mt-6 p-4 rounded-lg bg-green-50 border border-green-200">
                <div className="flex items-center gap-3">
                  <TreePine className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="font-medium text-green-800">Carbon Offset Status</p>
                    <p className="text-sm text-green-700">You've saved {(report.carbon_saved / 1000).toFixed(1)} tonnes of CO₂ this period. That's equivalent to planting {Math.round(report.carbon_saved / 21)} trees!</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="efficiency" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Efficiency Metrics</CardTitle>
              <CardDescription>Cooling, server utilization, water usage, and recycling rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <MetricCard name="green.cooling_efficiency" metric={report.metrics_summary['green.cooling_efficiency']} />
                <MetricCard name="green.server_utilization" metric={report.metrics_summary['green.server_utilization']} />
                <MetricCard name="green.water_usage" metric={report.metrics_summary['green.water_usage']} />
                <MetricCard name="green.recycling_rate" metric={report.metrics_summary['green.recycling_rate']} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sustainability" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sustainability Score Breakdown</CardTitle>
              <CardDescription>Detailed view of what impacts your sustainability score</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-center">
                  <SustainabilityGauge score={report.sustainability_score} size={240} />
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-4 rounded-lg bg-green-50 border border-green-200 text-center">
                    <Leaf className="h-8 w-8 mx-auto text-green-600 mb-2" />
                    <p className="text-lg font-bold text-green-800">{report.metrics_summary['green.renewable_percentage']?.avg.toFixed(0) || 'N/A'}%</p>
                    <p className="text-xs text-green-700">Renewable Energy</p>
                  </div>
                  <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 text-center">
                    <Target className="h-8 w-8 mx-auto text-blue-600 mb-2" />
                    <p className="text-lg font-bold text-blue-800">{report.metrics_summary['green.pue']?.avg.toFixed(2) || 'N/A'}</p>
                    <p className="text-xs text-blue-700">PUE Ratio</p>
                  </div>
                  <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-center">
                    <Recycle className="h-8 w-8 mx-auto text-emerald-600 mb-2" />
                    <p className="text-lg font-bold text-emerald-800">{report.metrics_summary['green.recycling_rate']?.avg.toFixed(0) || 'N/A'}%</p>
                    <p className="text-xs text-emerald-700">Recycling Rate</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>Sustainability Goals</CardTitle>
          <CardDescription>Track progress towards environmental targets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>PUE Target (&lt;1.3)</span>
                <span className={report.metrics_summary['green.pue']?.avg <= 1.3 ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                  Current: {report.metrics_summary['green.pue']?.avg.toFixed(2)}
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="h-2 rounded-full bg-green-500" style={{ width: `${Math.min(100, ((1.5 - report.metrics_summary['green.pue']?.avg) / 0.5) * 100)}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Renewable Energy (&gt;60%)</span>
                <span className={report.metrics_summary['green.renewable_percentage']?.avg >= 60 ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                  Current: {report.metrics_summary['green.renewable_percentage']?.avg.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="h-2 rounded-full bg-amber-500" style={{ width: `${Math.min(100, report.metrics_summary['green.renewable_percentage']?.avg || 0)}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Server Utilization (&gt;75%)</span>
                <span className={report.metrics_summary['green.server_utilization']?.avg >= 75 ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                  Current: {report.metrics_summary['green.server_utilization']?.avg.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="h-2 rounded-full bg-purple-500" style={{ width: `${Math.min(100, report.metrics_summary['green.server_utilization']?.avg || 0)}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Recycling Rate (&gt;70%)</span>
                <span className={report.metrics_summary['green.recycling_rate']?.avg >= 70 ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                  Current: {report.metrics_summary['green.recycling_rate']?.avg.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.min(100, report.metrics_summary['green.recycling_rate']?.avg || 0)}%` }} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common sustainability analytics tasks</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={() => handleExport('csv')}><Download className="h-4 w-4 mr-2" /> Export Report (CSV)</Button>
          <Button variant="outline" onClick={() => handleExport('json')}><Download className="h-4 w-4 mr-2" /> Export Report (JSON)</Button>
          <Button variant="outline" onClick={handleRefresh}><RefreshCw className="h-4 w-4 mr-2" /> Refresh Data</Button>
          <Button variant="outline" onClick={() => window.print()}><BarChart3 className="h-4 w-4 mr-2" /> Print Dashboard</Button>
          <Button variant="outline"><Award className="h-4 w-4 mr-2" /> View Certifications</Button>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">
        Last updated: {new Date(report.generated_at).toLocaleString()} | Period: {selectedPeriod} | Score: {report.sustainability_score.toFixed(1)}/100
      </p>
    </div>
  );
}
