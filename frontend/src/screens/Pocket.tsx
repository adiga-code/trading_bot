import { haptic } from '../lib/telegram'
import type { AppConfig, PayProduct } from '../types'

export function Pocket({ config, onBuy }: { config: AppConfig | null; onBuy: (p: PayProduct) => void }) {
  if (!config) return <div className="skeleton mx-4 mt-4 h-64 rounded-card" />

  const best = config.pocket_tiers[config.pocket_tiers.length - 1]

  return (
    <div className="fade-up px-4 pb-6 pt-4">
      <h2 className="font-display text-[20px] font-extrabold">PocketOption Аккаунты</h2>
      <p className="mt-2 rounded-card bg-card p-3.5 text-[12.5px] leading-relaxed text-t2 shadow-[0_6px_16px_rgba(0,0,0,0.35)]">
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
              className={`relative flex w-full flex-col gap-3 rounded-card p-4 text-left active:scale-[0.99] ${
                isBest
                  ? 'bg-[#1B160E] shadow-[0_0_30px_rgba(232,180,76,0.16),0_6px_16px_rgba(0,0,0,0.35)]'
                  : 'bg-card shadow-[0_6px_16px_rgba(0,0,0,0.35)]'
              }`}
            >
              {isBest && (
                <span className="inline-block w-fit rounded-md bg-gold-cta px-2.5 py-1 text-[10px] font-bold text-bg">
                  ⭐ Best offer
                </span>
              )}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <div className="text-[11px] uppercase tracking-wide text-t3">Платите</div>
                    <div className="tnum font-display text-[18px] font-bold text-t1">{t.pay_usd.toFixed(0)}$</div>
                  </div>
                  <div className="text-base text-t3">→</div>
                  <div>
                    <div className="text-[11px] uppercase tracking-wide text-t3">Получаете</div>
                    <div className="tnum font-display text-[18px] font-extrabold text-gold">{t.balance_usd.toFixed(0)}$</div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="inline-block rounded-md bg-up/10 px-2 py-0.5 text-[11px] font-bold text-up">
                  +{bonus}%
                </span>
                <span
                  className={`rounded-pill px-5 py-2.5 text-[13px] font-extrabold ${
                    isBest
                      ? 'bg-gold-cta text-bg shadow-[0_8px_18px_rgba(232,180,76,0.3)]'
                      : 'border-[1.5px] border-gold bg-transparent text-gold'
                  }`}
                >
                  Купить
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
