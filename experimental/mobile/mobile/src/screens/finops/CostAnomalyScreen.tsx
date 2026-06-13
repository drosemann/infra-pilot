import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

const severityColors: Record<string, string> = { critical: '#f87171', high: '#fb923c', medium: '#facc15', low: '#60a5fa' };

export default function CostAnomalyScreen() {
  const [detections, setDetections] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/anomaly/detections').then(r => setDetections(r.detections || [])).catch(() => {});
    apiClient.get('/api/v1/finops/anomaly/summary').then(setSummary).catch(() => {});
  }, []);

  const action = async (id: string, act: string) => {
    const res = await apiClient.post(`/api/v1/finops/anomaly/detections/${id}/${act}`, {});
    if (res.success) { Alert.alert('Done'); setDetections(detections.map(d => d.id === id ? { ...d, status: act === 'resolve' ? 'resolved' : 'investigating' } : d)); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Cost Anomalies</Text>
      {summary && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{summary.total_anomalies}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Total</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#f87171', fontSize: 20, fontWeight: 'bold' }}>{summary.critical_count}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Critical</Text>
          </View>
        </View>
      )}
      {detections.filter(d => d.status !== 'resolved').map((d: any) => (
        <View key={d.id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: severityColors[d.severity] || '#64748b' }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={{ color: '#fff', fontWeight: '600' }}>{d.resource_name}</Text>
            <Text style={{ color: severityColors[d.severity] || '#94a3b8', fontSize: 12 }}>{d.severity}</Text>
          </View>
          <Text style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>{d.reason}</Text>
          <Text style={{ color: '#f87171', fontSize: 12, marginTop: 4 }}>${d.cost_impact} impact · {d.method}</Text>
          {d.status === 'detected' && (
            <View style={{ flexDirection: 'row', marginTop: 8, gap: 8 }}>
              <TouchableOpacity onPress={() => action(d.id, 'investigate')} style={{ backgroundColor: '#2563eb', padding: 6, borderRadius: 4, flex: 1 }}>
                <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Investigate</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => action(d.id, 'resolve')} style={{ backgroundColor: '#16a34a', padding: 6, borderRadius: 4, flex: 1 }}>
                <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Resolve</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      ))}
    </ScrollView>
  );
}
