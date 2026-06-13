import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function IAMBridge() {
  const [mappings, setMappings] = useState([]);

  const fetchData = async () => {
    try {
      const res = await fetch(`${API}/api/iam/mappings`);
      setMappings(await res.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>IAM Bridge</Text>
      <FlatList
        data={mappings}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.source_role} → {item.target_role}</Text>
            <Text>{item.source_provider} → {item.target_provider}</Text>
            <Text style={item.active ? styles.active : styles.inactive}>
              {item.active ? 'Active' : 'Inactive'}
            </Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#e2e8f0', marginBottom: 16 },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  active: { color: '#22c55e' },
  inactive: { color: '#ef4444' },
});
