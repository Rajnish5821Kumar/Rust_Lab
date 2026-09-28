import type { SystemStatus } from '../hooks/useSystemStatus.ts';
import { StatusBadge } from './StatusBadge.tsx';

interface Props {
  status: SystemStatus;
  onRefresh: () => void;
}

const CHECK_LABELS: Record<string, string> = {
  database: 'PostgreSQL',
  redis: 'Redis',
};

export function SystemStatusCard({ status, onRefresh }: Props) {
  return (
    <section
      aria-labelledby="system-status-heading"
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="system-status-heading" className="text-sm font-semibold text-slate-900">
            System status
          </h2>
          <p className="mt-1 text-sm text-slate-500">Live connection to the DevVault API.</p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={status.state === 'loading'}
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <dl className="mt-5 divide-y divide-slate-100 text-sm">
        <Row label="API">
          {status.state === 'loading' && <StatusBadge tone="pending" label="Checking…" />}
          {status.state === 'error' && <StatusBadge tone="error" label="Unreachable" />}
          {status.state === 'ready' && (
            <StatusBadge tone="ok" label={`${status.health.service}: ${status.health.status}`} />
          )}
        </Row>
        {status.state === 'ready' &&
          (status.readiness ? (
            Object.entries(status.readiness.checks).map(([name, result]) => (
              <Row key={name} label={CHECK_LABELS[name] ?? name}>
                <StatusBadge
                  tone={result === 'ok' ? 'ok' : 'error'}
                  label={result === 'ok' ? 'Connected' : 'Unavailable'}
                />
              </Row>
            ))
          ) : (
            <Row label="Dependencies">
              <StatusBadge tone="error" label="Readiness unknown" />
            </Row>
          ))}
      </dl>

      {status.state === 'error' && (
        <p role="alert" className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">
          {status.message}. Is the API running on port 8000?
        </p>
      )}
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <dt className="text-slate-600">{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
