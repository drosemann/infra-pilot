import React from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const clusters = [
  { id: "1", name: "Prod Lakehouse", engine: "Apache Spark", region: "us-east-1", tables: 24, status: "active" },
  { id: "2", name: "Analytics Lake", engine: "Trino", region: "eu-west-1", tables: 12, status: "active" },
  { id: "3", name: "Dev Sandbox", engine: "Presto", region: "us-west-2", tables: 5, status: "active" },
];

export default function DataLakehouseScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Data Lakehouse</Text>
      <Text style={styles.subtitle}>Managed clusters across regions</Text>
      <FlatList
        data={clusters}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="server-outline" size={22} color="#3b82f6" />
              <Text style={styles.cardTitle}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: item.status === "active" ? "#065f46" : "#1e293b" }]}>
                <Text style={styles.badgeText}>{item.status}</Text>
              </View>
            </View>
            <Text style={styles.cardDetail}>Engine: {item.engine}</Text>
            <Text style={styles.cardDetail}>Region: {item.region}</Text>
            <Text style={styles.cardDetail}>Tables: {item.tables}</Text>
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
