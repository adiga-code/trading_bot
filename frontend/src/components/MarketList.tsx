import { fmtPct, fmtPrice } from '../lib/format'
import { haptic } from '../lib/telegram'
import type { Market } from '../types'
import { Sparkline } from './Sparkline'

export function MarketList({ markets, onOpen }: { markets: Market[]; onOpen: (m: Market) => void }) {
  if (!markets.length) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton h-14 rounded-card" />
        ))}
      </div>
    )
  }
  return (
    <div className="overflow-hidden rounded-card border border-stroke bg-card">
      {markets.map((m, i) => {
        const up = (m.pct ?? 0) >= 0
        return (
          <button
            key={m.symbol}
            onClick={() => {
              haptic('light')
              onOpen(m)
            }}
            className={`flex w-full items-center gap-3 px-3.5 py-2.5 text-left active:bg-card2 ${
              i > 0 ? 'border-t border-stroke' : ''
            }`}
          >
            <div className="min-w-0 flex-1">
              <div className="text-[13.5px] font-semibold">{m.name}</div>
              <div className="text-[11px] text-t3">{m.kind === 'metal' ? 'Спот · унция' : m.symbol}</div>
            </div>
            {m.kind === 'crypto' && <Sparkline closes={m.closes} up={up} />}
            <div className="w-[86px] text-right">
              <div className="tnum text-[13.5px] font-semibold">{fmtPrice(m.price)}</div>
              {m.pct != null ? (
                <div className={`tnum text-[11.5px] font-medium ${up ? 'text-up' : 'text-down'}`}>{fmtPct(m.pct)}</div>
              ) : (
                <div className="text-[11.5px] text-t3">LIVE</div>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
