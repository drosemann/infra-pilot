import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const profiles = [
  { id: "1", name: "PII Protection", targets: "users, customers", rules: 3, enabled: true },
  { id: "2", name: "Finance Masking", targets: "transactions", rules: 5, enabled: true },
];

export default function DataMaskingScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Data Masking</Text>
      <Text style={styles.subtitle}>Column-level anonymization</Text>
      <FlatList
        data={profiles}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="eye-off-outline" size={22} color="#ef4444" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: item.enabled ? "#065f46" : "#451a03" }]}>
                <Text style={[styles.badgeText, { color: item.enabled ? "#10b981" : "#f59e0b" }]}>{item.enabled ? "ON" : "OFF"}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>Targets: {item.targets}</Text>
            <Text style={styles.cardDetail}>Rules: {item.rules}</Text>
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
