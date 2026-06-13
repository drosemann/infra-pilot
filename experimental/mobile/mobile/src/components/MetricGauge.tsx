import { View, Text, StyleSheet } from 'react-native';
import { theme } from '../theme';

interface Props {
  label: string;
  value: number;
  max: number;
  unit?: string;
  color?: string;
}

export function MetricGauge({ label, value, max, unit = '%', color }: Props) {
  const percent = Math.min((value / max) * 100, 100);
  const gaugeColor = color || (percent > 80 ? theme.colors.danger : percent > 60 ? theme.colors.warning : theme.colors.success);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        <Text style={[styles.value, { color: gaugeColor }]}>
          {Math.round(value)}{unit}
        </Text>
      </View>
      <View style={styles.track}>
        <View
          style={[
            styles.fill,
            { width: `${percent}%`, backgroundColor: gaugeColor },
          ]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: theme.spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  label: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    fontWeight: '500',
  },
  value: {
    fontSize: theme.fontSize.sm,
    fontWeight: '700',
  },
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.colors.border,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    borderRadius: 4,
  },
});
