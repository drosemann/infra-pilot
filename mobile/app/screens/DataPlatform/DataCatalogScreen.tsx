import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const assets = [
  { id: "1", name: "users", type: "table", schema: "public", owner: "data-team", certified: true },
  { id: "2", name: "orders", type: "table", schema: "public", owner: "analytics", certified: true },
  { id: "3", name: "monthly_revenue", type: "view", schema: "analytics", owner: "finance", certified: false },
];

export default function DataCatalogScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Data Catalog</Text>
      <Text style={styles.subtitle}>Discover and govern data assets</Text>
      <FlatList
        data={assets}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name={item.type === "table" ? "grid-outline" : "eye-outline"} size={22} color="#8b5cf6" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              {item.certified && <Ionicons name="shield-checkmark" size={18} color="#10b981" />}
            </View>
            <Text style={styles.cardDetail}>Type: {item.type}</Text>
            <Text style={styles.cardDetail}>Schema: {item.schema}</Text>
            <Text style={styles.cardDetail}>Owner: {item.owner}</Text>
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
  cardDetail: { fontSize: 13, color: "#94a3b8", marginTop: 2 },
});
