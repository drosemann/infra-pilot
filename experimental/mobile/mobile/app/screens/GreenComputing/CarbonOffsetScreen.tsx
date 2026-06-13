import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";

const offsets = [
  { id: "off-001", tonnes: 10, project: "Reforestation Amazon", status: "purchased", date: "2026-05-15" },
  { id: "off-002", tonnes: 25, project: "Wind Farm Denmark", status: "purchased", date: "2026-05-10" },
  { id: "off-003", tonnes: 5, project: "Solar Park Spain", status: "pending", date: "2026-05-20" },
  { id: "off-004", tonnes: 50, project: "Methane Capture", status: "retired", date: "2026-04-28" },
];

const statusColors: Record<string, string> = {
  purchased: "#10b981",
  pending: "#f59e0b",
  retired: "#3b82f6",
};

export default function CarbonOffsetScreen() {
  const totalOffset = offsets.filter(o => o.status === "purchased" || o.status === "retired")
    .reduce((sum, o) => sum + o.tonnes, 0);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Carbon Offsets</Text>
      <View style={styles.summaryCard}>
        <Text style={styles.summaryValue}>{totalOffset} tCO₂</Text>
        <Text style={styles.summaryLabel}>Total Offset</Text>
      </View>
      <FlatList
        data={offsets}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.projectName}>{item.project}</Text>
              <View style={[styles.badge, { backgroundColor: statusColors[item.status] }]}>
                <Text style={styles.badgeText}>{item.status}</Text>
              </View>
            </View>
            <Text style={styles.detail}>Tonnes: {item.tonnes} tCO₂</Text>
            <Text style={styles.detail}>Date: {item.date}</Text>
          </View>
        )}
        keyExtractor={o => o.id}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  summaryCard: { backgroundColor: "#065f46", borderRadius: 16, padding: 24, alignItems: "center", marginBottom: 16 },
  summaryValue: { fontSize: 36, fontWeight: "bold", color: "#f8fafc" },
  summaryLabel: { fontSize: 14, color: "#a7f3d0" },
  card: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 12 },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  projectName: { fontSize: 16, fontWeight: "600", color: "#f8fafc", flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 12, marginLeft: 8 },
  badgeText: { fontSize: 11, fontWeight: "600", color: "#fff" },
  detail: { fontSize: 13, color: "#94a3b8", marginBottom: 2 },
});
