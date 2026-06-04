import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function NPSSurveysScreen() {
  const [surveys, setSurveys] = useState<any[]>([]);
  const [score, setScore] = useState<any>(null);

  useEffect(() => {
    endpoints.customerExperience.nps.surveys().then(setSurveys).catch(console.error);
    endpoints.customerExperience.nps.score().then(setScore).catch(console.error);
  }, []);

  const renderItem = ({ item }: any) => (
    <View style={styles.card}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.type}>{item.survey_type} · {item.trigger}</Text>
      <Text style={styles.status}>Status: {item.status}</Text>
      {item.response_count !== undefined && (
        <Text style={styles.responses}>Responses: {item.response_count}</Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>NPS Surveys</Text>
      {score && (
        <View style={styles.scoreCard}>
          <Text style={[styles.scoreValue, {
            color: score.nps_score >= 50 ? '#4caf50' : score.nps_score >= 0 ? '#ff9800' : '#f44336',
          }]}>
            {score.nps_score?.toFixed(0) || 'N/A'}
          </Text>
          <Text style={styles.scoreLabel}>NPS Score</Text>
        </View>
      )}
      <FlatList data={surveys} keyExtractor={(i) => i.id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  heading: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  scoreCard: { backgroundColor: '#1e1e1e', padding: 20, borderRadius: 12, alignItems: 'center', marginBottom: 16 },
  scoreValue: { fontSize: 48, fontWeight: 'bold' },
  scoreLabel: { fontSize: 14, color: '#aaa', marginTop: 4 },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  title: { fontSize: 16, color: '#fff', fontWeight: '600' },
  type: { fontSize: 12, color: '#888', marginTop: 2 },
  status: { fontSize: 14, color: '#aaa', marginTop: 4 },
  responses: { fontSize: 12, color: '#666', marginTop: 2 },
});
