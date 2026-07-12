import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { fmtCrypto, fmtUsd } from '../lib/format'
import { haptic, hapticNotify, openExternal, openInvoice } from '../lib/telegram'
import type { CryptoOption, PayProduct } from '../types'
import { useToast } from './Toast'

type Step = 'method' | 'crypto' | 'loading' | 'details' | 'error'

type InvoiceDetails = {
  url: string
  tg_link: string
  address: string
  payer_amount: string
  payer_currency: string
  expires_at: string
}

export function PaymentSheet({
  product,
  cryptoOptions,
  onClose,
}: {
  product: PayProduct | null
  cryptoOptions: CryptoOption[]
  onClose: () => void
}) {
  const toast = useToast()
  const [step, setStep] = useState<Step>('method')
  const [details, setDetails] = useState<InvoiceDetails | null>(null)
  const [error, setError] = useState('')
  const [loadingText, setLoadingText] = useState('Создаём счёт…')
  const [now, setNow] = useState(Date.now())

  useEffect(() => {
    setStep('method')
    setDetails(null)
    setError('')
  }, [product])

  useEffect(() => {
    if (step !== 'details' || !details?.expires_at) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [step, details])

  const timeLeft = useMemo(() => {
    if (!details?.expires_at) return null
    const diff = new Date(details.expires_at).getTime() - now
    if (isNaN(diff) || diff <= 0) return '0:00'
    const m = Math.floor(diff / 60000)
    const s = Math.floor((diff % 60000) / 1000)
    return `${m}:${String(s).padStart(2, '0')}`
  }, [details, now])

  if (!product) return null

  const fail = (msg: string) => {
    hapticNotify('error')
    setError(msg)
    setStep('error')
  }

  const payCrypto = async (opt: CryptoOption) => {
    haptic('medium')
    setLoadingText('Создаём счёт…')
    setStep('loading')
    try {
      const res = await api.post<InvoiceDetails>('/api/pay', {
        type: product.type,
        plan: product.plan,
        cur: opt.cur,
        net: opt.net,
      })
      setDetails(res)
      hapticNotify('success')
      setStep('details')
    } catch (e) {
      fail(e instanceof Error ? e.message : 'Ошибка платёжного шлюза')
    }
  }

  const payStars = async () => {
    haptic('medium')
    setLoadingText('Готовим счёт Stars…')
    setStep('loading')
    try {
      const res = await api.post<{ link: string }>('/api/stars', {
        type: product.type,
        plan: product.plan,
      })
      openInvoice(res.link, (status) => {
        if (status === 'paid') {
          hapticNotify('success')
          toast('Оплата прошла! 🎉')
        }
      })
      onClose()
    } catch (e) {
      fail(e instanceof Error ? e.message : 'Ошибка Stars')
    }
  }

  const copyAddress = () => {
    if (!details?.address) return
    navigator.clipboard?.writeText(details.address)
    haptic('light')
    toast('Адрес скопирован')
  }

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60" onClick={onClose} />
      <div
        className="sheet-in fixed bottom-0 left-0 right-0 z-50 mx-auto max-w-md rounded-t-[20px] border-t border-white/[0.08] bg-sheet"
        style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 16px)' }}
      >
        <div className="mx-auto mt-2.5 h-1 w-10 rounded-full bg-t3/40" />
        <div className="px-5 pt-4">
          {step === 'method' && (
            <div className="fade-up">
              <div className="font-display text-[17px] font-bold">Способ оплаты</div>
              <div className="tnum mt-0.5 text-[13px] text-t2">
                {product.name} · <span className="text-gold">{fmtUsd(product.amountUsd)}</span>
              </div>
              <button
                onClick={() => {
                  haptic('light')
                  setStep('crypto')
                }}
                className="mt-4 flex w-full items-center gap-3 rounded-card bg-card2 p-3.5 text-left active:scale-[0.99]"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-el bg-gold/15 text-lg">₿</span>
                <span className="flex-1">
                  <span className="block text-[14px] font-semibold">Криптовалюта</span>
                  <span className="block text-[12px] text-t3">BTC, ETH, USDT, TON, SOL и другие</span>
                </span>
                <Chevron />
              </button>
              <button
                onClick={payStars}
                className="mt-2.5 flex w-full items-center gap-3 rounded-card bg-card2 p-3.5 text-left active:scale-[0.99]"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-el bg-gold/15 text-lg">⭐</span>
                <span className="flex-1">
                  <span className="block text-[14px] font-semibold">Telegram Stars</span>
                  <span className="tnum block text-[12px] text-t3">{product.stars.toLocaleString('ru-RU')} ⭐</span>
                </span>
                <Chevron />
              </button>
            </div>
          )}

          {step === 'crypto' && (
            <div className="fade-up">
              <div className="font-display text-[17px] font-bold">Выберите криптовалюту</div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                {cryptoOptions.map((opt) => (
                  <button
                    key={`${opt.cur}-${opt.net}`}
                    onClick={() => payCrypto(opt)}
                    className="rounded-el bg-card2 px-3 py-2.5 text-left text-[13px] font-medium active:scale-[0.98]"
                  >
                    {opt.label}
                    <span className="block text-[10.5px] font-normal text-t3">{opt.net}</span>
                  </button>
                ))}
              </div>
              <button onClick={() => setStep('method')} className="mt-3 w-full py-2 text-[13px] text-t2">
                ← Назад
              </button>
            </div>
          )}

          {step === 'loading' && (
            <div className="fade-up flex flex-col items-center py-10">
              <div className="h-9 w-9 animate-spin rounded-full border-2 border-stroke border-t-gold" />
              <div className="mt-4 text-[13px] text-t2">{loadingText}</div>
            </div>
          )}

          {step === 'details' && details && (
            <div className="fade-up">
              <div className="flex items-center gap-2 text-up">
                <span className="text-lg">✓</span>
                <span className="font-display text-[16px] font-bold text-t1">Счёт создан</span>
              </div>
              <div className="mt-3 rounded-card bg-card2 p-4">
                <div className="text-[11px] uppercase tracking-wide text-t3">К оплате</div>
                <div className="tnum mt-1 font-display text-[22px] font-bold text-gold">
                  {fmtCrypto(details.payer_amount)} {details.payer_currency}
                </div>
                {details.address && (
                  <button onClick={copyAddress} className="mt-3 w-full text-left">
                    <div className="text-[11px] uppercase tracking-wide text-t3">Адрес (нажмите — копия)</div>
                    <div className="tnum mt-1 break-all rounded-el bg-bg px-3 py-2 text-[12px] text-t2">
                      {details.address}
                    </div>
                  </button>
                )}
                {timeLeft && (
                  <div className="mt-3 text-[12px] text-t3">
                    Истекает через <span className="tnum font-semibold text-t1">{timeLeft}</span>
                  </div>
                )}
              </div>
              {details.url && (
                <button
                  onClick={() => openExternal(details.url)}
                  className="mt-3 w-full rounded-pill bg-gold-cta py-[15px] text-[14px] font-extrabold text-bg shadow-[0_10px_26px_rgba(232,180,76,0.35)] active:scale-[0.99]"
                >
                  💳 Оплатить онлайн
                </button>
              )}
              {details.tg_link && details.tg_link !== details.url && (
                <button
                  onClick={() => openExternal(details.tg_link)}
                  className="mt-2 w-full rounded-pill border border-white/[0.12] bg-transparent py-3 text-[14px] font-semibold text-t2 active:scale-[0.99]"
                >
                  ⚡ Оплатить в Telegram
                </button>
              )}
              <div className="mt-3 pb-1 text-center text-[12px] text-t3">
                Бот проверит оплату автоматически и выдаст доступ
              </div>
            </div>
          )}

          {step === 'error' && (
            <div className="fade-up flex flex-col items-center py-8">
              <div className="text-3xl">😕</div>
              <div className="mt-2 text-center text-[13.5px] text-t2">{error}</div>
              <button
                onClick={() => setStep('method')}
                className="mt-4 rounded-pill bg-gold-cta px-6 py-2.5 text-[13px] font-bold text-bg"
              >
                Попробовать другой способ
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

function Chevron() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4 text-t3" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}
