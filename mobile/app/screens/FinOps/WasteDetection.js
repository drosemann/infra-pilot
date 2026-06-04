import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function WasteDetection() {
  const [findings, setFindings] = useState([]);
  const [summary, setSummary] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [fRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/waste/findings`),
        fetch(`${API}/api/finops/waste/summary`),
      ]);
      setFindings(await fRes.json());
      setSummary(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const runScan = async () => {
    try { await fetch(`${API}/api/finops/waste/scan`, { method: 'POST' }); await fetchData(); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  const cleanup = async (id) => {
    try { await fetch(`${API}/api/finops/waste/findings/${id}/cleanup`, { method: 'POST' }); await fetchData(); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.category}</Text>
      <Text>{item.resource} | Waste: ${item.estimated_waste}</Text>
      <Text style={item.severity === 'high' ? styles.high : styles.status}>{item.status}</Text>
      {item.status === 'open' && (
        <TouchableOpacity style={styles.actionBtn} onPress={() => cleanup(item.id)}>
          <Text style={styles.actionText}>Cleanup</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Waste Detection</Text>
      {summary && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Findings: {summary.total} | Waste: ${summary.total_waste}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={runScan}>
        <Text style={styles.addBtnText}>Run Scan</Text>
      </TouchableOpacity>
      <FlatList
        data={findings}
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
  addBtn: { backgroundColor: '#f59e0b', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  addBtnText: { color: '#fff', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  status: { color: '#94a3b8', marginTop: 4 },
  high: { color: '#ef4444', marginTop: 4 },
  actionBtn: { backgroundColor: '#22c55e', padding: 8, borderRadius: 6, marginTop: 8, alignSelf: 'flex-start' },
  actionText: { color: '#fff', fontWeight: '600' },
});
