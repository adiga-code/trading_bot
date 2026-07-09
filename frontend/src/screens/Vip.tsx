import { haptic } from '../lib/telegram'
import type { AppConfig, PayProduct, VipPlan } from '../types'

const PERKS = [
  'Ежедневные сигналы',
  'Анализ рынка',
  'Win Rate 68.9%+',
  'Поддержка 24/7',
  'Точки входа/выхода',
  '1943% прибыли',
]

function periodLabel(p: VipPlan): string {
  if (p.months === null) return 'Lifetime'
  if (p.months === 1) return '1 Месяц'
  return `${p.months} Месяца${p.months >= 5 ? '' : ''}`.replace('6 Месяца', '6 Месяцев')
}

export function Vip({ config, onBuy }: { config: AppConfig | null; onBuy: (p: PayProduct) => void }) {
  if (!config) return <div className="skeleton mx-4 mt-4 h-64 rounded-card" />

  return (
    <div className="fade-up px-4 pb-6 pt-4">
      <h2 className="font-display text-[19px] font-extrabold">💎 VIP Канал</h2>

      <div className="mt-3 rounded-card border border-stroke bg-card p-4">
        <div className="text-[11px] font-semibold uppercase tracking-widest text-t3">Что входит в VIP</div>
        <div className="mt-2.5 grid grid-cols-2 gap-1.5">
          {PERKS.map((perk) => (
            <div key={perk} className="flex items-center gap-1.5 text-[12.5px] text-t2">
              <span className="text-up">✓</span>
              {perk}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 space-y-2.5">
        {config.vip_plans.map((p) => {
          const hot = p.key === '3months'
          const lifetime = p.months === null
          const discount = Math.round((1 - p.price_usd / p.old_price_usd) * 100)
          return (
            <button
              key={p.key}
              onClick={() => {
                haptic('medium')
                onBuy({ type: 'vip', plan: p.key, name: p.name, amountUsd: p.price_usd, stars: p.stars })
              }}
              className={`relative w-full overflow-hidden rounded-card border p-4 text-left active:scale-[0.99] ${
                hot ? 'border-gold/50 bg-card' : 'border-stroke bg-card'
              }`}
            >
              {hot && (
                <span className="absolute right-3 top-3 rounded-full bg-gold px-2.5 py-0.5 text-[10px] font-bold text-bg">
                  🔥 Хит
                </span>
              )}
              {lifetime && (
                <span className="absolute right-3 top-3 rounded-full bg-card2 px-2.5 py-0.5 text-[10px] font-bold text-t2">
                  ♾ Навсегда
                </span>
              )}
              <div className="text-[12px] font-semibold uppercase tracking-wide text-t3">{periodLabel(p)}</div>
              <div className="mt-1 flex items-baseline gap-2">
                <span className={`tnum font-display text-[26px] font-extrabold ${hot ? 'text-gold' : 'text-t1'}`}>
                  ${p.price_usd.toFixed(0)}
                </span>
                <span className="tnum text-[13px] text-t3 line-through">${p.old_price_usd.toFixed(0)}</span>
                <span className="tnum rounded-md bg-up/10 px-1.5 py-0.5 text-[11px] font-bold text-up">
                  −{discount}%
                </span>
              </div>
              <div
                className={`mt-3 rounded-el py-2.5 text-center text-[13.5px] font-bold ${
                  hot ? 'bg-gold text-bg' : 'bg-card2 text-t1'
                }`}
              >
                Купить
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
