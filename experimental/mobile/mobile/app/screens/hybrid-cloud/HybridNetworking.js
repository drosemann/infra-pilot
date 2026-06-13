import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function HybridNetworking() {
  const [peers, setPeers] = useState([]);
  const [topology, setTopology] = useState(null);

  const fetchData = async () => {
    try {
      const [pRes, tRes] = await Promise.all([
        fetch(`${API}/api/mesh/peers`),
        fetch(`${API}/api/mesh/topology`),
      ]);
      setPeers(await pRes.json());
      setTopology(await tRes.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Mesh Network</Text>
      {topology && (
        <View style={styles.topologyCard}>
          <Text style={styles.topoText}>Peers: {topology.total_peers}</Text>
          <Text style={styles.topoText}>Tunnels: {topology.active_tunnels}</Text>
        </View>
      )}
      <FlatList
        data={peers}
        keyExtractor={(item) => item.peer_id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <Text>{item.node_type} | {item.endpoint}</Text>
            <Text style={item.connected ? styles.online : styles.offline}>
              {item.connected ? 'Connected' : 'Disconnected'}
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
  topologyCard: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 16, flexDirection: 'row', gap: 24 },
  topoText: { color: '#94a3b8', fontSize: 14 },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  online: { color: '#22c55e' },
  offline: { color: '#ef4444' },
});
