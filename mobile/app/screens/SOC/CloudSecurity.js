import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function CloudSecurity() {
  const [findings, setFindings] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchFindings = async () => {
    try { const r = await fetch(`${API}/api/soc/cloud/cspm`); setFindings(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchFindings(); }, []);
  const onRefresh = async () => { setRefreshing(true); await fetchFindings(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cloud Security</Text>
      <FlatList
        data={findings} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.resource}>{item.resource}</Text>
            <Text>Rule: {item.rule} | Severity: {item.severity}</Text>
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
  resource: { fontSize: 16, fontWeight: 'bold', color: '#9b59b6' },
});
