import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const screenWidth = Dimensions.get('window').width;

interface MetricSummary {
  avg: number;
  max: number;
  min: number;
  p95: number;
  p99: number;
  samples: number;
}

interface Report {
  generated_at: string;
  metrics_summary: Record<string, MetricSummary>;
  overall_status: string;
  alerts: string[];
}

const defaultReport: Report = {
  generated_at: new Date().toISOString(),
  metrics_summary: {
    'edge.cpu_usage': { avg: 45.2, max: 92.1, min: 12.3, p95: 85.4, p99: 90.1, samples: 1440 },
    'edge.memory_usage': { avg: 62.8, max: 95.5, min: 30.1, p95: 88.2, p99: 93.7, samples: 1440 },
    'edge.network_throughput': { avg: 456.7, max: 985.2, min: 102.3, p95: 876.5, p99: 945.1, samples: 1440 },
    'edge.response_time': { avg: 125.4, max: 890.2, min: 15.3, p95: 450.2, p99: 720.5, samples: 1440 },
    'edge.error_rate': { avg: 0.8, max: 5.2, min: 0.0, p95: 2.8, p99: 4.1, samples: 1440 },
    'iot.temperature': { avg: 24.5, max: 38.2, min: 18.1, p95: 32.5, p99: 35.8, samples: 1440 },
    'iot.humidity': { avg: 58.3, max: 82.1, min: 35.2, p95: 75.4, p99: 79.8, samples: 1440 },
  },
  overall_status: 'healthy',
  alerts: [],
};

const Sparkline: React.FC<{ values: number[]; color?: string; height?: number }> = ({ values, color = '#10b981', height = 30 }) => {
  if (!values.length) return null;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const width = Math.min(screenWidth - 60, 200);
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return (
    <View style={{ width, height }}>
      <svg width={width} height={height}>
        <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
      </svg>
    </View>
  );
};

const MetricRow: React.FC<{ name: string; metric: MetricSummary; onPress: () => void }> = ({ name, metric, onPress }) => {
  const getBarColor = (val: number) => {
    if (val > 80) return '#ef4444';
    if (val > 60) return '#f59e0b';
    return '#10b981';
  };

  const barPct = Math.min(100, (metric.avg / 100) * 100);
  const isEdge = name.startsWith('edge');
  const icon = isEdge ? '🖥' : '📡';

  return (
    <TouchableOpacity style={styles.metricRow} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.metricHeader}>
        <View style={styles.metricTitleRow}>
          <Text style={styles.metricIcon}>{icon}</Text>
          <Text style={styles.metricName}>{name}</Text>
        </View>
        <Text style={[styles.metricValue, { color: getBarColor(metric.avg) }]}>{metric.avg.toFixed(1)}</Text>
      </View>
      <View style={styles.barContainer}>
        <View style={[styles.bar, { width: `${barPct}%`, backgroundColor: getBarColor(metric.avg) }]} />
      </View>
      <View style={styles.metricDetails}>
        <Text style={styles.metricDetail}>min: {metric.min.toFixed(1)}</Text>
        <Text style={styles.metricDetail}>max: {metric.max.toFixed(1)}</Text>
        <Text style={styles.metricDetail}>p95: {metric.p95.toFixed(1)}</Text>
        <Text style={styles.metricDetail}>p99: {metric.p99.toFixed(1)}</Text>
      </View>
    </TouchableOpacity>
  );
};

const mockValues = Array.from({ length: 24 }, () => 30 + Math.random() * 60);

export default function EdgeAnalyticsScreen() {
  const [report, setReport] = useState<Report>(defaultReport);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'all' | 'edge' | 'iot'>('all');

  const onRefresh = useCallback(() => {
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

  const filteredEntries = Object.entries(report.metrics_summary).filter(([name]) => {
    if (selectedTab === 'edge') return name.startsWith('edge');
    if (selectedTab === 'iot') return name.startsWith('iot');
    return true;
  });

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        <View style={styles.header}>
          <Text style={styles.title}>Edge & IoT Analytics</Text>
          <Text style={styles.subtitle}>Real-time edge device and IoT sensor monitoring</Text>
        </View>

        <View style={styles.statusBanner(report.overall_status)}>
          <Text style={styles.statusText}>
            Status: {report.overall_status.toUpperCase()} | {Object.keys(report.metrics_summary).length} metrics tracked
          </Text>
        </View>

        <View style={styles.summaryCards}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>1,247</Text>
            <Text style={styles.summaryLabel}>Edge Devices</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>3,892</Text>
            <Text style={styles.summaryLabel}>IoT Sensors</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>{report.metrics_summary['edge.cpu_usage']?.avg.toFixed(0) || 'N/A'}%</Text>
            <Text style={styles.summaryLabel}>Avg CPU</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>{report.metrics_summary['edge.response_time']?.avg.toFixed(0) || 'N/A'}ms</Text>
            <Text style={styles.summaryLabel}>Avg Latency</Text>
          </View>
        </View>

        <View style={styles.sparklineCard}>
          <Text style={styles.sectionTitle}>CPU Usage Trend (24h)</Text>
          <Sparkline values={mockValues} color="#8b5cf6" />
        </View>

        <View style={styles.tabRow}>
          {(['all', 'edge', 'iot'] as const).map(tab => (
            <TouchableOpacity
              key={tab}
              style={[styles.tab, selectedTab === tab && styles.activeTab]}
              onPress={() => setSelectedTab(tab)}
            >
              <Text style={[styles.tabText, selectedTab === tab && styles.activeTabText]}>
                {tab === 'all' ? 'All' : tab === 'edge' ? '🖥 Edge' : '📡 IoT'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {filteredEntries.map(([name, metric]) => (
          <MetricRow
            key={name}
            name={name}
            metric={metric}
            onPress={() => {}}
          />
        ))}

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Last updated: {new Date(report.generated_at).toLocaleTimeString()}
          </Text>
          <Text style={styles.footerText}>
            {report.alerts.length} active alerts
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  header: { padding: 16 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#f1f5f9' },
  subtitle: { fontSize: 14, color: '#94a3b8', marginTop: 4 },
  statusBanner: (status: string) => ({
    marginHorizontal: 16,
    padding: 12,
    borderRadius: 8,
    backgroundColor: status === 'healthy' ? '#065f46' : '#92400e',
  }),
  statusText: { color: '#f1f5f9', fontSize: 13, fontWeight: '600' },
  summaryCards: { flexDirection: 'row', flexWrap: 'wrap', padding: 8 },
  summaryCard: {
    width: (screenWidth - 48) / 2,
    margin: 8,
    padding: 16,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    alignItems: 'center',
  },
  summaryValue: { fontSize: 24, fontWeight: 'bold', color: '#f1f5f9' },
  summaryLabel: { fontSize: 12, color: '#94a3b8', marginTop: 4 },
  sparklineCard: {
    margin: 16,
    padding: 16,
    backgroundColor: '#1e293b',
    borderRadius: 12,
  },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#f1f5f9', marginBottom: 12 },
  tabRow: { flexDirection: 'row', marginHorizontal: 16, marginBottom: 8, gap: 8 },
  tab: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, backgroundColor: '#1e293b' },
  activeTab: { backgroundColor: '#3b82f6' },
  tabText: { color: '#94a3b8', fontSize: 14, fontWeight: '500' },
  activeTabText: { color: '#ffffff' },
  metricRow: {
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 12,
    backgroundColor: '#1e293b',
    borderRadius: 10,
  },
  metricHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  metricTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  metricIcon: { fontSize: 16 },
  metricName: { color: '#e2e8f0', fontSize: 14, fontWeight: '500' },
  metricValue: { fontSize: 18, fontWeight: 'bold' },
  barContainer: { height: 6, backgroundColor: '#334155', borderRadius: 3, marginTop: 8, overflow: 'hidden' },
  bar: { height: 6, borderRadius: 3 },
  metricDetails: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  metricDetail: { color: '#64748b', fontSize: 11 },
  footer: { padding: 16, alignItems: 'center' },
  footerText: { color: '#64748b', fontSize: 12 },
});
