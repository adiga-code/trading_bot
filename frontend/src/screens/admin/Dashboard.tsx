import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import { fmtUsd } from '../../lib/format'

type StatsResponse = {
  users: { total: number; last7d: number; last30d: number; vip: number }
  purchases: {
    total: number
    revenue_total: number
    last7d: number
    revenue_7d: number
    last30d: number
    revenue_30d: number
  }
  pocket_orders_new: number
}

export function Dashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<StatsResponse>('/api/admin/stats')
      .then(setStats)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="rounded-card border border-down/30 bg-down/5 p-4 text-[13px] text-down">{error}</div>
  if (!stats) return <div className="skeleton h-56 rounded-card" />

  return (
    <div className="space-y-3">
      {stats.pocket_orders_new > 0 && (
        <div className="rounded-card border border-gold/40 bg-gold/10 p-3.5 text-[13px] font-semibold text-gold">
          🏦 Ждут выдачи: {stats.pocket_orders_new} PocketOption-заявок
        </div>
      )}

      <div className="grid grid-cols-2 gap-2.5">
        <Card label="Выручка всего" value={fmtUsd(stats.purchases.revenue_total)} accent="text-gold" />
        <Card label="Покупок всего" value={String(stats.purchases.total)} />
        <Card label="Выручка 7 дн" value={fmtUsd(stats.purchases.revenue_7d)} accent="text-up" sub={`${stats.purchases.last7d} покупок`} />
        <Card label="Выручка 30 дн" value={fmtUsd(stats.purchases.revenue_30d)} accent="text-up" sub={`${stats.purchases.last30d} покупок`} />
        <Card label="Пользователей" value={String(stats.users.total)} sub={`+${stats.users.last7d} за 7 дн`} />
        <Card label="VIP активных" value={String(stats.users.vip)} accent="text-gold" />
      </div>
    </div>
  )
}

function Card({ label, value, sub, accent = 'text-t1' }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className="rounded-card border border-stroke bg-card p-3.5">
      <div className="text-[10.5px] uppercase tracking-wide text-t3">{label}</div>
      <div className={`tnum mt-1 font-display text-[20px] font-extrabold ${accent}`}>{value}</div>
      {sub && <div className="tnum mt-0.5 text-[11px] text-t3">{sub}</div>}
    </div>
  )
}
