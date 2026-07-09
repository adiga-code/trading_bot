import { Counter } from '../components/Counter'
import { MarketList } from '../components/MarketList'
import { Ticker } from '../components/Ticker'
import { haptic, openExternal } from '../lib/telegram'
import type { AppConfig, Market, Tab } from '../types'

export function Home({
  markets,
  config,
  onTab,
  onOpenChart,
}: {
  markets: Market[]
  config: AppConfig | null
  onTab: (t: Tab) => void
  onOpenChart: (m: Market) => void
}) {
  return (
    <div className="fade-up pb-6">
      {/* hero */}
      <div className="relative overflow-hidden px-5 pb-5 pt-7 text-center">
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-40"
          style={{ background: 'radial-gradient(60% 100% at 50% 0%, rgba(232,180,76,0.14) 0%, transparent 70%)' }}
        />
        <div className="relative">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-gold/30 bg-gold/10 font-display text-2xl font-extrabold text-gold">
            F
          </div>
          <h1 className="mt-3 font-display text-[22px] font-extrabold tracking-wide">FOREX TRD'K</h1>
          <div className="mt-1 flex items-center justify-center gap-1.5 text-[12px] text-t2">
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-up" />
            Premium Crypto Signals · 24/7
          </div>
        </div>
      </div>

      <Ticker markets={markets} />

      {/* стат-карточки */}
      <div className="mt-4 grid grid-cols-4 gap-2 px-4">
        <Stat label="Прибыль" color="text-gold">
          <Counter to={1943} suffix="%" />
        </Stat>
        <Stat label="Win Rate" color="text-up">
          <Counter to={68.9} suffix="%" decimals={1} />
        </Stat>
        <Stat label="Сигналов" color="text-t1">
          <Counter to={45} />
        </Stat>
        <Stat label="Ср. %" color="text-up">
          <Counter to={62.7} suffix="%" decimals={1} />
        </Stat>
      </div>

      {/* рынки */}
      <div className="mt-5 px-4">
        <div className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-t3">Рынки</div>
        <MarketList markets={markets} onOpen={onOpenChart} />
      </div>

      {/* продукты */}
      <div className="mt-5 space-y-2.5 px-4">
        <button
          onClick={() => {
            haptic('light')
            onTab('vip')
          }}
          className="relative w-full overflow-hidden rounded-card border border-gold/25 bg-card p-4 text-left active:scale-[0.99]"
        >
          <div
            className="pointer-events-none absolute inset-0"
            style={{ background: 'radial-gradient(80% 120% at 100% 0%, rgba(232,180,76,0.10) 0%, transparent 60%)' }}
          />
          <div className="flex items-center justify-between">
            <span className="rounded-full bg-gold/15 px-2.5 py-0.5 text-[10px] font-bold tracking-widest text-gold">
              VIP CHANNEL
            </span>
            <Arrow />
          </div>
          <div className="mt-2 font-display text-[17px] font-bold">💎 VIP Канал</div>
          <div className="mt-0.5 text-[12.5px] text-t2">Сигналы с Win Rate 68.9% · от $45/мес</div>
        </button>

        <button
          onClick={() => {
            haptic('light')
            onTab('pocket')
          }}
          className="relative w-full overflow-hidden rounded-card border border-stroke bg-card p-4 text-left active:scale-[0.99]"
        >
          <div
            className="pointer-events-none absolute inset-0"
            style={{ background: 'radial-gradient(80% 120% at 100% 0%, rgba(52,211,153,0.08) 0%, transparent 60%)' }}
          />
          <div className="flex items-center justify-between">
            <span className="rounded-full bg-up/15 px-2.5 py-0.5 text-[10px] font-bold tracking-widest text-up">
              POCKET OPTION
            </span>
            <Arrow />
          </div>
          <div className="mt-2 font-display text-[17px] font-bold">🏦 Pocket Option</div>
          <div className="mt-0.5 text-[12.5px] text-t2">Платишь $65 → получаешь $87 на счёте</div>
        </button>
      </div>

      {/* поддержка */}
      {config && (
        <button
          onClick={() => openExternal(`https://t.me/${config.support_username}`)}
          className="mx-4 mt-4 flex w-[calc(100%-2rem)] items-center gap-3 rounded-card border border-stroke bg-card p-3.5 text-left active:scale-[0.99]"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-el bg-card2 text-lg">🆘</span>
          <span className="flex-1">
            <span className="block text-[14px] font-semibold">Поддержка</span>
            <span className="block text-[12px] text-t3">@{config.support_username} · 24/7</span>
          </span>
          <Arrow />
        </button>
      )}

      {config && (
        <div className="mt-5 flex justify-center gap-4 px-4 text-[11px] text-t3">
          <a href={config.privacy_url} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">
            Политика конфиденциальности
          </a>
          <a href={config.terms_url} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">
            Соглашение
          </a>
        </div>
      )}
    </div>
  )
}

function Stat({ label, color, children }: { label: string; color: string; children: React.ReactNode }) {
  return (
    <div className="rounded-card border border-stroke bg-card px-1 py-3 text-center">
      <div className={`font-display text-[15px] font-bold ${color}`}>{children}</div>
      <div className="mt-0.5 text-[10px] text-t3">{label}</div>
    </div>
  )
}

function Arrow() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4 text-t3" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}
