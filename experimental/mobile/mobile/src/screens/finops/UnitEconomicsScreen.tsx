import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function UnitEconomicsScreen() {
  const [overview, setOverview] = useState<any>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [customerId, setCustomerId] = useState('');
  const [customerData, setCustomerData] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/unit-economics/overview').then(setOverview).catch(() => {});
    apiClient.get('/api/v1/finops/unit-economics/violations').then(r => setViolations(r.violations || [])).catch(() => {});
  }, []);

  const lookupCustomer = async () => {
    const res = await apiClient.get(`/api/v1/finops/unit-economics/metrics?customer_id=${customerId}`);
    setCustomerData(res);
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Unit Economics</Text>
      {overview && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{overview.total_customers}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Customers</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#facc15', fontSize: 20, fontWeight: 'bold' }}>{overview.total_violations}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Violations</Text>
          </View>
        </View>
      )}
      <View style={{ flexDirection: 'row', marginBottom: 16 }}>
        <TextInput placeholder="Customer ID" value={customerId} onChangeText={setCustomerId} style={{ flex: 1, backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4 }} />
        <TouchableOpacity onPress={lookupCustomer} style={{ backgroundColor: '#2563eb', padding: 8, borderRadius: 4, marginLeft: 8 }}>
          <Text style={{ color: '#fff' }}>Lookup</Text>
        </TouchableOpacity>
      </View>
      {customerData && (
        <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <Text style={{ color: '#fff', fontWeight: '600' }}>Metrics for {customerId}</Text>
          {customerData.metrics?.map((m: any, i: number) => (
            <Text key={i} style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>{m.metric_name}: ${m.value}</Text>
          ))}
        </View>
      )}
      {violations.length > 0 && (
        <View>
          <Text style={{ color: '#f87171', fontWeight: '600', marginBottom: 8 }}>Violations</Text>
          {violations.map((v: any, i: number) => (
            <View key={i} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
              <Text style={{ color: '#fff' }}>{v.metric_name}</Text>
              <Text style={{ color: '#f87171', fontSize: 12 }}>{v.customer_id}: ${v.actual_value} (target: ${v.target_value})</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}
