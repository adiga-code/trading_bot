import { haptic } from '../lib/telegram'
import type { AppConfig, PayProduct } from '../types'

export function Pocket({ config, onBuy }: { config: AppConfig | null; onBuy: (p: PayProduct) => void }) {
  if (!config) return <div className="skeleton mx-4 mt-4 h-64 rounded-card" />

  const best = config.pocket_tiers[config.pocket_tiers.length - 1]

  return (
    <div className="fade-up px-4 pb-6 pt-4">
      <h2 className="font-display text-[19px] font-extrabold">🏦 PocketOption</h2>
      <p className="mt-2 rounded-card border border-stroke bg-card p-3.5 text-[12.5px] leading-relaxed text-t2">
        Готовый аккаунт PocketOption с балансом <strong className="text-t1">выше суммы оплаты</strong> — выдаётся
        после подтверждения платежа.
      </p>

      <div className="mt-4 space-y-2.5">
        {config.pocket_tiers.map((t) => {
          const bonus = Math.round((t.balance_usd / t.pay_usd - 1) * 100)
          const isBest = t.index === best.index
          return (
            <button
              key={t.index}
              onClick={() => {
                haptic('medium')
                onBuy({ type: 'pocket', plan: String(t.index), name: t.name, amountUsd: t.pay_usd, stars: t.stars })
              }}
              className={`relative w-full rounded-card border p-4 text-left active:scale-[0.99] ${
                isBest ? 'border-gold/50 bg-card' : 'border-stroke bg-card'
              }`}
            >
              {isBest && (
                <span className="absolute right-3 top-3 rounded-full bg-gold px-2.5 py-0.5 text-[10px] font-bold text-bg">
                  ⭐ Best offer
                </span>
              )}
              <div className="flex items-center gap-4">
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-t3">Платите</div>
                  <div className="tnum font-display text-[22px] font-extrabold">{t.pay_usd.toFixed(0)}$</div>
                </div>
                <div className="text-xl text-t3">→</div>
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-t3">Получаете</div>
                  <div className="tnum font-display text-[22px] font-extrabold text-up">{t.balance_usd.toFixed(0)}$</div>
                </div>
              </div>
              <div className="mt-2.5 inline-block rounded-md bg-up/10 px-2 py-0.5 text-[11.5px] font-semibold text-up">
                ✦ Бонус к балансу +{bonus}%
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
