import { afterEach, describe, expect, it, vi } from 'vitest';
import { mockFetch } from '../test/fetchMock.ts';
import { ApiError, getJson } from './client.ts';
import { fetchReadiness } from './health.ts';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('getJson', () => {
  it('returns the parsed body for a successful response', async () => {
    mockFetch({ '/api/health': { status: 200, body: { status: 'ok', service: 'devvault' } } });

    await expect(getJson('/api/health')).resolves.toEqual({ status: 'ok', service: 'devvault' });
  });

  it('turns the API error envelope into an ApiError', async () => {
    mockFetch({
      '/api/users/me': {
        status: 401,
        body: { error: { code: 'authentication_failed', message: 'Not authenticated' } },
      },
    });

    const error = await getJson('/api/users/me').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 401,
      code: 'authentication_failed',
      message: 'Not authenticated',
      requestId: 'test-request-id',
    });
  });

  it('reports network failures as network_error', async () => {
    mockFetch({ '/api/health': new TypeError('Failed to fetch') });

    await expect(getJson('/api/health')).rejects.toMatchObject({
      status: 0,
      code: 'network_error',
    });
  });

  it('handles non-JSON error bodies', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('<html>Bad gateway</html>', { status: 502 })),
    );

    await expect(getJson('/api/health')).rejects.toMatchObject({
      status: 502,
      code: 'http_error',
    });
  });
});

describe('fetchReadiness', () => {
  it('treats 503 as a readiness result, not an exception', async () => {
    const body = { status: 'error', checks: { database: 'ok', redis: 'error' } };
    mockFetch({ '/api/health/ready': { status: 503, body } });

    await expect(fetchReadiness()).resolves.toEqual(body);
  });
});
