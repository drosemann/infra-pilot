import { useRef, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, Platform } from 'react-native';
import { theme } from '../theme';
import { LogEntry } from '../types';

interface Props {
  logs: LogEntry[];
  filter?: 'info' | 'warn' | 'error';
}

const logColors: Record<string, string> = {
  info: theme.colors.text,
  warn: theme.colors.warning,
  error: theme.colors.danger,
  debug: theme.colors.textSecondary,
};

export function LogViewer({ logs, filter }: Props) {
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollToEnd({ animated: true });
    }
  }, [logs]);

  const filtered = filter ? logs.filter((l) => l.level === filter) : logs;

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.content}
      >
        {filtered.map((entry, i) => (
          <View key={i} style={styles.line}>
            <Text style={styles.timestamp}>{entry.timestamp}</Text>
            <Text style={[styles.level, { color: logColors[entry.level] || theme.colors.text }]}>
              [{entry.level.toUpperCase()}]
            </Text>
            <Text style={styles.message} selectable>
              {entry.message}
            </Text>
          </View>
        ))}
        {filtered.length === 0 && (
          <Text style={styles.empty}>No log entries</Text>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
    borderRadius: theme.borderRadius.md,
    overflow: 'hidden',
  },
  scroll: {
    flex: 1,
    padding: theme.spacing.sm,
  },
  content: {
    paddingBottom: theme.spacing.sm,
  },
  line: {
    flexDirection: 'row',
    marginBottom: 2,
  },
  timestamp: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginRight: 8,
  },
  level: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 11,
    fontWeight: '700',
    marginRight: 8,
    width: 50,
  },
  message: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 11,
    color: theme.colors.text,
    flex: 1,
  },
  empty: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 12,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    paddingVertical: theme.spacing.lg,
  },
});
