export function fmtPrice(p: number | null | undefined): string {
  if (p == null || isNaN(p)) return '—'
  if (p >= 1000) return p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (p >= 1) return p.toFixed(2)
  return p.toFixed(4)
}

export function fmtPct(p: number | null | undefined): string {
  if (p == null || isNaN(p)) return '—'
  return `${p >= 0 ? '+' : ''}${p.toFixed(2)}%`
}

export function fmtUsd(v: number): string {
  return `${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}$`
}

/** '45.00000000' → '45' */
export function fmtCrypto(amount: string): string {
  const v = parseFloat(amount)
  if (isNaN(v)) return amount
  return v.toFixed(8).replace(/\.?0+$/, '')
}

export function fmtDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
