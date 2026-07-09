// Обёртка над Telegram WebApp SDK: работает и в браузере без Telegram (dev-режим)

type TgWebApp = {
  initData: string
  ready: () => void
  expand: () => void
  setHeaderColor: (c: string) => void
  setBackgroundColor: (c: string) => void
  openLink: (url: string) => void
  openTelegramLink: (url: string) => void
  openInvoice: (url: string, cb?: (status: string) => void) => void
  BackButton: { show: () => void; hide: () => void; onClick: (cb: () => void) => void; offClick: (cb: () => void) => void }
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
  }
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TgWebApp }
  }
}

export const tg: TgWebApp | undefined = window.Telegram?.WebApp

export function initTelegram() {
  if (!tg) return
  try {
    tg.ready()
    tg.expand()
    tg.setHeaderColor('#0B0E14')
    tg.setBackgroundColor('#0B0E14')
  } catch {
    /* старые клиенты не знают части методов */
  }
}

export function getInitData(): string {
  return tg?.initData ?? ''
}

export function haptic(style: 'light' | 'medium' | 'heavy' = 'light') {
  try {
    tg?.HapticFeedback?.impactOccurred(style)
  } catch {
    /* noop */
  }
}

export function hapticNotify(type: 'error' | 'success' | 'warning') {
  try {
    tg?.HapticFeedback?.notificationOccurred(type)
  } catch {
    /* noop */
  }
}

export function openExternal(url: string) {
  if (!url) return
  if (tg) {
    if (url.startsWith('https://t.me/')) tg.openTelegramLink(url)
    else tg.openLink(url)
  } else {
    window.open(url, '_blank')
  }
}

export function openInvoice(url: string, cb?: (status: string) => void) {
  if (tg?.openInvoice) tg.openInvoice(url, cb)
  else window.open(url, '_blank')
}
