import { useCallback, useEffect, useState } from 'react'
import { UserSheet } from '../../components/admin/UserSheet'
import { api } from '../../lib/api'
import { fmtDate } from '../../lib/format'
import { useToast } from '../../components/Toast'
import type { AppConfig } from '../../types'

type AdminUser = {
  id: number
  display_name: string
  is_vip: boolean
  created_at: string
}

export function Users({ config }: { config: AppConfig | null }) {
  const toast = useToast()
  const [search, setSearch] = useState('')
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<AdminUser | null>(null)

  const load = useCallback(async (q: string) => {
    setLoading(true)
    try {
      const res = await api.get<{ items: AdminUser[] }>(`/api/admin/users?search=${encodeURIComponent(q)}`)
      setUsers(res.items)
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
    setLoading(false)
  }, [toast])

  useEffect(() => {
    const t = setTimeout(() => load(search), 300)
    return () => clearTimeout(t)
  }, [search, load])

  return (
    <div>
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Поиск: ник, имя или ID"
        className="w-full rounded-el border border-stroke bg-card px-3.5 py-2.5 text-[13.5px] text-t1 placeholder:text-t3 focus:border-gold/50 focus:outline-none"
      />
      <div className="mt-3 overflow-hidden rounded-card border border-stroke bg-card">
        {loading ? (
          <div className="skeleton h-40" />
        ) : users.length === 0 ? (
          <div className="p-4 text-center text-[13px] text-t3">Никого не найдено</div>
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
                <span className="block text-[13.5px] font-semibold">
                  {u.display_name} {u.is_vip && <span className="text-gold">💎</span>}
                </span>
                <span className="tnum block text-[11px] text-t3">
                  ID {u.id} · {fmtDate(u.created_at)}
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
          onChanged={() => load(search)}
        />
      )}
    </div>
  )
}
