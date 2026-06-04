import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function MultiCloudBroker() {
  const [resources, setResources] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchResources = async () => {
    try {
      const res = await fetch(`${API}/api/cloud/resources`);
      setResources(await res.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchResources(); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchResources();
    setRefreshing(false);
  };

  const provision = async () => {
    try {
      await fetch(`${API}/api/cloud/resources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'aws', type: 'ec2', name: `vm-${Date.now()}`, region: 'us-east-1' }),
      });
      await fetchResources();
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  const remove = async (id) => {
    try {
      await fetch(`${API}/api/cloud/resources/${id}`, { method: 'DELETE' });
      await fetchResources();
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.name}</Text>
      <Text>{item.provider} | {item.type} | {item.region}</Text>
      <Text style={styles.status}>{item.status}</Text>
      <TouchableOpacity style={styles.deleteBtn} onPress={() => remove(item.id)}>
        <Text style={styles.deleteText}>Delete</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Multi-Cloud Broker</Text>
      <TouchableOpacity style={styles.addBtn} onPress={provision}>
        <Text style={styles.addBtnText}>+ New Resource</Text>
      </TouchableOpacity>
      <FlatList
        data={resources}
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
  addBtn: { backgroundColor: '#3b82f6', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  addBtnText: { color: '#fff', fontWeight: '600' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  status: { color: '#22c55e', marginTop: 4 },
  deleteBtn: { backgroundColor: '#ef4444', padding: 8, borderRadius: 6, marginTop: 8, alignSelf: 'flex-start' },
  deleteText: { color: '#fff', fontWeight: '600' },
});
