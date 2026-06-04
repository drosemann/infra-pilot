import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export default function RootCauseAnalysisScreen() {
  const [incidents, setIncidents] = useState([
    { id: "1", title: "Web Server Down", status: "analyzed", rootCause: "High CPU due to memory leak", confidence: 0.92 },
    { id: "2", title: "Database Timeout", status: "analyzed", rootCause: "Connection pool exhausted", confidence: 0.88 },
  ]);
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Root Cause Analysis</Text>
      <Text style={styles.subtitle}>AI-powered incident diagnostics</Text>
      {incidents.map(inc => (
        <View key={inc.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="search-outline" size={20} color="#f59e0b" />
            <Text style={styles.cardTitle}>{inc.title}</Text>
          </View>
          <Text style={styles.cardText}>Status: {inc.status}</Text>
          <Text style={styles.cardText}>Root Cause: {inc.rootCause}</Text>
          <Text style={styles.cardText}>Confidence: {(inc.confidence * 100).toFixed(0)}%</Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc" },
  subtitle: { fontSize: 14, color: "#64748b", marginBottom: 20 },
  card: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 12 },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: "600", color: "#f8fafc" },
  cardText: { fontSize: 14, color: "#94a3b8", marginTop: 4 },
});
