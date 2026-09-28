import type { ReactNode } from 'react';

// Sections are listed so the navigation shape is visible, but only the overview exists yet.
const NAV_ITEMS = [
  { label: 'Overview', available: true },
  { label: 'Projects', available: false },
  { label: 'Repositories', available: false },
  { label: 'Pull requests', available: false },
  { label: 'CI/CD', available: false },
  { label: 'Security', available: false },
  { label: 'Reports', available: false },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white md:block">
        <div className="flex h-14 items-center gap-2 border-b border-slate-200 px-5">
          <img src="/favicon.svg" alt="" className="h-6 w-6" />
          <span className="font-semibold tracking-tight">DevVault</span>
        </div>
        <nav aria-label="Main" className="p-3">
          <ul className="space-y-0.5">
            {NAV_ITEMS.map((item) => (
              <li key={item.label}>
                <span
                  aria-current={item.available ? 'page' : undefined}
                  aria-disabled={!item.available}
                  className={`flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                    item.available
                      ? 'bg-indigo-50 font-medium text-indigo-700'
                      : 'cursor-not-allowed text-slate-400'
                  }`}
                >
                  {item.label}
                  {!item.available && <span className="text-[10px] uppercase">soon</span>}
                </span>
              </li>
            ))}
          </ul>
        </nav>
      </aside>
      <main className="flex-1">
        <header className="flex h-14 items-center border-b border-slate-200 bg-white px-6">
          <h1 className="text-base font-semibold">Overview</h1>
        </header>
        <div className="mx-auto max-w-6xl p-6">{children}</div>
      </main>
    </div>
  );
}
