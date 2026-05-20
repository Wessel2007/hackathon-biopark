import { useQuery } from '@tanstack/react-query'
import { getDashboardData, downloadPdf, runAllQueries } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { FileText, RefreshCw, LogOut, AlertTriangle } from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const { data, isLoading, refetch } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardData })

  function handleLogout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  async function handleRunAll() {
    await runAllQueries()
    setTimeout(() => refetch(), 3000)
  }

  if (isLoading) return <div className="p-8 text-gray-500">Carregando...</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-brand-900 text-white px-6 py-4 flex justify-between items-center">
        <h1 className="text-lg font-bold">Biopark — Protocolos</h1>
        <div className="flex gap-4 text-sm">
          <button onClick={() => navigate('/protocols')} className="hover:underline">Protocolos</button>
          <button onClick={() => navigate('/reports')} className="hover:underline">Relatórios</button>
          <button onClick={handleLogout} className="flex items-center gap-1 hover:underline">
            <LogOut size={14} /> Sair
          </button>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-brand-900">Visão Geral</h2>
          <div className="flex gap-2">
            <button
              onClick={handleRunAll}
              className="flex items-center gap-2 bg-brand-700 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-900 transition"
            >
              <RefreshCw size={14} /> Consultar Todos
            </button>
            <button
              onClick={downloadPdf}
              className="flex items-center gap-2 border border-brand-700 text-brand-700 px-4 py-2 rounded-lg text-sm hover:bg-brand-50 transition"
            >
              <FileText size={14} /> Baixar PDF
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Total de Protocolos" value={data?.total ?? 0} />
          <StatCard label="Protocolos Ativos" value={data?.ativos ?? 0} color="text-green-600" />
          <StatCard label="Com Mudança Recente" value={data?.com_mudanca_recente ?? 0} color="text-amber-600" />
        </div>

        {Object.entries(data?.por_projeto ?? {}).map(([projeto, items]) => (
          <div key={projeto} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="bg-brand-50 px-4 py-3 border-b border-gray-100">
              <h3 className="font-semibold text-brand-900">{projeto}</h3>
              <span className="text-xs text-gray-500">{items.length} protocolo(s)</span>
            </div>
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-500 bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2">Protocolo</th>
                  <th className="text-left px-4 py-2">Status</th>
                  <th className="text-left px-4 py-2">Situação</th>
                  <th className="text-left px-4 py-2">Duração</th>
                  <th className="text-left px-4 py-2">Última Consulta</th>
                  <th className="text-left px-4 py-2">Mudança</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id} className="border-t border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs">{p.protocolo}</td>
                    <td className="px-4 py-2"><StatusBadge status={p.status} /></td>
                    <td className="px-4 py-2 text-gray-600">{p.situacao ?? '-'}</td>
                    <td className="px-4 py-2">{p.duracao_dias ?? '-'} dias</td>
                    <td className="px-4 py-2 text-gray-400 text-xs">{p.ultima_consulta ? new Date(p.ultima_consulta).toLocaleString('pt-BR') : '-'}</td>
                    <td className="px-4 py-2">
                      {p.houve_mudanca && <AlertTriangle size={14} className="text-amber-500" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  )
}

function StatCard({ label, value, color = 'text-brand-900' }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
    </div>
  )
}

function StatusBadge({ status }) {
  const map = {
    APRO: 'bg-green-100 text-green-800',
    'EM ANDAMENTO': 'bg-blue-100 text-blue-800',
    PENDENTE: 'bg-yellow-100 text-yellow-800',
    CANCELADO: 'bg-red-100 text-red-800',
    REPROVADO: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[status] ?? 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  )
}
