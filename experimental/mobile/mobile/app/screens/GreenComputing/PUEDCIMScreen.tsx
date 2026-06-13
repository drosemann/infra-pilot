import React, { useState } from "react";
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Dimensions } from "react-native";
import { LineChart } from "react-native-chart-kit";

const screenWidth = Dimensions.get("window").width;

const pueData = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  datasets: [
    { data: [1.45, 1.42, 1.38, 1.35, 1.32, 1.28], color: () => "#ef4444" },
    { data: [1.30, 1.30, 1.25, 1.25, 1.20, 1.20], color: () => "#10b981" },
  ],
};

const facilities = [
  { name: "DC-1 San Jose", pue: 1.25, score: 92 },
  { name: "DC-2 Dallas", pue: 1.35, score: 78 },
  { name: "DC-3 Ashburn", pue: 1.18, score: 96 },
];

export default function PUEDCIMScreen() {
  const [selectedTab, setSelectedTab] = useState("overview");

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>PUE & DCIM</Text>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>1.28</Text><Text style={styles.statLabel}>Overall PUE</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>1.18</Text><Text style={styles.statLabel}>Best PUE</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>89%</Text><Text style={styles.statLabel}>Efficiency</Text></View>
      </View>

      <View style={styles.tabRow}>
        {["overview", "facilities", "cooling"].map(tab => (
          <TouchableOpacity key={tab} style={[styles.tab, selectedTab === tab && styles.activeTab]}
            onPress={() => setSelectedTab(tab)}>
            <Text style={[styles.tabText, selectedTab === tab && styles.activeTabText]}>{tab}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>PUE Trend (Actual vs Target)</Text>
        <LineChart
          data={pueData}
          width={screenWidth - 32}
          height={220}
          chartConfig={{
            backgroundColor: "#1e293b",
            backgroundGradientFrom: "#1e293b",
            backgroundGradientTo: "#1e293b",
            decimalCount: 2,
            color: (opacity = 1) => `rgba(239, 68, 68, ${opacity})`,
            labelColor: () => "#94a3b8",
          }}
          bezier
          style={styles.chart}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Facility Comparison</Text>
        {facilities.map(f => (
          <View key={f.name} style={styles.facilityCard}>
            <View style={styles.facilityHeader}>
              <Text style={styles.facilityName}>{f.name}</Text>
              <Text style={[styles.facilityScore, f.score >= 90 ? { color: "#10b981" } : { color: "#f59e0b" }]}>
                {f.score}/100
              </Text>
            </View>
            <View style={styles.facilityDetails}>
              <Text style={styles.detailText}>PUE: {f.pue}</Text>
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
  tabRow: { flexDirection: "row", marginBottom: 16, gap: 8 },
  tab: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: "#1e293b" },
  activeTab: { backgroundColor: "#3b82f6" },
  tabText: { fontSize: 14, color: "#94a3b8" },
  activeTabText: { color: "#fff", fontWeight: "600" },
  section: { backgroundColor: "#1e293b", borderRadius: 12, padding: 16, marginBottom: 16 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#f8fafc", marginBottom: 12 },
  chart: { borderRadius: 8, marginLeft: -8 },
  facilityCard: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: "#334155" },
  facilityHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  facilityName: { fontSize: 14, color: "#f8fafc", fontWeight: "500" },
  facilityScore: { fontSize: 14, fontWeight: "bold" },
  facilityDetails: { marginTop: 4 },
  detailText: { fontSize: 12, color: "#94a3b8" },
});
