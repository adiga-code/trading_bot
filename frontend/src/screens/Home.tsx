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
      <div className="relative overflow-hidden px-5 pb-6 pt-8 text-center">
        <div
          className="pointer-events-none absolute inset-0 bg-cover"
          style={{
            backgroundImage: "url('/assets/hero-bg.jpg')",
            backgroundPosition: 'center 35%',
            filter: 'blur(2px)',
            transform: 'scale(1.05)',
            opacity: 0.75,
          }}
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{ background: 'linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.72) 55%, #000000 100%)' }}
        />
        <div
          className="pointer-events-none absolute -left-12 -top-14 h-56 w-56 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(232,180,76,0.3) 0%, rgba(232,180,76,0) 70%)', filter: 'blur(10px)' }}
        />
        <div
          className="pointer-events-none absolute -right-14 -top-16 h-56 w-56 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(52,211,153,0.24) 0%, rgba(52,211,153,0) 70%)', filter: 'blur(10px)' }}
        />
        <div className="relative flex flex-col items-center gap-4">
          <div className="flex items-center gap-2">
            <img src="/assets/logo-mark.png" alt="" className="h-4 w-4" />
            <span className="font-display text-[14px] font-extrabold tracking-wide">FOREX TRD'K</span>
          </div>
          <img
            src="/assets/btc-coin.png"
            alt=""
            className="ftk-float h-[88px] w-[88px]"
            style={{ filter: 'drop-shadow(0 10px 22px rgba(232,180,76,0.35))' }}
          />
          <div className="flex flex-col items-center gap-2.5">
            <div className="flex items-center gap-1.5 text-[12px] tracking-wide text-t2">
              <span className="live-dot h-1.5 w-1.5 rounded-full bg-up" />
              Premium Crypto Signals · 24/7
            </div>
            <h1
              className="font-display font-extrabold leading-[1.15] tracking-wide text-t1"
              style={{ fontSize: 'clamp(19px, 6.2vw, 26px)' }}
            >
              Точность, за которую
              <br />
              платят профессионалы
            </h1>
          </div>
          <button
            onClick={() => {
              haptic('light')
              onTab('vip')
            }}
            className="w-full rounded-pill bg-gold-cta py-[15px] text-[14px] font-extrabold text-bg shadow-[0_10px_28px_rgba(232,180,76,0.35)] active:scale-[0.98]"
          >
            Открыть VIP-канал
          </button>
        </div>
      </div>

      <Ticker markets={markets} />

      {/* стат-карточки */}
      <div className="mt-4 grid grid-cols-4 gap-2 px-4">
        <Stat label="Прибыль" color="text-gold" highlight>
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
          className="relative w-full overflow-hidden rounded-card bg-[#1B160E] p-4 text-left shadow-[0_0_24px_rgba(232,180,76,0.12),0_6px_16px_rgba(0,0,0,0.35)] active:scale-[0.99]"
        >
          <div className="flex items-center justify-between">
            <span className="rounded-md bg-gold-cta px-2.5 py-1 text-[10px] font-bold tracking-widest text-bg">
              VIP CHANNEL
            </span>
            <Arrow />
          </div>
          <div className="mt-2 font-display text-[15px] font-bold">Приватные сигналы 24/7</div>
          <div className="mt-0.5 text-[12px] text-t2">Вход, тейк-профит, стоп-лосс</div>
        </button>

        <button
          onClick={() => {
            haptic('light')
            onTab('pocket')
          }}
          className="relative w-full overflow-hidden rounded-card bg-[#111C18] p-4 text-left shadow-[0_0_20px_rgba(52,211,153,0.08),0_6px_16px_rgba(0,0,0,0.35)] active:scale-[0.99]"
        >
          <div className="flex items-center justify-between">
            <span className="rounded-md bg-up px-2.5 py-1 text-[10px] font-bold tracking-widest text-bg">
              POCKET OPTION
            </span>
            <Arrow />
          </div>
          <div className="mt-2 font-display text-[15px] font-bold">Готовые аккаунты с балансом</div>
          <div className="mt-0.5 text-[12px] text-t2">Выгода до +52%</div>
        </button>

        {config && (
          <button
            onClick={() => {
              haptic('light')
              openExternal(`https://t.me/${config.support_username}`)
            }}
            className="relative w-full overflow-hidden rounded-card bg-[#22110F] p-4 text-left shadow-[0_0_20px_rgba(248,113,113,0.14),0_6px_16px_rgba(0,0,0,0.35)] active:scale-[0.99]"
          >
            <div className="flex items-center justify-between">
              <span className="rounded-md bg-down px-2.5 py-1 text-[10px] font-bold tracking-widest text-bg">
                ПОДДЕРЖКА
              </span>
              <Arrow />
            </div>
            <div className="mt-2 font-display text-[15px] font-bold">Если возник вопрос</div>
            <div className="mt-0.5 text-[12px] text-t2">Ответим в ближайшее время</div>
          </button>
        )}
      </div>

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

function Stat({
  label,
  color,
  highlight,
  children,
}: {
  label: string
  color: string
  highlight?: boolean
  children: React.ReactNode
}) {
  return (
    <div
      className={`rounded-stat px-1 py-3 text-center ${
        highlight
          ? 'border border-gold/40 bg-[linear-gradient(180deg,#1D1A12_0%,#10141B_100%)] shadow-[0_0_26px_rgba(232,180,76,0.15),0_10px_24px_rgba(0,0,0,0.28)]'
          : 'border border-white/[0.07] bg-[linear-gradient(180deg,#161B26_0%,#10141B_100%)] shadow-[0_10px_24px_rgba(0,0,0,0.28)]'
      }`}
    >
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
