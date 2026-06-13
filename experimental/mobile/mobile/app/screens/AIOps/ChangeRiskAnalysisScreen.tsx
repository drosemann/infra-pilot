import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const changes = [
  { id: "1", title: "Update nginx config", type: "config_change", risk: "low", status: "approved", target: "nginx-proxy" },
  { id: "2", title: "DB schema migration", type: "migration", risk: "high", status: "pending", target: "postgres-db" },
  { id: "3", title: "Scale api to 5 replicas", type: "scaling", risk: "medium", status: "approved", target: "api-service" },
];

export default function ChangeRiskAnalysisScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Change Risk Analysis</Text>
      <Text style={styles.subtitle}>AI-driven change impact assessment</Text>
      {changes.map(c => (
        <View key={c.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons
              name={c.risk === "low" ? "shield-checkmark" : c.risk === "medium" ? "shield-half" : "shield"}
              size={20}
              color={c.risk === "low" ? "#10b981" : c.risk === "medium" ? "#f59e0b" : "#ef4444"}
            />
            <Text style={styles.cardTitle}>{c.title}</Text>
          </View>
          <Text style={styles.cardText}>Type: {c.type}</Text>
          <Text style={styles.cardText}>Risk: {c.risk}</Text>
          <Text style={styles.cardText}>Status: {c.status}</Text>
          <Text style={styles.cardText}>Target: {c.target}</Text>
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
