import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getDashboardData, downloadPdf, runAllQueries } from '../services/api'
import { useNavigate } from 'react-router-dom'
import {
  FileText, RefreshCw, LogOut, AlertTriangle,
  Building2, ClipboardList, BarChart3, CheckCircle2, Zap, ChevronDown,
} from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const [selectedProject, setSelectedProject] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const { data, isLoading, refetch } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardData })

  function handleLogout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  async function handleRunAll() {
    await runAllQueries()
    setTimeout(() => refetch(), 3000)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-brand-950 border-b border-brand-900/50 text-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
              <Building2 size={14} />
            </div>
            <span className="font-bold text-sm tracking-tight">Biopark</span>
            <span className="text-brand-700 text-sm select-none">·</span>
            <span className="text-brand-300 text-sm">Protocolos</span>
          </div>
          <div className="flex items-center gap-1">
            <NavBtn onClick={() => navigate('/protocols')} icon={ClipboardList}>Protocolos</NavBtn>
            <NavBtn onClick={() => navigate('/reports')} icon={BarChart3}>Relatórios</NavBtn>
            <div className="w-px h-5 bg-brand-800 mx-1" />
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-brand-400 hover:text-white hover:bg-brand-800 text-sm transition"
            >
              <LogOut size={13} /> Sair
            </button>
          </div>
        </div>
      </nav>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Spinner />
        </div>
      ) : (
        <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Visão Geral</h1>
              <p className="text-sm text-gray-400 mt-0.5">Painel de acompanhamento de protocolos</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleRunAll}
                className="flex items-center gap-2 bg-brand-700 hover:bg-brand-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
              >
                <RefreshCw size={14} /> Consultar Todos
              </button>
              <button
                onClick={downloadPdf}
                className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition shadow-sm"
              >
                <FileText size={14} /> Baixar PDF
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard label="Total de Protocolos"  value={data?.total ?? 0}                icon={ClipboardList} color="blue" />
            <StatCard label="Protocolos Ativos"    value={data?.ativos ?? 0}               icon={CheckCircle2}  color="green" />
            <StatCard label="Com Mudança Recente"  value={data?.com_mudanca_recente ?? 0}  icon={Zap}           color="amber" />
          </div>

          {/* Seletor de empreendimento */}
          {Object.keys(data?.por_projeto ?? {}).length > 1 && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-500 font-medium whitespace-nowrap">Empreendimento</label>
              <div className="relative">
                {dropdownOpen && (
                  <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
                )}
                <button
                  onClick={() => setDropdownOpen(v => !v)}
                  className="relative flex items-center gap-2 bg-white border border-gray-200 rounded-xl pl-8 pr-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm transition min-w-56"
                >
                  <Building2 size={13} className="absolute left-3 text-gray-400 pointer-events-none" />
                  <span className="flex-1 text-left truncate">
                    {selectedProject || 'Todos os empreendimentos'}
                  </span>
                  <ChevronDown size={13} className={`text-gray-400 transition-transform flex-shrink-0 ${dropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {dropdownOpen && (
                  <div className="absolute top-full left-0 mt-1 z-20 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden min-w-full">
                    <ul className="max-h-[324px] overflow-y-auto py-1">
                      <li>
                        <button
                          onClick={() => { setSelectedProject(''); setDropdownOpen(false) }}
                          className={`w-full text-left px-4 py-2 text-sm transition ${selectedProject === '' ? 'bg-brand-50 text-brand-700 font-medium' : 'text-gray-700 hover:bg-gray-50'}`}
                        >
                          Todos os empreendimentos
                        </button>
                      </li>
                      {Object.entries(data.por_projeto).map(([projeto, items]) => (
                        <li key={projeto}>
                          <button
                            onClick={() => { setSelectedProject(projeto); setDropdownOpen(false) }}
                            className={`w-full text-left px-4 py-2 text-sm transition flex items-center justify-between gap-4 ${selectedProject === projeto ? 'bg-brand-50 text-brand-700 font-medium' : 'text-gray-700 hover:bg-gray-50'}`}
                          >
                            <span className="truncate">{projeto}</span>
                            <span className={`text-xs px-1.5 py-0.5 rounded-full flex-shrink-0 ${selectedProject === projeto ? 'bg-brand-100 text-brand-700' : 'bg-gray-100 text-gray-500'}`}>
                              {items.length}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {Object.entries(data?.por_projeto ?? {})
            .filter(([projeto]) => !selectedProject || projeto === selectedProject)
            .map(([projeto, items]) => (
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
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-50">
                    {['Protocolo', 'Status', 'Situação', 'Duração', 'Última Consulta', 'Mudança'].map(h => (
                      <th key={h} className="text-left px-5 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {items.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="px-5 py-3 font-mono text-xs text-gray-500">{p.protocolo}</td>
                      <td className="px-5 py-3"><StatusBadge status={p.status} /></td>
                      <td className="px-5 py-3 text-gray-500 text-xs">{p.situacao ?? <span className="text-gray-300">—</span>}</td>
                      <td className="px-5 py-3 text-gray-400 text-xs">{p.duracao_dias != null ? `${p.duracao_dias} dias` : <span className="text-gray-300">—</span>}</td>
                      <td className="px-5 py-3 text-gray-400 text-xs">
                        {p.ultima_consulta ? new Date(p.ultima_consulta).toLocaleString('pt-BR') : <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-5 py-3">
                        {p.houve_mudanca && (
                          <span className="inline-flex items-center gap-1 text-xs bg-amber-50 text-amber-700 border border-amber-100 px-2 py-0.5 rounded-full">
                            <AlertTriangle size={10} /> Mudança
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function NavBtn({ onClick, icon: Icon, children }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-brand-300 hover:text-white hover:bg-brand-800 text-sm transition"
    >
      <Icon size={13} /> {children}
    </button>
  )
}

function StatCard({ label, value, icon: Icon, color }) {
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
          <p className="text-4xl font-bold text-gray-900 mt-2 leading-none tabular-nums">{value}</p>
        </div>
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${c.icon}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }) {
  const map = {
    APRO:         'bg-emerald-50 text-emerald-700 border-emerald-200',
    APROVADO:     'bg-emerald-50 text-emerald-700 border-emerald-200',
    'EM ANDAMENTO': 'bg-blue-50 text-blue-700 border-blue-200',
    PENDENTE:     'bg-amber-50 text-amber-700 border-amber-200',
    CANCELADO:    'bg-red-50 text-red-700 border-red-200',
    REPROVADO:    'bg-red-50 text-red-700 border-red-200',
  }
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border leading-none ${map[status] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}>
      {status === 'EM ANDAMENTO' ? 'ANDAMENTO' : status}
    </span>
  )
}

function Spinner() {
  return (
    <div className="flex items-center gap-3 text-gray-400 text-sm">
      <svg className="animate-spin h-5 w-5 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      Carregando dados...
    </div>
  )
}
