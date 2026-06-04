import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function DiscountArbitrage() {
  const [workloads, setWorkloads] = useState([]);
  const [savings, setSavings] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [wRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/arbitrage/workloads`),
        fetch(`${API}/api/finops/arbitrage/savings`),
      ]);
      setWorkloads(await wRes.json());
      setSavings(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const registerWorkload = async () => {
    try {
      await fetch(`${API}/api/finops/arbitrage/workloads`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: `wl-${Date.now()}`, cpu_cores: 8, memory_gb: 32, storage_gb: 200, data_transfer_gb: 500, current_provider: 'aws', current_cost: 1500 }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.name}</Text>
      <Text>{item.current_provider} | ${item.current_cost}/mo</Text>
      <Text style={styles.status}>{item.status}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Discount Arbitrage</Text>
      {savings && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Potential Savings: ${savings.total_potential_savings}</Text>
          <Text style={styles.summaryText}>Best Provider: {savings.best_provider} | Avg Savings: {savings.average_savings_pct}%</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={registerWorkload}>
        <Text style={styles.addBtnText}>+ Register Workload</Text>
      </TouchableOpacity>
      <FlatList
        data={workloads}
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
  addBtn: { backgroundColor: '#8b5cf6', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  addBtnText: { color: '#fff', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  status: { color: '#22c55e', marginTop: 4 },
});
