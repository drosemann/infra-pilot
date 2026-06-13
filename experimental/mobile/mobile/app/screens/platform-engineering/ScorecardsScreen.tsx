import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Modal, TextInput, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface TeamScore {
  id: string; name: string; org: string; score: number; rating: string;
  deployFreq: number; leadTime: number; changeFailRate: number;
}

const mockTeams: TeamScore[] = [
  { id: 't1', name: 'platform-team', org: 'engineering', score: 94, rating: 'elite', deployFreq: 8.5, leadTime: 2.3, changeFailRate: 0.03 },
  { id: 't2', name: 'finops-team', org: 'engineering', score: 78, rating: 'high', deployFreq: 3.2, leadTime: 12.5, changeFailRate: 0.08 },
  { id: 't3', name: 'data-team', org: 'data', score: 62, rating: 'medium', deployFreq: 1.5, leadTime: 48.0, changeFailRate: 0.12 },
  { id: 't4', name: 'web-team', org: 'engineering', score: 85, rating: 'high', deployFreq: 4.0, leadTime: 8.0, changeFailRate: 0.06 },
  { id: 't5', name: 'security-team', org: 'security', score: 45, rating: 'low', deployFreq: 0.3, leadTime: 120.0, changeFailRate: 0.20 },
];

const ratingColors: Record<string, string> = { elite: '#10b981', high: '#3b82f6', medium: '#f59e0b', low: '#ef4444' };

export default function ScorecardsScreen() {
  const [teams, setTeams] = useState<TeamScore[]>(mockTeams);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selected, setSelected] = useState<TeamScore | null>(null);
  const [name, setName] = useState(''); const [org, setOrg] = useState('');

  const handleCreate = () => {
    if (!name) { Alert.alert('Error', 'Team name required'); return; }
    const team: TeamScore = { id: `t${Date.now()}`, name, org: org || 'engineering', score: 0, rating: 'low', deployFreq: 0, leadTime: 0, changeFailRate: 0 };
    setTeams([team, ...teams]); setName(''); setOrg(''); setModalVisible(false);
  };

  const renderTeam = ({ item }: { item: TeamScore }) => (
    <TouchableOpacity style={styles.card} onPress={() => { setSelected(item); setDetailVisible(true); }}>
      <View style={styles.cardHeader}>
        <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{item.name}</Text><Text style={styles.cardSubtitle}>{item.org}</Text></View>
        <Text style={[styles.scoreText, { color: ratingColors[item.rating] }]}>{item.score}</Text>
        <View style={[styles.ratingBadge, { backgroundColor: ratingColors[item.rating] + '20' }]}><Text style={[styles.ratingText, { color: ratingColors[item.rating] }]}>{item.rating}</Text></View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Scorecards</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(true)}><Text style={styles.addButtonText}>+ Team</Text></TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>{teams.length}</Text><Text style={styles.statLabel}>Teams</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{teams.filter(t => t.rating === 'elite').length}</Text><Text style={styles.statLabel}>Elite</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{teams.filter(t => t.rating === 'high').length}</Text><Text style={styles.statLabel}>High</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>{Math.round(teams.reduce((a, t) => a + t.score, 0) / teams.length)}</Text><Text style={styles.statLabel}>Avg</Text></View>
      </View>

      <FlatList data={teams} renderItem={renderTeam} keyExtractor={t => t.id} contentContainerStyle={styles.list} />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Create Team</Text>
            <TextInput style={styles.input} placeholder="Team name" value={name} onChangeText={setName} />
            <TextInput style={styles.input} placeholder="Organization" value={org} onChangeText={setOrg} />
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
            <Text style={styles.modalTitle}>{selected?.name}</Text>
            {selected && (
              <View>
                {[{ l: 'Organization', v: selected.org }, { l: 'DORA Score', v: `${selected.score}/100` }, { l: 'Rating', v: selected.rating }, { l: 'Deploy Frequency', v: `${selected.deployFreq}/day` }, { l: 'Lead Time', v: `${selected.leadTime}h` }, { l: 'Change Fail Rate', v: `${(selected.changeFailRate * 100).toFixed(1)}%` }].map(d => (
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
  statsRow: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', margin: 12, borderRadius: 12, elevation: 1 },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  statLabel: { fontSize: 11, color: '#64748b', marginTop: 2 },
  list: { paddingHorizontal: 12, paddingBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, elevation: 1 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardSubtitle: { fontSize: 12, color: '#64748b', marginTop: 2 },
  scoreText: { fontSize: 24, fontWeight: '700' },
  ratingBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  ratingText: { fontSize: 12, fontWeight: '600' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 24 },
  modalContent: { backgroundColor: '#fff', borderRadius: 16, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 16 },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 14 },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  cancelBtn: { flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  cancelBtnText: { fontSize: 14, color: '#64748b' },
  submitBtn: { flex: 1, padding: 12, borderRadius: 8, backgroundColor: '#3b82f6', alignItems: 'center' },
  submitBtnText: { color: '#fff', fontWeight: '600' },
  detailItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  detailLabel: { color: '#64748b', fontWeight: '500' },
});
