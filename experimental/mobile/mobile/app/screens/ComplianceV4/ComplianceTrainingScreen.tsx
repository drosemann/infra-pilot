import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export default function ComplianceTrainingScreen() {
  const [data, setData] = useState([
    { id: "1", title: "Compliance Training Item 1", status: "active", detail: "Sample detail for Compliance Training" },
    { id: "2", title: "Compliance Training Item 2", status: "pending", detail: "Another sample detail" },
  ]);
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Compliance Training</Text>
      <Text style={styles.subtitle}> management</Text>
      {data.map(item => (
        <View key={item.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="options-outline" size={20} color="#3b82f6" />
            <Text style={styles.cardTitle}>{item.title}</Text>
          </View>
          <Text style={styles.cardText}>Status: {item.status}</Text>
          <Text style={styles.cardText}>{item.detail}</Text>
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