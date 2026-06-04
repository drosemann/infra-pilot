import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function CostAllocation() {
  const [summary, setSummary] = useState(null);

  const fetchData = async () => {
    try {
      const res = await fetch(`${API}/api/cost-allocation/summary`);
      setSummary(await res.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cost Allocation</Text>
      {summary && (
        <View style={styles.summaryCard}>
          <Text style={styles.amount}>Allocated: ${summary.total_allocated.toFixed(2)}</Text>
          <Text>Teams: {summary.active_teams}</Text>
          <Text>Allocations: {summary.total_allocations}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#e2e8f0', marginBottom: 16 },
  summaryCard: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 16 },
  amount: { fontSize: 20, fontWeight: 'bold', color: '#22c55e', marginBottom: 8 },
});
