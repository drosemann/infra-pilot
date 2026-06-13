import { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { theme } from '../../src/theme';
import { LoadingState } from '../../src/components/LoadingState';
import { MetricGauge } from '../../src/components/MetricGauge';
import { StatusBadge } from '../../src/components/StatusBadge';
import { useServers } from '../../src/hooks/useServers';
import { endpoints } from '../../src/api/endpoints';
import { useAuth } from '../../src/hooks/useAuth';

export default function DashboardScreen() {
  const { servers, isLoading, isOffline, refetch } = useServers();
  const { state } = useAuth();
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, []);

  async function loadMetrics() {
    try {
      const data = await endpoints.metrics.aggregated();
      setMetrics(data);
    } catch {
      // silently fail
    }
  }

  async function onRefresh() {
    setRefreshing(true);
    await refetch();
    await loadMetrics();
    setRefreshing(false);
  }

  if (isLoading && !refreshing) {
    return <LoadingState message="Loading dashboard..." />;
  }

  const runningCount = servers.filter((s) => s.status === 'running').length;
  const stoppedCount = servers.filter((s) => s.status === 'stopped').length;
  const errorCount = servers.filter((s) => s.status === 'error').length;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
    >
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Ionicons name="cloud-offline-outline" size={16} color={theme.colors.warning} />
          <Text style={styles.offlineText}>Showing cached data</Text>
        </View>
      )}

      <View style={styles.welcomeRow}>
        <Text style={styles.greeting}>
          Hello, {state.user?.display_name || 'User'}
        </Text>
        <Text style={styles.serverCount}>
          {servers.length} server{servers.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <View style={styles.statsRow}>
        <View style={[styles.statCard, { borderLeftColor: theme.colors.success }]}>
          <Text style={styles.statNumber}>{runningCount}</Text>
          <Text style={styles.statLabel}>Running</Text>
        </View>
        <View style={[styles.statCard, { borderLeftColor: theme.colors.textSecondary }]}>
          <Text style={styles.statNumber}>{stoppedCount}</Text>
          <Text style={styles.statLabel}>Stopped</Text>
        </View>
        <View style={[styles.statCard, { borderLeftColor: theme.colors.danger }]}>
          <Text style={styles.statNumber}>{errorCount}</Text>
          <Text style={styles.statLabel}>Errors</Text>
        </View>
      </View>

      {metrics && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Metrics</Text>
          <View style={styles.metricsCard}>
            <MetricGauge
              label="CPU Usage"
              value={metrics.cpu_percent || 0}
              max={100}
              color={theme.colors.accent}
            />
            <MetricGauge
              label="Memory"
              value={metrics.memory_percent || 0}
              max={100}
              color={theme.colors.secondary}
            />
          </View>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActions}>
          <View
            style={styles.actionCard}
            onTouchEnd={() => router.push('/backups')}
          >
            <Ionicons name="cloud-upload-outline" size={24} color={theme.colors.primary} />
            <Text style={styles.actionLabel}>Backups</Text>
          </View>
          <View
            style={styles.actionCard}
            onTouchEnd={() => router.push('/billing')}
          >
            <Ionicons name="wallet-outline" size={24} color={theme.colors.secondary} />
            <Text style={styles.actionLabel}>Billing</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Servers</Text>
        {servers.slice(0, 5).map((server) => (
          <View
            key={server.id}
            style={styles.serverRow}
            onTouchEnd={() => router.push(`/server/${server.id}`)}
          >
            <View style={styles.serverInfo}>
              <Text style={styles.serverName}>{server.name}</Text>
              <Text style={styles.serverImage}>{server.image}</Text>
            </View>
            <StatusBadge status={server.status} />
          </View>
        ))}
        {servers.length === 0 && (
          <Text style={styles.emptyText}>No servers found</Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: theme.spacing.md,
    paddingBottom: 32,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.warning + '20',
    borderRadius: theme.borderRadius.sm,
    padding: theme.spacing.sm,
    marginBottom: theme.spacing.md,
    gap: 6,
  },
  offlineText: {
    color: theme.colors.warning,
    fontSize: theme.fontSize.sm,
    fontWeight: '600',
  },
  welcomeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  greeting: {
    fontSize: theme.fontSize.xl,
    fontWeight: '700',
    color: theme.colors.text,
  },
  serverCount: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  statsRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.lg,
  },
  statCard: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    borderLeftWidth: 3,
    padding: theme.spacing.md,
  },
  statNumber: {
    fontSize: theme.fontSize.xl,
    fontWeight: '800',
    color: theme.colors.text,
  },
  statLabel: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  section: {
    marginBottom: theme.spacing.lg,
  },
  sectionTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  metricsCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  quickActions: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  actionCard: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  actionLabel: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
    fontWeight: '600',
  },
  serverRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.xs,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  serverInfo: {
    flex: 1,
    marginRight: theme.spacing.sm,
  },
  serverName: {
    fontSize: theme.fontSize.md,
    fontWeight: '600',
    color: theme.colors.text,
  },
  serverImage: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  emptyText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    paddingVertical: theme.spacing.lg,
  },
});
