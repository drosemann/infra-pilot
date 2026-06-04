import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const pipelines = [
  { id: "1", name: "ETL Users", status: "running", nodes: 3, schedule: "0 */6 * * *" },
  { id: "2", name: "Orders Sync", status: "running", nodes: 4, schedule: "0 * * * *" },
  { id: "3", name: "Analytics Rollup", status: "stopped", nodes: 5, schedule: "0 0 * * *" },
];

export default function PipelineObservabilityScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Pipeline Observability</Text>
      <Text style={styles.subtitle}>End-to-end data pipeline monitoring</Text>
      <FlatList
        data={pipelines}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="git-branch-outline" size={22} color="#3b82f6" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: item.status === "running" ? "#065f46" : "#451a03" }]}>
                <Text style={[styles.badgeText, { color: item.status === "running" ? "#10b981" : "#f59e0b" }]}>{item.status}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>Nodes: {item.nodes}</Text>
            <Text style={styles.cardDetail}>Schedule: {item.schedule}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc" },
  subtitle: { fontSize: 14, color: "#64748b", marginBottom: 20 },
  card: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 12 },
  cardHeader: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: "600", color: "#f1f5f9", marginLeft: 8, flex: 1 },
  badge: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2 },
  badgeText: { fontSize: 11, fontWeight: "600" },
  cardDetail: { fontSize: 13, color: "#94a3b8", marginTop: 2 },
});
