import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

const priorityColors: Record<string, string> = {
  low: '#4caf50', medium: '#ff9800', high: '#f44336', critical: '#9c27b0',
};

export default function TicketingScreen({ navigation }: any) {
  const [tickets, setTickets] = useState<any[]>([]);

  useEffect(() => {
    endpoints.customerExperience.tickets.list().then(setTickets).catch(console.error);
  }, []);

  const renderItem = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('TicketDetail', { ticketId: item.id })}
    >
      <View style={styles.header}>
        <Text style={styles.subject} numberOfLines={1}>{item.subject}</Text>
        <Text style={[styles.priority, { color: priorityColors[item.priority] || '#fff' }]}>
          {item.priority}
        </Text>
      </View>
      <Text style={styles.status}>Status: {item.status}</Text>
      <Text style={styles.meta}>Customer: {item.customer_name || item.customer_id}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Support Tickets</Text>
      <FlatList data={tickets} keyExtractor={(i) => i.id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  subject: { fontSize: 16, color: '#fff', fontWeight: '600', flex: 1 },
  priority: { fontSize: 12, fontWeight: 'bold', marginLeft: 8 },
  status: { fontSize: 14, color: '#aaa', marginTop: 4 },
  meta: { fontSize: 12, color: '#888', marginTop: 2 },
});
