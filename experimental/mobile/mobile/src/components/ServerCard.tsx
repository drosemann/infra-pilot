import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Server } from '../types';
import { theme } from '../theme';
import { StatusBadge } from './StatusBadge';
import { formatDate } from '../utils/formatting';

interface Props {
  server: Server;
  onPress: (server: Server) => void;
}

export function ServerCard({ server, onPress }: Props) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => onPress(server)}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Ionicons name="server-outline" size={22} color={theme.colors.primary} />
        </View>
        <View style={styles.info}>
          <Text style={styles.name} numberOfLines={1}>
            {server.name}
          </Text>
          <Text style={styles.image} numberOfLines={1}>
            {server.image}
          </Text>
        </View>
        <StatusBadge status={server.status} />
      </View>

      <View style={styles.details}>
        <View style={styles.detailItem}>
          <Ionicons name="cube-outline" size={14} color={theme.colors.textSecondary} />
          <Text style={styles.detailText}>
            {server.cpu_shares || 0} CPU
          </Text>
        </View>
        <View style={styles.detailItem}>
          <Ionicons name="hardware-chip-outline" size={14} color={theme.colors.textSecondary} />
          <Text style={styles.detailText}>
            {server.memory_limit || '512M'}
          </Text>
        </View>
        <View style={styles.detailItem}>
          <Ionicons name="time-outline" size={14} color={theme.colors.textSecondary} />
          <Text style={styles.detailText}>
            {formatDate(server.created_at)}
          </Text>
        </View>
      </View>

      <View style={styles.actions}>
        <Ionicons name="play" size={18} color={theme.colors.success} />
        <Ionicons name="stop" size={18} color={theme.colors.danger} style={styles.actionIcon} />
        <Ionicons name="refresh" size={18} color={theme.colors.warning} style={styles.actionIcon} />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: theme.colors.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.spacing.sm,
  },
  info: {
    flex: 1,
    marginRight: theme.spacing.sm,
  },
  name: {
    fontSize: theme.fontSize.md,
    fontWeight: '700',
    color: theme.colors.text,
  },
  image: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  details: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.xs,
    paddingTop: theme.spacing.xs,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailText: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    marginLeft: 4,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: theme.spacing.sm,
    paddingTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  actionIcon: {
    marginLeft: theme.spacing.md,
  },
});
