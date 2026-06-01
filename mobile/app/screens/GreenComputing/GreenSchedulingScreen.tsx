import React from "react";
import { View, Text, ScrollView, StyleSheet, Dimensions } from "react-native";
import { LineChart, BarChart } from "react-native-chart-kit";

const screenWidth = Dimensions.get("window").width;

const intensityData = {
  labels: ["00", "04", "08", "12", "16", "20"],
  datasets: [{ data: [180, 130, 320, 410, 350, 250] }],
};

const recommendations = [
  { job: "Backup Task", current: "14:00", suggested: "02:00", savings: "0.8 kg CO₂" },
  { job: "Data Sync", current: "10:00", suggested: "04:00", savings: "1.2 kg CO₂" },
  { job: "Batch Processing", current: "16:00", suggested: "06:00", savings: "2.1 kg CO₂" },
  { job: "Report Generation", current: "08:00", suggested: "03:00", savings: "0.5 kg CO₂" },
];

export default function GreenSchedulingScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Green Scheduling</Text>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>47</Text><Text style={styles.statLabel}>Jobs</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>12.4</Text><Text style={styles.statLabel}>kg CO₂ saved</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>94%</Text><Text style={styles.statLabel}>Optimization</Text></View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Carbon Intensity (gCO₂/kWh)</Text>
        <LineChart
          data={intensityData}
          width={screenWidth - 32}
          height={200}
          chartConfig={{
            backgroundColor: "#1e293b",
            backgroundGradientFrom: "#1e293b",
            backgroundGradientTo: "#1e293b",
            color: (opacity = 1) => `rgba(239, 68, 68, ${opacity})`,
            labelColor: () => "#94a3b8",
          }}
          bezier
          style={styles.chart}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Optimization Recommendations</Text>
        {recommendations.map(r => (
          <View key={r.job} style={styles.recCard}>
            <Text style={styles.recJob}>{r.job}</Text>
            <View style={styles.recDetails}>
              <Text style={styles.recTime}>{r.current} → <Text style={{ color: "#10b981" }}>{r.suggested}</Text></Text>
              <Text style={styles.recSavings}>{r.savings}</Text>
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
  chart: { borderRadius: 8, marginLeft: -8 },
  recCard: { backgroundColor: "#0f172a", borderRadius: 8, padding: 12, marginBottom: 8 },
  recJob: { fontSize: 14, fontWeight: "500", color: "#f8fafc" },
  recDetails: { flexDirection: "row", justifyContent: "space-between", marginTop: 4 },
  recTime: { fontSize: 12, color: "#94a3b8" },
  recSavings: { fontSize: 12, color: "#10b981", fontWeight: "500" },
});
