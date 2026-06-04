import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function FinOpsReporting() {
  const [reports, setReports] = useState([]);
  const [summary, setSummary] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [rRes, sRes] = await Promise.all([
        fetch(`${API}/api/finops/reports`),
        fetch(`${API}/api/finops/reports/summary`),
      ]);
      setReports(await rRes.json());
      setSummary(await sRes.json());
    } catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchData(); }, []);

  const generateReport = async () => {
    try {
      await fetch(`${API}/api/finops/reports/generate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_type: 'executive_summary', period: 'monthly' }),
      });
      await fetchData();
    } catch (e) { Alert.alert('Error', e.message); }
  };

  const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.report_type}</Text>
      <Text>Period: {item.period} | Status: {item.status}</Text>
      <Text style={styles.date}>{item.generated_at}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>FinOps Reporting</Text>
      {summary && (
        <View style={styles.summary}>
          <Text style={styles.summaryText}>Total Reports: {summary.total_reports}</Text>
          <Text style={styles.summaryText}>Types: {summary.report_types?.join(', ')}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.addBtn} onPress={generateReport}>
        <Text style={styles.addBtnText}>+ Generate Report</Text>
      </TouchableOpacity>
      <FlatList
        data={reports}
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
  date: { color: '#94a3b8', marginTop: 4 },
});
