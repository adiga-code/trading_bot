import { fmtPct, fmtPrice } from '../lib/format'
import { haptic } from '../lib/telegram'
import type { Market } from '../types'
import { Sparkline } from './Sparkline'

const ICON_BG: Record<string, string> = {
  BTC: 'linear-gradient(145deg,#F7931A,#C9720C)',
  ETH: 'linear-gradient(145deg,#8E9BC7,#5A6591)',
  SOL: 'linear-gradient(145deg,#9945FF,#14F195)',
  TON: 'linear-gradient(145deg,#4CC1E8,#2A82A8)',
  BNB: 'linear-gradient(145deg,#F3BA2F,#C9930E)',
  XRP: 'linear-gradient(145deg,#33333A,#0F0F12)',
  XAU: 'linear-gradient(145deg,#E8C468,#B8912F)',
  XAG: 'linear-gradient(145deg,#C9CDD3,#8B909A)',
}

// запасной детерминированный цвет для символов вне ICON_BG — чисто визуально, в данные не пишется
function fallbackIconBg(seed: string) {
  let hash = 0
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0
  const hue = hash % 360
  return `linear-gradient(145deg, hsl(${hue},70%,55%), hsl(${hue},70%,35%))`
}

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
    <div className="divide-y divide-white/[0.045] overflow-hidden rounded-card bg-card shadow-[0_6px_16px_rgba(0,0,0,0.35)]">
      {markets.map((m) => {
        const up = (m.pct ?? 0) >= 0
        const sym = m.kind === 'metal' ? m.symbol : m.symbol.replace('USDT', '')
        return (
          <button
            key={m.symbol}
            onClick={() => {
              haptic('light')
              onOpen(m)
            }}
            className="flex w-full items-center gap-3 px-3.5 py-2.5 text-left active:bg-card2"
          >
            <div
              className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full text-[10px] font-extrabold text-bg shadow-[0_2px_8px_rgba(0,0,0,0.4)]"
              style={{ background: ICON_BG[sym] ?? fallbackIconBg(sym) }}
            >
              {sym}
            </div>
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
