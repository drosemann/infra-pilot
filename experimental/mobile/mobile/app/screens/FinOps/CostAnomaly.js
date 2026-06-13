import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function CostAnomaly() {
  const [anomalies, setAnomalies] = useState([]);
  const [summary, setSummary] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [aRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/anomaly/detections`),
        fetch(`${API}/api/finops/anomaly/summary`),
      ]);
      setAnomalies(await aRes.json());
      setSummary(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const ingestSpend = async () => {
    try {
      await fetch(`${API}/api/finops/anomaly/ingest`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service: 'EC2', amount: Math.random() * 20000, region: 'us-east-1' }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const resolve = async (id) => {
    try { await fetch(`${API}/api/finops/anomaly/detections/${id}/resolve`, { method: 'POST' }); await fetchData(); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={[styles.card, item.severity === 'critical' && styles.critical]}>
      <Text style={styles.name}>{item.service} - ${item.amount}</Text>
      <Text>Severity: {item.severity} | Region: {item.region}</Text>
      <Text style={styles.status}>{item.status}</Text>
      {item.status === 'open' && (
        <TouchableOpacity style={styles.actionBtn} onPress={() => resolve(item.id)}>
          <Text style={styles.actionText}>Resolve</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cost Anomaly Detection</Text>
      {summary && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Total: {summary.total} | Critical: {summary.critical}</Text>
          <Text style={styles.summaryText}>Excess Spend: ${summary.estimated_excess_spend}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={ingestSpend}>
        <Text style={styles.addBtnText}>+ Ingest Spend</Text>
      </TouchableOpacity>
      <FlatList
        data={anomalies}
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
  critical: { borderLeftWidth: 4, borderLeftColor: '#ef4444' },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  status: { color: '#f59e0b', marginTop: 4 },
  actionBtn: { backgroundColor: '#22c55e', padding: 8, borderRadius: 6, marginTop: 8, alignSelf: 'flex-start' },
  actionText: { color: '#fff', fontWeight: '600' },
});
