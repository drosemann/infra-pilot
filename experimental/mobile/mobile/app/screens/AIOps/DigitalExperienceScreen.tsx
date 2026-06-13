import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const monitors = [
  { id: "1", name: "Production App", url: "https://app.example.com", status: "active", uptime: 99.97, lastCheck: "2s ago" },
  { id: "2", name: "API Gateway", url: "https://api.example.com", status: "active", uptime: 99.89, lastCheck: "5s ago" },
  { id: "3", name: "CDN Edge", url: "https://cdn.example.com", status: "degraded", uptime: 98.45, lastCheck: "1m ago" },
];

export default function DigitalExperienceScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Digital Experience</Text>
      <Text style={styles.subtitle}>Synthetic monitoring & Core Web Vitals</Text>
      {monitors.map(m => (
        <View key={m.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons
              name={m.status === "active" ? "checkmark-circle" : "alert-circle"}
              size={20}
              color={m.status === "active" ? "#10b981" : "#ef4444"}
            />
            <Text style={styles.cardTitle}>{m.name}</Text>
          </View>
          <Text style={styles.cardText}>{m.url}</Text>
          <Text style={styles.cardText}>Uptime: {m.uptime}%</Text>
          <Text style={styles.cardText}>Last check: {m.lastCheck}</Text>
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
