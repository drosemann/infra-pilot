import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function CommitmentOptimizer() {
  const [recommendations, setRecommendations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [recRes, sumRes] = await Promise.all([
        fetch(`${API}/api/finops/commitment/recommendations`),
        fetch(`${API}/api/finops/commitment/summary`),
      ]);
      setRecommendations(await recRes.json());
      setSummary(await sumRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const implement = async (id) => {
    try {
      await fetch(`${API}/api/finops/commitment/recommendations/${id}/implement`, { method: 'POST' });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.provider} - {item.commitment_type}</Text>
      <Text>Term: {item.term} | Savings: ${item.estimated_monthly_savings}/mo</Text>
      <Text style={styles.status}>{item.status}</Text>
      {item.status === 'open' && (
        <TouchableOpacity style={styles.actionBtn} onPress={() => implement(item.id)}>
          <Text style={styles.actionText}>Implement</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Commitment Optimizer</Text>
      {summary && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Open: {summary.open} | Implemented: {summary.implemented}</Text>
          <Text style={styles.summaryText}>Est. Savings: ${summary.total_estimated_savings}</Text>
        </View>
      )}
      <FlatList
        data={recommendations}
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
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  status: { color: '#22c55e', marginTop: 4 },
  actionBtn: { backgroundColor: '#3b82f6', padding: 8, borderRadius: 6, marginTop: 8, alignSelf: 'flex-start' },
  actionText: { color: '#fff', fontWeight: '600' },
});
