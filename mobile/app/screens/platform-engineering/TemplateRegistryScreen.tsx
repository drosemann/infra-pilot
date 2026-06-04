import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Blueprint {
  id: string; name: string; type: string; version: string; owner: string; status: string; usage: number; rating: number;
}

const blueprints: Blueprint[] = [
  { id: 'bp1', name: 'ECS Fargate Service', type: 'terraform', version: '2.1.0', owner: 'platform', status: 'published', usage: 42, rating: 4.5 },
  { id: 'bp2', name: 'GCP Cloud Run Service', type: 'pulumi', version: '1.3.0', owner: 'platform', status: 'published', usage: 28, rating: 4.2 },
  { id: 'bp3', name: 'Lambda Event Processor', type: 'cloudformation', version: '3.0.1', owner: 'data', status: 'published', usage: 35, rating: 4.8 },
  { id: 'bp4', name: 'Kubernetes Helm Chart', type: 'helm', version: '1.0.0', owner: 'platform', status: 'draft', usage: 0, rating: 0 },
  { id: 'bp5', name: 'VPC with Subnets', type: 'terraform', version: '2.0.0', owner: 'networking', status: 'published', usage: 55, rating: 4.6 },
  { id: 'bp6', name: 'RDS PostgreSQL', type: 'arm', version: '1.1.0', owner: 'data', status: 'deprecated', usage: 12, rating: 3.9 },
];

const statusColors: Record<string, string> = { published: '#10b981', draft: '#6b7280', deprecated: '#ef4444', archived: '#f59e0b' };

export default function TemplateRegistryScreen({ navigation }: any) {
  const [search, setSearch] = useState('');
  const [createVisible, setCreateVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<Blueprint | null>(null);
  const [name, setName] = useState(''); const [type, setType] = useState('terraform');
  const [owner, setOwner] = useState('');

  const filtered = blueprints.filter(b => search ? b.name.toLowerCase().includes(search.toLowerCase()) || b.type.includes(search) : true);

  const handleCreate = () => {
    if (!name || !owner) { Alert.alert('Error', 'Name and owner required'); return; }
    setCreateVisible(false); setName(''); setOwner('');
  };

  const renderBlueprint = ({ item }: { item: Blueprint }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.name}</Text><Text style={styles.cardSubtitle}>{item.type} v{item.version} - {item.owner}</Text></View>
        <View style={[styles.statusBadge, { backgroundColor: (statusColors[item.status] || '#6b7280') + '20' }]}>
          <Text style={[styles.statusText, { color: statusColors[item.status] || '#6b7280' }]}>{item.status}</Text>
        </View>
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.usageText}>{item.usage} uses</Text>
        {item.rating > 0 && <Text style={styles.ratingText}>{'★'.repeat(Math.round(item.rating))} {item.rating}</Text>}
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Template Registry</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setCreateVisible(true)}><Text style={styles.addButtonText}>+ New</Text></TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{blueprints.length}</Text><Text style={styles.statLabel}>Blueprints</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{blueprints.filter(b => b.status === 'published').length}</Text><Text style={styles.statLabel}>Published</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{blueprints.reduce((a, b) => a + b.usage, 0)}</Text><Text style={styles.statLabel}>Total Usage</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{blueprints.filter(b => b.rating > 0).reduce((a, b) => a + b.rating, 0).toFixed(1)}</Text><Text style={styles.statLabel}>Avg Rating</Text></View>
      </View>

      <TextInput style={styles.searchInput} placeholder="Search blueprints..." value={search} onChangeText={setSearch} />

      <FlatList data={filtered} renderItem={renderBlueprint} keyExtractor={b => b.id} contentContainerStyle={styles.list} />

      <Modal visible={createVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>New Blueprint</Text>
            <TextInput style={styles.input} placeholder="Name" value={name} onChangeText={setName} />
            <Text style={styles.label}>Type</Text>
            <View style={styles.pickerRow}>
              {['terraform', 'pulumi', 'cloudformation', 'helm'].map(t => (
                <TouchableOpacity key={t} style={[styles.pickerBtn, type === t && styles.pickerBtnActive]} onPress={() => setType(t)}>
                  <Text style={[styles.pickerBtnText, type === t && styles.pickerBtnTextActive]}>{t}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TextInput style={styles.input} placeholder="Owner" value={owner} onChangeText={setOwner} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setCreateVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleCreate}><Text style={styles.submitBtnText}>Create</Text></TouchableOpacity>
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
                {[{ l: 'Type', v: selected.type }, { l: 'Version', v: selected.version }, { l: 'Owner', v: selected.owner }, { l: 'Status', v: selected.status }, { l: 'Usage', v: `${selected.usage} deployments` }, { l: 'Rating', v: selected.rating > 0 ? `${selected.rating}/5` : 'Not rated' }].map(d => (
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
  title: { fontSize: 22, fontWeight: '700', color: '#0f172a' },
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
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  statusText: { fontSize: 11, fontWeight: '600' },
  cardFooter: { flexDirection: 'row', gap: 12, marginTop: 8 },
  usageText: { fontSize: 12, color: '#94a3b8' },
  ratingText: { fontSize: 12, color: '#f59e0b' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 24 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 16 },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 14 },
  label: { fontSize: 13, color: '#64748b', marginBottom: 6 },
  pickerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 12 },
  pickerBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0' },
  pickerBtnActive: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
  pickerBtnText: { fontSize: 12, color: '#64748b' },
  pickerBtnTextActive: { color: '#fff' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  cancelBtn: { flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  cancelBtnText: { fontSize: 14, color: '#64748b' },
  submitBtn: { flex: 1, padding: 12, borderRadius: 8, backgroundColor: '#3b82f6', alignItems: 'center' },
  submitBtnText: { color: '#fff', fontWeight: '600' },
  detailItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  detailLabel: { color: '#64748b', fontWeight: '500' },
});
