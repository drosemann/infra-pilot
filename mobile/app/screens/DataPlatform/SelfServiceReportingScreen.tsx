import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const reports = [
  { id: "1", name: "Monthly Sales", mode: "visual", widgets: 4, schedule: "daily" },
  { id: "2", name: "User Growth", mode: "sql", widgets: 2, schedule: "weekly" },
  { id: "3", name: "Revenue Summary", mode: "visual", widgets: 6, schedule: "monthly" },
];

export default function SelfServiceReportingScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Self-Service Reporting</Text>
      <Text style={styles.subtitle}>Create and schedule reports</Text>
      <FlatList
        data={reports}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="bar-chart-outline" size={22} color="#06b6d4" />
              <Text style={styles.cardTitle}>{item.name}</Text>
            </View>
            <Text style={styles.cardDetail}>Mode: {item.mode}</Text>
            <Text style={styles.cardDetail}>Widgets: {item.widgets}</Text>
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
  cardDetail: { fontSize: 13, color: "#94a3b8", marginTop: 2 },
});
