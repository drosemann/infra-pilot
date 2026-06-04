import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function SIEM() {
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAlerts = async () => {
    try { const r = await fetch(`${API}/api/soc/siem/alerts`); setAlerts(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchAlerts(); }, []);
  const onRefresh = async () => { setRefreshing(true); await fetchAlerts(); setRefreshing(false); };

  const colorForSeverity = (sev) => {
    if (sev === 'critical') return '#e74c3c';
    if (sev === 'high') return '#e67e22';
    if (sev === 'medium') return '#f1c40f';
    return '#3498db';
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>SIEM Alerts</Text>
      <FlatList
        data={alerts} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={[styles.card, { borderLeftColor: colorForSeverity(item.severity), borderLeftWidth: 4 }]}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text>Severity: {item.severity}</Text>
            <Text>Source: {item.source}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#0f0f1a' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1a1a2e', padding: 16, borderRadius: 8, marginBottom: 12 },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
});
