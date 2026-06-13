import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Service {
  id: string; name: string; owner: string; lang: string; tier: string; score: number; status: string;
}

const mockServices: Service[] = [
  { id: 's1', name: 'user-service', owner: 'platform', lang: 'python', tier: 't1', score: 92, status: 'active' },
  { id: 's2', name: 'payment-api', owner: 'finops', lang: 'go', tier: 't1', score: 88, status: 'active' },
  { id: 's3', name: 'notification-svc', owner: 'platform', lang: 'typescript', tier: 't2', score: 65, status: 'active' },
  { id: 's4', name: 'data-pipeline', owner: 'data', lang: 'python', tier: 't2', score: 72, status: 'active' },
  { id: 's5', name: 'inventory-svc', owner: 'platform', lang: 'java', tier: 't3', score: 45, status: 'in_development' },
  { id: 's6', name: 'analytics-api', owner: 'data', lang: 'python', tier: 't2', score: 81, status: 'active' },
  { id: 's7', name: 'frontend-web', owner: 'web', lang: 'typescript', tier: 't3', score: 90, status: 'active' },
  { id: 's8', name: 'legacy-migrate', owner: 'platform', lang: 'php', tier: 't4', score: 25, status: 'deprecated' },
];

const tierColors: Record<string, string> = { t1: '#ef4444', t2: '#f97316', t3: '#3b82f6', t4: '#6b7280', t5: '#10b981' };

export default function ServiceCatalogScreen() {
  const [services, setServices] = useState<Service[]>(mockServices);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<Service | null>(null);
  const [name, setName] = useState(''); const [owner, setOwner] = useState('');
  const [lang, setLang] = useState('python'); const [tier, setTier] = useState('t3');

  const filtered = services.filter(s => {
    if (search && !s.name.includes(search) && !s.owner.includes(search)) return false;
    if (tierFilter && s.tier !== tierFilter) return false;
    return true;
  });

  const handleRegister = () => {
    if (!name || !owner) { Alert.alert('Error', 'Name and owner required'); return; }
    const svc: Service = { id: `s${Date.now()}`, name, owner, lang, tier, score: 0, status: 'in_development' };
    setServices([svc, ...services]);
    setName(''); setModalVisible(false);
  };

  const renderService = ({ item }: { item: Service }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>{item.name}</Text>
          <Text style={styles.cardSubtitle}>{item.owner} - {item.lang}</Text>
        </View>
        <Text style={[styles.tierBadge, { color: tierColors[item.tier] || '#6b7280' }]}>{item.tier.toUpperCase()}</Text>
        <Text style={[styles.score, { color: item.score >= 80 ? '#10b981' : item.score >= 50 ? '#f59e0b' : '#ef4444' }]}>{item.score}%</Text>
      </View>
      <Text style={styles.statusText}>{item.status}</Text>
    </TouchableOpacity>
  );

  const tiers = ['t1', 't2', 't3', 't4', 't5'];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Service Catalog</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Register</Text></TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{services.length}</Text><Text style={styles.statLabel}>Total</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{Math.round(services.reduce((a, s) => a + s.score, 0) / services.length)}%</Text><Text style={styles.statLabel}>Avg Score</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{services.filter(s => s.tier === 't1').length}</Text><Text style={styles.statLabel}>Tier 1</Text></View>
        <View style={styles.stat}><Text style={[styles.statValue, { color: '#ef4444' }]}>{services.filter(s => s.score < 50).length}</Text><Text style={styles.statLabel}>Below 50</Text></View>
      </View>

      <View style={styles.filterRow}>
        <TextInput style={[styles.searchInput, { flex: 1 }]} placeholder="Search..." value={search} onChangeText={setSearch} />
        <View style={styles.tierPicker}>
          {tiers.map(t => (
            <TouchableOpacity key={t} style={[styles.tierBtn, tierFilter === t && styles.tierBtnActive]} onPress={() => setTierFilter(tierFilter === t ? '' : t)}>
              <Text style={[styles.tierBtnText, tierFilter === t && styles.tierBtnTextActive]}>{t.toUpperCase()}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <FlatList data={filtered} renderItem={renderService} keyExtractor={s => s.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Register Service</Text>
            <TextInput style={styles.input} placeholder="Name" value={name} onChangeText={setName} />
            <TextInput style={styles.input} placeholder="Owner" value={owner} onChangeText={setOwner} />
            <Text style={styles.label}>Language</Text>
            <View style={styles.pickerRow}>
              {['python', 'go', 'typescript', 'java'].map(l => (
                <TouchableOpacity key={l} style={[styles.pickerBtn, lang === l && styles.pickerBtnActive]} onPress={() => setLang(l)}>
                  <Text style={[styles.pickerBtnText, lang === l && styles.pickerBtnTextActive]}>{l}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.label}>Tier</Text>
            <View style={styles.pickerRow}>
              {tiers.map(t => (
                <TouchableOpacity key={t} style={[styles.pickerBtn, tier === t && styles.pickerBtnActive]} onPress={() => setTier(t)}>
                  <Text style={[styles.pickerBtnText, tier === t && styles.pickerBtnTextActive]}>{t.toUpperCase()}</Text>
                </TouchableOpacity>
              ))}
            </View>
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
              <View>
                {[{ l: 'Owner', v: selected.owner }, { l: 'Language', v: selected.lang }, { l: 'Tier', v: selected.tier.toUpperCase() }, { l: 'Score', v: `${selected.score}%` }, { l: 'Status', v: selected.status }].map(d => (
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
  addButton: { backgroundColor: '#3b82f6', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', marginTop: 8, marginHorizontal: 12, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 8, gap: 8 },
  searchInput: { backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', padding: 10, fontSize: 14 },
  tierPicker: { flexDirection: 'row', gap: 4 },
  tierBtn: { paddingHorizontal: 8, paddingVertical: 8, borderRadius: 6, borderWidth: 1, borderColor: '#e2e8f0', backgroundColor: '#fff' },
  tierBtnActive: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
  tierBtnText: { fontSize: 11, color: '#64748b' },
  tierBtnTextActive: { color: '#fff' },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardSubtitle: { fontSize: 12, color: '#64748b', marginTop: 2 },
  tierBadge: { fontSize: 11, fontWeight: '700' },
  score: { fontSize: 18, fontWeight: '700' },
  statusText: { fontSize: 11, color: '#94a3b8', marginTop: 4 },
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
