import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const resources = [
  { id: "1", name: "web-cluster", metric: "cpu", current: 65, forecast: 82, policy: "aggressive" },
  { id: "2", name: "api-gateway", metric: "cpu", current: 42, forecast: 58, policy: "balanced" },
  { id: "3", name: "worker-pool", metric: "memory", current: 71, forecast: 93, policy: "aggressive" },
];

export default function PredictiveScalingScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Predictive Scaling</Text>
      <Text style={styles.subtitle}>ML-driven auto-scaling forecasts</Text>
      {resources.map(r => (
        <View key={r.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="trending-up" size={20} color="#3b82f6" />
            <Text style={styles.cardTitle}>{r.name}</Text>
          </View>
          <Text style={styles.cardText}>Metric: {r.metric}</Text>
          <Text style={styles.cardText}>Current: {r.current}%</Text>
          <Text style={styles.cardText}>Forecast: {r.forecast}%</Text>
          <Text style={styles.cardText}>Policy: {r.policy}</Text>
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
