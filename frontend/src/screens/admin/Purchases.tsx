import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import { fmtDate, fmtUsd } from '../../lib/format'

type PurchaseItem = {
  id: number
  user: string
  product_type: string
  plan_name: string
  amount_usd: number
  created_at: string
}

type PaymentItem = {
  id: number
  user_id: number
  gateway: string
  plan_name: string
  amount_usd: number
  status: string
  created_at: string
}

const STATUS_STYLE: Record<string, string> = {
  paid: 'bg-up/10 text-up',
  pending: 'bg-gold/10 text-gold',
  cancelled: 'bg-down/10 text-down',
  expired: 'bg-card2 text-t3',
}

export function Purchases() {
  const [tab, setTab] = useState<'purchases' | 'payments'>('purchases')
  const [purchases, setPurchases] = useState<PurchaseItem[] | null>(null)
  const [payments, setPayments] = useState<PaymentItem[] | null>(null)

  useEffect(() => {
    api.get<{ items: PurchaseItem[] }>('/api/admin/purchases').then((r) => setPurchases(r.items)).catch(() => setPurchases([]))
    api.get<{ items: PaymentItem[] }>('/api/admin/payments').then((r) => setPayments(r.items)).catch(() => setPayments([]))
  }, [])

  return (
    <div>
      <div className="flex gap-1.5">
        <Pill active={tab === 'purchases'} onClick={() => setTab('purchases')}>Покупки</Pill>
        <Pill active={tab === 'payments'} onClick={() => setTab('payments')}>Счета</Pill>
      </div>

      <div className="mt-3 overflow-hidden rounded-card border border-stroke bg-card">
        {tab === 'purchases' ? (
          purchases === null ? (
            <div className="skeleton h-40" />
          ) : purchases.length === 0 ? (
            <Empty text="Покупок пока нет" />
          ) : (
            purchases.map((p, i) => (
              <div key={p.id} className={`px-3.5 py-2.5 ${i > 0 ? 'border-t border-stroke' : ''}`}>
                <div className="flex items-center justify-between">
                  <span className="text-[13px] font-semibold">{p.user}</span>
                  <span className="tnum text-[13px] font-bold text-gold">{fmtUsd(p.amount_usd)}</span>
                </div>
                <div className="mt-0.5 flex items-center justify-between text-[11.5px] text-t3">
                  <span>{p.plan_name}</span>
                  <span className="tnum">{fmtDate(p.created_at)}</span>
                </div>
              </div>
            ))
          )
        ) : payments === null ? (
          <div className="skeleton h-40" />
        ) : payments.length === 0 ? (
          <Empty text="Счетов пока нет" />
        ) : (
          payments.map((p, i) => (
            <div key={p.id} className={`px-3.5 py-2.5 ${i > 0 ? 'border-t border-stroke' : ''}`}>
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-semibold">{p.plan_name}</span>
                <span className={`rounded-md px-1.5 py-0.5 text-[10.5px] font-bold uppercase ${STATUS_STYLE[p.status] ?? 'bg-card2 text-t3'}`}>
                  {p.status}
                </span>
              </div>
              <div className="mt-0.5 flex items-center justify-between text-[11.5px] text-t3">
                <span className="tnum">ID {p.user_id} · {p.gateway}</span>
                <span className="tnum">{fmtUsd(p.amount_usd)} · {fmtDate(p.created_at)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function Pill({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3.5 py-1.5 text-[12.5px] font-semibold ${
        active ? 'bg-card2 text-t1' : 'text-t3'
      }`}
    >
      {children}
    </button>
  )
}

function Empty({ text }: { text: string }) {
  return <div className="p-5 text-center text-[13px] text-t3">{text}</div>
}
