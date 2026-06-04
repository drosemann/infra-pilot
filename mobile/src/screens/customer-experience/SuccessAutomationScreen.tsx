import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function SuccessAutomationScreen() {
  const [plays, setPlays] = useState<any[]>([]);

  useEffect(() => {
    endpoints.customerExperience.success.plays().then(setPlays).catch(console.error);
  }, []);

  const renderItem = ({ item }: any) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.name}</Text>
      <Text style={styles.desc}>{item.description}</Text>
      <Text style={styles.trigger}>Trigger: {item.trigger_event}</Text>
      <Text style={[styles.status, {
        color: item.status === 'active' ? '#4caf50' : item.status === 'paused' ? '#ff9800' : '#888',
      }]}>
        {item.status}
      </Text>
      <Text style={styles.actions}>{item.actions?.length || 0} action(s)</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Success Automation</Text>
      <FlatList data={plays} keyExtractor={(i) => i.id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  heading: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, color: '#fff', fontWeight: '600' },
  desc: { fontSize: 14, color: '#aaa', marginTop: 2 },
  trigger: { fontSize: 12, color: '#888', marginTop: 4 },
  status: { fontSize: 14, fontWeight: 'bold', marginTop: 4 },
  actions: { fontSize: 12, color: '#666', marginTop: 2 },
});
