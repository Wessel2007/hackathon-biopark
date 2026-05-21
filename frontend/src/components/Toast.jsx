import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { X, AlertTriangle, AlertCircle } from 'lucide-react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const toast = useCallback((message, type = 'error') => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => dismiss(id), 6000)
  }, [dismiss])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}

function ToastContainer({ toasts, onDismiss }) {
  if (toasts.length === 0) return null
  return (
    <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-2 w-[360px] max-w-[calc(100vw-3rem)]">
      {toasts.map(t => <ToastItem key={t.id} {...t} onDismiss={onDismiss} />)}
    </div>
  )
}

function ToastItem({ id, message, type, onDismiss }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 10)
    return () => clearTimeout(t)
  }, [])

  const styles = {
    error: {
      wrap: 'bg-red-50 border-red-200 shadow-red-100/60',
      text: 'text-red-800',
      sub:  'text-red-600',
      btn:  'text-red-400 hover:text-red-700',
      icon: <AlertCircle size={16} className="text-red-500 shrink-0 mt-0.5" />,
      label: 'Erro na consulta',
    },
    warning: {
      wrap: 'bg-amber-50 border-amber-200 shadow-amber-100/60',
      text: 'text-amber-800',
      sub:  'text-amber-600',
      btn:  'text-amber-400 hover:text-amber-700',
      icon: <AlertTriangle size={16} className="text-amber-500 shrink-0 mt-0.5" />,
      label: 'Atenção',
    },
  }

  const s = styles[type] || styles.error

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3.5 rounded-xl border shadow-lg text-sm transition-all duration-300 ${s.wrap} ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}
    >
      {s.icon}
      <div className="flex-1 min-w-0">
        <p className={`font-semibold text-[12px] uppercase tracking-wider mb-0.5 ${s.sub}`}>{s.label}</p>
        <p className={`leading-snug break-words ${s.text}`}>{message}</p>
      </div>
      <button
        onClick={() => onDismiss(id)}
        className={`shrink-0 transition ${s.btn}`}
        aria-label="Fechar"
      >
        <X size={14} />
      </button>
    </div>
  )
}
