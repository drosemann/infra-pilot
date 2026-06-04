import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function CarbonCostOptimizer() {
  const [assets, setAssets] = useState([]);
  const [sustainability, setSustainability] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [aRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/carbon/assets`),
        fetch(`${API}/api/finops/carbon/sustainability-budget`),
      ]);
      setAssets(await aRes.json());
      setSustainability(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const registerAsset = async () => {
    try {
      await fetch(`${API}/api/finops/carbon/assets`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: `asset-${Date.now()}`, provider: 'aws', region: 'us-east-1', monthly_cost: Math.round(Math.random() * 5000), kwh: Math.round(Math.random() * 20000) }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.name}</Text>
      <Text>{item.provider} | {item.region} | ${item.monthly_cost}/mo</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Carbon-Aware Optimizer</Text>
      {sustainability && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>YTD Carbon: {sustainability.current_ytd} tons</Text>
          <Text style={styles.summaryText}>Target: {sustainability.annual_target} tons | Remaining: {sustainability.budget_remaining}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={registerAsset}>
        <Text style={styles.addBtnText}>+ Register Asset</Text>
      </TouchableOpacity>
      <FlatList
        data={assets}
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
  addBtn: { backgroundColor: '#22c55e', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  addBtnText: { color: '#fff', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
});
