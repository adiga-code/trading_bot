import { useState } from 'react'
import { haptic } from '../../lib/telegram'
import type { AppConfig } from '../../types'
import { Broadcast } from './Broadcast'
import { Dashboard } from './Dashboard'
import { PocketOrders } from './PocketOrders'
import { Purchases } from './Purchases'
import { Users } from './Users'

const SECTIONS = [
  { id: 'dashboard', label: 'Дашборд' },
  { id: 'users', label: 'Юзеры' },
  { id: 'purchases', label: 'Покупки' },
  { id: 'pocket', label: 'Pocket' },
  { id: 'broadcast', label: 'Рассылка' },
] as const

type SectionId = (typeof SECTIONS)[number]['id']

export function Admin({ config }: { config: AppConfig | null }) {
  const [section, setSection] = useState<SectionId>('dashboard')

  return (
    <div className="fade-up pb-6 pt-4">
      <div className="px-4">
        <h2 className="font-display text-[19px] font-extrabold">👑 Админка</h2>
        <div className="mt-3 flex gap-1.5 overflow-x-auto pb-1">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                haptic('light')
                setSection(s.id)
              }}
              className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12.5px] font-semibold ${
                section === s.id ? 'bg-gold text-bg' : 'border border-stroke bg-card text-t2'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-3 px-4">
        {section === 'dashboard' && <Dashboard />}
        {section === 'users' && <Users config={config} />}
        {section === 'purchases' && <Purchases />}
        {section === 'pocket' && <PocketOrders />}
        {section === 'broadcast' && <Broadcast />}
      </div>
    </div>
  )
}
