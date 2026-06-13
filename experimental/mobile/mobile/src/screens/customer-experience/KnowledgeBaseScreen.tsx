import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { endpoints } from '../../api/endpoints';

export default function KnowledgeBaseScreen({ navigation }: any) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const search = async () => {
    if (!query.trim()) return;
    try {
      const res = await endpoints.customerExperience.knowledgeBase.search({ q: query });
      setResults(res);
    } catch (e) {
      console.error(e);
    }
  };

  const renderItem = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('ArticleDetail', { articleId: item.id })}
    >
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.category}>{item.category}</Text>
      <Text style={styles.snippet} numberOfLines={2}>{item.content?.substring(0, 100)}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Knowledge Base</Text>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.input}
          placeholder="Search articles..."
          placeholderTextColor="#666"
          value={query}
          onChangeText={setQuery}
        />
        <TouchableOpacity style={styles.searchButton} onPress={search}>
          <Text style={styles.searchButtonText}>Search</Text>
        </TouchableOpacity>
      </View>
      <FlatList data={results} keyExtractor={(i) => i.id} renderItem={renderItem} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#121212' },
  heading: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  searchRow: { flexDirection: 'row', marginBottom: 16 },
  input: { flex: 1, backgroundColor: '#1e1e1e', color: '#fff', borderRadius: 8, padding: 12, marginRight: 8 },
  searchButton: { backgroundColor: '#1976d2', padding: 12, borderRadius: 8, justifyContent: 'center' },
  searchButtonText: { color: '#fff', fontWeight: 'bold' },
  card: { backgroundColor: '#1e1e1e', padding: 16, borderRadius: 8, marginBottom: 12 },
  title: { fontSize: 16, color: '#fff', fontWeight: '600' },
  category: { fontSize: 12, color: '#888', marginTop: 2 },
  snippet: { fontSize: 14, color: '#aaa', marginTop: 4 },
});
