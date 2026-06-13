import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const services = [
  { id: "1", name: "Web Server", health: "healthy", score: 0.96, trend: "stable" },
  { id: "2", name: "API Gateway", health: "degraded", score: 0.72, trend: "degrading" },
  { id: "3", name: "Database", health: "healthy", score: 0.91, trend: "improving" },
];

export default function HealthForecastingScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Health Forecasting</Text>
      <Text style={styles.subtitle}>Service health prediction & trends</Text>
      {services.map(s => (
        <View key={s.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons
              name={s.health === "healthy" ? "heart" : "heart-half"}
              size={20}
              color={s.health === "healthy" ? "#10b981" : "#ef4444"}
            />
            <Text style={styles.cardTitle}>{s.name}</Text>
          </View>
          <Text style={styles.cardText}>Health: {s.health}</Text>
          <Text style={styles.cardText}>Score: {(s.score * 100).toFixed(0)}%</Text>
          <Text style={styles.cardText}>Trend: {s.trend}</Text>
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
