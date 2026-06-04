import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const rules = [
  { id: "1", name: "Non-null email", dataset: "users", column: "email", severity: "high", enabled: true },
  { id: "2", name: "Unique user_id", dataset: "users", column: "user_id", severity: "critical", enabled: true },
  { id: "3", name: "Range amount", dataset: "orders", column: "amount", severity: "medium", enabled: false },
];

export default function DataQualityScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Data Quality</Text>
      <Text style={styles.subtitle}>Validation rules and scorecards</Text>
      <FlatList
        data={rules}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="checkmark-circle-outline" size={22} color="#f59e0b" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: item.enabled ? "#065f46" : "#451a03" }]}>
                <Text style={[styles.badgeText, { color: item.enabled ? "#10b981" : "#f59e0b" }]}>{item.enabled ? "ON" : "OFF"}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>Dataset: {item.dataset}.{item.column}</Text>
            <Text style={styles.cardDetail}>Severity: {item.severity}</Text>
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
