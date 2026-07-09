import { useCallback, useEffect, useState } from 'react'
import { api } from '../../lib/api'
import { fmtDate } from '../../lib/format'
import { hapticNotify } from '../../lib/telegram'
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
  const [messageText, setMessageText] = useState('')

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

  const grantVip = async (planKey: string) => {
    if (!selected) return
    try {
      await api.post(`/api/admin/users/${selected.id}/vip`, { plan_key: planKey })
      hapticNotify('success')
      toast('VIP выдан, инвайт отправлен')
      setSelected(null)
      load(search)
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  const revokeVip = async () => {
    if (!selected) return
    try {
      await api.del(`/api/admin/users/${selected.id}/vip`)
      toast('VIP снят')
      setSelected(null)
      load(search)
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  const sendMessage = async () => {
    if (!selected || !messageText.trim()) return
    try {
      await api.post(`/api/admin/users/${selected.id}/message`, { text: messageText.trim() })
      hapticNotify('success')
      toast('Сообщение отправлено')
      setMessageText('')
      setSelected(null)
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
  }

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
        <>
          <div className="fixed inset-0 z-40 bg-black/60" onClick={() => setSelected(null)} />
          <div
            className="sheet-in fixed bottom-0 left-0 right-0 z-50 mx-auto max-w-md rounded-t-3xl border-t border-stroke bg-card px-5 pt-4"
            style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 20px)' }}
          >
            <div className="font-display text-[16px] font-bold">
              {selected.display_name} {selected.is_vip && '💎'}
            </div>
            <div className="tnum mt-0.5 text-[12px] text-t3">ID {selected.id}</div>

            <div className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-t3">
              {selected.is_vip ? 'VIP управление' : 'Выдать VIP'}
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {config?.vip_plans.map((p) => (
                <button
                  key={p.key}
                  onClick={() => grantVip(p.key)}
                  className="rounded-el border border-stroke bg-card2 px-3 py-2 text-[12.5px] font-semibold active:scale-[0.98]"
                >
                  {p.name.replace('VIP ', '')}
                </button>
              ))}
            </div>
            {selected.is_vip && (
              <button
                onClick={revokeVip}
                className="mt-2 w-full rounded-el border border-down/40 bg-down/10 py-2 text-[12.5px] font-semibold text-down"
              >
                🚫 Снять VIP и убрать из канала
              </button>
            )}

            <div className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-t3">Написать пользователю</div>
            <textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              rows={2}
              placeholder="Текст сообщения…"
              className="mt-2 w-full rounded-el border border-stroke bg-card2 px-3 py-2 text-[13px] placeholder:text-t3 focus:border-gold/50 focus:outline-none"
            />
            <button
              onClick={sendMessage}
              disabled={!messageText.trim()}
              className="mt-2 w-full rounded-el bg-gold py-2.5 text-[13.5px] font-bold text-bg disabled:opacity-40"
            >
              Отправить
            </button>
          </div>
        </>
      )}
    </div>
  )
}
