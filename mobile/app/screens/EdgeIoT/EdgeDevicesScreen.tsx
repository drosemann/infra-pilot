import React from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from "react-native";

const devices = [
  { id: "dev-001", name: "Temp Sensor A1", type: "sensor", status: "online", battery: 87 },
  { id: "dev-002", name: "Gateway NYC-1", type: "gateway", status: "online", battery: 100 },
  { id: "dev-003", name: "Camera B2", type: "camera", status: "offline", battery: 12 },
  { id: "dev-004", name: "Actuator C1", type: "actuator", status: "online", battery: 94 },
  { id: "dev-005", name: "Humidity Sensor D3", type: "sensor", status: "degraded", battery: 45 },
];

const statusColors: Record<string, string> = {
  online: "#10b981",
  offline: "#ef4444",
  degraded: "#f59e0b",
};

export default function EdgeDevicesScreen() {
  const renderItem = ({ item }: any) => (
    <TouchableOpacity style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.deviceName}>{item.name}</Text>
        <View style={[styles.statusBadge, { backgroundColor: statusColors[item.status] || "#6b7280" }]}>
          <Text style={styles.statusText}>{item.status}</Text>
        </View>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.detail}>ID: {item.id}</Text>
        <Text style={styles.detail}>Type: {item.type}</Text>
        <Text style={[styles.detail, item.battery < 20 && { color: "#ef4444", fontWeight: "bold" }]}>
          Battery: {item.battery}%
        </Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Edge Devices</Text>
      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>3</Text><Text style={styles.statLabel}>Online</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>1</Text><Text style={styles.statLabel}>Degraded</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>1</Text><Text style={styles.statLabel}>Offline</Text></View>
      </View>
      <FlatList data={devices} renderItem={renderItem} keyExtractor={d => d.id} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  statsRow: { flexDirection: "row", justifyContent: "space-around", marginBottom: 16 },
  stat: { alignItems: "center" },
  statValue: { fontSize: 24, fontWeight: "bold", color: "#f8fafc" },
  statLabel: { fontSize: 12, color: "#94a3b8" },
  card: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 12 },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  deviceName: { fontSize: 16, fontWeight: "600", color: "#f8fafc" },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 12 },
  statusText: { fontSize: 11, fontWeight: "600", color: "#fff" },
  cardBody: {},
  detail: { fontSize: 13, color: "#94a3b8", marginBottom: 2 },
});
