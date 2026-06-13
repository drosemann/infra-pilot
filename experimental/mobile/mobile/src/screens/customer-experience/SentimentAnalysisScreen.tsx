import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function SentimentAnalysisScreen() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);

  const analyze = async () => {
    try {
      const res = await endpoints.customerExperience.sentiment.analyze({ text, source_type: 'mobile' });
      setResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  const scoreColor = (score: number) => {
    if (score > 0.3) return '#4caf50';
    if (score > -0.3) return '#ff9800';
    return '#f44336';
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Sentiment Analysis</Text>
      <TextInput
        style={styles.input}
        multiline
        placeholder="Enter text to analyze..."
        placeholderTextColor="#666"
        value={text}
        onChangeText={setText}
      />
      <TouchableOpacity style={styles.button} onPress={analyze}>
        <Text style={styles.buttonText}>Analyze</Text>
      </TouchableOpacity>
      {result && (
        <View style={styles.resultCard}>
          <Text style={[styles.score, { color: scoreColor(result.score) }]}>
            Score: {result.score?.toFixed(2)}
          </Text>
          <Text style={styles.label}>Label: {result.label}</Text>
          <Text style={styles.confidence}>Confidence: {(result.confidence * 100).toFixed(1)}%</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  input: { backgroundColor: '#1e1e1e', color: '#fff', borderRadius: 8, padding: 12, minHeight: 100, marginBottom: 12 },
  button: { backgroundColor: '#1976d2', padding: 14, borderRadius: 8, alignItems: 'center', marginBottom: 16 },
  buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  resultCard: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8 },
  score: { fontSize: 28, fontWeight: 'bold', marginBottom: 4 },
  label: { fontSize: 18, color: '#fff', marginBottom: 4 },
  confidence: { fontSize: 14, color: '#aaa' },
});
