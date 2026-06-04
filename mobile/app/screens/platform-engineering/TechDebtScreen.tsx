import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface DebtItem {
  id: string; title: string; service: string; category: string; severity: string; status: string; effort: number; assignee: string;
}

const mockItems: DebtItem[] = [
  { id: 'd1', title: 'Outdated: requests v2.25 -> v2.31', service: 'user-service', category: 'outdated_dependencies', severity: 'high', status: 'open', effort: 2, assignee: 'alice' },
  { id: 'd2', title: 'Deprecated API: /v1/users', service: 'payment-api', category: 'deprecated_apis', severity: 'critical', status: 'in_progress', effort: 8, assignee: 'bob' },
  { id: 'd3', title: 'Low test coverage (23%)', service: 'notification-svc', category: 'test_coverage', severity: 'medium', status: 'open', effort: 16, assignee: '' },
  { id: 'd4', title: 'Hardcoded config values', service: 'data-pipeline', category: 'code_smells', severity: 'medium', status: 'resolved', effort: 4, assignee: 'alice' },
  { id: 'd5', title: 'CVE-2024-1234 in lodash', service: 'frontend-web', category: 'security_vulnerabilities', severity: 'critical', status: 'open', effort: 6, assignee: 'charlie' },
];

const severityColors: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#3b82f6', info: '#6b7280' };

export default function TechDebtScreen() {
  const [items, setItems] = useState<DebtItem[]>(mockItems);
  const [filter, setFilter] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<DebtItem | null>(null);
  const [title, setTitle] = useState(''); const [severity, setSeverity] = useState('medium');
  const [service, setService] = useState(''); const [category, setCategory] = useState('code_smells');

  const filtered = items.filter(i => filter ? i.status === filter || i.severity === filter : true);

  const handleReport = () => {
    if (!title || !service) { Alert.alert('Error', 'Title and service required'); return; }
    const item: DebtItem = { id: `d${Date.now()}`, title, service, category, severity, status: 'open', effort: 0, assignee: '' };
    setItems([item, ...items]); setTitle(''); setService(''); setModalVisible(false);
  };

  const handleResolve = (id: string) => {
    setItems(items.map(i => i.id === id ? { ...i, status: 'resolved' } : i));
  };

  const renderItem = ({ item }: { item: DebtItem }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.cardSubtitle}>{item.service} - {item.category.replace(/_/g, ' ')}</Text></View>
        <View style={[styles.severityBadge, { backgroundColor: (severityColors[item.severity] || '#6b7280') + '20' }]}>
          <Text style={[styles.severityText, { color: severityColors[item.severity] }]}>{item.severity}</Text>
        </View>
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.statusText}>{item.status}</Text>
        <Text style={styles.effortText}>{item.effort}h</Text>
        {item.assignee ? <Text style={styles.assigneeText}>{item.assignee}</Text> : null}
        {item.status === 'open' && (
          <TouchableOpacity style={styles.resolveBtn} onPress={() => handleResolve(item.id)}><Text style={styles.resolveBtnText}>Fix</Text></TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Technical Debt</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Report</Text></TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{items.filter(i => i.status === 'open').length}</Text><Text style={styles.statLabel}>Open</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{items.filter(i => i.status === 'in_progress').length}</Text><Text style={styles.statLabel}>In Progress</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{items.filter(i => i.status === 'resolved').length}</Text><Text style={styles.statLabel}>Resolved</Text></View>
        <View style={styles.stat}><Text style={[styles.statValue, { color: '#ef4444' }]}>{items.filter(i => i.severity === 'critical').length}</Text><Text style={styles.statLabel}>Critical</Text></View>
      </View>

      <View style={styles.filterRow}>
        {['', 'open', 'in_progress', 'resolved'].map(f => (
          <TouchableOpacity key={f} style={[styles.filterBtn, filter === f && styles.filterBtnActive]} onPress={() => setFilter(f)}>
            <Text style={[styles.filterBtnText, filter === f && styles.filterBtnTextActive]}>{f || 'All'}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList data={filtered} renderItem={renderItem} keyExtractor={i => i.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Report Tech Debt</Text>
            <TextInput style={styles.input} placeholder="Title" value={title} onChangeText={setTitle} />
            <TextInput style={styles.input} placeholder="Service ID" value={service} onChangeText={setService} />
            <Text style={styles.label}>Severity</Text>
            <View style={styles.pickerRow}>{['critical', 'high', 'medium', 'low'].map(s => (
              <TouchableOpacity key={s} style={[styles.pickerBtn, severity === s && styles.pickerBtnActive]} onPress={() => setSeverity(s)}>
                <Text style={[styles.pickerBtnText, severity === s && styles.pickerBtnTextActive]}>{s}</Text>
              </TouchableOpacity>
            ))}</View>
            <Text style={styles.label}>Category</Text>
            <View style={styles.pickerRow}>{['code_smells', 'security_vulnerabilities', 'outdated_dependencies', 'test_coverage'].map(c => (
              <TouchableOpacity key={c} style={[styles.pickerBtn, category === c && styles.pickerBtnActive]} onPress={() => setCategory(c)}>
                <Text style={[styles.pickerBtnText, category === c && styles.pickerBtnTextActive]}>{c.replace(/_/g, ' ')}</Text>
              </TouchableOpacity>
            ))}</View>
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleReport}><Text style={styles.submitBtnText}>Report</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={detailVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{selected?.title}</Text>
            {selected && (
              <View>
                {[{ l: 'Service', v: selected.service }, { l: 'Category', v: selected.category.replace(/_/g, ' ') }, { l: 'Severity', v: selected.severity }, { l: 'Status', v: selected.status }, { l: 'Effort', v: `${selected.effort}h` }, { l: 'Assignee', v: selected.assignee || 'Unassigned' }].map(d => (
                  <View key={d.l} style={styles.detailItem}><Text style={styles.detailLabel}>{d.l}</Text><Text>{d.v}</Text></View>
                ))}
              </View>
            )}
            <TouchableOpacity style={styles.submitBtn} onPress={() => setDetailVisible(false)}><Text style={styles.submitBtnText}>Close</Text></TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e2e8f0' },
  title: { fontSize: 24, fontWeight: '700', color: '#0f172a' },
  addButton: { backgroundColor: '#ef4444', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', margin: 12, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, gap: 6, marginBottom: 4 },
  filterBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 1, borderColor: '#e2e8f0' },
  filterBtnActive: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
  filterBtnText: { fontSize: 12, color: '#64748b' },
  filterBtnTextActive: { color: '#fff' },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', alignItems: 'center' },
  cardTitle: { fontSize: 14, fontWeight: '600', flex: 1 },
  cardSubtitle: { fontSize: 11, color: '#64748b', marginTop: 2 },
  severityBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  severityText: { fontSize: 11, fontWeight: '600' },
  cardFooter: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 8 },
  statusText: { fontSize: 12, color: '#64748b' },
  effortText: { fontSize: 12, color: '#94a3b8' },
  assigneeText: { fontSize: 12, color: '#3b82f6' },
  resolveBtn: { backgroundColor: '#10b981', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 6 },
  resolveBtnText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 24 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 16 },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 14 },
  label: { fontSize: 13, color: '#64748b', marginBottom: 6 },
  pickerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 12 },
  pickerBtn: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0' },
  pickerBtnActive: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
  pickerBtnText: { fontSize: 11, color: '#64748b' },
  pickerBtnTextActive: { color: '#fff' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  cancelBtn: { flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  cancelBtnText: { fontSize: 14, color: '#64748b' },
  submitBtn: { flex: 1, padding: 12, borderRadius: 8, backgroundColor: '#3b82f6', alignItems: 'center' },
  submitBtnText: { color: '#fff', fontWeight: '600' },
  detailItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  detailLabel: { color: '#64748b', fontWeight: '500' },
});
