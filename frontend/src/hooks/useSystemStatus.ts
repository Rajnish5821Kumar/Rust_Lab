import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '../api/client.ts';
import {
  fetchHealth,
  fetchReadiness,
  type HealthResponse,
  type ReadinessResponse,
} from '../api/health.ts';

export type SystemStatus =
  | { state: 'loading' }
  | { state: 'error'; message: string }
  | { state: 'ready'; health: HealthResponse; readiness: ReadinessResponse | null };

/** Loads API liveness and readiness. Readiness failing does not hide a live API. */
export function useSystemStatus(): { status: SystemStatus; refresh: () => void } {
  const [status, setStatus] = useState<SystemStatus>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    async function load(): Promise<void> {
      try {
        const health = await fetchHealth({ signal });
        const readiness = await fetchReadiness({ signal }).catch((error: unknown) => {
          if (signal.aborted) throw error;
          return null;
        });
        setStatus({ state: 'ready', health, readiness });
      } catch (error) {
        if (signal.aborted) return;
        const message = error instanceof ApiError ? error.message : 'Unexpected error';
        setStatus({ state: 'error', message });
      }
    }

    void load();
    return () => controller.abort();
  }, [attempt]);

  const refresh = useCallback(() => {
    setStatus({ state: 'loading' });
    setAttempt((n) => n + 1);
  }, []);

  return { status, refresh };
}
