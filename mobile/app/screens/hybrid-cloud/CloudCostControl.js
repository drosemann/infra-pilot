import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function CloudCostControl() {
  const [summary, setSummary] = useState(null);
  const [budgets, setBudgets] = useState([]);

  const fetchData = async () => {
    try {
      const [sRes, bRes] = await Promise.all([
        fetch(`${API}/api/cost/summary`),
        fetch(`${API}/api/cost/budgets`),
      ]);
      setSummary(await sRes.json());
      setBudgets(await bRes.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cost Control</Text>
      {summary && (
        <View style={styles.summaryCard}>
          <Text style={styles.total}>Total: ${summary.total.toFixed(2)}</Text>
          <Text>Records: {summary.record_count}</Text>
        </View>
      )}
      <Text style={styles.subtitle}>Budgets</Text>
      <FlatList
        data={budgets}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text>${item.spent} / ${item.amount}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#e2e8f0', marginBottom: 16 },
  subtitle: { fontSize: 18, fontWeight: '600', color: '#94a3b8', marginBottom: 8 },
  summaryCard: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 16 },
  total: { fontSize: 20, fontWeight: 'bold', color: '#22c55e' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
});
