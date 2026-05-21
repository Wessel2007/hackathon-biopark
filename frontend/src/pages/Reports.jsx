import { useQuery } from '@tanstack/react-query'
import { getDashboardData, downloadPdf } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, Building2, ClipboardList, CheckCircle2, AlertTriangle, BarChart3, Zap } from 'lucide-react'

export default function Reports() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardData })

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-brand-950 border-b border-brand-900/50 text-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="text-brand-400 hover:text-white transition">
              <ArrowLeft size={16} />
            </button>
            <div className="w-px h-5 bg-brand-800" />
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-brand-600 rounded-md flex items-center justify-center">
                <BarChart3 size={12} />
              </div>
              <span className="font-semibold text-sm">Relatórios</span>
            </div>
          </div>
          <button
            onClick={downloadPdf}
            className="flex items-center gap-1.5 bg-brand-800 hover:bg-brand-700 text-white px-3 py-1.5 rounded-lg text-sm transition"
          >
            <Download size={13} /> Baixar PDF
          </button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-gray-400 text-sm">
              <svg className="animate-spin h-5 w-5 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Carregando relatório...
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Relatórios</h1>
              <p className="text-sm text-gray-400 mt-0.5">Resumo consolidado de protocolos por projeto</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <ReportCard label="Total de Protocolos"  value={data?.total}               icon={ClipboardList} color="blue" />
              <ReportCard label="Protocolos Ativos"    value={data?.ativos}              icon={CheckCircle2}  color="green" />
              <ReportCard label="Com Mudança Recente"  value={data?.com_mudanca_recente} icon={Zap}           color="amber" />
            </div>

            {Object.entries(data?.por_projeto ?? {}).map(([projeto, items]) => (
              <div key={projeto} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2.5 bg-gray-50/60">
                  <div className="w-7 h-7 bg-brand-100 rounded-lg flex items-center justify-center">
                    <Building2 size={13} className="text-brand-700" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{projeto}</h3>
                    <p className="text-xs text-gray-400">{items.length} protocolo(s)</p>
                  </div>
                </div>
                <div className="divide-y divide-gray-50">
                  <div className="px-5 py-2 flex items-center justify-between gap-4 bg-gray-50/60 border-b border-gray-100">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider flex-shrink-0">Protocolo</span>
                      <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Status</span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] font-semibold text-gray-400 uppercase tracking-wider flex-shrink-0">
                      <span>Duração</span>
                      <span>Última Consulta</span>
                      <span className="w-16 text-center">Situação</span>
                    </div>
                  </div>
                  {items.map((p) => (
                    <div key={p.id} className="px-5 py-3.5 flex items-center justify-between gap-4 hover:bg-gray-50/50 transition-colors">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="font-mono text-xs text-gray-400 flex-shrink-0">{p.protocolo}</span>
                        <StatusPill status={p.status} changed={p.houve_mudanca} />
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-400 flex-shrink-0">
                        <span>{p.duracao_dias != null ? `${p.duracao_dias} dias` : '—'}</span>
                        <span>{p.ultima_consulta ? new Date(p.ultima_consulta).toLocaleDateString('pt-BR') : 'sem consulta'}</span>
                        <span className="w-16 flex justify-center">
                          {p.houve_mudanca && (
                            <span className="flex items-center gap-1 text-amber-600 font-medium bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full">
                              <AlertTriangle size={10} /> Mudança
                            </span>
                          )}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ReportCard({ label, value, icon: Icon, color }) {
  const c = {
    blue:  { bar: 'bg-brand-600',   icon: 'bg-brand-50  text-brand-600'   },
    green: { bar: 'bg-emerald-500', icon: 'bg-emerald-50 text-emerald-600' },
    amber: { bar: 'bg-amber-400',   icon: 'bg-amber-50  text-amber-600'   },
  }[color]
  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
      <div className={`h-1 ${c.bar}`} />
      <div className="px-5 py-5 flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{label}</p>
          <p className="text-4xl font-bold text-gray-900 mt-2 leading-none tabular-nums">{value ?? 0}</p>
        </div>
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${c.icon}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

function StatusPill({ status, changed }) {
  const map = {
    APRO:           'bg-emerald-50 text-emerald-700 border-emerald-200',
    APROVADO:       'bg-emerald-50 text-emerald-700 border-emerald-200',
    'EM ANDAMENTO': 'bg-blue-50 text-blue-700 border-blue-200',
    PENDENTE:       'bg-amber-50 text-amber-700 border-amber-200',
    CANCELADO:      'bg-red-50 text-red-700 border-red-200',
    REPROVADO:      'bg-red-50 text-red-700 border-red-200',
  }
  const base = changed
    ? 'bg-amber-100 text-amber-800 border-amber-300'
    : (map[status] ?? 'bg-gray-100 text-gray-600 border-gray-200')
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border leading-none ${base}`}>
      {status === 'EM ANDAMENTO' ? 'ANDAMENTO' : status}
    </span>
  )
}
