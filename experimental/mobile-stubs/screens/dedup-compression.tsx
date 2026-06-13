import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

const DedupCompressionScreen: React.FC = () => {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>DedupCompression</Text>
      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>Content coming soon</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f1a', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 16 },
  placeholder: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingVertical: 60 },
  placeholderText: { color: '#666', fontSize: 16 },
});

export default DedupCompressionScreen;
