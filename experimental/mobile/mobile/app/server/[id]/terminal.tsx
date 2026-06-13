import { useState, useCallback } from 'react';
import { View, StyleSheet, useWindowDimensions } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { theme } from '../../../src/theme';
import { Terminal } from '../../../src/components/Terminal';
import { useWebSocket } from '../../../src/hooks/useWebSocket';

export default function ServerTerminalScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [lines, setLines] = useState<string[]>([
    'Welcome to Infra Pilot Terminal',
    'Type a command to execute on the server',
    '---',
  ]);
  const { width } = useWindowDimensions();

  const { isConnected, send } = useWebSocket({
    onMessage: (data) => {
      if (data.type === 'terminal' && data.line) {
        setLines((prev) => [...prev, data.line]);
      }
    },
  });

  const handleCommand = useCallback(
    (command: string) => {
      setLines((prev) => [...prev, `$ ${command}`]);
      send({ type: 'terminal', command, serverId: id });
    },
    [id, send]
  );

  return (
    <View style={[styles.container, { width }]}>
      <Terminal
        lines={lines}
        onCommand={handleCommand}
        isConnected={isConnected}
      />
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
