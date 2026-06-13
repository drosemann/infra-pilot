import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function BudgetForecast() {
  const [budgets, setBudgets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [bRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/budget`),
        fetch(`${API}/api/finops/budget/summary`),
      ]);
      setBudgets(await bRes.json());
      setSummary(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const createBudget = async () => {
    try {
      await fetch(`${API}/api/finops/budget`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: `budget-${Date.now()}`, amount: Math.round(Math.random() * 50000), period: 'monthly' }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const recordSpend = async (id) => {
    try {
      await fetch(`${API}/api/finops/budget/${id}/spend`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: Math.round(Math.random() * 5000) }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.name}</Text>
      <Text>Budget: ${item.amount} | Spent: ${item.spent || 0}</Text>
      <Text style={item.spent > item.amount * 0.8 ? styles.atRisk : styles.status}>{item.status}</Text>
      <TouchableOpacity style={styles.actionBtn} onPress={() => recordSpend(item.id)}>
        <Text style={styles.actionText}>+ Spend</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Budget & Forecast</Text>
      {summary && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Budgets: {summary.total_budgets} | Total: ${summary.total_budget_amount}</Text>
          <Text style={styles.summaryText}>Utilization: {summary.utilization_pct.toFixed(1)}% | At Risk: {summary.at_risk}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={createBudget}>
        <Text style={styles.addBtnText}>+ New Budget</Text>
      </TouchableOpacity>
      <FlatList
        data={budgets}
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
  atRisk: { color: '#ef4444', marginTop: 4 },
  actionBtn: { backgroundColor: '#8b5cf6', padding: 8, borderRadius: 6, marginTop: 8, alignSelf: 'flex-start' },
  actionText: { color: '#fff', fontWeight: '600' },
});
