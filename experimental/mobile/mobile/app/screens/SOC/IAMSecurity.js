import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function IAMSecurity() {
  const [users, setUsers] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchUsers = async () => {
    try { const r = await fetch(`${API}/api/soc/iam/users`); setUsers(await r.json()); }
    catch (e) { Alert.alert('Error', e.message); }
  };

  useEffect(() => { fetchUsers(); }, []);
  const onRefresh = async () => { setRefreshing(true); await fetchUsers(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>IAM Users</Text>
      <FlatList
        data={users} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.username}</Text>
            <Text>{item.email} | MFA: {item.mfa_enabled ? '✓' : '✗'}</Text>
            <Text>Roles: {(item.roles || []).join(', ')}</Text>
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
  name: { fontSize: 16, fontWeight: 'bold', color: '#f39c12' },
});
