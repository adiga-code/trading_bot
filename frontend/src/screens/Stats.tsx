import { useCallback, useEffect, useState } from 'react'
import { fmtPct, fmtPrice } from '../lib/format'
import { load24hChanges } from '../lib/market'
import { haptic } from '../lib/telegram'
import type { AppConfig } from '../types'

export function Stats({ config }: { config: AppConfig | null }) {
  const [rows, setRows] = useState<Record<string, { pct: number; price: number }>>({})
  const [loading, setLoading] = useState(true)
  const [updatedAt, setUpdatedAt] = useState<number | null>(null)
  const [tick, setTick] = useState(0)

  const pairs = config?.trading_pairs ?? []

  const refresh = useCallback(async () => {
    if (!pairs.length) return
    setLoading(true)
    const data = await load24hChanges(pairs)
    setRows(data)
    setUpdatedAt(Date.now())
    setLoading(false)
  }, [pairs.length])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 30000)
    return () => clearInterval(t)
  }, [refresh])

  // «обновлено N сек назад»
  useEffect(() => {
    const t = setInterval(() => setTick((v) => v + 1), 1000)
    return () => clearInterval(t)
  }, [])
  void tick

  const secAgo = updatedAt ? Math.max(0, Math.round((Date.now() - updatedAt) / 1000)) : null

  return (
    <div className="fade-up px-4 pb-6 pt-4">
      <h2 className="font-display text-[20px] font-extrabold">Статистика</h2>

      <div className="mt-3 grid grid-cols-4 gap-2">
        <Meta value="1943%" label="Прибыль" cls="text-gold" highlight />
        <Meta value="68.9%" label="Win Rate" cls="text-up" />
        <Meta value="45" label="Сигналов" cls="text-t1" />
        <Meta value="62.7%" label="Ср. профит" cls="text-up" />
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[12px] font-semibold text-t2">
          <span className="live-dot h-1.5 w-1.5 rounded-full bg-up" />
          LIVE — Binance
        </div>
        <div className="tnum text-[11px] text-t3">{secAgo != null ? `обновлено ${secAgo} с назад` : ''}</div>
      </div>

      <div className="mt-2 overflow-hidden rounded-card bg-card shadow-[0_6px_16px_rgba(0,0,0,0.35)]">
        <div className="flex items-center justify-between border-b border-white/[0.06] px-3.5 py-2.5 text-[10px] uppercase tracking-wide text-t3">
          <span>Пара</span>
          <span className="flex items-center gap-3">
            <span>Цена</span>
            <span className="w-[64px] text-right">24ч</span>
          </span>
        </div>
        {pairs.map((pair) => {
          const row = rows[pair]
          const up = row ? row.pct >= 0 : true
          return (
            <div
              key={pair}
              className="flex items-center justify-between border-t border-white/[0.04] px-3.5 py-2 first:border-t-0"
            >
              <span className="tnum text-[12.5px] font-medium text-t2">{pair}</span>
              {loading && !row ? (
                <span className="skeleton h-4 w-24 rounded" />
              ) : row ? (
                <span className="flex items-center gap-3">
                  <span className="tnum text-[12.5px] text-t1">{fmtPrice(row.price)}</span>
                  <span className={`tnum w-[64px] text-right text-[12.5px] font-semibold ${up ? 'text-up' : 'text-down'}`}>
                    {fmtPct(row.pct)}
                  </span>
                </span>
              ) : (
                <span className="text-[12px] text-t3">N/A</span>
              )}
            </div>
          )
        })}
      </div>

      <button
        onClick={() => {
          haptic('light')
          refresh()
        }}
        disabled={loading}
        className="mt-3 w-full rounded-pill bg-card2 py-2.5 text-[13px] font-semibold text-t2 active:scale-[0.99] disabled:opacity-60"
      >
        {loading ? 'Обновляем…' : '🔄 Обновить'}
      </button>
    </div>
  )
}

function Meta({ value, label, cls, highlight }: { value: string; label: string; cls: string; highlight?: boolean }) {
  return (
    <div
      className={`rounded-stat px-1 py-3 text-center ${
        highlight
          ? 'border border-gold/40 bg-[linear-gradient(180deg,#1D1A12_0%,#10141B_100%)] shadow-[0_0_26px_rgba(232,180,76,0.15),0_10px_24px_rgba(0,0,0,0.28)]'
          : 'border border-white/[0.07] bg-[linear-gradient(180deg,#161B26_0%,#10141B_100%)] shadow-[0_10px_24px_rgba(0,0,0,0.28)]'
      }`}
    >
      <div className={`tnum font-display text-[15px] font-bold ${cls}`}>{value}</div>
      <div className="mt-0.5 text-[10px] text-t3">{label}</div>
    </div>
  )
}
