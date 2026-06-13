import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Environment {
  id: string; name: string; type: string; project: string; status: string; branch: string; pr: number; createdBy: string; expiresIn: string;
}

const mockEnvs: Environment[] = [
  { id: 'e1', name: 'pr-142-feat-auth', type: 'pr', project: 'user-service', status: 'running', branch: 'feat/auth', pr: 142, createdBy: 'alice', expiresIn: '22h' },
  { id: 'e2', name: 'staging-data-pipeline', type: 'branch', project: 'data-pipeline', status: 'running', branch: 'main', pr: 0, createdBy: 'bob', expiresIn: '48h' },
  { id: 'e3', name: 'pr-145-fix-cache', type: 'pr', project: 'frontend-web', status: 'provisioning', branch: 'fix/cache', pr: 145, createdBy: 'charlie', expiresIn: 'N/A' },
  { id: 'e4', name: 'feat-ml-training', type: 'feature', project: 'data-pipeline', status: 'running', branch: 'feat/ml-training', pr: 0, createdBy: 'alice', expiresIn: '12h' },
  { id: 'e5', name: 'pr-148-upgrade-deps', type: 'pr', project: 'payment-api', status: 'terminated', branch: 'upgrade/deps', pr: 148, createdBy: 'bob', expiresIn: 'Expired' },
];

const statusColors: Record<string, string> = { running: '#10b981', provisioning: '#3b82f6', terminated: '#6b7280', degraded: '#f59e0b', failed: '#ef4444' };

export default function EnvironmentsScreen() {
  const [envs, setEnvs] = useState<Environment[]>(mockEnvs);
  const [filter, setFilter] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [name, setName] = useState(''); const [project, setProject] = useState('user-service');
  const [envType, setEnvType] = useState('pr'); const [branch, setBranch] = useState(''); const [ttl, setTtl] = useState('24');

  const filtered = envs.filter(e => filter ? e.status === filter : true);

  const handleProvision = () => {
    if (!name) { Alert.alert('Error', 'Name required'); return; }
    const env: Environment = { id: `e${Date.now()}`, name, type: envType, project, status: 'provisioning', branch: branch || 'main', pr: 0, createdBy: 'current-user', expiresIn: `${ttl}h` };
    setEnvs([env, ...envs]); setName(''); setModalVisible(false);
  };

  const handleTerminate = (id: string) => {
    setEnvs(envs.map(e => e.id === id ? { ...e, status: 'terminated', expiresIn: 'Expired' } : e));
  };

  const renderEnv = ({ item }: { item: Environment }) => (
    <TouchableOpacity style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.name}</Text><Text style={styles.cardSubtitle}>{item.project} - Branch: {item.branch}</Text></View>
        <View style={[styles.statusBadge, { backgroundColor: (statusColors[item.status] || '#6b7280') + '20' }]}>
          <Text style={[styles.statusText, { color: statusColors[item.status] || '#6b7280' }]}>{item.status}</Text>
        </View>
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.footerText}>{item.type === 'pr' ? `PR #${item.pr}` : item.type}</Text>
        <Text style={styles.footerText}>By: {item.createdBy}</Text>
        <Text style={styles.footerText}>{item.expiresIn}</Text>
        {item.status === 'running' && (
          <TouchableOpacity style={styles.termBtn} onPress={() => handleTerminate(item.id)}><Text style={styles.termBtnText}>Terminate</Text></TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Environments</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Provision</Text></TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{envs.filter(e => e.status === 'running').length}</Text><Text style={styles.statLabel}>Running</Text></View>
        <View style={styles.stat}><Text style={[styles.statValue, { color: '#3b82f6' }]}>{envs.filter(e => e.status === 'provisioning').length}</Text><Text style={styles.statLabel}>Provisioning</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{envs.filter(e => e.type === 'pr').length}</Text><Text style={styles.statLabel}>PR Envs</Text></View>
        <View style={styles.stat}><Text style={[styles.statValue, { color: '#f59e0b' }]}>2</Text><Text style={styles.statLabel}>Expiring</Text></View>
      </View>

      <View style={styles.filterRow}>
        {['', 'running', 'provisioning', 'terminated'].map(f => (
          <TouchableOpacity key={f} style={[styles.filterBtn, filter === f && styles.filterBtnActive]} onPress={() => setFilter(f)}>
            <Text style={[styles.filterBtnText, filter === f && styles.filterBtnTextActive]}>{f || 'All'}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList data={filtered} renderItem={renderEnv} keyExtractor={e => e.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Provision Environment</Text>
            <TextInput style={styles.input} placeholder="Name" value={name} onChangeText={setName} />
            <Text style={styles.label}>Type</Text>
            <View style={styles.pickerRow}>{['pr', 'branch', 'feature', 'ephemeral'].map(t => (
              <TouchableOpacity key={t} style={[styles.pickerBtn, envType === t && styles.pickerBtnActive]} onPress={() => setEnvType(t)}>
                <Text style={[styles.pickerBtnText, envType === t && styles.pickerBtnTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}</View>
            <Text style={styles.label}>Project</Text>
            <View style={styles.pickerRow}>{['user-service', 'payment-api', 'data-pipeline', 'frontend-web'].map(p => (
              <TouchableOpacity key={p} style={[styles.pickerBtn, project === p && styles.pickerBtnActive]} onPress={() => setProject(p)}>
                <Text style={[styles.pickerBtnText, project === p && styles.pickerBtnTextActive]}>{p}</Text>
              </TouchableOpacity>
            ))}</View>
            <TextInput style={styles.input} placeholder="Branch" value={branch} onChangeText={setBranch} />
            <TextInput style={styles.input} placeholder="TTL hours" value={ttl} onChangeText={setTtl} keyboardType="numeric" />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleProvision}><Text style={styles.submitBtnText}>Provision</Text></TouchableOpacity>
            </View>
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
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, gap: 6, marginBottom: 4 },
  filterBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 1, borderColor: '#e2e8f0' },
  filterBtnActive: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
  filterBtnText: { fontSize: 12, color: '#64748b' },
  filterBtnTextActive: { color: '#fff' },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row' },
  cardTitle: { fontSize: 15, fontWeight: '600' },
  cardSubtitle: { fontSize: 11, color: '#64748b', marginTop: 2 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  statusText: { fontSize: 11, fontWeight: '600' },
  cardFooter: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 8, flexWrap: 'wrap' },
  footerText: { fontSize: 11, color: '#94a3b8' },
  termBtn: { backgroundColor: '#ef4444', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 6 },
  termBtnText: { color: '#fff', fontSize: 11, fontWeight: '600' },
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
});
