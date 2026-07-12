import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import { fmtDate } from '../../lib/format'
import { hapticNotify } from '../../lib/telegram'
import type { AppConfig } from '../../types'
import { useToast } from '../Toast'

type UserDetail = {
  id: number
  display_name: string
  is_vip: boolean
  username: string | null
  subscription: {
    plan_name: string
    status: string
    started_at: string
    expires_at: string | null
  } | null
  purchases: {
    id: number
    plan_name: string
    amount_usd: number
    created_at: string
  }[]
}

export function UserSheet({
  userId,
  displayName,
  isVip,
  config,
  onClose,
  onChanged,
}: {
  userId: number
  displayName: string
  isVip: boolean
  config: AppConfig | null
  onClose: () => void
  onChanged: () => void
}) {
  const toast = useToast()
  const [detail, setDetail] = useState<UserDetail | null>(null)
  const [messageText, setMessageText] = useState('')

  useEffect(() => {
    setDetail(null)
    api
      .get<UserDetail>(`/api/admin/users/${userId}`)
      .then(setDetail)
      .catch(() => setDetail(null))
  }, [userId])

  const grantVip = async (planKey: string) => {
    try {
      await api.post(`/api/admin/users/${userId}/vip`, { plan_key: planKey })
      hapticNotify('success')
      toast('VIP выдан, инвайт отправлен')
      onChanged()
      onClose()
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  const revokeVip = async () => {
    try {
      await api.del(`/api/admin/users/${userId}/vip`)
      toast('VIP снят')
      onChanged()
      onClose()
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  const sendMessage = async () => {
    if (!messageText.trim()) return
    try {
      await api.post(`/api/admin/users/${userId}/message`, { text: messageText.trim() })
      hapticNotify('success')
      toast('Сообщение отправлено')
      setMessageText('')
      onClose()
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
  }

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60" onClick={onClose} />
      <div
        className="sheet-in fixed bottom-0 left-0 right-0 z-50 mx-auto max-h-[85vh] max-w-md overflow-y-auto rounded-t-3xl border-t border-stroke bg-card px-5 pt-4"
        style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 20px)' }}
      >
        <div className="font-display text-[16px] font-bold">
          {displayName} {isVip && '💎'}
        </div>
        <div className="tnum mt-0.5 text-[12px] text-t3">
          ID {userId}
          {detail?.username && <> · @{detail.username}</>}
        </div>

        <div className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-t3">Подписка</div>
        {detail === null ? (
          <div className="skeleton mt-2 h-12 rounded-el" />
        ) : detail.subscription ? (
          <div className="mt-2 rounded-el border border-stroke bg-card2 px-3 py-2.5">
            <div className="text-[13px] font-semibold">
              {detail.subscription.plan_name}
              <span className={detail.subscription.status === 'active' ? 'ml-2 text-up' : 'ml-2 text-down'}>
                {detail.subscription.status === 'active' ? '● активна' : '● истекла'}
              </span>
            </div>
            <div className="tnum mt-0.5 text-[11.5px] text-t3">
              с {fmtDate(detail.subscription.started_at)} ·{' '}
              {detail.subscription.expires_at ? `до ${fmtDate(detail.subscription.expires_at)}` : 'навсегда'}
            </div>
            {detail.purchases.length > 0 && (
              <div className="tnum mt-1 text-[11.5px] text-t3">
                Покупок: {detail.purchases.length} · последняя {fmtDate(detail.purchases[0].created_at)} (
                {detail.purchases[0].amount_usd.toFixed(0)}$)
              </div>
            )}
          </div>
        ) : (
          <div className="mt-2 rounded-el border border-stroke bg-card2 px-3 py-2.5 text-[12.5px] text-t3">
            Подписки нет
            {detail.purchases.length > 0 && <span className="tnum"> · покупок: {detail.purchases.length}</span>}
          </div>
        )}

        <div className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-t3">
          {isVip ? 'VIP управление' : 'Выдать VIP'}
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
        {isVip && (
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
          className="mt-2 w-full rounded-el bg-gold py-2.5 text-[13.5px] font-bold text-bg disabled:bg-card2 disabled:text-t3"
        >
          Отправить
        </button>
      </div>
    </>
  )
}
