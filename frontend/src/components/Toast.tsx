import { createContext, useCallback, useContext, useRef, useState } from 'react'

const ToastCtx = createContext<(msg: string) => void>(() => {})

export function useToast() {
  return useContext(ToastCtx)
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout>>()

  const show = useCallback((m: string) => {
    setMsg(m)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setMsg(null), 2200)
  }, [])

  return (
    <ToastCtx.Provider value={show}>
      {children}
      {msg && (
        <div className="fade-up fixed bottom-24 left-1/2 z-[60] -translate-x-1/2 rounded-el border border-stroke bg-card2 px-4 py-2 text-[13px] text-t1 shadow-xl">
          {msg}
        </div>
      )}
    </ToastCtx.Provider>
  )
}
