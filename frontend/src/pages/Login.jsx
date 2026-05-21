import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'
import { Building2, Eye, EyeOff, Shield, Clock, Zap } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { access_token } = await login(email, password)
      localStorage.setItem('token', access_token)
      navigate('/')
    } catch {
      setError('E-mail ou senha inválidos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-3/5 relative bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800 flex-col justify-between p-12 overflow-hidden">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/5 rounded-full" />
        <div className="absolute -bottom-32 -left-32 w-[500px] h-[500px] bg-white/5 rounded-full" />
        <div className="absolute top-1/2 right-0 w-72 h-72 bg-brand-700/20 rounded-full translate-x-1/2 -translate-y-1/2" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-9 h-9 bg-brand-600 rounded-xl flex items-center justify-center shadow-lg">
            <Building2 className="text-white" size={18} />
          </div>
          <span className="text-white text-xl font-bold tracking-tight">Biopark</span>
        </div>

        <div className="relative z-10 space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold text-white leading-tight">
              Gestão inteligente<br />de protocolos<br />
              <span className="text-brand-300">públicos</span>
            </h1>
            <p className="text-brand-200 text-base leading-relaxed max-w-sm">
              Centralize e monitore todas as suas tramitações em órgãos públicos em uma única plataforma.
            </p>
          </div>

          <div className="space-y-3.5">
            {[
              { icon: Zap,    text: 'Consultas automáticas em tempo real' },
              { icon: Shield, text: 'Alertas de mudança instantâneos' },
              { icon: Clock,  text: 'Histórico completo de tramitações' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-8 h-8 bg-brand-700/60 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Icon size={15} className="text-brand-300" />
                </div>
                <span className="text-brand-100 text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-brand-500 text-xs">
          © {new Date().getFullYear()} Biopark · Todos os direitos reservados
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center bg-gray-50 p-8">
        <div className="w-full max-w-sm space-y-8">
          <div className="lg:hidden flex items-center gap-3">
            <div className="w-9 h-9 bg-brand-700 rounded-xl flex items-center justify-center">
              <Building2 className="text-white" size={18} />
            </div>
            <span className="text-brand-900 text-xl font-bold">Biopark</span>
          </div>

          <div>
            <h2 className="text-2xl font-bold text-gray-900">Acesse sua conta</h2>
            <p className="mt-1 text-gray-500 text-sm">Informe suas credenciais para continuar</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-gray-700">E-mail</label>
              <input
                type="email"
                required
                placeholder="seuemail@empresa.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition shadow-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-gray-700">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 pr-11 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2.5 bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl text-sm">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full flex-shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-700 hover:bg-brand-800 text-white rounded-xl py-3 text-sm font-semibold transition shadow-md shadow-brand-700/20 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Entrando...
                </>
              ) : 'Entrar'}
            </button>
          </form>

          <p className="text-center text-xs text-gray-400">
            Biopark · Gestão de Protocolos Públicos
          </p>
        </div>
      </div>
    </div>
  )
}
