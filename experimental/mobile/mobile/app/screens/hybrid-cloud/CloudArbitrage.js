import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API = 'http://localhost:4000';

export default function CloudArbitrage() {
  const [prices, setPrices] = useState([]);
  const [savings, setSavings] = useState(null);

  const fetchData = async () => {
    try {
      const [pRes, sRes] = await Promise.all([
        fetch(`${API}/api/arbitrage/compare?vCPU=2&memory=4`),
        fetch(`${API}/api/arbitrage/savings`),
      ]);
      setPrices(await pRes.json());
      setSavings(await sRes.json());
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cloud Arbitrage</Text>
      {savings && (
        <View style={styles.savingsCard}>
          <Text style={styles.savingsText}>Monthly: ${savings.total_savings_per_month.toFixed(2)}</Text>
        </View>
      )}
      <FlatList
        data={prices}
        keyExtractor={(item) => item.provider}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.provider}</Text>
            <Text>Spot: ${item.spot_price}/hr | On-Demand: ${item.on_demand}/hr</Text>
            <Text style={styles.savings}>Save {item.savings}%</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#e2e8f0', marginBottom: 16 },
  savingsCard: { backgroundColor: '#166534', padding: 16, borderRadius: 8, marginBottom: 16 },
  savingsText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 8, marginBottom: 12 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9' },
  savings: { color: '#22c55e', fontWeight: '600', marginTop: 4 },
});
