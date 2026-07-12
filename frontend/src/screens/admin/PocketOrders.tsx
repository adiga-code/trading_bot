import { useCallback, useEffect, useState } from 'react'
import { api } from '../../lib/api'
import { fmtDate, fmtUsd } from '../../lib/format'
import { hapticNotify } from '../../lib/telegram'
import { useToast } from '../../components/Toast'

type Order = {
  id: number
  user: string
  user_id: number
  amount_usd: number
  balance_usd: number
  status: 'new' | 'fulfilled'
  created_at: string
}

export function PocketOrders() {
  const toast = useToast()
  const [orders, setOrders] = useState<Order[] | null>(null)
  const [selected, setSelected] = useState<Order | null>(null)
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)

  const load = useCallback(() => {
    api.get<{ items: Order[] }>('/api/admin/pocket-orders').then((r) => setOrders(r.items)).catch(() => setOrders([]))
  }, [])

  useEffect(load, [load])

  const fulfill = async () => {
    if (!selected || !text.trim()) return
    setSending(true)
    try {
      await api.post(`/api/admin/pocket-orders/${selected.id}/fulfill`, { text: text.trim() })
      hapticNotify('success')
      toast('Аккаунт выдан')
      setSelected(null)
      setText('')
      load()
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
    setSending(false)
  }

  if (orders === null) return <div className="skeleton h-48 rounded-card" />

  return (
    <div>
      <div className="overflow-hidden rounded-card border border-stroke bg-card">
        {orders.length === 0 ? (
          <div className="p-5 text-center text-[13px] text-t3">Заявок пока нет</div>
        ) : (
          orders.map((o, i) => (
            <div key={o.id} className={`px-3.5 py-2.5 ${i > 0 ? 'border-t border-stroke' : ''}`}>
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-semibold">{o.user}</span>
                {o.status === 'new' ? (
                  <button
                    onClick={() => setSelected(o)}
                    className="rounded-el bg-gold px-3 py-1 text-[12px] font-bold text-bg"
                  >
                    Выдать
                  </button>
                ) : (
                  <span className="rounded-md bg-up/10 px-1.5 py-0.5 text-[10.5px] font-bold uppercase text-up">
                    выдано
                  </span>
                )}
              </div>
              <div className="tnum mt-0.5 text-[11.5px] text-t3">
                {fmtUsd(o.amount_usd)} → баланс {fmtUsd(o.balance_usd)} · {fmtDate(o.created_at)}
              </div>
            </div>
          ))
        )}
      </div>

      {selected && (
        <>
          <div className="fixed inset-0 z-40 bg-black/60" onClick={() => setSelected(null)} />
          <div
            className="sheet-in fixed bottom-0 left-0 right-0 z-50 mx-auto max-h-[85vh] max-w-md overflow-y-auto rounded-t-3xl border-t border-stroke bg-card px-5 pt-4"
            style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 20px)' }}
          >
            <div className="font-display text-[16px] font-bold">📦 Выдача PocketOption</div>
            <div className="tnum mt-0.5 text-[12px] text-t3">
              {selected.user} · {fmtUsd(selected.amount_usd)} → {fmtUsd(selected.balance_usd)}
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={4}
              placeholder="Логин, пароль, ссылка — всё, что получит клиент"
              className="mt-3 w-full rounded-el border border-stroke bg-card2 px-3 py-2 text-[13px] placeholder:text-t3 focus:border-gold/50 focus:outline-none"
            />
            <button
              onClick={fulfill}
              disabled={!text.trim() || sending}
              className="mt-2 w-full rounded-el bg-gold py-2.5 text-[13.5px] font-bold text-bg disabled:opacity-40"
            >
              {sending ? 'Отправляем…' : 'Отправить клиенту и закрыть заявку'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
