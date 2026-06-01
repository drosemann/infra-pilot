import React from "react";
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from "react-native";

const policies = [
  { name: "Night Shutdown", scope: "global", action: "hibernate", schedule: "22:00-06:00", enabled: true, savings: "120 kWh/day" },
  { name: "Weekend Standby", scope: "device", action: "shutdown", schedule: "Fri 18:00-Mon 08:00", enabled: true, savings: "340 kWh/weekend" },
  { name: "Idle Timeout", scope: "group", action: "sleep", schedule: "15 min idle", enabled: true, savings: "45 kWh/day" },
];

const effectiveness = [
  { policy: "Night Shutdown", compliance: 96, saved: "3,600 kWh" },
  { policy: "Weekend Standby", compliance: 88, saved: "1,360 kWh" },
  { policy: "Idle Timeout", compliance: 72, saved: "1,350 kWh" },
];

export default function AutoShutdownScreen() {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Auto Shutdown</Text>

      <View style={styles.statsRow}>
        <View style={styles.stat}><Text style={styles.statValue}>4</Text><Text style={styles.statLabel}>Policies</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>3</Text><Text style={styles.statLabel}>Active</Text></View>
        <View style={styles.stat}><Text style={styles.statValue}>165</Text><Text style={styles.statLabel}>kWh/day</Text></View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Policies</Text>
        {policies.map(p => (
          <View key={p.name} style={styles.policyCard}>
            <View style={styles.policyHeader}>
              <Text style={styles.policyName}>{p.name}</Text>
              <View style={[styles.statusDot, { backgroundColor: p.enabled ? "#10b981" : "#6b7280" }]} />
            </View>
            <View style={styles.policyDetails}>
              <Text style={styles.detailText}>{p.action} · {p.schedule}</Text>
              <Text style={styles.savingsText}>{p.savings}</Text>
            </View>
            <View style={styles.tags}>
              <View style={styles.tag}><Text style={styles.tagText}>{p.scope}</Text></View>
            </View>
          </View>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Effectiveness</Text>
        {effectiveness.map(e => (
          <View key={e.policy} style={styles.effRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.effName}>{e.policy}</Text>
              <Text style={styles.effSaved}>{e.saved}</Text>
            </View>
            <View style={{ alignItems: "flex-end" }}>
              <Text style={styles.effPct}>{e.compliance}%</Text>
              <View style={styles.progressBg}>
                <View style={[styles.progressFill, { width: `${e.compliance}%` }]} />
              </View>
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
  policyCard: { backgroundColor: "#0f172a", borderRadius: 8, padding: 12, marginBottom: 8 },
  policyHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  policyName: { fontSize: 14, fontWeight: "600", color: "#f8fafc" },
  statusDot: { width: 10, height: 10, borderRadius: 5 },
  policyDetails: { marginTop: 4 },
  detailText: { fontSize: 12, color: "#94a3b8" },
  savingsText: { fontSize: 12, color: "#10b981", marginTop: 2 },
  tags: { flexDirection: "row", marginTop: 6, gap: 4 },
  tag: { backgroundColor: "#334155", paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  tagText: { fontSize: 10, color: "#94a3b8" },
  effRow: { flexDirection: "row", alignItems: "center", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#334155" },
  effName: { fontSize: 14, color: "#f8fafc" },
  effSaved: { fontSize: 12, color: "#10b981", marginTop: 2 },
  effPct: { fontSize: 14, fontWeight: "bold", color: "#f8fafc" },
  progressBg: { width: 60, height: 6, backgroundColor: "#334155", borderRadius: 3, marginTop: 4, overflow: "hidden" },
  progressFill: { height: 6, backgroundColor: "#10b981", borderRadius: 3 },
});
