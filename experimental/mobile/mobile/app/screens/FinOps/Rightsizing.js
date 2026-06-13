import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function Rightsizing() {
  const [recommendations, setRecommendations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [rRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/rightsizing/recommendations`),
        fetch(`${API}/api/finops/rightsizing/summary`),
      ]);
      setRecommendations(await rRes.json());
      setSummary(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const approveRec = async (id) => {
    try { await fetch(`${API}/api/finops/rightsizing/recommendations/${id}/approve`, { method: 'POST' }); await fetchData(); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.resource || item.id}</Text>
      <Text>Savings: ${item.estimated_savings}/mo | Confidence: {item.confidence}</Text>
      <Text style={styles.status}>{item.status}</Text>
      {item.status === 'open' && (
        <TouchableOpacity style={styles.actionBtn} onPress={() => approveRec(item.id)}>
          <Text style={styles.actionText}>Approve</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Right-Sizing</Text>
      {summary && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Open: {summary.open} | Approved: {summary.approved}</Text>
          <Text style={styles.summaryText}>Potential Savings: ${summary.total_potential_savings}</Text>
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
  status: { color: '#f59e0b', marginTop: 4 },
  actionBtn: { backgroundColor: '#3b82f6', padding: 8, borderRadius: 6, marginTop: 8, alignSelf: 'flex-start' },
  actionText: { color: '#fff', fontWeight: '600' },
});
