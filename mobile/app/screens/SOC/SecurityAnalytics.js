import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function SecurityAnalytics() {
  const [dashboards, setDashboards] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboards = async () => {
    try { const r = await fetch(`${API}/api/soc/analytics/dashboards`); setDashboards(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchDashboards(); }, []);
  const onRefresh = async () => { setRefreshing(true); await fetchDashboards(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Security Analytics</Text>
      <View style={styles.metrics}>
        <View style={styles.metric}><Text style={styles.metricValue}>14m</Text><Text style={styles.metricLabel}>MTTD</Text></View>
        <View style={styles.metric}><Text style={styles.metricValue}>42m</Text><Text style={styles.metricLabel}>MTTR</Text></View>
        <View style={styles.metric}><Text style={styles.metricValue}>96.2%</Text><Text style={styles.metricLabel}>Detection</Text></View>
      </View>
      <FlatList
        data={dashboards} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text>Widgets: {(item.widgets || []).join(', ')}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#0f0f1a' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  metrics: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 16 },
  metric: { alignItems: 'center' },
  metricValue: { fontSize: 24, fontWeight: 'bold', color: '#e67e22' },
  metricLabel: { color: '#999', fontSize: 12 },
  card: { backgroundColor: '#1a1a2e', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#e67e22' },
});
