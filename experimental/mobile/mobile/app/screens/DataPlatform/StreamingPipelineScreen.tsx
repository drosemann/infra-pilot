import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const clusters = [
  { id: "1", name: "Prod Kafka", provider: "Kafka", nodes: 5, topics: 12, status: "active" },
  { id: "2", name: "Dev Redpanda", provider: "Redpanda", nodes: 3, topics: 6, status: "active" },
  { id: "3", name: "Staging Stream", provider: "Kafka", nodes: 3, topics: 4, status: "active" },
];

export default function StreamingPipelineScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Streaming Pipeline</Text>
      <Text style={styles.subtitle}>Real-time data streaming clusters</Text>
      <FlatList
        data={clusters}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="git-network-outline" size={22} color="#10b981" />
              <Text style={styles.cardTitle}>{item.name}</Text>
            </View>
            <Text style={styles.cardDetail}>Provider: {item.provider}</Text>
            <Text style={styles.cardDetail}>Nodes: {item.nodes}</Text>
            <Text style={styles.cardDetail}>Topics: {item.topics}</Text>
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
