import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function CarbonCostOptimizerScreen() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [sustainability, setSustainability] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', provider: 'aws', region: 'us-east-1', monthly_cost: '1000' });

  useEffect(() => {
    apiClient.get('/api/v1/finops/carbon/recommendations').then(r => setRecommendations(r.recommendations || [])).catch(() => {});
    apiClient.get('/api/v1/finops/carbon/sustainability-budget').then(setSustainability).catch(() => {});
  }, []);

  const registerAsset = async () => {
    const res = await apiClient.post('/api/v1/finops/carbon/assets', { ...form, monthly_cost: parseFloat(form.monthly_cost) });
    if (res.id) { Alert.alert('Asset registered!'); setShowForm(false); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Carbon Cost Optimizer</Text>
      <TouchableOpacity onPress={() => setShowForm(!showForm)} style={{ backgroundColor: '#16a34a', padding: 10, borderRadius: 8, marginBottom: 16 }}>
        <Text style={{ color: '#fff', textAlign: 'center' }}>{showForm ? 'Cancel' : '+ Register Asset'}</Text>
      </TouchableOpacity>
      {showForm && (
        <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <TextInput placeholder="Name" value={form.name} onChangeText={v => setForm({...form, name: v})} style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TextInput placeholder="Monthly cost" value={form.monthly_cost} onChangeText={v => setForm({...form, monthly_cost: v})} keyboardType="numeric" style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TouchableOpacity onPress={registerAsset} style={{ backgroundColor: '#16a34a', padding: 8, borderRadius: 4 }}>
            <Text style={{ color: '#fff', textAlign: 'center' }}>Register</Text>
          </TouchableOpacity>
        </View>
      )}
      {sustainability && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#4ade80', fontSize: 20, fontWeight: 'bold' }}>{sustainability.total_annual_co2_tons}t</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Annual CO2</Text>
          </View>
        </View>
      )}
      {recommendations.map((r: any) => (
        <View key={r.id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
          <Text style={{ color: '#fff', fontWeight: '600' }}>{r.asset_name}: {r.current_region} → {r.recommended_region}</Text>
          <Text style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>Cost: ${r.current_monthly_cost} → ${r.new_monthly_cost}</Text>
          <Text style={{ color: '#4ade80', fontSize: 12 }}>CO2: {r.current_monthly_co2_kg}kg → {r.new_monthly_co2_kg}kg</Text>
        </View>
      ))}
    </ScrollView>
  );
}
