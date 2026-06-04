import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Survey {
  id: string; title: string; type: string; status: string; createdBy: string; questions: number; responses: number;
}

interface NpsResult {
  score: number; promoters: number; detractors: number; passives: number; total: number; responseRate: number;
}

const mockSurveys: Survey[] = [
  { id: 'sv1', title: 'Platform NPS Q1 2025', type: 'nps', status: 'active', createdBy: 'platform-lead', questions: 1, responses: 45 },
  { id: 'sv2', title: 'Developer Satisfaction', type: 'satisfaction', status: 'active', createdBy: 'eng-mgr', questions: 7, responses: 32 },
  { id: 'sv3', title: 'Wellbeing Check-in', type: 'wellbeing', status: 'closed', createdBy: 'hr-lead', questions: 5, responses: 128 },
  { id: 'sv4', title: 'Platform Tooling Feedback', type: 'tooling', status: 'draft', createdBy: 'platform-lead', questions: 3, responses: 0 },
  { id: 'sv5', title: 'CI/CD Pipeline Survey', type: 'process', status: 'closed', createdBy: 'devops-lead', questions: 4, responses: 67 },
];

const mockNps: NpsResult = { score: 42, promoters: 18, detractors: 8, passives: 19, total: 45, responseRate: 75 };

const statusColors: Record<string, string> = { active: '#10b981', draft: '#6b7280', closed: '#f59e0b', archived: '#94a3b8' };

export default function PulseScreen() {
  const [surveys, setSurveys] = useState<Survey[]>(mockSurveys);
  const [nps] = useState<NpsResult>(mockNps);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<Survey | null>(null);
  const [title, setTitle] = useState(''); const [surveyType, setSurveyType] = useState('nps');
  const [createdBy, setCreatedBy] = useState('');

  const handleCreate = () => {
    if (!title || !createdBy) { Alert.alert('Error', 'Title and creator required'); return; }
    const survey: Survey = { id: `sv${Date.now()}`, title, type: surveyType, status: 'draft', createdBy, questions: surveyType === 'nps' ? 1 : 5, responses: 0 };
    setSurveys([survey, ...surveys]); setTitle(''); setCreatedBy(''); setModalVisible(false);
  };

  const renderSurvey = ({ item }: { item: Survey }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.cardSubtitle}>{item.type} - {item.createdBy}</Text></View>
        <View style={[styles.statusBadge, { backgroundColor: (statusColors[item.status] || '#6b7280') + '20' }]}>
          <Text style={[styles.statusText, { color: statusColors[item.status] || '#6b7280' }]}>{item.status}</Text>
        </View>
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.footerText}>{item.questions} questions</Text>
        <Text style={styles.footerText}>{item.responses} responses</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Developer Pulse</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Survey</Text></TouchableOpacity>
      </View>

      <View style={styles.npsCard}>
        <Text style={styles.npsTitle}>Net Promoter Score</Text>
        <Text style={styles.npsScore}>{nps.score}</Text>
        <View style={styles.npsRow}>
          <View style={styles.npsStat}><Text style={styles.npsStatValue}>{nps.promoters}</Text><Text style={styles.npsStatLabel}>Promoters</Text></View>
          <View style={styles.npsStat}><Text style={styles.npsStatValue}>{nps.passives}</Text><Text style={styles.npsStatLabel}>Passives</Text></View>
          <View style={styles.npsStat}><Text style={[styles.npsStatValue, { color: '#ef4444' }]}>{nps.detractors}</Text><Text style={styles.npsStatLabel}>Detractors</Text></View>
        </View>
        <Text style={styles.npsMeta}>{nps.total} responses - {nps.responseRate}% response rate</Text>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{surveys.length}</Text><Text style={styles.statLabel}>Total</Text></View>
        <View style={styles.stat}><Text style={[styles.statValue, { color: '#10b981' }]}>{surveys.filter(s => s.status === 'active').length}</Text><Text style={styles.statLabel}>Active</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{surveys.reduce((a, s) => a + s.responses, 0)}</Text><Text style={styles.statLabel}>Responses</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{nps.score}</Text><Text style={styles.statLabel}>NPS</Text></View>
      </View>

      <FlatList data={surveys} renderItem={renderSurvey} keyExtractor={s => s.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Create Survey</Text>
            <TextInput style={styles.input} placeholder="Title" value={title} onChangeText={setTitle} />
            <Text style={styles.label}>Type</Text>
            <View style={styles.pickerRow}>{['nps', 'satisfaction', 'wellbeing', 'tooling', 'process', 'custom'].map(t => (
              <TouchableOpacity key={t} style={[styles.pickerBtn, surveyType === t && styles.pickerBtnActive]} onPress={() => setSurveyType(t)}>
                <Text style={[styles.pickerBtnText, surveyType === t && styles.pickerBtnTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}</View>
            <TextInput style={styles.input} placeholder="Created by" value={createdBy} onChangeText={setCreatedBy} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitBtn} onPress={handleCreate}><Text style={styles.submitBtnText}>Create</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={detailVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{selected?.title}</Text>
            {selected && (
              <ScrollView>
                {[{ l: 'Type', v: selected.type }, { l: 'Status', v: selected.status }, { l: 'Created By', v: selected.createdBy }, { l: 'Questions', v: String(selected.questions) }, { l: 'Responses', v: String(selected.responses) }].map(d => (
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
  addButton: { backgroundColor: '#8b5cf6', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  npsCard: { backgroundColor: '#fff', margin: 12, borderRadius: 12, padding: 20, elevation: 2, alignItems: 'center' },
  npsTitle: { fontSize: 14, color: '#64748b', fontWeight: '500' },
  npsScore: { fontSize: 48, fontWeight: '800', color: '#8b5cf6', marginVertical: 8 },
  npsRow: { flexDirection: 'row', gap: 32, marginVertical: 8 },
  npsStat: { alignItems: 'center' },
  npsStatValue: { fontSize: 20, fontWeight: '700', color: '#10b981' },
  npsStatLabel: { fontSize: 11, color: '#64748b' },
  npsMeta: { fontSize: 12, color: '#94a3b8', marginTop: 4 },
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', marginHorizontal: 12, marginBottom: 8, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', alignItems: 'center' },
  cardTitle: { fontSize: 15, fontWeight: '600', flex: 1 },
  cardSubtitle: { fontSize: 11, color: '#64748b', marginTop: 2 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  statusText: { fontSize: 11, fontWeight: '600' },
  cardFooter: { flexDirection: 'row', gap: 12, marginTop: 8 },
  footerText: { fontSize: 12, color: '#94a3b8' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 24 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 16 },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 14 },
  label: { fontSize: 13, color: '#64748b', marginBottom: 6 },
  pickerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 12 },
  pickerBtn: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0' },
  pickerBtnActive: { backgroundColor: '#8b5cf6', borderColor: '#8b5cf6' },
  pickerBtnText: { fontSize: 11, color: '#64748b' },
  pickerBtnTextActive: { color: '#fff' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  cancelBtn: { flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  cancelBtnText: { fontSize: 14, color: '#64748b' },
  submitBtn: { flex: 1, padding: 12, borderRadius: 8, backgroundColor: '#8b5cf6', alignItems: 'center' },
  submitBtnText: { color: '#fff', fontWeight: '600' },
  detailItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  detailLabel: { color: '#64748b', fontWeight: '500' },
});
