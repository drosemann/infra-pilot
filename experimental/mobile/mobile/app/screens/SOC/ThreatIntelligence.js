import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function ThreatIntelligence() {
  const [iocs, setIocs] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchIocs = async () => {
    try { const r = await fetch(`${API}/api/soc/ti/iocs`); setIocs(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchIocs(); }, []);

  const onRefresh = async () => { setRefreshing(true); await fetchIocs(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Threat Intelligence</Text>
      <TouchableOpacity style={styles.addBtn}><Text style={styles.addBtnText}>+ Add IOC</Text></TouchableOpacity>
      <FlatList
        data={iocs} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.type}: {item.value}</Text>
            <Text>Confidence: {item.confidence}%</Text>
            <Text>Source: {item.source}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No IoCs found</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#0f0f1a' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  addBtn: { backgroundColor: '#e74c3c', padding: 12, borderRadius: 8, marginBottom: 16, alignItems: 'center' },
  addBtnText: { color: '#fff', fontWeight: 'bold' },
  card: { backgroundColor: '#1a1a2e', padding: 16, borderRadius: 8, marginBottom: 12 },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  empty: { color: '#666', textAlign: 'center', marginTop: 40 },
});
