// Рыночные данные для главного экрана: Binance напрямую, металлы через наш бэкенд
import type { Market } from '../types'

const HOME_COINS = [
  { s: 'BTCUSDT', n: 'Bitcoin' },
  { s: 'ETHUSDT', n: 'Ethereum' },
  { s: 'SOLUSDT', n: 'Solana' },
  { s: 'TONUSDT', n: 'Toncoin' },
  { s: 'BNBUSDT', n: 'BNB' },
  { s: 'XRPUSDT', n: 'XRP' },
]

export async function loadHomeMarkets(): Promise<Market[]> {
  const out: Market[] = []
  try {
    const syms = JSON.stringify(HOME_COINS.map((c) => c.s))
    const [tickers, ...klines] = await Promise.all([
      fetch(`https://api.binance.com/api/v3/ticker/24hr?symbols=${syms}`).then((r) => r.json()),
      ...HOME_COINS.map((c) =>
        fetch(`https://api.binance.com/api/v3/klines?symbol=${c.s}&interval=1h&limit=24`)
          .then((r) => r.json())
          .catch(() => []),
      ),
    ])
    const bySym = new Map<string, { price: number; pct: number }>(
      (tickers as Array<Record<string, string>>).map((t) => [
        t.symbol,
        { price: parseFloat(t.lastPrice), pct: parseFloat(t.priceChangePercent) },
      ]),
    )
    HOME_COINS.forEach((c, i) => {
      const t = bySym.get(c.s)
      const closes = Array.isArray(klines[i])
        ? (klines[i] as unknown[][]).map((k) => parseFloat(String(k[4])))
        : []
      out.push({
        symbol: c.s,
        name: c.n,
        price: t?.price ?? null,
        pct: t?.pct ?? null,
        closes,
        kind: 'crypto',
      })
    })
  } catch {
    HOME_COINS.forEach((c) =>
      out.push({ symbol: c.s, name: c.n, price: null, pct: null, closes: [], kind: 'crypto' }),
    )
  }

  try {
    const metals = await fetch('/api/metals').then((r) => r.json())
    out.push({
      symbol: 'XAU', name: 'Золото', price: metals?.gold?.price ?? null, pct: null,
      closes: [], kind: 'metal', metalKey: 'gold', ysym: 'GC=F',
    })
    out.push({
      symbol: 'XAG', name: 'Серебро', price: metals?.silver?.price ?? null, pct: null,
      closes: [], kind: 'metal', metalKey: 'silver', ysym: 'SI=F',
    })
  } catch {
    /* металлы просто не покажем */
  }
  return out
}

export async function load24hChanges(pairs: string[]): Promise<Record<string, { pct: number; price: number }>> {
  const out: Record<string, { pct: number; price: number }> = {}
  try {
    const all = (await fetch('https://api.binance.com/api/v3/ticker/24hr').then((r) => r.json())) as Array<
      Record<string, string>
    >
    const wanted = new Set(pairs)
    for (const t of all) {
      if (wanted.has(t.symbol)) {
        out[t.symbol] = { pct: parseFloat(t.priceChangePercent), price: parseFloat(t.lastPrice) }
      }
    }
  } catch {
    /* вернём что есть */
  }
  return out
}
