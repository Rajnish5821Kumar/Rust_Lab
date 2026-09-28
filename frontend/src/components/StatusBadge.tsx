type Tone = 'ok' | 'error' | 'pending';

const STYLES: Record<Tone, string> = {
  ok: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  error: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  pending: 'bg-slate-100 text-slate-600 ring-slate-500/20',
};

const DOT: Record<Tone, string> = {
  ok: 'bg-emerald-500',
  error: 'bg-rose-500',
  pending: 'bg-slate-400',
};

export function StatusBadge({ tone, label }: { tone: Tone; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[tone]}`}
    >
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${DOT[tone]}`} />
      {label}
    </span>
  );
}
