import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const alerts = [
  { id: "1", name: "HighCPU", source: "prometheus", severity: "critical", status: "firing", message: "CPU at 95%" },
  { id: "2", name: "DiskFull", source: "node_exporter", severity: "warning", status: "acknowledged", message: "Disk 85%" },
  { id: "3", name: "HighMem", source: "prometheus", severity: "warning", status: "suppressed", message: "Memory 78%" },
];

export default function AlertCorrelationScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Alert Correlation</Text>
      <Text style={styles.subtitle}>Dedup, suppression & grouping</Text>
      {alerts.map(a => (
        <View key={a.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons
              name={a.severity === "critical" ? "warning" : "information-circle"}
              size={20}
              color={a.severity === "critical" ? "#ef4444" : "#f59e0b"}
            />
            <Text style={styles.cardTitle}>{a.name}</Text>
          </View>
          <Text style={styles.cardText}>Source: {a.source}</Text>
          <Text style={styles.cardText}>Status: {a.status}</Text>
          <Text style={styles.cardText}>{a.message}</Text>
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
