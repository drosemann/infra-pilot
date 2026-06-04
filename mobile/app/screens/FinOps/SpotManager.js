import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function SpotManager() {
  const [fleets, setFleets] = useState([]);
  const [savings, setSavings] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [fRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/spot/fleets`),
        fetch(`${API}/api/finops/spot/savings`),
      ]);
      setFleets(await fRes.json());
      setSavings(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const createFleet = async () => {
    try {
      await fetch(`${API}/api/finops/spot/fleets`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: `fleet-${Date.now()}`, instance_types: ['m5.large'], target_capacity: 2, regions: ['us-east-1'] }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.name}</Text>
      <Text>Instances: {item.running_instances} | Savings: {item.savings_pct}%</Text>
      <Text style={styles.status}>{item.status}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Spot Manager</Text>
      {savings && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Total Savings: ${savings.total_savings} ({savings.savings_pct}%)</Text>
          <Text style={styles.summaryText}>Fleets: {savings.fleets_count} | Instances: {savings.instance_count}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={createFleet}>
        <Text style={styles.addBtnText}>+ New Fleet</Text>
      </TouchableOpacity>
      <FlatList
        data={fleets}
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
  status: { color: '#22c55e', marginTop: 4 },
});
