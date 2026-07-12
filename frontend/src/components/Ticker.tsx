import type { Market } from '../types'
import { fmtPct, fmtPrice } from '../lib/format'

export function Ticker({ markets }: { markets: Market[] }) {
  const items = markets.filter((m) => m.price != null)
  if (!items.length) {
    return <div className="skeleton mx-4 h-8 rounded-el" />
  }
  const row = (
    <>
      {items.map((m) => (
        <span key={m.symbol} className="tnum mx-3 inline-flex items-center gap-1.5 text-[12px]">
          <span className="font-semibold text-t2">{m.symbol.replace('USDT', '')}</span>
          <span className="text-t1">{fmtPrice(m.price)}</span>
          {m.pct != null && (
            <span className={m.pct >= 0 ? 'text-up' : 'text-down'}>{fmtPct(m.pct)}</span>
          )}
        </span>
      ))}
    </>
  )
  return (
    <div className="mx-4 mt-1 overflow-hidden rounded-row bg-[rgba(21,23,28,0.55)] py-3 backdrop-blur-sm">
      <div className="animate-marquee whitespace-nowrap" style={{ width: 'max-content' }}>
        {row}
        {row}
      </div>
    </div>
  )
}
