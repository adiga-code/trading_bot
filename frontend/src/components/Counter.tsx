import { useEffect, useRef, useState } from 'react'

// Анимированный счётчик для стат-карточек
export function Counter({ to, suffix = '', decimals = 0, duration = 1200 }: { to: number; suffix?: string; decimals?: number; duration?: number }) {
  const [value, setValue] = useState(0)
  const raf = useRef<number>()

  useEffect(() => {
    const start = performance.now()
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3)
      setValue(to * eased)
      if (t < 1) raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current)
    }
  }, [to, duration])

  return <span className="tnum">{value.toFixed(decimals)}{suffix}</span>
}
