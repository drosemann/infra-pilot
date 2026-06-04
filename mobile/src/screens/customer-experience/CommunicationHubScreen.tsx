import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function CommunicationHubScreen() {
  const [batches, setBatches] = useState<any[]>([]);

  useEffect(() => {
    endpoints.customerExperience.communication.batches().then(setBatches).catch(console.error);
  }, []);

  const renderItem = ({ item }: any) => (
    <View style={styles.card}>
      <Text style={styles.type}>{item.type} — {item.priority}</Text>
      <Text style={styles.subject}>{item.subject}</Text>
      <Text style={styles.status}>Status: {item.status} · Sent: {item.sent_count || 0}/{item.total_recipients || 0}</Text>
      <Text style={styles.date}>{item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Communication Hub</Text>
      <FlatList data={batches} keyExtractor={(i) => i.id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  heading: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  type: { fontSize: 12, color: '#888', textTransform: 'uppercase' },
  subject: { fontSize: 16, color: '#fff', fontWeight: '600', marginTop: 4 },
  status: { fontSize: 14, color: '#aaa', marginTop: 4 },
  date: { fontSize: 12, color: '#666', marginTop: 2 },
});
