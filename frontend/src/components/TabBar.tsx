import { haptic } from '../lib/telegram'
import type { Tab } from '../types'

const TABS: { id: Tab; label: string; icon: JSX.Element }[] = [
  {
    id: 'home',
    label: 'Главная',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" />
      </svg>
    ),
  },
  {
    id: 'vip',
    label: 'VIP',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 3h12l4 6-10 12L2 9z" /><path d="M2 9h20" />
      </svg>
    ),
  },
  {
    id: 'pocket',
    label: 'Pocket',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="6" width="18" height="14" rx="2" /><path d="M3 10h18" /><path d="M8 3v3M16 3v3" />
      </svg>
    ),
  },
  {
    id: 'stats',
    label: 'Статы',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
      </svg>
    ),
  },
]

const ADMIN_TAB: { id: Tab; label: string; icon: JSX.Element } = {
  id: 'admin',
  label: 'Админ',
  icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
    </svg>
  ),
}

export function TabBar({ tab, onChange, isAdmin }: { tab: Tab; onChange: (t: Tab) => void; isAdmin: boolean }) {
  const tabs = isAdmin ? [...TABS, ADMIN_TAB] : TABS
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-stroke bg-bg/80 backdrop-blur-lg"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="mx-auto flex max-w-md">
        {tabs.map((t) => {
          const active = tab === t.id
          return (
            <button
              key={t.id}
              onClick={() => {
                haptic('light')
                onChange(t.id)
              }}
              className={`relative flex flex-1 flex-col items-center gap-1 pb-2 pt-2.5 text-[11px] font-medium transition-colors ${
                active ? 'text-gold' : 'text-t3'
              }`}
            >
              <span className={`absolute top-0 h-0.5 w-8 rounded-full transition-opacity ${active ? 'bg-gold opacity-100' : 'opacity-0'}`} />
              <span className="h-5 w-5">{t.icon}</span>
              {t.label}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
