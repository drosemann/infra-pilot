import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const remediations = [
  { id: "1", incident: "High CPU", action: "Restart Service", status: "completed", pattern: "high_cpu" },
  { id: "2", incident: "Memory Leak", action: "Scale Up", status: "approved", pattern: "memory_leak" },
  { id: "3", incident: "Deploy Failure", action: "Rollback", status: "pending", pattern: "deploy_failure" },
];

export default function IncidentRemediationScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Incident Remediation</Text>
      <Text style={styles.subtitle}>Automated resolution engine</Text>
      {remediations.map(rem => (
        <View key={rem.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons
              name={rem.status === "completed" ? "checkmark-circle" : rem.status === "approved" ? "hourglass" : "time-outline"}
              size={20}
              color={rem.status === "completed" ? "#10b981" : rem.status === "approved" ? "#f59e0b" : "#64748b"}
            />
            <Text style={styles.cardTitle}>{rem.incident}</Text>
          </View>
          <Text style={styles.cardText}>Action: {rem.action}</Text>
          <Text style={styles.cardText}>Status: {rem.status}</Text>
          <Text style={styles.cardText}>Pattern: {rem.pattern}</Text>
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
