import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function RightsizingScreen() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/rightsizing/recommendations').then(r => setRecommendations(r.recommendations || [])).catch(() => {});
    apiClient.get('/api/v1/finops/rightsizing/summary').then(setSummary).catch(() => {});
  }, []);

  const action = async (id: string, act: string) => {
    const res = await apiClient.post(`/api/v1/finops/rightsizing/recommendations/${id}/${act}`, {});
    if (res.success) { Alert.alert('Done'); setRecommendations(recommendations.map(r => r.id === id ? { ...r, status: act === 'implement' ? 'implemented' : act === 'approve' ? 'approved' : 'dismissed' } : r)); }
  };

  const priorityColors: Record<string, string> = { critical: '#f87171', high: '#fb923c', medium: '#facc15', low: '#60a5fa' };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Right-Sizing</Text>
      {summary && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{summary.total_recommendations}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Total</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#4ade80', fontSize: 20, fontWeight: 'bold' }}>${summary.potential_monthly_savings}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Savings</Text>
          </View>
        </View>
      )}
      {recommendations.map((r: any) => (
        <View key={r.id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: priorityColors[r.priority] || '#64748b' }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={{ color: '#fff', fontWeight: '600' }}>{r.resource_name}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>{r.status}</Text>
          </View>
          <Text style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>{r.reason}</Text>
          <Text style={{ color: '#4ade80', fontSize: 12, marginTop: 4 }}>{r.current_size} → {r.recommended_size} · Save ${r.monthly_savings}/mo</Text>
          {r.status === 'pending' && (
            <View style={{ flexDirection: 'row', marginTop: 8, gap: 8 }}>
              <TouchableOpacity onPress={() => action(r.id, 'approve')} style={{ backgroundColor: '#2563eb', padding: 6, borderRadius: 4, flex: 1 }}>
                <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Approve</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => action(r.id, 'dismiss')} style={{ backgroundColor: '#64748b', padding: 6, borderRadius: 4, flex: 1 }}>
                <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Dismiss</Text>
              </TouchableOpacity>
            </View>
          )}
          {r.status === 'approved' && (
            <TouchableOpacity onPress={() => action(r.id, 'implement')} style={{ backgroundColor: '#16a34a', padding: 6, borderRadius: 4, marginTop: 8 }}>
              <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Implement</Text>
            </TouchableOpacity>
          )}
        </View>
      ))}
    </ScrollView>
  );
}
