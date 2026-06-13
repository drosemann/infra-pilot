import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function AdoptionAnalyticsScreen() {
  const [customerId, setCustomerId] = useState('');
  const [features, setFeatures] = useState<any[]>([]);

  const loadFeatures = async () => {
    if (!customerId) return;
    try {
      const res = await endpoints.customerExperience.adoption.features(customerId);
      setFeatures(res);
    } catch (e) {
      console.error(e);
    }
  };

  const renderItem = ({ item }: any) => (
    <View style={styles.card}>
      <Text style={styles.featureName}>{item.feature_name || item.feature_id}</Text>
      <Text style={styles.count}>Usage count: {item.usage_count || 0}</Text>
      <Text style={styles.last}>Last used: {item.last_used ? new Date(item.last_used).toLocaleDateString() : 'Never'}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Adoption Analytics</Text>
      <TextInput
        style={styles.input}
        placeholder="Customer ID"
        placeholderTextColor="#666"
        value={customerId}
        onChangeText={setCustomerId}
      />
      <TouchableOpacity style={styles.button} onPress={loadFeatures}>
        <Text style={styles.buttonText}>Load Features</Text>
      </TouchableOpacity>
      <FlatList data={features} keyExtractor={(i, idx) => `${i.feature_id}-${idx}`} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  input: { backgroundColor: '#1e1e1e', color: '#fff', borderRadius: 8, padding: 12, marginBottom: 12 },
  button: { backgroundColor: '#1976d2', padding: 14, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  featureName: { fontSize: 16, color: '#fff', fontWeight: '600' },
  count: { fontSize: 14, color: '#ccc', marginTop: 4 },
  last: { fontSize: 12, color: '#888', marginTop: 2 },
});
