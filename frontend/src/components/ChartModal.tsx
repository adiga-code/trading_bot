import { CandlestickData, IChartApi, ISeriesApi, UTCTimestamp, createChart } from 'lightweight-charts'
import { useEffect, useRef, useState } from 'react'
import { fmtPct, fmtPrice } from '../lib/format'
import { haptic, tg } from '../lib/telegram'
import type { Market } from '../types'

const TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d', '1w'] as const
type Tf = (typeof TIMEFRAMES)[number]
const BINANCE_LIMIT: Record<Tf, number> = { '5m': 96, '15m': 96, '1h': 72, '4h': 90, '1d': 120, '1w': 120 }

export function ChartModal({ market, onClose }: { market: Market | null; onClose: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval>>()
  const [tf, setTf] = useState<Tf>('1h')
  const [price, setPrice] = useState<number | null>(market?.price ?? null)

  // BackButton Telegram закрывает график
  useEffect(() => {
    const back = tg?.BackButton
    if (!market || !back) return
    const close = () => onClose()
    back.show()
    back.onClick(close)
    return () => {
      back.offClick(close)
      back.hide()
    }
  }, [market, onClose])

  useEffect(() => {
    if (!market || !containerRef.current) return
    const el = containerRef.current
    const chart = createChart(el, {
      autoSize: true,
      layout: { background: { color: '#0B0E14' }, textColor: '#5B6472' },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.07)' },
      timeScale: { borderColor: 'rgba(255,255,255,0.07)', timeVisible: true, secondsVisible: false },
    })
    const series = chart.addCandlestickSeries({
      upColor: '#34D399',
      downColor: '#F87171',
      borderUpColor: '#34D399',
      borderDownColor: '#F87171',
      wickUpColor: '#34D399',
      wickDownColor: '#F87171',
    })
    chartRef.current = chart
    seriesRef.current = series

    let cancelled = false

    async function load() {
      let candles: CandlestickData[] = []
      if (market!.kind === 'crypto') {
        try {
          const raw = (await fetch(
            `https://api.binance.com/api/v3/klines?symbol=${market!.symbol}&interval=${tf}&limit=${BINANCE_LIMIT[tf]}`,
          ).then((r) => r.json())) as unknown[][]
          candles = raw.map((k) => ({
            time: (Number(k[0]) / 1000) as UTCTimestamp,
            open: parseFloat(String(k[1])),
            high: parseFloat(String(k[2])),
            low: parseFloat(String(k[3])),
            close: parseFloat(String(k[4])),
          }))
        } catch {
          /* график останется пустым */
        }
      } else {
        try {
          const data = await fetch(
            `/api/metalchart?symbol=${encodeURIComponent(market!.ysym ?? 'GC=F')}&tf=${tf}`,
          ).then((r) => r.json())
          candles = (data.candles ?? []).map((c: { time: number; open: number; high: number; low: number; close: number }) => ({
            ...c,
            time: c.time as UTCTimestamp,
          }))
          if (data.price != null) setPrice(data.price)
        } catch {
          /* ignore */
        }
      }
      if (!cancelled && candles.length) {
        series.setData(candles)
        setPrice(candles[candles.length - 1].close)
        chart.timeScale().fitContent()
      }
    }

    function startLive() {
      if (market!.kind === 'crypto') {
        try {
          const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${market!.symbol.toLowerCase()}@kline_${tf}`)
          ws.onmessage = (e) => {
            try {
              const k = JSON.parse(e.data).k
              const candle: CandlestickData = {
                time: (Math.floor(k.t / 1000)) as UTCTimestamp,
                open: +k.o, high: +k.h, low: +k.l, close: +k.c,
              }
              seriesRef.current?.update(candle)
              setPrice(+k.c)
            } catch {
              /* ignore */
            }
          }
          wsRef.current = ws
        } catch {
          /* без live-обновлений */
        }
      } else {
        // у металлов нет бесплатного websocket — обновляем спот раз в 15 сек
        pollRef.current = setInterval(async () => {
          try {
            const m = await fetch('/api/metals').then((r) => r.json())
            const p = market!.metalKey ? m?.[market!.metalKey]?.price : null
            if (p != null) setPrice(p)
          } catch {
            /* ignore */
          }
        }, 15000)
      }
    }

    load().then(() => !cancelled && startLive())

    return () => {
      cancelled = true
      wsRef.current?.close()
      wsRef.current = null
      clearInterval(pollRef.current)
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, [market, tf])

  if (!market) return null

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-bg">
      <div className="flex items-center gap-3 border-b border-stroke px-4 py-3" style={{ paddingTop: 'calc(env(safe-area-inset-top) + 12px)' }}>
        <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-el border border-stroke bg-card">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <div className="flex-1">
          <div className="font-display text-[15px] font-bold">{market.name}</div>
          <div className="tnum text-[13px] text-t2">{fmtPrice(price)}</div>
        </div>
        {market.pct != null && (
          <div className={`tnum rounded-el px-2 py-1 text-[12px] font-semibold ${market.pct >= 0 ? 'bg-up/10 text-up' : 'bg-down/10 text-down'}`}>
            {fmtPct(market.pct)}
          </div>
        )}
      </div>
      <div className="flex gap-1.5 px-4 py-2.5">
        {TIMEFRAMES.map((t) => (
          <button
            key={t}
            onClick={() => {
              haptic('light')
              setTf(t)
            }}
            className={`tnum rounded-el px-3 py-1.5 text-[12px] font-semibold ${
              tf === t ? 'bg-gold text-bg' : 'border border-stroke bg-card text-t2'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <div ref={containerRef} className="min-h-0 flex-1" />
    </div>
  )
}
