import { haptic } from '../lib/telegram'
import type { Tab } from '../types'

const TABS: { id: Tab; label: string; icon: JSX.Element }[] = [
  {
    id: 'home',
    label: 'Главная',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 11l9-7 9 7" /><path d="M5 10v10h14V10" />
      </svg>
    ),
  },
  {
    id: 'vip',
    label: 'VIP',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 8l4 3 5-6 5 6 4-3-2 11H5L3 8z" />
      </svg>
    ),
  },
  {
    id: 'pocket',
    label: 'Pocket',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="3" y="6" width="18" height="13" rx="2" /><path d="M3 10h18M15 14h3" />
      </svg>
    ),
  },
  {
    id: 'stats',
    label: 'Статы',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M4 20V10M12 20V4M20 20v-7" />
      </svg>
    ),
  },
]

const ADMIN_TAB: { id: Tab; label: string; icon: JSX.Element } = {
  id: 'admin',
  label: 'Админ',
  icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 00.3 1.9l.1.1a2 2 0 11-2.9 2.9l-.1-.1a1.7 1.7 0 00-1.9-.3 1.7 1.7 0 00-1 1.6V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1-1.6 1.7 1.7 0 00-1.9.3l-.1.1a2 2 0 11-2.9-2.9l.1-.1a1.7 1.7 0 00.3-1.9 1.7 1.7 0 00-1.6-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.6-1 1.7 1.7 0 00-.3-1.9l-.1-.1a2 2 0 112.9-2.9l.1.1a1.7 1.7 0 001.9.3H9a1.7 1.7 0 001-1.6V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.6 1.7 1.7 0 001.9-.3l.1-.1a2 2 0 112.9 2.9l-.1.1a1.7 1.7 0 00-.3 1.9V9a1.7 1.7 0 001.6 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.6 1z" />
    </svg>
  ),
}

export function TabBar({ tab, onChange, isAdmin }: { tab: Tab; onChange: (t: Tab) => void; isAdmin: boolean }) {
  const tabs = isAdmin ? [...TABS, ADMIN_TAB] : TABS
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-white/[0.07] bg-[rgba(15,18,26,0.86)] shadow-[0_-12px_30px_rgba(0,0,0,0.35)] backdrop-blur-[18px]"
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
              <span className={`absolute left-[20%] right-[20%] top-0 h-0.5 rounded-full transition-opacity ${active ? 'bg-gold opacity-100' : 'opacity-0'}`} />
              <span className="h-5 w-5">{t.icon}</span>
              {t.label}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
