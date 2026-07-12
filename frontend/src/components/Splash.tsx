import { useEffect, useState } from 'react'

export function Splash() {
  const [visible, setVisible] = useState(true)
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const t1 = setTimeout(() => setFading(true), 2600)
    const t2 = setTimeout(() => setVisible(false), 3000)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [])

  if (!visible) return null

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black transition-opacity duration-[400ms] ease-out"
      style={{ opacity: fading ? 0 : 1 }}
    >
      <div className="ftk-logofade flex items-center gap-1.5">
        <img
          src="/assets/logo-mark.png"
          alt="Forex Trd'K"
          className="h-[26px] w-[26px] object-contain"
          style={{ filter: 'drop-shadow(0 6px 16px rgba(52,211,153,0.3))' }}
        />
        <span className="font-display text-[20px] font-extrabold tracking-wide text-t1">FOREX TRD'K</span>
      </div>
    </div>
  )
}
