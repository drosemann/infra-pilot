import React from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const stats = [
  { id: "1", title: "Edge Devices", value: "24", icon: "hardware-chip-outline", color: "#3b82f6" },
  { id: "2", title: "IoT Pipelines", value: "12", icon: "git-network-outline", color: "#10b981" },
  { id: "3", title: "Functions Deployed", value: "38", icon: "code-slash-outline", color: "#8b5cf6" },
  { id: "4", title: "ML Models", value: "7", icon: "brain-outline", color: "#f59e0b" },
  { id: "5", title: "Mesh Nodes", value: "15", icon: "wifi-outline", color: "#06b6d4" },
  { id: "6", title: "Data Processed", value: "2.4 TB", icon: "cloud-download-outline", color: "#f43f5e" },
];

export default function EdgeDashboardScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Edge & IoT</Text>
      <Text style={styles.subtitle}>Infrastructure at the edge</Text>
      <View style={styles.grid}>
        {stats.map(stat => (
          <TouchableOpacity key={stat.id} style={styles.card}>
            <Ionicons name={stat.icon as any} size={28} color={stat.color} />
            <Text style={[styles.cardValue, { color: stat.color }]}>{stat.value}</Text>
            <Text style={styles.cardLabel}>{stat.title}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc" },
  subtitle: { fontSize: 14, color: "#64748b", marginBottom: 20 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  card: {
    backgroundColor: "#1e293b", borderRadius: 16, padding: 20, alignItems: "center",
    width: "47%", aspectRatio: 1, justifyContent: "center",
  },
  cardValue: { fontSize: 28, fontWeight: "bold", marginTop: 8 },
  cardLabel: { fontSize: 12, color: "#94a3b8", marginTop: 4 },
});
