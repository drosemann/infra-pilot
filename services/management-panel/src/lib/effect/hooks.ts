import { useEffect, useState, useCallback } from 'react';
import type { Stream as StreamType } from 'effect';
import { Effect, Stream } from 'effect';

export interface EffectState<A, E> {
  data: A | null;
  error: E | null;
  loading: boolean;
}

/**
 * Runs an Effect on mount and when dependencies change, storing its result or
 * promise rejection in state. Cleanup suppresses updates from that automatic
 * run without interrupting the underlying Effect.
 *
 * @param effect - Factory invoked for each automatic run or manual refresh.
 * @param deps - React dependencies that trigger a new run; defaults to mount only.
 * @returns Data, error, loading state, and a refresh function that starts a new run.
 */
export function useEffectful<A, E>(
  effect: () => Effect.Effect<A, E, never>,
  deps: any[] = []
): EffectState<A, E> & { refresh: () => void } {
  const [state, setState] = useState<EffectState<A, E>>({
    data: null,
    error: null,
    loading: true,
  });

  const run = useCallback(() => {
    let cancelled = false;
    setState(s => ({ ...s, loading: true }));

    // NOTE: Effect.runCallback only supports `onExit` in the installed
    // Effect version, so use runPromise to reliably settle the state.
    Effect.runPromise(effect()).then(
      (data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      },
      (error) => {
        if (!cancelled) setState({ data: null, error: error as E, loading: false });
      },
    );

    return () => {
      cancelled = true;
    };
  }, deps);

  useEffect(() => {
    const cancel = run();
    return () => cancel?.();
  }, [run]);

  return { ...state, refresh: run };
}

export function useMutation<A, E, P extends any[] = []>(
  effectFactory: (...args: P) => Effect.Effect<A, E, never>
): {
  execute: (...args: P) => Promise<A>;
  state: EffectState<A, E>;
  reset: () => void;
} {
  const [state, setState] = useState<EffectState<A, E>>({
    data: null,
    error: null,
    loading: false,
  });

  const execute = useCallback(async (...args: P): Promise<A> => {
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const result = await Effect.runPromise(effectFactory(...args));
      setState({ data: result, error: null, loading: false });
      return result;
    } catch (error) {
      setState({ data: null, error: error as E, loading: false });
      throw error;
    }
  }, [effectFactory]);

  const reset = useCallback(() => {
    setState({ data: null, error: null, loading: false });
  }, []);

  return { execute, state, reset };
}

/**
 * Collects stream emissions in order, resetting data and errors on each run.
 * Completion or promise rejection clears the running state. Cleanup suppresses
 * further state updates without interrupting the underlying subscription.
 *
 * @param streamFactory - Creates the stream on mount and when dependencies change.
 * @param deps - React dependencies that restart collection; defaults to mount only.
 * @returns Collected data, any rejection, and matching loading and running flags.
 */
export function useEffectStream<A, E>(
  streamFactory: () => StreamType.Stream<A, E, never>,
  deps: any[] = []
): { data: A[]; error: E | null; loading: boolean; running: boolean } {
  const [data, setData] = useState<A[]>([]);
  const [error, setError] = useState<E | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData([]);
    setError(null);
    setRunning(true);

    const subscription = Stream.runForEach(streamFactory(), (item) =>
      Effect.sync(() => {
        if (!cancelled) setData(prev => [...prev, item]);
      })
    );

    Effect.runPromise(subscription).then(
      () => { if (!cancelled) setRunning(false); },
      (e) => { if (!cancelled) { setError(e as E); setRunning(false); } },
    );

    return () => { cancelled = true; };
  }, deps);

  return { data, error, loading: running, running };
}

export const useAsyncEffect = useEffectful;
