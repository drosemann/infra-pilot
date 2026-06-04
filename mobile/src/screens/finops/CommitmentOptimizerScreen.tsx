import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function CommitmentOptimizerScreen() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/commitment/recommendations').then(r => setRecommendations(r.recommendations || [])).catch(() => {});
    apiClient.get('/api/v1/finops/commitment/summary').then(setSummary).catch(() => {});
  }, []);

  const implement = async (id: string) => {
    const res = await apiClient.post(`/api/v1/finops/commitment/recommendations/${id}/implement`, {});
    if (res.success) { Alert.alert('Implemented'); setRecommendations(recommendations.map(r => r.id === id ? { ...r, status: 'implemented' } : r)); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Commitment Optimizer</Text>
      {summary && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1, minWidth: '45%' }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{summary.total_recommendations}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Recommendations</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1, minWidth: '45%' }}>
            <Text style={{ color: '#4ade80', fontSize: 20, fontWeight: 'bold' }}>${summary.potential_monthly_savings}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Monthly Savings</Text>
          </View>
        </View>
      )}
      {recommendations.map((r: any) => (
        <View key={r.id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
          <Text style={{ color: '#fff', fontWeight: '600' }}>{r.resource_name} · {r.recommended_type}</Text>
          <Text style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>{r.reason}</Text>
          <Text style={{ color: '#4ade80', fontSize: 12, marginTop: 4 }}>Save ${r.monthly_savings}/mo</Text>
          {r.status === 'pending' && (
            <TouchableOpacity onPress={() => implement(r.id)} style={{ backgroundColor: '#2563eb', padding: 8, borderRadius: 4, marginTop: 8 }}>
              <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Implement</Text>
            </TouchableOpacity>
          )}
        </View>
      ))}
    </ScrollView>
  );
}
