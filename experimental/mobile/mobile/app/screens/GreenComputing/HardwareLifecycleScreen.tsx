import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";

const assets = [
  { name: "Dell R740-01", type: "server", status: "active", age: 2.5, eol: "2028-06" },
  { name: "Cisco 9300-01", type: "switch", status: "active", age: 1.2, eol: "2030-03" },
  { name: "NetApp FAS8200", type: "storage", status: "active", age: 3.8, eol: "2026-12" },
  { name: "NVIDIA A100-01", type: "gpu", status: "active", age: 0.8, eol: "2029-05" },
  { name: "SuperMicro-01", type: "server", status: "maintenance", age: 4.2, eol: "2026-03" },
  { name: "Juniper EX4600", type: "network", status: "decommissioned", age: 6.1, eol: "2024-08" },
];

const statusColors: Record<string, string> = {
  active: "#10b981",
  maintenance: "#f59e0b",
  decommissioned: "#ef4444",
};

export default function HardwareLifecycleScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Hardware Lifecycle</Text>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>6</Text><Text style={styles.statLabel}>Assets</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>4</Text><Text style={styles.statLabel}>Active</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>2</Text><Text style={styles.statLabel}>Near EOL</Text></View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Asset Inventory</Text>
        {assets.map(a => (
          <View key={a.name} style={styles.assetCard}>
            <View style={styles.assetHeader}>
              <Text style={styles.assetName}>{a.name}</Text>
              <View style={[styles.statusBadge, { backgroundColor: statusColors[a.status] || "#6b7280" }]}>
                <Text style={styles.statusText}>{a.status}</Text>
              </View>
            </View>
            <View style={styles.assetDetails}>
              <Text style={styles.detailText}>Type: {a.type}</Text>
              <Text style={styles.detailText}>Age: {a.age} yrs</Text>
              <Text style={[styles.detailText, a.eol < "2027" ? { color: "#ef4444" } : { color: "#94a3b8" }]}>
                EOL: {a.eol}
              </Text>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  statsRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: 20 },
  stat: { backgroundColor: "#1e293b", borderRadius: 12, padding: 12, alignItems: "center", flex: 1, marginHorizontal: 4 },
  statValue: { fontSize: 20, fontWeight: "bold", color: "#f8fafc" },
  statLabel: { fontSize: 11, color: "#94a3b8", marginTop: 2 },
  section: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 16 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#f8fafc", marginBottom: 12 },
  assetCard: { backgroundColor: "#0f172a", borderRadius: 8, padding: 12, marginBottom: 8 },
  assetHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  assetName: { fontSize: 14, fontWeight: "500", color: "#f8fafc", flex: 1 },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  statusText: { fontSize: 10, fontWeight: "600", color: "#fff" },
  assetDetails: { flexDirection: "row", justifyContent: "space-between", marginTop: 8 },
  detailText: { fontSize: 12, color: "#94a3b8" },
});
