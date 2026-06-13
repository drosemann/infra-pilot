import { View, Text, StyleSheet } from 'react-native';
import { theme } from '../theme';

type Status = 'running' | 'stopped' | 'restarting' | 'error' | 'success' | 'failed' | 'active' | 'paused' | 'pending';

const statusColors: Record<string, string> = {
  running: theme.colors.success,
  stopped: theme.colors.textSecondary,
  restarting: theme.colors.warning,
  error: theme.colors.danger,
  success: theme.colors.success,
  failed: theme.colors.danger,
  active: theme.colors.success,
  paused: theme.colors.warning,
  pending: theme.colors.info,
};

interface Props {
  status: Status;
  label?: string;
}

export function StatusBadge({ status, label }: Props) {
  const color = statusColors[status] || theme.colors.textSecondary;
  return (
    <View style={[styles.badge, { backgroundColor: color + '20', borderColor: color }]}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={[styles.text, { color }]}>
        {label || status.charAt(0).toUpperCase() + status.slice(1)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  text: {
    fontSize: 13,
    fontWeight: '600',
  },
});
