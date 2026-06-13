import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

export default function BudgetForecastScreen() {
  const [budgets, setBudgets] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', amount: '1000', period: 'monthly' });

  useEffect(() => {
    apiClient.get('/api/v1/finops/budget').then(r => setBudgets(r.budgets || [])).catch(() => {});
    apiClient.get('/api/v1/finops/budget/summary').then(setSummary).catch(() => {});
  }, []);

  const create = async () => {
    const res = await apiClient.post('/api/v1/finops/budget', { ...form, amount: parseFloat(form.amount) });
    if (res.id) { Alert.alert('Budget created'); setShowForm(false); setBudgets([...budgets, res]); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Budget Forecast</Text>
      {summary && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{summary.total_budgets}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Budgets</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#facc15', fontSize: 20, fontWeight: 'bold' }}>{summary.on_track}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>On Track</Text>
          </View>
        </View>
      )}
      <TouchableOpacity onPress={() => setShowForm(!showForm)} style={{ backgroundColor: '#2563eb', padding: 10, borderRadius: 8, marginBottom: 16 }}>
        <Text style={{ color: '#fff', textAlign: 'center' }}>{showForm ? 'Cancel' : '+ New Budget'}</Text>
      </TouchableOpacity>
      {showForm && (
        <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <TextInput placeholder="Name" value={form.name} onChangeText={v => setForm({...form, name: v})} style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TextInput placeholder="Amount" value={form.amount} onChangeText={v => setForm({...form, amount: v})} keyboardType="numeric" style={{ backgroundColor: '#334155', color: '#fff', padding: 8, borderRadius: 4, marginBottom: 8 }} />
          <TouchableOpacity onPress={create} style={{ backgroundColor: '#2563eb', padding: 8, borderRadius: 4 }}>
            <Text style={{ color: '#fff', textAlign: 'center' }}>Create</Text>
          </TouchableOpacity>
        </View>
      )}
      {budgets.map((b: any) => {
        const pct = b.amount > 0 ? ((b.spent || 0) / b.amount) * 100 : 0;
        return (
          <View key={b.id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={{ color: '#fff', fontWeight: '600' }}>{b.name}</Text>
              <Text style={{ color: pct > 90 ? '#f87171' : pct > 75 ? '#facc15' : '#4ade80', fontSize: 12 }}>{pct.toFixed(0)}%</Text>
            </View>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>${b.spent || 0} / ${b.amount} ({b.period})</Text>
            <View style={{ height: 4, backgroundColor: '#334155', borderRadius: 2, marginTop: 4 }}>
              <View style={{ width: `${Math.min(pct, 100)}%`, height: 4, backgroundColor: pct > 90 ? '#f87171' : pct > 75 ? '#facc15' : '#4ade80', borderRadius: 2 }} />
            </View>
          </View>
        );
      })}
    </ScrollView>
  );
}
