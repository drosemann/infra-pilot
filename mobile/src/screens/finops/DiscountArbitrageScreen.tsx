import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView } from 'react-native';
import { apiClient } from '../../api/client';

export default function DiscountArbitrageScreen() {
  const [comparisons, setComparisons] = useState<any[]>([]);
  const [savings, setSavings] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/arbitrage/comparisons').then(r => setComparisons(r.comparisons || [])).catch(() => {});
    apiClient.get('/api/v1/finops/arbitrage/savings').then(setSavings).catch(() => {});
  }, []);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>Discount Arbitrage</Text>
      {savings && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>${savings.total_current_monthly?.toLocaleString()}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Current Spend</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#4ade80', fontSize: 20, fontWeight: 'bold' }}>${savings.total_potential_monthly_savings?.toLocaleString()}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Potential Savings</Text>
          </View>
        </View>
      )}
      {comparisons.filter(c => c.best_option).map((c: any) => (
        <View key={c.workload_id} style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, marginBottom: 8 }}>
          <Text style={{ color: '#fff', fontWeight: '600' }}>{c.workload_name}</Text>
          <Text style={{ color: '#94a3b8', fontSize: 12, marginTop: 2 }}>Current: {c.current_provider} — ${c.current_monthly_cost}/mo</Text>
          <View style={{ backgroundColor: '#334155', padding: 8, borderRadius: 4, marginTop: 8 }}>
            <Text style={{ color: '#4ade80', fontWeight: '600' }}>{c.best_option.provider_name} ({c.best_option.discount_type})</Text>
            <Text style={{ color: '#fff', fontSize: 12 }}>${c.best_option.effective_monthly_cost}/mo</Text>
            <Text style={{ color: '#4ade80', fontSize: 12 }}>Save ${c.potential_monthly_savings}/mo</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}
