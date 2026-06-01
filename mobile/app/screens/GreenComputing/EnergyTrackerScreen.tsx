import React from "react";
import { View, Text, ScrollView, StyleSheet, Dimensions } from "react-native";
import { LineChart } from "react-native-chart-kit";

const screenWidth = Dimensions.get("window").width;

const energyData = {
  labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  datasets: [{ data: [520, 510, 560, 555, 595, 560, 550] }],
};

const sourceData = [
  { source: "Grid", pct: 55, color: "#6b7280" },
  { source: "Solar", pct: 28, color: "#fbbf24" },
  { source: "Wind", pct: 17, color: "#3b82f6" },
];

const topDevices = [
  { name: "Server A1", watts: 2450, daily: 58.8 },
  { name: "GPU Cluster", watts: 3800, daily: 91.2 },
  { name: "Storage C3", watts: 1800, daily: 43.2 },
];

export default function EnergyTrackerScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Energy Tracker</Text>

      <View style={styles.summaryRow}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>14.6 kW</Text>
          <Text style={styles.summaryLabel}>Current Draw</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>350 kWh</Text>
          <Text style={styles.summaryLabel}>Today</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>10,850</Text>
          <Text style={styles.summaryLabel}>This Month</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Daily Consumption (kWh)</Text>
        <LineChart
          data={energyData}
          width={screenWidth - 32}
          height={220}
          chartConfig={{
            backgroundColor: "#1e293b",
            backgroundGradientFrom: "#1e293b",
            backgroundGradientTo: "#1e293b",
            decimalCount: 0,
            color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
            labelColor: () => "#94a3b8",
          }}
          bezier
          style={styles.chart}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Source Breakdown</Text>
        {sourceData.map(s => (
          <View key={s.source} style={styles.sourceRow}>
            <View style={styles.sourceHeader}>
              <Text style={styles.sourceName}>{s.source}</Text>
              <Text style={[styles.sourcePct, { color: s.color }]}>{s.pct}%</Text>
            </View>
            <View style={styles.progressBg}>
              <View style={[styles.progressFill, { width: `${s.pct}%`, backgroundColor: s.color }]} />
            </View>
          </View>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Top Consumers</Text>
        {topDevices.map(d => (
          <View key={d.name} style={styles.deviceRow}>
            <Text style={styles.deviceName}>{d.name}</Text>
            <Text style={styles.devicePower}>{d.watts}W</Text>
            <Text style={styles.deviceDaily}>{d.daily} kWh/d</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f172a", padding: 16 },
  title: { fontSize: 28, fontWeight: "bold", color: "#f8fafc", marginBottom: 16 },
  summaryRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: 20 },
  summaryCard: { backgroundColor: "#1e293b", borderRadius: 12, padding: 12, alignItems: "center", flex: 1, marginHorizontal: 4 },
  summaryValue: { fontSize: 18, fontWeight: "bold", color: "#f8fafc" },
  summaryLabel: { fontSize: 11, color: "#94a3b8", marginTop: 2 },
  section: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 16 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#f8fafc", marginBottom: 12 },
  chart: { borderRadius: 8, marginLeft: -8 },
  sourceRow: { marginBottom: 12 },
  sourceHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  sourceName: { fontSize: 14, color: "#f8fafc" },
  sourcePct: { fontSize: 14, fontWeight: "bold" },
  progressBg: { height: 8, backgroundColor: "#334155", borderRadius: 4, overflow: "hidden" },
  progressFill: { height: 8, borderRadius: 4 },
  deviceRow: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#334155" },
  deviceName: { fontSize: 14, color: "#f8fafc", flex: 1 },
  devicePower: { fontSize: 14, color: "#94a3b8", width: 70, textAlign: "right" },
  deviceDaily: { fontSize: 14, color: "#3b82f6", width: 70, textAlign: "right" },
});
