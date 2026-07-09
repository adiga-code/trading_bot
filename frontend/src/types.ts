export type VipPlan = {
  key: string
  name: string
  months: number | null
  price_usd: number
  old_price_usd: number
  stars: number
}

export type PocketTier = {
  index: number
  pay_usd: number
  balance_usd: number
  stars: number
  name: string
}

export type CryptoOption = { label: string; cur: string; net: string }

export type AppConfig = {
  vip_plans: VipPlan[]
  pocket_tiers: PocketTier[]
  crypto_options: CryptoOption[]
  trading_pairs: string[]
  support_username: string
  privacy_url: string
  terms_url: string
}

export type Me = {
  id: number
  username: string | null
  is_admin: boolean
  is_vip: boolean
  vip_expires_at: string | null
}

export type Market = {
  symbol: string
  name: string
  price: number | null
  pct: number | null
  closes: number[]
  kind: 'crypto' | 'metal'
  metalKey?: 'gold' | 'silver'
  ysym?: string
}

export type PayProduct = {
  type: 'vip' | 'pocket'
  plan: string
  name: string
  amountUsd: number
  stars: number
}

export type Tab = 'home' | 'vip' | 'pocket' | 'stats' | 'admin'
