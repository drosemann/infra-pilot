import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface ScaffoldInstance {
  id: string; template: string; service: string; owner: string;
  status: string; currentStep: string; completedSteps: string[];
  repoUrl: string; errors: string[];
}

const mockInstances: ScaffoldInstance[] = [
  { id: 's1', template: 'FastAPI Microservice', service: 'user-api-v2', owner: 'platform-team', status: 'completed', currentStep: 'completed', completedSteps: ['repo_creation', 'ci_cd_setup', 'cloud_resources', 'monitoring', 'on_call_config', 'documentation'], repoUrl: 'https://github.com/infrapilot/user-api-v2', errors: [] },
  { id: 's2', template: 'Express Service', service: 'payment-gw', owner: 'finops-team', status: 'in_progress', currentStep: 'cloud_resources', completedSteps: ['repo_creation', 'ci_cd_setup'], repoUrl: 'https://github.com/infrapilot/payment-gw', errors: [] },
  { id: 's3', template: 'Go Event Processor', service: 'event-ingestor', owner: 'data-team', status: 'failed', currentStep: 'ci_cd_setup', completedSteps: ['repo_creation'], repoUrl: '', errors: ['CI pipeline setup failed'] },
];

const templates = ['FastAPI Microservice', 'Express Service', 'Go Event Processor', 'Data Pipeline'];

export default function ScaffoldScreen() {
  const [instances, setInstances] = useState<ScaffoldInstance[]>(mockInstances);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<ScaffoldInstance | null>(null);
  const [template, setTemplate] = useState(templates[0]);
  const [serviceName, setServiceName] = useState('');
  const [owner, setOwner] = useState('');

  const statusColor = (s: string) => s === 'completed' ? '#10b981' : s === 'in_progress' ? '#f59e0b' : '#ef4444';

  const handleStart = () => {
    if (!serviceName || !owner) { Alert.alert('Error', 'Service name and owner required'); return; }
    const inst: ScaffoldInstance = {
      id: `s${Date.now()}`, template, service: serviceName, owner,
      status: 'in_progress', currentStep: 'repo_creation', completedSteps: [], repoUrl: '', errors: [],
    };
    setInstances([inst, ...instances]);
    setServiceName(''); setTemplate(templates[0]); setModalVisible(false);
  };

  const renderItem = ({ item }: { item: ScaffoldInstance }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.service}</Text>
        <Text style={[styles.status, { color: statusColor(item.status) }]}>{item.status}</Text>
      </View>
      <Text style={styles.cardSubtitle}>{item.template} - {item.owner}</Text>
      <Text style={styles.stepText}>Step: {item.currentStep} | Completed: {item.completedSteps.length}</Text>
      {item.repoUrl ? <Text style={styles.repoText}>Repo: {item.repoUrl}</Text> : null}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Golden Path Scaffolder</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}>
          <Text style={styles.addButtonText}>+ New</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{instances.filter(i => i.status === 'completed').length}</Text><Text style={styles.statLabel}>Completed</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{instances.filter(i => i.status === 'in_progress').length}</Text><Text style={styles.statLabel}>In Progress</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{instances.filter(i => i.status === 'failed').length}</Text><Text style={styles.statLabel}>Failed</Text></View>
      </View>

      <FlatList data={instances} renderItem={renderItem} keyExtractor={i => i.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Start Scaffold</Text>
            <Text style={styles.label}>Template</Text>
            <View style={styles.pickerRow}>
              {templates.map(t => (
                <TouchableOpacity key={t} style={[styles.pickerBtn, template === t && styles.pickerBtnActive]} onPress={() => setTemplate(t)}>
                  <Text style={[styles.pickerBtnText, template === t && styles.pickerBtnTextActive]}>{t.split(' ')[0]}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TextInput style={styles.input} placeholder="Service name" value={serviceName} onChangeText={setServiceName} />
            <TextInput style={styles.input} placeholder="Owner" value={owner} onChangeText={setOwner} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleStart}><Text style={styles.submitBtnText}>Start</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={detailVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{selected?.service}</Text>
            {selected && (
              <ScrollView>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Template</Text><Text>{selected.template}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Owner</Text><Text>{selected.owner}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Status</Text><Text style={{ color: statusColor(selected.status) }}>{selected.status}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Current Step</Text><Text>{selected.currentStep}</Text></View>
                <View style={styles.detailItem}><Text style={styles.detailLabel}>Completed Steps</Text><Text>{selected.completedSteps.length}</Text></View>
                {selected.errors.length > 0 && (
                  <View style={styles.detailItem}><Text style={styles.detailLabel}>Errors</Text><Text style={{ color: '#ef4444' }}>{selected.errors.join(', ')}</Text></View>
                )}
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
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', marginTop: 8, marginHorizontal: 12, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  status: { fontSize: 13, fontWeight: '600' },
  cardSubtitle: { fontSize: 13, color: '#64748b', marginTop: 4 },
  stepText: { fontSize: 12, color: '#94a3b8', marginTop: 4 },
  repoText: { fontSize: 11, color: '#3b82f6', marginTop: 2 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 24 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20, maxHeight: '80%' },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 16 },
  label: { fontSize: 13, color: '#64748b', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 14 },
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
  detailLabel: { color: '#64748b', fontWeight: '500', fontSize: 14 },
});
