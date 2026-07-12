import { useEffect, useState } from 'react'
import { UserSheet } from '../../components/admin/UserSheet'
import { api } from '../../lib/api'
import { fmtDate } from '../../lib/format'
import { useToast } from '../../components/Toast'
import type { AppConfig } from '../../types'

type VipUser = {
  id: number
  display_name: string
  is_vip: boolean
  plan_name: string
  expires_at: string | null
}

export function VipUsers({ config }: { config: AppConfig | null }) {
  const toast = useToast()
  const [users, setUsers] = useState<VipUser[] | null>(null)
  const [selected, setSelected] = useState<VipUser | null>(null)

  const load = () => {
    api
      .get<{ items: VipUser[] }>('/api/admin/vip-users')
      .then((r) => setUsers(r.items))
      .catch((e) => {
        toast(e instanceof Error ? e.message : 'Ошибка')
        setUsers([])
      })
  }

  useEffect(load, [])

  if (users === null) return <div className="skeleton h-40 rounded-card" />

  return (
    <div>
      <div className="overflow-hidden rounded-card border border-stroke bg-card">
        {users.length === 0 ? (
          <div className="p-4 text-center text-[13px] text-t3">Сейчас никого нет в VIP</div>
        ) : (
          users.map((u, i) => (
            <button
              key={u.id}
              onClick={() => setSelected(u)}
              className={`flex w-full items-center justify-between px-3.5 py-2.5 text-left active:bg-card2 ${
                i > 0 ? 'border-t border-stroke' : ''
              }`}
            >
              <span>
                <span className="block text-[13.5px] font-semibold">{u.display_name} 💎</span>
                <span className="tnum block text-[11px] text-t3">
                  {u.plan_name} · {u.expires_at ? `до ${fmtDate(u.expires_at)}` : 'навсегда'}
                </span>
              </span>
              <span className="text-t3">›</span>
            </button>
          ))
        )}
      </div>

      {selected && (
        <UserSheet
          userId={selected.id}
          displayName={selected.display_name}
          isVip={selected.is_vip}
          config={config}
          onClose={() => setSelected(null)}
          onChanged={load}
        />
      )}
    </div>
  )
}
