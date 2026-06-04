import React, { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from 'react-native';

const API = 'http://localhost:4000';

export default function SOARPlatform() {
  const [playbooks, setPlaybooks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPlaybooks = async () => {
    try {
      const res = await fetch(`${API}/api/soc/soar/playbooks`);
      setPlaybooks(await res.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchPlaybooks(); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPlaybooks();
    setRefreshing(false);
  };

  const executePlaybook = async (id) => {
    try {
      await fetch(`${API}/api/soc/soar/playbooks/${id}/execute`, { method: 'POST' });
      Alert.alert('Executed', `Playbook ${id} triggered`);
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>SOAR Platform</Text>
      <TouchableOpacity style={styles.addBtn} onPress={() => Alert.prompt('Create Playbook', 'Enter name:')}>
        <Text style={styles.addBtnText}>+ New Playbook</Text>
      </TouchableOpacity>
      <FlatList
        data={playbooks}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.name}</Text>
            <Text>Trigger: {item.trigger}</Text>
            <Text>Status: {item.enabled ? 'Active' : 'Disabled'}</Text>
            <TouchableOpacity style={styles.action} onPress={() => executePlaybook(item.id)}>
              <Text style={styles.actionText}>Execute</Text>
            </TouchableOpacity>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No playbooks found</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#0f0f1a' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  addBtn: { backgroundColor: '#2ecc71', padding: 12, borderRadius: 8, marginBottom: 16, alignItems: 'center' },
  addBtnText: { color: '#fff', fontWeight: 'bold' },
  card: { backgroundColor: '#1a1a2e', padding: 16, borderRadius: 8, marginBottom: 12 },
  cardTitle: { fontSize: 18, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  action: { backgroundColor: '#3498db', padding: 8, borderRadius: 4, marginTop: 8, alignItems: 'center' },
  actionText: { color: '#fff' },
  empty: { color: '#666', textAlign: 'center', marginTop: 40 },
});
