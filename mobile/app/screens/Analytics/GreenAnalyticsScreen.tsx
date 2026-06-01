import React, { useState, useCallback } from 'react';
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

interface GreenReport {
  generated_at: string;
  metrics_summary: Record<string, MetricSummary>;
  overall_status: string;
  alerts: string[];
  sustainability_score: number;
  carbon_saved: number;
  energy_saved: number;
  cost_saved: number;
}

const defaultReport: GreenReport = {
  generated_at: new Date().toISOString(),
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

const GaugeView: React.FC<{ score: number; size?: number }> = ({ score, size = 120 }) => {
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <View style={[styles.gaugeContainer, { width: size, height: size }]}>
      <View style={[styles.gaugeCircle, { borderColor: color }]}>
        <Text style={[styles.gaugeScore, { color }]}>{score.toFixed(0)}</Text>
        <Text style={styles.gaugeLabel}>/100</Text>
      </View>
    </View>
  );
};

const MetricRow: React.FC<{ name: string; metric: MetricSummary; onPress: () => void }> = ({ name, metric, onPress }) => {
  const displayName = name.replace('green.', '');
  const barPct = Math.min(100, (metric.avg / 100) * 100);
  const getBarColor = (val: number) => {
    if (name.includes('carbon') || name.includes('power_usage') || name.includes('energy_cost') || name.includes('water')) {
      return val > 70 ? '#ef4444' : val > 50 ? '#f59e0b' : '#10b981';
    }
    return val > 70 ? '#10b981' : val > 50 ? '#f59e0b' : '#ef4444';
  };

  const getUnit = (metricName: string) => {
    if (metricName.includes('power_usage')) return 'kW';
    if (metricName.includes('carbon')) return 'kg';
    if (metricName.includes('energy_cost')) return '$';
    if (metricName.includes('water')) return 'L';
    if (metricName.includes('renewable') || metricName.includes('server') || metricName.includes('recycling')) return '%';
    return '';
  };

  const getIcon = (metricName: string) => {
    if (metricName.includes('power')) return '⚡';
    if (metricName.includes('carbon')) return '💨';
    if (metricName.includes('pue')) return '📊';
    if (metricName.includes('energy_cost')) return '💰';
    if (metricName.includes('renewable')) return '☀️';
    if (metricName.includes('cooling')) return '🌡️';
    if (metricName.includes('server')) return '🖥️';
    if (metricName.includes('water')) return '💧';
    if (metricName.includes('recycling')) return '♻️';
    if (metricName.includes('sustainability')) return '🌿';
    return '📈';
  };

  return (
    <TouchableOpacity style={styles.metricRow} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.metricHeader}>
        <View style={styles.metricTitleRow}>
          <Text style={styles.metricIcon}>{getIcon(name)}</Text>
          <Text style={styles.metricName}>{displayName}</Text>
        </View>
        <Text style={[styles.metricValue, { color: getBarColor(metric.avg) }]}>
          {metric.avg.toFixed(1)} <Text style={styles.metricUnit}>{getUnit(name)}</Text>
        </Text>
      </View>
      <View style={styles.barContainer}>
        <View style={[styles.bar, { width: `${barPct}%`, backgroundColor: getBarColor(metric.avg) }]} />
      </View>
      <View style={styles.metricDetails}>
        <Text style={styles.metricDetail}>↓ {metric.min.toFixed(1)}</Text>
        <Text style={styles.metricDetail}>↑ {metric.max.toFixed(1)}</Text>
        <Text style={styles.metricDetail}>p95 {metric.p95.toFixed(1)}</Text>
        <Text style={styles.metricDetail}>p99 {metric.p99.toFixed(1)}</Text>
      </View>
    </TouchableOpacity>
  );
};

export default function GreenAnalyticsScreen() {
  const [report, setReport] = useState<GreenReport>(defaultReport);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'all' | 'energy' | 'carbon' | 'efficiency'>('all');

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => {
      setReport(prev => ({
        ...prev,
        generated_at: new Date().toISOString(),
        sustainability_score: 60 + Math.random() * 35,
        carbon_saved: prev.carbon_saved * (1 + Math.random() * 0.05),
        metrics_summary: Object.fromEntries(
          Object.entries(prev.metrics_summary).map(([k, v]) => [k, { ...v, avg: v.avg * (0.95 + Math.random() * 0.1) }])
        ),
      }));
      setRefreshing(false);
    }, 1000);
  }, []);

  const filteredEntries = Object.entries(report.metrics_summary).filter(([name]) => {
    if (selectedTab === 'energy') return name.includes('power') || name.includes('pue') || name.includes('renewable') || name.includes('energy_cost');
    if (selectedTab === 'carbon') return name.includes('carbon') || name.includes('sustainability');
    if (selectedTab === 'efficiency') return name.includes('cooling') || name.includes('server') || name.includes('water') || name.includes('recycling');
    return true;
  });

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        <View style={styles.header}>
          <Text style={styles.title}>🌿 Green Analytics</Text>
          <Text style={styles.subtitle}>Sustainability metrics and environmental impact tracking</Text>
        </View>

        <View style={styles.gaugeRow}>
          <GaugeView score={report.sustainability_score} />
          <View style={styles.gaugeStats}>
            <View style={styles.gaugeStat}>
              <Text style={styles.gaugeStatValue}>{(report.carbon_saved / 1000).toFixed(1)}t</Text>
              <Text style={styles.gaugeStatLabel}>CO₂ Saved</Text>
            </View>
            <View style={styles.gaugeStat}>
              <Text style={styles.gaugeStatValue}>{(report.energy_saved / 1000).toFixed(1)}MWh</Text>
              <Text style={styles.gaugeStatLabel}>Energy Saved</Text>
            </View>
            <View style={styles.gaugeStat}>
              <Text style={styles.gaugeStatValue}>${(report.cost_saved / 1000).toFixed(1)}K</Text>
              <Text style={styles.gaugeStatLabel}>Cost Saved</Text>
            </View>
          </View>
        </View>

        <View style={styles.statusBanner(report.overall_status)}>
          <Text style={styles.statusText}>
            Score: {report.sustainability_score.toFixed(1)}/100 | {Object.keys(report.metrics_summary).length} metrics
          </Text>
        </View>

        <View style={styles.summaryCards}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>{report.metrics_summary['green.pue']?.avg.toFixed(2)}</Text>
            <Text style={styles.summaryLabel}>PUE</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>{report.metrics_summary['green.renewable_percentage']?.avg.toFixed(0)}%</Text>
            <Text style={styles.summaryLabel}>Renewable</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>{report.metrics_summary['green.cooling_efficiency']?.avg.toFixed(2)}</Text>
            <Text style={styles.summaryLabel}>Cooling Eff</Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryValue}>{report.metrics_summary['green.server_utilization']?.avg.toFixed(0)}%</Text>
            <Text style={styles.summaryLabel}>Utilization</Text>
          </View>
        </View>

        <View style={styles.tabRow}>
          {(['all', 'energy', 'carbon', 'efficiency'] as const).map(tab => (
            <TouchableOpacity
              key={tab}
              style={[styles.tab, selectedTab === tab && styles.activeTab]}
              onPress={() => setSelectedTab(tab)}
            >
              <Text style={[styles.tabText, selectedTab === tab && styles.activeTabText]}>
                {tab === 'all' ? 'All' : tab === 'energy' ? '⚡' : tab === 'carbon' ? '💨' : '🎯'}
                {' '}{tab.charAt(0).toUpperCase() + tab.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.offsetCard}>
          <Text style={styles.offsetTitle}>🌱 Carbon Offset Status</Text>
          <Text style={styles.offsetText}>
            You've saved {(report.carbon_saved / 1000).toFixed(1)} tonnes of CO₂. Equivalent to planting {Math.round(report.carbon_saved / 21)} trees!
          </Text>
          <View style={styles.progressContainer}>
            <View style={[styles.progressBar, { width: `${report.sustainability_score}%` }]} />
          </View>
        </View>

        {filteredEntries.map(([name, metric]) => (
          <MetricRow key={name} name={name} metric={metric} onPress={() => {}} />
        ))}

        <View style={styles.footer}>
          <Text style={styles.footerText}>Last updated: {new Date(report.generated_at).toLocaleTimeString()}</Text>
          <Text style={styles.footerText}>Score: {report.sustainability_score.toFixed(1)}/100</Text>
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
  gaugeRow: { flexDirection: 'row', padding: 16, alignItems: 'center' },
  gaugeContainer: { justifyContent: 'center', alignItems: 'center' },
  gaugeCircle: {
    width: 120, height: 120, borderRadius: 60, borderWidth: 6,
    justifyContent: 'center', alignItems: 'center', backgroundColor: '#1e293b',
  },
  gaugeScore: { fontSize: 36, fontWeight: 'bold' },
  gaugeLabel: { fontSize: 12, color: '#64748b' },
  gaugeStats: { flex: 1, marginLeft: 16 },
  gaugeStat: { marginBottom: 8 },
  gaugeStatValue: { fontSize: 20, fontWeight: 'bold', color: '#f1f5f9' },
  gaugeStatLabel: { fontSize: 11, color: '#94a3b8' },
  statusBanner: (status: string) => ({
    marginHorizontal: 16, padding: 12, borderRadius: 8,
    backgroundColor: status === 'healthy' ? '#065f46' : '#92400e',
  }),
  statusText: { color: '#f1f5f9', fontSize: 13, fontWeight: '600' },
  summaryCards: { flexDirection: 'row', flexWrap: 'wrap', padding: 8 },
  summaryCard: {
    width: (screenWidth - 48) / 2, margin: 8, padding: 16,
    backgroundColor: '#1e293b', borderRadius: 12, alignItems: 'center',
  },
  summaryValue: { fontSize: 24, fontWeight: 'bold', color: '#f1f5f9' },
  summaryLabel: { fontSize: 12, color: '#94a3b8', marginTop: 4 },
  tabRow: { flexDirection: 'row', marginHorizontal: 16, marginBottom: 8, gap: 8 },
  tab: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, backgroundColor: '#1e293b' },
  activeTab: { backgroundColor: '#10b981' },
  tabText: { color: '#94a3b8', fontSize: 14, fontWeight: '500' },
  activeTabText: { color: '#ffffff' },
  offsetCard: {
    margin: 16, padding: 16, backgroundColor: '#064e3b', borderRadius: 12,
    borderWidth: 1, borderColor: '#047857',
  },
  offsetTitle: { fontSize: 16, fontWeight: '600', color: '#a7f3d0', marginBottom: 8 },
  offsetText: { fontSize: 13, color: '#6ee7b7', lineHeight: 20 },
  progressContainer: { height: 8, backgroundColor: '#065f46', borderRadius: 4, marginTop: 12, overflow: 'hidden' },
  progressBar: { height: 8, backgroundColor: '#10b981', borderRadius: 4 },
  metricRow: {
    marginHorizontal: 16, marginVertical: 4, padding: 12,
    backgroundColor: '#1e293b', borderRadius: 10,
  },
  metricHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  metricTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  metricIcon: { fontSize: 16 },
  metricName: { color: '#e2e8f0', fontSize: 14, fontWeight: '500' },
  metricValue: { fontSize: 18, fontWeight: 'bold' },
  metricUnit: { fontSize: 12, fontWeight: 'normal' },
  barContainer: { height: 6, backgroundColor: '#334155', borderRadius: 3, marginTop: 8, overflow: 'hidden' },
  bar: { height: 6, borderRadius: 3 },
  metricDetails: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  metricDetail: { color: '#64748b', fontSize: 11 },
  footer: { padding: 16, alignItems: 'center' },
  footerText: { color: '#64748b', fontSize: 12 },
});
