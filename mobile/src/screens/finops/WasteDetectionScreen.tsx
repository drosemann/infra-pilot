import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function WasteDetectionScreen() {
  const [findings, setFindings] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/waste/summary').then(setSummary).catch(() => {});
    apiClient.get('/api/v1/finops/waste/findings').then(r => setFindings(r.findings || [])).catch(() => {});
  }, []);

  const scan = async () => {
    const res = await apiClient.post('/api/v1/finops/waste/scan', {});
    if (res.findings !== undefined) { Alert.alert(`Scan done: ${res.findings} items`); const fr = await apiClient.get('/api/v1/finops/waste/findings'); setFindings(fr.findings || []); }
  };

  const action = async (id: string, act: string) => {
    const res = await apiClient.post(`/api/v1/finops/waste/findings/${id}/${act}`, {});
    if (res.success) { Alert.alert('Done'); setFindings(findings.map(f => f.id === id ? { ...f, status: act === 'cleanup' ? 'cleaned_up' : act === 'approve' ? 'approved_for_cleanup' : 'dismissed' } : f)); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Waste Detection</Text>
      <TouchableOpacity onPress={scan} style={{ backgroundColor: '#7c3aed', padding: 10, borderRadius: 8, marginBottom: 16 }}>
        <Text style={{ color: '#fff', textAlign: 'center' }}>Scan Now</Text>
      </TouchableOpacity>
      {summary && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{summary.total_findings}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Findings</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#f87171', fontSize: 20, fontWeight: 'bold' }}>${summary.total_monthly_waste}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Monthly Waste</Text>
          </View>
        </View>
      )}
      {findings.filter(f => f.status !== 'cleaned_up').map((f: any) => (
        <View key={f.id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <View>
              <Text style={{ color: '#fff', fontWeight: '600' }}>{f.resource_name}</Text>
              <Text style={{ color: '#f87171', fontSize: 12, marginTop: 2 }}>${f.monthly_waste}/mo</Text>
            </View>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>{f.category}</Text>
          </View>
          <Text style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>{f.reason}</Text>
          {f.status === 'detected' && (
            <View style={{ flexDirection: 'row', marginTop: 8, gap: 8 }}>
              {f.auto_cleanup_eligible && (
                <TouchableOpacity onPress={() => action(f.id, 'approve')} style={{ backgroundColor: '#facc15', padding: 6, borderRadius: 4, flex: 1 }}>
                  <Text style={{ color: '#000', textAlign: 'center', fontSize: 12 }}>Approve</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity onPress={() => action(f.id, 'dismiss')} style={{ backgroundColor: '#64748b', padding: 6, borderRadius: 4, flex: 1 }}>
                <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Dismiss</Text>
              </TouchableOpacity>
            </View>
          )}
          {f.status === 'approved_for_cleanup' && (
            <TouchableOpacity onPress={() => action(f.id, 'cleanup')} style={{ backgroundColor: '#16a34a', padding: 6, borderRadius: 4, marginTop: 8 }}>
              <Text style={{ color: '#fff', textAlign: 'center', fontSize: 12 }}>Cleanup</Text>
            </TouchableOpacity>
          )}
        </View>
      ))}
    </ScrollView>
  );
}
