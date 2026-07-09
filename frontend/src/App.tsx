import { useEffect, useState } from 'react'
import { ChartModal } from './components/ChartModal'
import { PaymentSheet } from './components/PaymentSheet'
import { TabBar } from './components/TabBar'
import { ToastProvider } from './components/Toast'
import { api } from './lib/api'
import { loadHomeMarkets } from './lib/market'
import { getInitData, initTelegram } from './lib/telegram'
import { Admin } from './screens/admin/Admin'
import { Home } from './screens/Home'
import { Pocket } from './screens/Pocket'
import { Stats } from './screens/Stats'
import { Vip } from './screens/Vip'
import type { AppConfig, Market, Me, PayProduct, Tab } from './types'

export default function App() {
  const [tab, setTab] = useState<Tab>('home')
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [me, setMe] = useState<Me | null>(null)
  const [markets, setMarkets] = useState<Market[]>([])
  const [payProduct, setPayProduct] = useState<PayProduct | null>(null)
  const [chartMarket, setChartMarket] = useState<Market | null>(null)

  useEffect(() => {
    initTelegram()
    api.get<AppConfig>('/api/config').then(setConfig).catch(() => {})
    if (getInitData()) {
      api.get<Me>('/api/me').then(setMe).catch(() => {})
    }
    loadHomeMarkets().then(setMarkets)
    const t = setInterval(() => loadHomeMarkets().then(setMarkets), 30000)
    return () => clearInterval(t)
  }, [])

  return (
    <ToastProvider>
      <div className="mx-auto min-h-screen max-w-md pb-20" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
        {tab === 'home' && <Home markets={markets} config={config} onTab={setTab} onOpenChart={setChartMarket} />}
        {tab === 'vip' && <Vip config={config} onBuy={setPayProduct} />}
        {tab === 'pocket' && <Pocket config={config} onBuy={setPayProduct} />}
        {tab === 'stats' && <Stats config={config} />}
        {tab === 'admin' && me?.is_admin && <Admin config={config} />}
      </div>

      <TabBar tab={tab} onChange={setTab} isAdmin={Boolean(me?.is_admin)} />

      <PaymentSheet
        product={payProduct}
        cryptoOptions={config?.crypto_options ?? []}
        onClose={() => setPayProduct(null)}
      />
      <ChartModal market={chartMarket} onClose={() => setChartMarket(null)} />
    </ToastProvider>
  )
}
