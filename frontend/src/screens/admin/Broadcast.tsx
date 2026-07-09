import { useState } from 'react'
import { api } from '../../lib/api'
import { hapticNotify } from '../../lib/telegram'
import { useToast } from '../../components/Toast'

export function Broadcast() {
  const toast = useToast()
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [confirm, setConfirm] = useState(false)

  const send = async () => {
    setSending(true)
    try {
      const res = await api.post<{ recipients: number }>('/api/admin/broadcast', { text: text.trim() })
      hapticNotify('success')
      toast(`Рассылка запущена: ${res.recipients} получателей`)
      setText('')
      setConfirm(false)
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Ошибка')
    }
    setSending(false)
  }

  return (
    <div>
      <div className="rounded-card border border-stroke bg-card p-4">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-t3">Сообщение всем пользователям</div>
        <textarea
          value={text}
          onChange={(e) => {
            setText(e.target.value)
            setConfirm(false)
          }}
          rows={5}
          placeholder={'Текст рассылки…\nМожно использовать HTML: <b>жирный</b>, <i>курсив</i>'}
          className="mt-2 w-full rounded-el border border-stroke bg-card2 px-3 py-2 text-[13px] placeholder:text-t3 focus:border-gold/50 focus:outline-none"
        />
        {text.trim() && (
          <div className="mt-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-t3">Предпросмотр</div>
            <div
              className="mt-1.5 rounded-el bg-bg px-3 py-2.5 text-[13px] leading-relaxed"
              dangerouslySetInnerHTML={{ __html: text }}
            />
          </div>
        )}
        {!confirm ? (
          <button
            onClick={() => setConfirm(true)}
            disabled={!text.trim()}
            className="mt-3 w-full rounded-el border border-stroke bg-card2 py-2.5 text-[13.5px] font-bold disabled:opacity-40"
          >
            Отправить рассылку
          </button>
        ) : (
          <button
            onClick={send}
            disabled={sending}
            className="mt-3 w-full rounded-el bg-down py-2.5 text-[13.5px] font-bold text-bg disabled:opacity-60"
          >
            {sending ? 'Запускаем…' : '⚠️ Подтвердить: отправить ВСЕМ'}
          </button>
        )}
      </div>
    </div>
  )
}
