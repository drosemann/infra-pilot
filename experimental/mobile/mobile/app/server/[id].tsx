import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../src/theme';
import { Server, ServerMetric } from '../../src/types';
import { endpoints } from '../../src/api/endpoints';
import { LoadingState } from '../../src/components/LoadingState';
import { MetricGauge } from '../../src/components/MetricGauge';
import { StatusBadge } from '../../src/components/StatusBadge';
import { formatDate, formatBytes, formatUptime } from '../../src/utils/formatting';

export default function ServerDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [server, setServer] = useState<Server | null>(null);
  const [metrics, setMetrics] = useState<ServerMetric | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const [serverData, metricsData] = await Promise.all([
        endpoints.servers.get(id),
        endpoints.metrics.get(id, '5m'),
      ]);
      setServer(serverData);
      if (metricsData.length > 0) {
        setMetrics(metricsData[metricsData.length - 1]);
      }
    } catch (e: any) {
      Alert.alert('Error', e?.message || 'Failed to load server');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  async function handleAction(action: 'start' | 'stop' | 'restart') {
    if (!id) return;
    try {
      const updated = await endpoints.servers[action](id);
      setServer(updated);
    } catch (e: any) {
      Alert.alert('Error', e?.message || `Failed to ${action} server`);
    }
  }

  if (isLoading && !server) {
    return <LoadingState message="Loading server details..." />;
  }

  if (!server) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Server not found</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
    >
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <StatusBadge status={server.status} />
          {server.started_at && (
            <Text style={styles.uptime}>
              Up {formatUptime(server.started_at)}
            </Text>
          )}
        </View>
        <Text style={styles.image}>{server.image}</Text>
        <Text style={styles.created}>Created {formatDate(server.created_at)}</Text>

        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionBtn, { backgroundColor: theme.colors.success + '20' }]}
            onPress={() => handleAction('start')}
          >
            <Ionicons name="play" size={18} color={theme.colors.success} />
            <Text style={[styles.actionBtnText, { color: theme.colors.success }]}>Start</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionBtn, { backgroundColor: theme.colors.danger + '20' }]}
            onPress={() => handleAction('stop')}
          >
            <Ionicons name="stop" size={18} color={theme.colors.danger} />
            <Text style={[styles.actionBtnText, { color: theme.colors.danger }]}>Stop</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionBtn, { backgroundColor: theme.colors.warning + '20' }]}
            onPress={() => handleAction('restart')}
          >
            <Ionicons name="refresh" size={18} color={theme.colors.warning} />
            <Text style={[styles.actionBtnText, { color: theme.colors.warning }]}>Restart</Text>
          </TouchableOpacity>
        </View>
      </View>

      {metrics && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Resource Usage</Text>
          <MetricGauge
            label="CPU"
            value={metrics.cpu_percent}
            max={100}
            color={theme.colors.accent}
          />
          <MetricGauge
            label="Memory"
            value={(metrics.memory_used_mb / metrics.memory_total_mb) * 100}
            max={100}
            color={theme.colors.secondary}
          />
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>RAM</Text>
            <Text style={styles.metricValue}>
              {formatBytes(metrics.memory_used_mb)} / {formatBytes(metrics.memory_total_mb)}
            </Text>
          </View>
          {metrics.tps != null && (
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>TPS</Text>
              <Text style={styles.metricValue}>{metrics.tps.toFixed(1)}</Text>
            </View>
          )}
        </View>
      )}

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Configuration</Text>
        <View style={styles.configRow}>
          <Text style={styles.configLabel}>CPU Shares</Text>
          <Text style={styles.configValue}>{server.cpu_shares || 'Default'}</Text>
        </View>
        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Memory Limit</Text>
          <Text style={styles.configValue}>{server.memory_limit || 'Default'}</Text>
        </View>
        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Restart Policy</Text>
          <Text style={styles.configValue}>{server.restart_policy || 'none'}</Text>
        </View>
        {server.javaVersion && (
          <View style={styles.configRow}>
            <Text style={styles.configLabel}>Java Version</Text>
            <Text style={styles.configValue}>{server.javaVersion}</Text>
          </View>
        )}
      </View>

      <View style={styles.navSection}>
        <TouchableOpacity
          style={styles.navRow}
          onPress={() => router.push(`/server/${id}/logs`)}
        >
          <View style={styles.navLeft}>
            <Ionicons name="document-text-outline" size={20} color={theme.colors.accent} />
            <Text style={styles.navLabel}>Live Logs</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={theme.colors.textSecondary} />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.navRow}
          onPress={() => router.push(`/server/${id}/terminal`)}
        >
          <View style={styles.navLeft}>
            <Ionicons name="terminal-outline" size={20} color={theme.colors.secondary} />
            <Text style={styles.navLabel}>Terminal</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={theme.colors.textSecondary} />
        </TouchableOpacity>
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
  errorText: {
    fontSize: theme.fontSize.md,
    color: theme.colors.danger,
    textAlign: 'center',
    marginTop: theme.spacing.xl,
  },
  header: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  uptime: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.success,
    fontWeight: '600',
  },
  image: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  created: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  actionRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.borderRadius.sm,
    gap: 6,
  },
  actionBtnText: {
    fontSize: theme.fontSize.sm,
    fontWeight: '700',
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  cardTitle: {
    fontSize: theme.fontSize.md,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.sm,
    paddingTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  metricLabel: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  metricValue: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
    fontWeight: '600',
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  configLabel: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  configValue: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
    fontWeight: '600',
  },
  navSection: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    overflow: 'hidden',
  },
  navRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  navLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  navLabel: {
    fontSize: theme.fontSize.md,
    color: theme.colors.text,
  },
});
