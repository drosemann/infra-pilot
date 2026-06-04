import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface DocItem {
  id: string; title: string; type: string; format: string; service: string; version: number; words: number; hasDiagram: boolean;
}

interface AdrItem {
  id: string; title: string; status: string; domain: string; authors: string[];
}

const mockDocs: DocItem[] = [
  { id: 'd1', title: 'User Service Architecture', type: 'architecture', format: 'markdown', service: 'user-service', version: 3, words: 2500, hasDiagram: true },
  { id: 'd2', title: 'System Context - Payment API', type: 'system_context', format: 'markdown', service: 'payment-api', version: 1, words: 800, hasDiagram: true },
  { id: 'd3', title: 'Runbook - Data Pipeline', type: 'runbook', format: 'markdown', service: 'data-pipeline', version: 2, words: 1800, hasDiagram: false },
  { id: 'd4', title: 'API Reference - Notifications', type: 'api_reference', format: 'html', service: 'notification-svc', version: 1, words: 3200, hasDiagram: false },
];

const mockAdrs: AdrItem[] = [
  { id: 'adr1', title: 'Use PostgreSQL for persistence', status: 'approved', domain: 'data', authors: ['alice'] },
  { id: 'adr2', title: 'Migrate to gRPC for inter-service', status: 'proposed', domain: 'architecture', authors: ['bob'] },
  { id: 'adr3', title: 'Adopt event-driven for notifications', status: 'approved', domain: 'architecture', authors: ['charlie'] },
  { id: 'adr4', title: 'Use Redis for caching layer', status: 'superseded', domain: 'infrastructure', authors: ['alice'] },
];

const statusColors: Record<string, string> = { approved: '#10b981', proposed: '#f59e0b', superseded: '#6b7280', rejected: '#ef4444' };

export default function DocGenScreen() {
  const [activeTab, setActiveTab] = useState<'docs' | 'adrs'>('docs');
  const [modalVisible, setModalVisible] = useState(false);
  const [detailDoc, setDetailDoc] = useState<DocItem | null>(null);
  const [detailAdr, setDetailAdr] = useState<AdrItem | null>(null);
  const [docDetailVisible, setDocDetailVisible] = useState(false);
  const [adrDetailVisible, setAdrDetailVisible] = useState(false);
  const [title, setTitle] = useState(''); const [docType, setDocType] = useState('architecture');
  const [service, setService] = useState('');

  const handleGenerate = () => {
    if (!title || !service) { Alert.alert('Error', 'Title and service required'); return; }
    setModalVisible(false); setTitle(''); setService('');
  };

  const renderDoc = ({ item }: { item: DocItem }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setDetailDoc(item); setDocDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.cardSubtitle}>{item.type} - {item.service} v{item.version}</Text></View>
        {item.hasDiagram && <Text style={styles.diagramBadge}>📊</Text>}
      </View>
      <Text style={styles.footerText}>{item.format} - {item.words} words</Text>
    </TouchableOpacity>
  );

  const renderAdr = ({ item }: { item: AdrItem }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setDetailAdr(item); setAdrDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.cardSubtitle}>{item.domain} - {item.authors.join(', ')}</Text></View>
        <View style={[styles.statusBadge, { backgroundColor: (statusColors[item.status] || '#6b7280') + '20' }]}>
          <Text style={[styles.statusText, { color: statusColors[item.status] || '#6b7280' }]}>{item.status}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Doc Generator</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Generate</Text></TouchableOpacity>
      </View>

      <View style={styles.tabRow}>
        <TouchableOpacity style={[styles.tab, activeTab === 'docs' && styles.tabActive]} onPress={() => setActiveTab('docs')}>
          <Text style={[styles.tabText, activeTab === 'docs' && styles.tabTextActive]}>Documents ({mockDocs.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.tab, activeTab === 'adrs' && styles.tabActive]} onPress={() => setActiveTab('adrs')}>
          <Text style={[styles.tabText, activeTab === 'adrs' && styles.tabTextActive]}>ADRs ({mockAdrs.length})</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{mockDocs.length}</Text><Text style={styles.statLabel}>Documents</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{mockAdrs.length}</Text><Text style={styles.statLabel}>ADRs</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{mockAdrs.filter(a => a.status === 'approved').length}</Text><Text style={styles.statLabel}>Approved</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{mockDocs.filter(d => d.hasDiagram).length}</Text><Text style={styles.statLabel}>With Diagrams</Text></View>
      </View>

      <FlatList data={activeTab === 'docs' ? mockDocs : mockAdrs} renderItem={activeTab === 'docs' ? renderDoc : renderAdr} keyExtractor={i => i.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Generate Document</Text>
            <TextInput style={styles.input} placeholder="Title" value={title} onChangeText={setTitle} />
            <Text style={styles.label}>Type</Text>
            <View style={styles.pickerRow}>{['architecture', 'adr', 'runbook', 'api_reference', 'system_context'].map(t => (
              <TouchableOpacity key={t} style={[styles.pickerBtn, docType === t && styles.pickerBtnActive]} onPress={() => setDocType(t)}>
                <Text style={[styles.pickerBtnText, docType === t && styles.pickerBtnTextActive]}>{t.replace(/_/g, ' ')}</Text>
              </TouchableOpacity>
            ))}</View>
            <TextInput style={styles.input} placeholder="Service ID" value={service} onChangeText={setService} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleGenerate}><Text style={styles.submitBtnText}>Generate</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={docDetailVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{detailDoc?.title}</Text>
            {detailDoc && (<View>{[{ l: 'Type', v: detailDoc.type }, { l: 'Format', v: detailDoc.format }, { l: 'Service', v: detailDoc.service }, { l: 'Version', v: String(detailDoc.version) }, { l: 'Words', v: String(detailDoc.words) }, { l: 'Has Diagram', v: detailDoc.hasDiagram ? 'Yes' : 'No' }].map(d => (<View key={d.l} style={styles.detailItem}><Text style={styles.detailLabel}>{d.l}</Text><Text>{d.v}</Text></View>))}</View>)}
            <TouchableOpacity style={styles.submitBtn} onPress={() => setDocDetailVisible(false)}><Text style={styles.submitBtnText}>Close</Text></TouchableOpacity>
          </View>
        </View>
      </Modal>

      <Modal visible={adrDetailVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{detailAdr?.title}</Text>
            {detailAdr && (<View>{[{ l: 'Status', v: detailAdr.status }, { l: 'Domain', v: detailAdr.domain }, { l: 'Authors', v: detailAdr.authors.join(', ') }].map(d => (<View key={d.l} style={styles.detailItem}><Text style={styles.detailLabel}>{d.l}</Text><Text>{d.v}</Text></View>))}</View>)}
            <TouchableOpacity style={styles.submitBtn} onPress={() => setAdrDetailVisible(false)}><Text style={styles.submitBtnText}>Close</Text></TouchableOpacity>
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
  addButton: { backgroundColor: '#3b82f6', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  tabRow: { flexDirection: 'row', backgroundColor: '#fff', paddingHorizontal: 12, paddingTop: 8 },
  tab: { paddingVertical: 10, paddingHorizontal: 20, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabActive: { borderBottomColor: '#3b82f6' },
  tabText: { fontSize: 14, color: '#64748b' },
  tabTextActive: { color: '#3b82f6', fontWeight: '600' },
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', margin: 12, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', alignItems: 'center' },
  cardTitle: { fontSize: 15, fontWeight: '600', flex: 1 },
  cardSubtitle: { fontSize: 11, color: '#64748b', marginTop: 2 },
  diagramBadge: { fontSize: 18 },
  footerText: { fontSize: 11, color: '#94a3b8', marginTop: 4 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  statusText: { fontSize: 11, fontWeight: '600' },
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
