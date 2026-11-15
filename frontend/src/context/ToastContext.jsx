import { createContext, useCallback, useContext, useState } from 'react'
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react'

const ToastCtx = createContext(null)
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const dismiss = useCallback((id) => setItems((p) => p.filter((t) => t.id !== id)), [])
  const push = useCallback(
    (type, message) => {
      const id = Math.random().toString(36).slice(2)
      setItems((p) => [...p, { id, type, message }])
      setTimeout(() => dismiss(id), 5000)
    },
    [dismiss],
  )
  const api = {
    success: (m) => push('success', m),
    error: (m) => push('error', m),
    info: (m) => push('info', m),
  }
  const Icon = { success: CheckCircle2, error: AlertTriangle, info: Info }
  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {items.map((t) => {
          const I = Icon[t.type]
          return (
            <div key={t.id} className={`toast toast-${t.type}`}>
              <I size={18} />
              <span>{t.message}</span>
              <button onClick={() => dismiss(t.id)} aria-label="Dismiss"><X size={14} /></button>
            </div>
          )
        })}
      </div>
    </ToastCtx.Provider>
  )
}
