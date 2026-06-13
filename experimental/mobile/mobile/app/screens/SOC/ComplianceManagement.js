import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function ComplianceManagement() {
  const [frameworks, setFrameworks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchFrameworks = async () => {
    try { const r = await fetch(`${API}/api/soc/compliance/frameworks`); setFrameworks(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchFrameworks(); }, []);
  const onRefresh = async () => { setRefreshing(true); await fetchFrameworks(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Compliance Frameworks</Text>
      <FlatList
        data={frameworks} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text>Status: {item.status} | Version: {item.version}</Text>
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
  name: { fontSize: 16, fontWeight: 'bold', color: '#2ecc71' },
});
