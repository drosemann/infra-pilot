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
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../src/theme';
import { BackupJob, BackupStatusEntry } from '../src/types';
import { endpoints } from '../src/api/endpoints';
import { LoadingState } from '../src/components/LoadingState';
import { EmptyState } from '../src/components/EmptyState';
import { StatusBadge } from '../src/components/StatusBadge';
import { formatDate, formatBytes, timeAgo } from '../src/utils/formatting';

export default function BackupsScreen() {
  const [jobs, setJobs] = useState<BackupJob[]>([]);
  const [statuses, setStatuses] = useState<Record<string, BackupStatusEntry[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await endpoints.backups.list();
      setJobs(data);

      const statusMap: Record<string, BackupStatusEntry[]> = {};
      await Promise.all(
        data.map(async (job) => {
          try {
            statusMap[job.id] = await endpoints.backups.status(job.id);
          } catch { /* ignore */ }
        })
      );
      setStatuses(statusMap);
    } catch (e: any) {
      Alert.alert('Error', e?.message || 'Failed to load backups');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  if (isLoading && !refreshing) {
    return <LoadingState message="Loading backups..." />;
  }

  if (jobs.length === 0) {
    return (
      <View style={styles.container}>
        <EmptyState
          icon="cloud-upload-outline"
          title="No Backup Jobs"
          subtitle="Create a backup job to automatically back up your servers"
        />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
    >
      {jobs.map((job) => {
        const jobStatuses = statuses[job.id] || [];
        const latest = jobStatuses[0];

        return (
          <View key={job.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <View>
                <Text style={styles.jobName}>{job.name}</Text>
                <Text style={styles.schedule}>
                  {job.schedule_type.charAt(0).toUpperCase() + job.schedule_type.slice(1)}
                </Text>
              </View>
              <StatusBadge status={job.status} />
            </View>

            <View style={styles.details}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Retention</Text>
                <Text style={styles.detailValue}>{job.retention_count} backups</Text>
              </View>
              {job.last_run && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Last Run</Text>
                  <Text style={styles.detailValue}>{timeAgo(job.last_run)}</Text>
                </View>
              )}
              {job.next_run && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Next Run</Text>
                  <Text style={styles.detailValue}>{formatDate(job.next_run)}</Text>
                </View>
              )}
            </View>

            {latest && (
              <View style={styles.latestStatus}>
                <Text style={styles.statusTitle}>Latest Backup</Text>
                <View style={styles.statusRow}>
                  <StatusBadge status={latest.status} />
                  {latest.size_mb > 0 && (
                    <Text style={styles.size}>{formatBytes(latest.size_mb)}</Text>
                  )}
                </View>
                {latest.completed_at && (
                  <Text style={styles.statusDate}>{formatDate(latest.completed_at)}</Text>
                )}
                {latest.error_message && (
                  <Text style={styles.errorMsg}>{latest.error_message}</Text>
                )}
              </View>
            )}
          </View>
        );
      })}
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
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: theme.spacing.sm,
  },
  jobName: {
    fontSize: theme.fontSize.md,
    fontWeight: '700',
    color: theme.colors.text,
  },
  schedule: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  details: {
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
    paddingTop: theme.spacing.sm,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  detailValue: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
    fontWeight: '500',
  },
  latestStatus: {
    marginTop: theme.spacing.sm,
    paddingTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  statusTitle: {
    fontSize: theme.fontSize.xs,
    fontWeight: '600',
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  size: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.text,
    fontWeight: '500',
  },
  statusDate: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  errorMsg: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.danger,
    marginTop: 4,
  },
});
