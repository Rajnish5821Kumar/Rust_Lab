import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App.tsx';
import { mockFetch } from './test/fetchMock.ts';

const HEALTHY = {
  '/api/health': { status: 200, body: { status: 'ok', service: 'devvault' } },
  '/api/health/ready': {
    status: 200,
    body: { status: 'ok', checks: { database: 'ok', redis: 'ok' } },
  },
};

afterEach(() => {
  vi.unstubAllGlobals();
});

function statusCard() {
  return within(screen.getByRole('region', { name: 'System status' }));
}

describe('App dashboard', () => {
  it('shows a live API and connected dependencies', async () => {
    mockFetch(HEALTHY);

    render(<App />);

    expect(await statusCard().findByText('devvault: ok')).toBeInTheDocument();
    expect(statusCard().getByText('PostgreSQL')).toBeInTheDocument();
    expect(statusCard().getAllByText('Connected')).toHaveLength(2);
  });

  it('flags an unavailable dependency reported by readiness', async () => {
    mockFetch({
      ...HEALTHY,
      '/api/health/ready': {
        status: 503,
        body: { status: 'error', checks: { database: 'ok', redis: 'error' } },
      },
    });

    render(<App />);

    expect(await statusCard().findByText('Unavailable')).toBeInTheDocument();
    expect(statusCard().getByText('Connected')).toBeInTheDocument();
  });

  it('shows an error when the API is unreachable', async () => {
    mockFetch({ '/api/health': new TypeError('Failed to fetch') });

    render(<App />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the DevVault API');
    expect(statusCard().getByText('Unreachable')).toBeInTheDocument();
  });

  it('re-fetches status when Refresh is clicked', async () => {
    const fetchMock = mockFetch(HEALTHY);
    render(<App />);
    await statusCard().findByText('devvault: ok');
    const callsBefore = fetchMock.mock.calls.length;

    await userEvent.click(statusCard().getByRole('button', { name: 'Refresh' }));

    await statusCard().findByText('devvault: ok');
    expect(fetchMock.mock.calls.length).toBe(callsBefore + 2);
  });
});
