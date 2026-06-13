import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function CloudMigration() {
  const [workloads, setWorkloads] = useState([]);
  const [waves, setWaves] = useState([]);

  const fetchData = async () => {
    try {
      const [wlRes, wvRes] = await Promise.all([
        fetch(`${API}/api/migration/workloads`),
        fetch(`${API}/api/migration/waves`),
      ]);
      setWorkloads(await wlRes.json());
      setWaves(await wvRes.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const assessAll = async () => {
    for (const wl of workloads) {
      await fetch(`${API}/api/migration/workloads/${wl.id}/assess`);
    }
    await fetchData();
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Migration Toolkit</Text>
      <TouchableOpacity style={styles.assessBtn} onPress={assessAll}>
        <Text style={styles.assessBtnText}>Assess All</Text>
      </TouchableOpacity>
      <Text style={styles.subtitle}>Workloads ({workloads.length})</Text>
      <FlatList
        data={workloads}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text>{item.os_type} | {item.vcpu}vCPU | {item.memory_gb}GB</Text>
            <Text>State: {item.state}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#e2e8f0', marginBottom: 16 },
  subtitle: { fontSize: 18, fontWeight: '600', color: '#94a3b8', marginVertical: 8 },
  assessBtn: { backgroundColor: '#8b5cf6', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 8 },
  assessBtnText: { color: '#fff', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
});
