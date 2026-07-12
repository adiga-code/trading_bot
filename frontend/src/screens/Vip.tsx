import { haptic } from '../lib/telegram'
import type { AppConfig, PayProduct, VipPlan } from '../types'

const PERKS = [
  'Торговые сигналы 24/7',
  'Точные точки входа',
  'Take Profit и Stop Loss',
  'Закрытый VIP-чат',
  'Разбор сделок аналитиком',
  'Приоритетная поддержка',
  'Обучающие материалы',
]

function periodLabel(p: VipPlan): string {
  if (p.months === null) return 'Lifetime'
  if (p.months === 1) return '1 Месяц'
  return `${p.months} Месяца${p.months >= 5 ? '' : ''}`.replace('6 Месяца', '6 Месяцев')
}

export function Vip({ config, onBuy }: { config: AppConfig | null; onBuy: (p: PayProduct) => void }) {
  if (!config) return <div className="skeleton mx-4 mt-4 h-64 rounded-card" />

  const heroPlan = config.vip_plans.find((p) => p.key === '3months') ?? config.vip_plans[0]
  const otherPlans = config.vip_plans.filter((p) => p !== heroPlan)

  const buy = (p: VipPlan) => {
    haptic('medium')
    onBuy({ type: 'vip', plan: p.key, name: p.name, amountUsd: p.price_usd, stars: p.stars })
  }

  const heroDiscount = heroPlan ? Math.round((1 - heroPlan.price_usd / heroPlan.old_price_usd) * 100) : 0

  return (
    <div className="fade-up px-4 pb-6 pt-4">
      <div className="flex flex-col gap-2">
        <h2 className="font-display text-[24px] font-extrabold tracking-wide">VIP Подписка</h2>
        <p className="text-[13px] leading-relaxed text-t2">
          Получите полный доступ к торговым сигналам, аналитике и закрытому VIP-сообществу.
        </p>
        <div className="mt-0.5 flex items-center gap-1.5">
          <span className="text-[13px] tracking-widest text-gold">★★★★★</span>
          <span className="text-[12px] font-bold text-t1">4.9</span>
          <span className="text-[12px] text-t3">· 250+ активных участников</span>
        </div>
      </div>

      <div className="mt-4 rounded-card bg-card p-4 shadow-[0_6px_16px_rgba(0,0,0,0.35)]">
        <div className="font-display text-[14px] font-bold text-t1">Что входит</div>
        <div className="mt-2.5 grid grid-cols-2 gap-x-3 gap-y-3">
          {PERKS.map((perk) => (
            <div key={perk} className="flex items-start gap-1.5 text-[12px] leading-[1.4] text-[#C4CCD6]">
              <span className="text-up">✓</span>
              {perk}
            </div>
          ))}
        </div>
      </div>

      {heroPlan && (
        <button
          onClick={() => buy(heroPlan)}
          className="relative mt-4 w-full overflow-hidden rounded-hero border border-white/[0.05] bg-[#17191F] p-6 text-left shadow-[0_0_40px_rgba(242,183,66,0.14),0_20px_40px_rgba(0,0,0,0.4)] active:scale-[0.99]"
        >
          <span className="inline-block rounded-md bg-gold-hero px-2.5 py-1 text-[11px] font-bold text-bg">
            🔥 Самый популярный
          </span>
          <div className="mt-1.5 font-display text-[15px] font-bold text-t1">{periodLabel(heroPlan)}</div>
          <div className="mt-1 flex items-baseline gap-2.5">
            <span className="tnum font-display text-[38px] font-extrabold tracking-tight text-t1">
              {heroPlan.price_usd.toFixed(0)}$
            </span>
            <span className="tnum text-[16px] text-t3 line-through">{heroPlan.old_price_usd.toFixed(0)}$</span>
          </div>
          <div className="mt-0.5 text-[13px] font-semibold text-up">
            Экономия {(heroPlan.old_price_usd - heroPlan.price_usd).toFixed(0)}$ (−{heroDiscount}%)
          </div>
          <div className="mt-3.5 flex h-[58px] w-full items-center justify-center rounded-[20px] bg-gold-hero text-[16px] font-extrabold text-bg shadow-[0_14px_30px_rgba(242,183,66,0.38)]">
            Получить VIP
          </div>
        </button>
      )}

      <div className="mt-2.5 space-y-2.5">
        {otherPlans.map((p) => {
          const lifetime = p.months === null
          const discount = Math.round((1 - p.price_usd / p.old_price_usd) * 100)
          return (
            <button
              key={p.key}
              onClick={() => buy(p)}
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
