import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Component {
  id: string;
  name: string;
  type: string;
  owner: string;
  health: number;
  maturity: string;
  deps: number;
  depBy: number;
}

const mockComponents: Component[] = [
  { id: 'c1', name: 'user-service', type: 'service', owner: 'platform-team', health: 92, maturity: 'level_4', deps: 3, depBy: 5 },
  { id: 'c2', name: 'payment-api', type: 'api', owner: 'finops-team', health: 88, maturity: 'level_3', deps: 2, depBy: 8 },
  { id: 'c3', name: 'auth-lib', type: 'library', owner: 'security-team', health: 95, maturity: 'level_5', deps: 0, depBy: 12 },
  { id: 'c4', name: 'notification-svc', type: 'service', owner: 'platform-team', health: 78, maturity: 'level_2', deps: 4, depBy: 3 },
  { id: 'c5', name: 'data-pipeline', type: 'service', owner: 'data-team', health: 85, maturity: 'level_3', deps: 5, depBy: 2 },
  { id: 'c6', name: 'frontend-web', type: 'service', owner: 'web-team', health: 90, maturity: 'level_3', deps: 6, depBy: 1 },
];

export default function DevPortalScreen({ navigation }: any) {
  const [components, setComponents] = useState<Component[]>(mockComponents);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const [search, setSearch] = useState('');
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('service');
  const [newOwner, setNewOwner] = useState('');

  const getHealthColor = (h: number) => h >= 90 ? '#10b981' : h >= 75 ? '#f59e0b' : '#ef4444';

  const filtered = components.filter(c =>
    c.name.includes(search) || c.owner.includes(search)
  );

  const handleRegister = () => {
    if (!newName || !newOwner) { Alert.alert('Error', 'Name and owner required'); return; }
    const comp: Component = {
      id: `c${Date.now()}`, name: newName, type: newType, owner: newOwner,
      health: 100, maturity: 'level_1', deps: 0, depBy: 0,
    };
    setComponents([comp, ...components]);
    setNewName(''); setNewOwner(''); setModalVisible(false);
  };

  const renderComponent = ({ item }: { item: Component }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelectedComponent(item); setDetailModalVisible(true); }}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.name}</Text>
        <Text style={[styles.healthText, { color: getHealthColor(item.health) }]}>{item.health}%</Text>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardSubtitle}>{item.type} - {item.owner}</Text>
        <View style={styles.badgeRow}>
          <View style={styles.badge}><Text style={styles.badgeText}>{item.maturity}</Text></View>
          <Text style={styles.depsText}>Deps: {item.deps} Used by: {item.depBy}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Software Catalog</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}>
          <Text style={styles.addButtonText}>+ Register</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{components.length}</Text><Text style={styles.statLabel}>Components</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>4</Text><Text style={styles.statLabel}>Systems</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>88%</Text><Text style={styles.statLabel}>Avg Health</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>2</Text><Text style={styles.statLabel}>Level 4+</Text></View>
      </View>

      <TextInput style={styles.searchInput} placeholder="Search by name or owner..." value={search} onChangeText={setSearch} />

      <FlatList data={filtered} renderItem={renderComponent} keyExtractor={item => item.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Register Component</Text>
            <TextInput style={styles.input} placeholder="Name" value={newName} onChangeText={setNewName} />
            <View style={styles.typeRow}>
              {['service', 'api', 'library'].map(t => (
                <TouchableOpacity key={t} style={[styles.typeBtn, newType === t && styles.typeBtnActive]} onPress={() => setNewType(t)}>
                  <Text style={[styles.typeBtnText, newType === t && styles.typeBtnTextActive]}>{t}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TextInput style={styles.input} placeholder="Owner" value={newOwner} onChangeText={setNewOwner} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleRegister}><Text style={styles.submitBtnText}>Register</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={detailModalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{selectedComponent?.name}</Text>
            {selectedComponent && (
              <View style={styles.detailRow}>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Type</Text><Text>{selectedComponent.type}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Owner</Text><Text>{selectedComponent.owner}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Health</Text><Text>{selectedComponent.health}%</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Maturity</Text><Text>{selectedComponent.maturity}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Dependencies</Text><Text>{selectedComponent.deps}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Depended By</Text><Text>{selectedComponent.depBy}</Text></View>
              </View>
            )}
            <TouchableOpacity style={styles.submitBtn} onPress={() => setDetailModalVisible(false)}><Text style={styles.submitBtnText}>Close</Text></TouchableOpacity>
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
  searchInput: { margin: 12, padding: 12, backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', fontSize: 14 },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: '600', color: '#0f172a' },
  healthText: { fontSize: 16, fontWeight: '700' },
  cardBody: { marginTop: 6 },
  cardSubtitle: { fontSize: 13, color: '#64748b' },
  badgeRow: { flexDirection: 'row', alignItems: 'center', marginTop: 6, gap: 8 },
  badge: { backgroundColor: '#e0f2fe', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  badgeText: { fontSize: 11, color: '#0369a1' },
  depsText: { fontSize: 11, color: '#94a3b8' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 24 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 16, color: '#0f172a' },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 14 },
  typeRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  typeBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  typeBtnActive: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
  typeBtnText: { fontSize: 13, color: '#64748b' },
  typeBtnTextActive: { color: '#fff' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  cancelBtn: { flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  cancelBtnText: { color: '#64748b', fontWeight: '600' },
  submitBtn: { flex: 1, padding: 12, borderRadius: 8, backgroundColor: '#3b82f6', alignItems: 'center' },
  submitBtnText: { color: '#fff', fontWeight: '600' },
  detailRow: { marginBottom: 16 },
  detailItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  detailLabel: { color: '#64748b', fontWeight: '500' },
});
