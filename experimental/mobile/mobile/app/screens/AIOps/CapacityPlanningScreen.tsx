import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const resources = [
  { id: "1", name: "web-cluster", metric: "cpu", utilization: 0.72, recommended: "+25%", priority: "high" },
  { id: "2", name: "db-cluster", metric: "storage", utilization: 0.88, recommended: "+50%", priority: "critical" },
  { id: "3", name: "cache-cluster", metric: "memory", utilization: 0.45, recommended: "none", priority: "low" },
];

export default function CapacityPlanningScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Capacity Planning</Text>
      <Text style={styles.subtitle}>AI-driven capacity recommendations</Text>
      {resources.map(r => (
        <View key={r.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons
              name={r.priority === "critical" ? "alert-circle" : "bar-chart"}
              size={20}
              color={r.priority === "critical" ? "#ef4444" : r.priority === "high" ? "#f59e0b" : "#10b981"}
            />
            <Text style={styles.cardTitle}>{r.name}</Text>
          </View>
          <Text style={styles.cardText}>Metric: {r.metric}</Text>
          <Text style={styles.cardText}>Utilization: {(r.utilization * 100).toFixed(0)}%</Text>
          <Text style={styles.cardText}>Recommendation: {r.recommended}</Text>
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
