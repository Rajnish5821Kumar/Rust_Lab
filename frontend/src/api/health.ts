import { getJson, type RequestOptions } from './client.ts';

export type CheckStatus = 'ok' | 'error';

export interface HealthResponse {
  status: 'ok';
  service: string;
}

export interface ReadinessResponse {
  status: CheckStatus;
  checks: Record<string, CheckStatus>;
}

export function fetchHealth(options?: RequestOptions): Promise<HealthResponse> {
  return getJson<HealthResponse>('/api/health', options);
}

export function fetchReadiness(options?: RequestOptions): Promise<ReadinessResponse> {
  // 503 carries a normal readiness body listing which dependency is down.
  return getJson<ReadinessResponse>('/api/health/ready', { ...options, acceptStatuses: [503] });
}
