import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function SpotManagerScreen() {
  const [fleets, setFleets] = useState<any[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [instances, setInstances] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', instance_type: 't3.medium', target_capacity: 2 });

  useEffect(() => {
    apiClient.get('/api/v1/finops/spot/fleets').then(r => setFleets(r.fleets || [])).catch(() => {});
  }, []);

  const createFleet = async () => {
    const res = await apiClient.post('/api/v1/finops/spot/fleets', form);
    if (res.id) { Alert.alert('Fleet created'); setShowForm(false); setFleets([...fleets, res]); }
  };

  const toggleExpand = async (id: string) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    const res = await apiClient.get(`/api/v1/finops/spot/fleets/${id}/instances`);
    setInstances(res.instances || []);
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Spot Manager</Text>
      <TouchableOpacity onPress={() => setShowForm(!showForm)} style={{ backgroundColor: '#7c3aed', padding: 10, borderRadius: 8, marginBottom: 16 }}>
        <Text style={{ color: '#fff', textAlign: 'center' }}>{showForm ? 'Cancel' : '+ New Fleet'}</Text>
      </TouchableOpacity>
      {showForm && (
        <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <TextInput placeholder="Name" value={form.name} onChangeText={v => setForm({...form, name: v})} style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TextInput placeholder="Instance type" value={form.instance_type} onChangeText={v => setForm({...form, instance_type: v})} style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TextInput placeholder="Target capacity" value={String(form.target_capacity)} onChangeText={v => setForm({...form, target_capacity: parseInt(v) || 0})} keyboardType="numeric" style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TouchableOpacity onPress={createFleet} style={{ backgroundColor: '#7c3aed', padding: 8, borderRadius: 4 }}>
            <Text style={{ color: '#fff', textAlign: 'center' }}>Create</Text>
          </TouchableOpacity>
        </View>
      )}
      {fleets.map((f: any) => (
        <TouchableOpacity key={f.id} onPress={() => toggleExpand(f.id)} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={{ color: '#fff', fontWeight: '600' }}>{f.name}</Text>
            <Text style={{ color: f.status === 'active' ? '#4ade80' : '#facc15', fontSize: 12 }}>{f.status}</Text>
          </View>
          <Text style={{ color: '#94a3b8', fontSize: 12 }}>{f.instance_type} · {f.target_capacity} instances</Text>
          {expanded === f.id && instances.map((inst: any) => (
            <View key={inst.id} style={{ backgroundColor: '#334155', padding: 8, borderRadius: 4, marginTop: 4 }}>
              <Text style={{ color: '#fff', fontSize: 12 }}>{inst.instance_id} · {inst.status}</Text>
            </View>
          ))}
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}
