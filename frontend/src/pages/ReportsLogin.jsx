import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'
import { Eye, EyeOff, ArrowRight, BarChart2 } from 'lucide-react'

export default function ReportsLogin() {
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
      localStorage.setItem('reports_token', access_token)
      navigate('/reports')
    } catch {
      setError('E-mail ou senha inválidos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-paper text-ink">

      {/* ─── LEFT — form ─── */}
      <div className="flex flex-col justify-between p-8 sm:p-12 bg-surface lg:border-r border-line">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="logo-mark w-7 h-7" />
            <span className="font-semibold tracking-tight">Biopark <span className="text-muted font-normal">/ Relatórios</span></span>
          </div>
          <div className="hidden sm:inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-[11px] bg-paper text-muted">
            <span className="dot bg-accent-green" />
            todos os sistemas operando
          </div>
        </div>

        <div className="w-full max-w-sm">
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted mb-3">
            02 / relatórios
          </div>
          <h1 className="text-[40px] sm:text-[44px] font-medium leading-[1.05] tracking-tight">
            Painel executivo
          </h1>
          <p className="text-sm text-muted mt-2 mb-8">
            Confirme seu acesso para visualizar KPIs, gráficos e relatórios analíticos.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">E-mail corporativo</label>
              <input
                type="email"
                required
                placeholder="voce@biopark.com.br"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl text-sm bg-paper border border-line-2 outline-none transition focus:ring-2 focus:ring-ink/10 focus:border-ink/30"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-20 rounded-xl text-sm bg-paper border border-line-2 outline-none transition focus:ring-2 focus:ring-ink/10 focus:border-ink/30"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] font-medium text-muted hover:text-ink px-2 py-1 rounded transition flex items-center gap-1"
                >
                  {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                  {showPassword ? 'ocultar' : 'mostrar'}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <button
                type="button"
                onClick={() => navigate('/')}
                className="text-muted hover:text-ink font-medium transition"
              >
                ← Voltar aos protocolos
              </button>
            </div>

            {error && (
              <div className="flex items-center gap-2.5 bg-red-50 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-sm">
                <span className="dot bg-accent-red" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 bg-ink text-lime hover:bg-ink-2 transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Verificando...
                </>
              ) : (
                <>
                  Acessar relatórios
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        </div>

        <div className="flex items-center justify-between text-[11px] text-muted-faint">
          <span>© {new Date().getFullYear()} Biopark · Relatórios</span>
          <div className="hidden sm:flex gap-4">
            <span>Termos</span><span>Privacidade</span><span>Status</span>
          </div>
        </div>
      </div>

      {/* ─── RIGHT — product preview ─── */}
      <div className="hidden lg:flex flex-col justify-between p-12 relative overflow-hidden bg-paper">
        <div className="absolute inset-0 opacity-60 pointer-events-none bg-grid" />

        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-medium mb-5 bg-ink text-lime">
            <span className="live-dot" />
            Analítico
          </div>
          <h2 className="text-[52px] font-medium leading-[0.98] tracking-tight">
            Dados que<br/>
            <span className="text-muted">revelam padrões,</span><br/>
            decisões melhores.
          </h2>
          <p className="text-sm text-muted mt-5 max-w-md leading-relaxed">
            Visualize a performance dos protocolos, identifique gargalos e acompanhe a evolução de cada processo com gráficos em tempo real.
          </p>
        </div>

        {/* Mock analytics card */}
        <div className="relative z-10 rounded-2xl overflow-hidden shadow-pop bg-surface border border-line-2">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-line bg-paper">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-accent-red/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-accent-amber/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-accent-green/70" />
            </div>
            <div className="font-mono text-[10px] text-muted">biopark.app / relatórios</div>
            <div className="w-12" />
          </div>

          <div className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-muted">Performance · 30d</div>
                <div className="text-2xl font-semibold num mt-0.5">Painel executivo</div>
              </div>
              <div className="flex items-center gap-1 text-xs font-medium text-accent-green">
                <BarChart2 size={12} /> Atualizado
              </div>
            </div>

            {/* KPI mini grid */}
            <div className="grid grid-cols-3 gap-2 mb-4">
              {[['127', 'Total'], ['94', 'Ativos'], ['7', 'Críticos']].map(([n, l]) => (
                <div key={l} className="rounded-lg p-2.5 bg-paper">
                  <div className="text-[10px] text-muted">{l}</div>
                  <div className="text-lg font-semibold num">{n}</div>
                </div>
              ))}
            </div>

            {/* Status bar chart mock */}
            <div className="space-y-1.5">
              {[['Em andamento', 45, '#3454ff'], ['Aprovado', 30, '#2a8a55'], ['Pendente', 15, '#ff8a2a'], ['Outros', 10, '#dfdeda']].map(([label, pct, color]) => (
                <div key={label} className="flex items-center gap-2">
                  <div className="text-[10px] text-muted w-20 truncate">{label}</div>
                  <div className="flex-1 h-1.5 rounded-full bg-line overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
                  </div>
                  <div className="text-[10px] font-mono text-muted w-6 text-right">{pct}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
