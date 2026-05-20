import { useQuery } from '@tanstack/react-query'
import { getDashboardData, downloadPdf } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Download } from 'lucide-react'

export default function Reports() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardData })

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-brand-900 text-white px-6 py-4 flex justify-between items-center">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:underline text-sm">
          <ArrowLeft size={14} /> Dashboard
        </button>
        <h1 className="text-lg font-bold">Relatórios</h1>
        <button onClick={downloadPdf} className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded text-sm hover:bg-white/20">
          <Download size={14} /> Baixar PDF
        </button>
      </nav>

      <div className="max-w-5xl mx-auto p-6">
        {isLoading ? <p className="text-gray-500">Carregando...</p> : (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <Card label="Total" value={data?.total} />
              <Card label="Ativos" value={data?.ativos} color="text-green-600" />
              <Card label="Com Mudança" value={data?.com_mudanca_recente} color="text-amber-600" />
            </div>

            {Object.entries(data?.por_projeto ?? {}).map(([projeto, items]) => (
              <div key={projeto} className="bg-white rounded-xl border shadow-sm overflow-hidden">
                <div className="bg-brand-50 px-4 py-3 font-semibold text-brand-900 border-b">
                  {projeto} — {items.length} protocolo(s)
                </div>
                <div className="divide-y">
                  {items.map((p) => (
                    <div key={p.id} className="px-4 py-3 flex justify-between items-center text-sm">
                      <div>
                        <span className="font-mono text-xs text-gray-500">{p.protocolo}</span>
                        <span className={`ml-3 px-2 py-0.5 rounded-full text-xs ${p.houve_mudanca ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-600'}`}>
                          {p.status}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400">
                        {p.duracao_dias ?? '-'} dias | {p.ultima_consulta ? new Date(p.ultima_consulta).toLocaleDateString('pt-BR') : 'sem consulta'}
                        {p.houve_mudanca && <span className="ml-2 text-amber-600 font-medium">⚠ Mudança</span>}
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

function Card({ label, value, color = 'text-brand-900' }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${color}`}>{value ?? 0}</p>
    </div>
  )
}
