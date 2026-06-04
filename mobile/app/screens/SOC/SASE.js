import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function SASE() {
  const [policies, setPolicies] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPolicies = async () => {
    try { const r = await fetch(`${API}/api/soc/sase/policies`); setPolicies(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchPolicies(); }, []);
  const onRefresh = async () => { setRefreshing(true); await fetchPolicies(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>SASE</Text>
      <FlatList
        data={policies} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.name}</Text>
            <Text>Type: {item.type}</Text>
            <Text>{item.enabled ? '✓ Enabled' : '✗ Disabled'}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No policies</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#0f0f1a' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1a1a2e', padding: 16, borderRadius: 8, marginBottom: 12 },
  cardTitle: { fontSize: 18, fontWeight: 'bold', color: '#fff' },
  empty: { color: '#666', textAlign: 'center', marginTop: 40 },
});
