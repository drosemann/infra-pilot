import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function CloudBursting() {
  const [workloads, setWorkloads] = useState([]);
  const [burstStatus, setBurstStatus] = useState(null);

  const fetchData = async () => {
    try {
      const [wlRes, burstRes] = await Promise.all([
        fetch(`${API}/api/burst/workloads`),
        fetch(`${API}/api/burst/check`),
      ]);
      setWorkloads(await wlRes.json());
      setBurstStatus(await burstRes.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const startBurst = async () => {
    await fetch(`${API}/api/burst/start`, { method: 'POST' });
    await fetchData();
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cloud Bursting</Text>
      {burstStatus && (
        <View style={styles.statusCard}>
          <Text>Utilization: {burstStatus.utilization}%</Text>
          <Text>Burst needed: {burstStatus.burst_needed ? 'Yes' : 'No'}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.burstBtn} onPress={startBurst}>
        <Text style={styles.burstBtnText}>Start Burst</Text>
      </TouchableOpacity>
      <FlatList
        data={workloads}
        keyExtractor={(item) => item.workload_id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text>Capacity: {item.current_capacity}/{item.target_capacity}</Text>
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
  statusCard: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  burstBtn: { backgroundColor: '#f59e0b', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  burstBtnText: { color: '#000', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
});
