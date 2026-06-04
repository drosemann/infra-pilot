import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const customers = [
  { id: "1", name: "Acme Corp", domain: "acme.com", embeds: 3, active: true },
  { id: "2", name: "Globex Inc", domain: "globex.com", embeds: 1, active: true },
  { id: "3", name: "Initech", domain: "initech.com", embeds: 0, active: false },
];

export default function EmbeddedAnalyticsScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Embedded Analytics</Text>
      <Text style={styles.subtitle}>White-label analytics for customers</Text>
      <FlatList
        data={customers}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="briefcase-outline" size={22} color="#8b5cf6" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: item.active ? "#065f46" : "#451a03" }]}>
                <Text style={[styles.badgeText, { color: item.active ? "#10b981" : "#f59e0b" }]}>{item.active ? "Active" : "Inactive"}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>Domain: {item.domain}</Text>
            <Text style={styles.cardDetail}>Embeds: {item.embeds}</Text>
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
