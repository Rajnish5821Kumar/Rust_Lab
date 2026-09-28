import { vi } from 'vitest';

type Route = { status: number; body: unknown } | Error;

/** Stub global fetch with fixed responses keyed by request path. */
export function mockFetch(routes: Record<string, Route>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString();
    const path = new URL(url, 'http://localhost').pathname;
    const route = routes[path];
    if (!route) throw new Error(`Unexpected fetch to ${path}`);
    if (route instanceof Error) throw route;
    return new Response(JSON.stringify(route.body), {
      status: route.status,
      headers: { 'Content-Type': 'application/json', 'X-Request-ID': 'test-request-id' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}
