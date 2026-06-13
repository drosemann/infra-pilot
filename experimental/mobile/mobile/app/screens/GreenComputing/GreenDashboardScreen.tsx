import React from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const stats = [
  { id: "1", title: "Energy Usage", value: "2,650 MWh", icon: "flash-outline", color: "#f59e0b" },
  { id: "2", title: "CO₂ Emissions", value: "7.8 t", icon: "leaf-outline", color: "#10b981" },
  { id: "3", title: "Renewable %", value: "60%", icon: "sunny-outline", color: "#fbbf24" },
  { id: "4", title: "Carbon Intensity", value: "294", icon: "pulse-outline", color: "#ef4444" },
  { id: "5", title: "Avg PUE", value: "1.25", icon: "trending-down-outline", color: "#3b82f6" },
  { id: "6", title: "Offsets Purchased", value: "90 t", icon: "shield-checkmark-outline", color: "#8b5cf6" },
];

export default function GreenDashboardScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Green Computing</Text>
      <Text style={styles.subtitle}>Sustainability metrics</Text>
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
  cardValue: { fontSize: 24, fontWeight: "bold", marginTop: 8 },
  cardLabel: { fontSize: 12, color: "#94a3b8", marginTop: 4 },
});
