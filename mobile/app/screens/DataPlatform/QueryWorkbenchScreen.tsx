import React, { useState } from "react";
import { View, Text, TextInput, FlatList, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const savedQueries = [
  { id: "1", name: "Daily Active Users", sql: "SELECT COUNT(*) FROM users WHERE last_seen > now() - interval '24h'", database: "prod" },
  { id: "2", name: "Revenue MTD", sql: "SELECT SUM(amount) FROM orders WHERE created_at >= date_trunc('month', now())", database: "analytics" },
];

export default function QueryWorkbenchScreen() {
  const [query, setQuery] = useState("SELECT * FROM users LIMIT 10");
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Query Workbench</Text>
      <Text style={styles.subtitle}>Interactive SQL editor</Text>
      <View style={styles.editor}>
        <TextInput style={styles.input} value={query} onChangeText={setQuery} multiline placeholder="Enter SQL..." placeholderTextColor="#475569" />
        <TouchableOpacity style={styles.runBtn}>
          <Ionicons name="play" size={18} color="#fff" />
          <Text style={styles.runText}>Run</Text>
        </TouchableOpacity>
      </View>
      <Text style={styles.sectionTitle}>Saved Queries</Text>
      <FlatList
        data={savedQueries}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.queryCard}>
            <Text style={styles.queryName}>{item.name}</Text>
            <Text style={styles.querySql} numberOfLines={2}>{item.sql}</Text>
            <Text style={styles.queryDb}>{item.database}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc" },
  subtitle: { fontSize: 14, color: "#64748b", marginBottom: 20 },
  editor: { backgroundColor: "#1e293b", borderRadius: 12, padding: 12, marginBottom: 20 },
  input: { color: "#e2e8f0", fontSize: 13, fontFamily: "monospace", minHeight: 80, textAlignVertical: "top" },
  runBtn: { flexDirection: "row", alignItems: "center", backgroundColor: "#3b82f6", borderRadius: 8, padding: 10, alignSelf: "flex-end", marginTop: 8 },
  runText: { color: "#fff", fontWeight: "600", fontSize: 14, marginLeft: 6 },
  sectionTitle: { fontSize: 18, fontWeight: "600", color: "#e2e8f0", marginBottom: 12 },
  queryCard: { backgroundColor: "#1e293b", borderRadius: 10, padding: 14, marginBottom: 10 },
  queryName: { fontSize: 15, fontWeight: "600", color: "#f1f5f9" },
  querySql: { fontSize: 12, color: "#64748b", fontFamily: "monospace", marginTop: 4 },
  queryDb: { fontSize: 11, color: "#3b82f6", marginTop: 4 },
});
