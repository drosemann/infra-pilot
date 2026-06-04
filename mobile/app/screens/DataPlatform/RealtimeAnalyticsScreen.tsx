import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const dashboards = [
  { id: "1", name: "Infra Monitor", panels: 6, refresh: 5, status: "active" },
  { id: "2", name: "App Performance", panels: 4, refresh: 10, status: "active" },
  { id: "3", name: "Business KPIs", panels: 8, refresh: 30, status: "active" },
];

export default function RealtimeAnalyticsScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Real-Time Analytics</Text>
      <Text style={styles.subtitle}>Live operational dashboards</Text>
      <FlatList
        data={dashboards}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="pulse-outline" size={22} color="#f43f5e" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: "#065f46" }]}>
                <Text style={styles.badgeText}>LIVE</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>Panels: {item.panels}</Text>
            <Text style={styles.cardDetail}>Refresh: {item.refresh}s</Text>
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
  badgeText: { fontSize: 11, color: "#10b981", fontWeight: "600" },
  cardDetail: { fontSize: 13, color: "#94a3b8", marginTop: 2 },
});
