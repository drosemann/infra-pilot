import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface ApiEntry {
  id: string; name: string; type: string; version: string; owner: string; lifecycle: string; endpoints: number; consumers: number;
}

const mockApis: ApiEntry[] = [
  { id: 'a1', name: 'User API', type: 'rest', version: '2.1.0', owner: 'platform', lifecycle: 'stable', endpoints: 12, consumers: 8 },
  { id: 'a2', name: 'Payment Gateway', type: 'rest', version: '3.0.0', owner: 'finops', lifecycle: 'stable', endpoints: 8, consumers: 5 },
  { id: 'a3', name: 'Notification Service', type: 'grpc', version: '1.5.0', owner: 'platform', lifecycle: 'beta', endpoints: 6, consumers: 3 },
  { id: 'a4', name: 'Data Analytics', type: 'graphql', version: '1.0.0', owner: 'data', lifecycle: 'development', endpoints: 4, consumers: 0 },
  { id: 'a5', name: 'Legacy SOAP API', type: 'soap', version: '1.0.0', owner: 'platform', lifecycle: 'deprecated', endpoints: 3, consumers: 1 },
  { id: 'a6', name: 'Event Stream', type: 'asyncapi', version: '0.9.0', owner: 'data', lifecycle: 'beta', endpoints: 2, consumers: 4 },
];

const lifecycleColors: Record<string, string> = { stable: '#10b981', beta: '#3b82f6', development: '#f59e0b', deprecated: '#ef4444', sunset: '#6b7280', design: '#8b5cf6' };

export default function ApiCatalogScreen() {
  const [apis, setApis] = useState<ApiEntry[]>(mockApis);
  const [search, setSearch] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<ApiEntry | null>(null);
  const [name, setName] = useState(''); const [apiType, setApiType] = useState('rest');
  const [version, setVersion] = useState('1.0.0'); const [owner, setOwner] = useState('');

  const filtered = apis.filter(a => search ? a.name.toLowerCase().includes(search.toLowerCase()) || a.owner.includes(search) : true);

  const handleRegister = () => {
    if (!name || !owner) { Alert.alert('Error', 'Name and owner required'); return; }
    const api: ApiEntry = { id: `a${Date.now()}`, name, type: apiType, version, owner, lifecycle: 'development', endpoints: 0, consumers: 0 };
    setApis([api, ...apis]); setName(''); setOwner(''); setModalVisible(false);
  };

  const renderApi = ({ item }: { item: ApiEntry }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.name}</Text><Text style={styles.cardSubtitle}>{item.type} v{item.version} - {item.owner}</Text></View>
        <View style={[styles.lifecycleBadge, { backgroundColor: (lifecycleColors[item.lifecycle] || '#6b7280') + '20' }]}>
          <Text style={[styles.lifecycleText, { color: lifecycleColors[item.lifecycle] || '#6b7280' }]}>{item.lifecycle}</Text>
        </View>
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.footerText}>{item.endpoints} endpoints</Text>
        <Text style={styles.footerText}>{item.consumers} consumers</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>API Catalog</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Register</Text></TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{apis.length}</Text><Text style={styles.statLabel}>Total APIs</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{apis.filter(a => a.lifecycle === 'stable').length}</Text><Text style={styles.statLabel}>Stable</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{apis.reduce((a, api) => a + api.endpoints, 0)}</Text><Text style={styles.statLabel}>Endpoints</Text></View>
        <View style={styles.stat}><Text style={[styles.statValue, { color: '#ef4444' }]}>{apis.filter(a => a.lifecycle === 'deprecated').length}</Text><Text style={styles.statLabel}>Deprecated</Text></View>
      </View>

      <TextInput style={styles.searchInput} placeholder="Search APIs..." value={search} onChangeText={setSearch} />

      <FlatList data={filtered} renderItem={renderApi} keyExtractor={a => a.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Register API</Text>
            <TextInput style={styles.input} placeholder="Name" value={name} onChangeText={setName} />
            <Text style={styles.label}>Type</Text>
            <View style={styles.pickerRow}>{['rest', 'grpc', 'graphql', 'websocket', 'soap', 'asyncapi'].map(t => (
              <TouchableOpacity key={t} style={[styles.pickerBtn, apiType === t && styles.pickerBtnActive]} onPress={() => setApiType(t)}>
                <Text style={[styles.pickerBtnText, apiType === t && styles.pickerBtnTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}</View>
            <TextInput style={styles.input} placeholder="Version" value={version} onChangeText={setVersion} />
            <TextInput style={styles.input} placeholder="Owner" value={owner} onChangeText={setOwner} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleRegister}><Text style={styles.submitBtnText}>Register</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={detailVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{selected?.name}</Text>
            {selected && (
              <ScrollView>
                {[{ l: 'Type', v: selected.type }, { l: 'Version', v: selected.version }, { l: 'Owner', v: selected.owner }, { l: 'Lifecycle', v: selected.lifecycle }, { l: 'Endpoints', v: String(selected.endpoints) }, { l: 'Consumers', v: String(selected.consumers) }].map(d => (
                  <View key={d.l} style={styles.detailItem}><Text style={styles.detailLabel}>{d.l}</Text><Text>{d.v}</Text></View>
                ))}
              </ScrollView>
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
  addButton: { backgroundColor: '#3b82f6', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', margin: 12, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  searchInput: { margin: 12, padding: 12, backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', fontSize: 14 },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardSubtitle: { fontSize: 12, color: '#64748b', marginTop: 2 },
  lifecycleBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  lifecycleText: { fontSize: 11, fontWeight: '600' },
  cardFooter: { flexDirection: 'row', gap: 12, marginTop: 8 },
  footerText: { fontSize: 12, color: '#94a3b8' },
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
