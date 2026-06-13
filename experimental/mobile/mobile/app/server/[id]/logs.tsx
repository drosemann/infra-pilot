import { useState, useEffect, useCallback } from 'react';
import { View, StyleSheet, useWindowDimensions } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { theme } from '../../../src/theme';
import { LogEntry } from '../../../src/types';
import { endpoints } from '../../../src/api/endpoints';
import { LogViewer } from '../../../src/components/LogViewer';
import { LoadingState } from '../../../src/components/LoadingState';

export default function ServerLogsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { width } = useWindowDimensions();

  const loadLogs = useCallback(async () => {
    if (!id) return;
    try {
      const data = await endpoints.logs.get(id, 200, 0);
      setLogs(data);
    } catch {
      // silent
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  // Polling for live logs
  useEffect(() => {
    const interval = setInterval(loadLogs, 5000);
    return () => clearInterval(interval);
  }, [loadLogs]);

  if (isLoading) {
    return <LoadingState message="Loading logs..." />;
  }

  return (
    <View style={[styles.container, { width }]}>
      <LogViewer logs={logs} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    padding: theme.spacing.sm,
  },
});
