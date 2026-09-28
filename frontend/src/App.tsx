import { Layout } from './components/Layout.tsx';
import { SystemStatusCard } from './components/SystemStatusCard.tsx';
import { useSystemStatus } from './hooks/useSystemStatus.ts';

export default function App() {
  const { status, refresh } = useSystemStatus();

  return (
    <Layout>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <SystemStatusCard status={status} onRefresh={refresh} />
        </div>
        <section className="rounded-xl border border-dashed border-slate-300 bg-white/50 p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-900">Repository analytics</h2>
          <p className="mt-2 text-sm text-slate-500">
            Commit, contributor, pull request, CI and security metrics will appear here once
            projects and repositories can be connected.
          </p>
        </section>
      </div>
    </Layout>
  );
}
