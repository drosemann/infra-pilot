import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function UnitEconomics() {
  const [metrics, setMetrics] = useState([]);
  const [overview, setOverview] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [mRes, oRes] = await Promise.all([
        fetch(`${API}/api/finops/unit-economics/metrics`),
        fetch(`${API}/api/finops/unit-economics/overview`),
      ]);
      setMetrics(await mRes.json());
      setOverview(await oRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const recordMetric = async () => {
    try {
      await fetch(`${API}/api/finops/unit-economics/metrics`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: `cust-${Date.now()}`, metric_name: 'cost_per_user', value: Math.random() * 20, dimension: 'compute' }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.metric_name}</Text>
      <Text>Customer: {item.customer_id} | Value: {item.value}</Text>
      <Text style={styles.dim}>Dimension: {item.dimension}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Unit Economics</Text>
      {overview && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Metrics: {overview.total_metrics} | Targets: {overview.total_targets}</Text>
          <Text style={styles.summaryText}>Violations: {overview.violations}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={recordMetric}>
        <Text style={styles.addBtnText}>+ Record Metric</Text>
      </TouchableOpacity>
      <FlatList
        data={metrics}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#e2e8f0', marginBottom: 16 },
  summary: { backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 16 },
  summaryText: { color: '#94a3b8', fontSize: 14 },
  addBtn: { backgroundColor: '#3b82f6', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  addBtnText: { color: '#fff', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  dim: { color: '#94a3b8', marginTop: 4 },
});
