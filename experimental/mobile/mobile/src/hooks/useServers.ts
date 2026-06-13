import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Server } from '../types';
import { endpoints } from '../api/endpoints';

const CACHE_KEY = 'cached_servers';

export function useServers() {
  const [servers, setServers] = useState<Server[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  const loadCached = useCallback(async () => {
    try {
      const cached = await AsyncStorage.getItem(CACHE_KEY);
      if (cached) {
        setServers(JSON.parse(cached));
        setIsOffline(true);
      }
    } catch {
      // ignore cache errors
    }
  }, []);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setIsOffline(false);
    try {
      const data = await endpoints.servers.list();
      setServers(data);
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (e: any) {
      if (e?.message?.includes('Network') || e?.code === 'ERR_NETWORK') {
        await loadCached();
      } else {
        setError(e?.message || 'Failed to load servers');
      }
    } finally {
      setIsLoading(false);
    }
  }, [loadCached]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const getServer = useCallback(
    (id: string) => servers.find((s) => s.id === id) || null,
    [servers]
  );

  return { servers, isLoading, error, isOffline, refetch: fetch, getServer };
}
