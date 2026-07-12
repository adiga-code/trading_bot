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

      <div className="mt-3 rounded-card bg-card p-4 shadow-[0_6px_16px_rgba(0,0,0,0.35)]">
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
          const onClick = () => {
            haptic('medium')
            onBuy({ type: 'vip', plan: p.key, name: p.name, amountUsd: p.price_usd, stars: p.stars })
          }

          if (hot) {
            return (
              <button
                key={p.key}
                onClick={onClick}
                className="relative w-full overflow-hidden rounded-hero border border-white/[0.05] bg-[#17191F] p-6 text-left shadow-[0_0_40px_rgba(242,183,66,0.14),0_20px_40px_rgba(0,0,0,0.4)] active:scale-[0.99]"
              >
                <span className="inline-block rounded-md bg-gold-hero px-2.5 py-1 text-[11px] font-bold text-bg">
                  🔥 Самый популярный
                </span>
                <div className="mt-1.5 font-display text-[15px] font-bold text-t1">{periodLabel(p)}</div>
                <div className="mt-1 flex items-baseline gap-2.5">
                  <span className="tnum font-display text-[38px] font-extrabold tracking-tight text-t1">
                    {p.price_usd.toFixed(0)}$
                  </span>
                  <span className="tnum text-[16px] text-t3 line-through">{p.old_price_usd.toFixed(0)}$</span>
                </div>
                <div className="mt-0.5 text-[13px] font-semibold text-up">
                  Экономия {(p.old_price_usd - p.price_usd).toFixed(0)}$ (−{discount}%)
                </div>
                <div className="mt-3.5 flex h-[58px] w-full items-center justify-center rounded-[20px] bg-gold-hero text-[16px] font-extrabold text-bg shadow-[0_14px_30px_rgba(242,183,66,0.38)]">
                  Получить VIP
                </div>
              </button>
            )
          }

          return (
            <button
              key={p.key}
              onClick={onClick}
              className="flex w-full items-center justify-between gap-3 rounded-row bg-card p-4 text-left shadow-[0_6px_16px_rgba(0,0,0,0.3)] active:scale-[0.99]"
            >
              <div>
                {lifetime && (
                  <span className="mb-1 inline-block rounded-md bg-card2 px-2 py-0.5 text-[10px] font-bold text-t2">
                    ♾ Навсегда
                  </span>
                )}
                <div className="font-display text-[13px] font-bold text-t1">{periodLabel(p)}</div>
                <div className="mt-1 flex items-baseline gap-1.5">
                  <span className="tnum font-display text-[18px] font-extrabold text-t1">{p.price_usd.toFixed(0)}$</span>
                  <span className="tnum text-[12px] text-t3 line-through">{p.old_price_usd.toFixed(0)}$</span>
                </div>
                <div className="mt-0.5 text-[11px] text-t3">−{discount}%</div>
              </div>
              <span className="shrink-0 rounded-pill bg-[#232830] px-[22px] py-[11px] text-[13px] font-bold text-t1">
                Выбрать
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
