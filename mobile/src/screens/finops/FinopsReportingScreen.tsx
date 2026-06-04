import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { apiClient } from '../../api/client';

const reportTypes = ['executive_summary', 'cost_breakdown', 'savings_opportunity', 'budget_vs_actual', 'showback', 'chargeback', 'commitment_utilization', 'waste_analysis', 'forecast', 'compliance', 'kpi_dashboard'];

export default function FinopsReportingScreen() {
  const [reports, setReports] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    apiClient.get('/api/v1/finops/reports/summary').then(setSummary).catch(() => {});
    apiClient.get('/api/v1/finops/reports').then(r => setReports(r.reports || [])).catch(() => {});
  }, []);

  const generate = async (type: string) => {
    setGenerating(true);
    const res = await apiClient.post('/api/v1/finops/reports/generate', { report_type: type, period: 'monthly' });
    if (res.id) { setReports([res, ...reports]); setSelectedReport(res); Alert.alert('Report generated!'); }
    setGenerating(false);
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0f172a', padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 }}>FinOps Reports</Text>
      {summary && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>{summary.total_reports}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>Reports</Text>
          </View>
          <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8, flex: 1 }}>
            <Text style={{ color: '#4ade80', fontSize: 20, fontWeight: 'bold' }}>{summary.kpis_on_track}</Text>
            <Text style={{ color: '#94a3b8', fontSize: 12 }}>KPIs On Track</Text>
          </View>
        </View>
      )}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {reportTypes.map((type) => (
          <TouchableOpacity key={type} onPress={() => generate(type)} disabled={generating}
            style={{ backgroundColor: '#1e293b', padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#334155' }}>
            <Text style={{ color: '#fff', fontSize: 12 }}>{type.replace(/_/g, ' ')}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {selectedReport && selectedReport.data && (
        <View style={{ backgroundColor: '#1e293b', padding: 12, borderRadius: 8 }}>
          <Text style={{ color: '#fff', fontWeight: '600', marginBottom: 8 }}>{selectedReport.type.replace(/_/g, ' ').toUpperCase()} Report</Text>
          <Text style={{ color: '#94a3b8', fontSize: 10 }}>{JSON.stringify(selectedReport.data, null, 2)}</Text>
        </View>
      )}
    </ScrollView>
  );
}
