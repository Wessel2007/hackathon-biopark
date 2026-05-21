import { useNavigate } from 'react-router-dom'
import { ShieldOff } from 'lucide-react'

export default function Forbidden() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-paper text-ink p-8">
      <div className="flex flex-col items-center gap-4 max-w-sm text-center">
        <div className="w-14 h-14 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center">
          <ShieldOff size={24} className="text-accent-red" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Acesso negado</h1>
          <p className="text-sm text-muted mt-2">
            Você não tem permissão para acessar esta área. Apenas administradores podem visualizar os relatórios.
          </p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="mt-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-ink text-lime hover:bg-ink-2 transition"
        >
          Voltar ao início
        </button>
      </div>
    </div>
  )
}
