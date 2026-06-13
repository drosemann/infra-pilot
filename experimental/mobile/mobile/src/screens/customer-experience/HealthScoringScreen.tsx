import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function HealthScoringScreen({ navigation }: any) {
  const [profiles, setProfiles] = useState<any[]>([]);

  useEffect(() => {
    endpoints.customerExperience.health.profiles().then(setProfiles).catch(console.error);
  }, []);

  const renderItem = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('HealthDetail', { customerId: item.customer_id })}
    >
      <Text style={styles.name}>{item.customer_name || item.customer_id}</Text>
      <Text style={[styles.score, {
        color: item.overall_score >= 70 ? '#4caf50' : item.overall_score >= 40 ? '#ff9800' : '#f44336',
      }]}>
        {item.overall_score?.toFixed(0) || 'N/A'}
      </Text>
      <Text style={styles.risk}>Risk: {item.risk_level || 'unknown'}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Customer Health Scoring</Text>
      <FlatList data={profiles} keyExtractor={(i) => i.customer_id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, color: '#fff', fontWeight: '600' },
  score: { fontSize: 32, fontWeight: 'bold', marginVertical: 4 },
  risk: { fontSize: 14, color: '#aaa' },
});
