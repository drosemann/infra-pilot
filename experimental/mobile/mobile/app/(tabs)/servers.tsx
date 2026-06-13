import { ScrollView, StyleSheet, RefreshControl, View, Text } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../src/theme';
import { useServers } from '../../src/hooks/useServers';
import { ServerCard } from '../../src/components/ServerCard';
import { LoadingState } from '../../src/components/LoadingState';
import { EmptyState } from '../../src/components/EmptyState';
import { Server } from '../../src/types';

export default function ServersScreen() {
  const { servers, isLoading, isOffline, error, refetch } = useServers();
  const router = useRouter();

  if (isLoading && servers.length === 0) {
    return <LoadingState message="Loading servers..." />;
  }

  if (error) {
    return (
      <View style={styles.container}>
        <EmptyState
          icon="alert-circle-outline"
          title="Failed to load servers"
          subtitle={error}
        />
      </View>
    );
  }

  if (servers.length === 0) {
    return (
      <View style={styles.container}>
        <EmptyState
          icon="server-outline"
          title="No Servers"
          subtitle="Create your first server to get started"
        />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={false}
          onRefresh={refetch}
          tintColor={theme.colors.primary}
        />
      }
    >
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>Showing cached data</Text>
        </View>
      )}
      {servers.map((server: Server) => (
        <ServerCard
          key={server.id}
          server={server}
          onPress={(s) => router.push(`/server/${s.id}`)}
        />
      ))}
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
    alignItems: 'center',
    padding: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
    backgroundColor: theme.colors.warning + '20',
    borderRadius: theme.borderRadius.sm,
  },
  offlineText: {
    color: theme.colors.warning,
    fontSize: theme.fontSize.sm,
    fontWeight: '600',
  },
});
