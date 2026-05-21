import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
} from 'recharts'
import {
  ArrowLeft, Download, BarChart3, CheckCircle2, ClipboardList,
  Zap, XCircle, Timer, Building2, Filter,
} from 'lucide-react'
import { getDashboardData, downloadPdf } from '../services/api'

const STATUS_COLORS = {
  'EM ANDAMENTO': '#2563eb',
  PENDENTE: '#f59e0b',
  APROVADO: '#10b981',
  CANCELADO: '#ef4444',
  REPROVADO: '#dc2626',
}

const PALETTE = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

const TIPO_MAP = {
  erro:            { label: 'Erro',            cls: 'bg-red-50 text-red-700 border-red-200' },
  sem_atualizacao: { label: 'Sem atualização', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
  duracao_alta:    { label: 'Duração alta',    cls: 'bg-orange-50 text-orange-700 border-orange-200' },
}

export default function Reports() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ projeto: '', orgao: '', status: '', ativo: '' })

  const params = useMemo(() => {
    const p = {}
    if (filters.projeto) p.projeto = filters.projeto
    if (filters.orgao)   p.orgao   = filters.orgao
    if (filters.status)  p.status  = filters.status
    if (filters.ativo !== '') p.ativo = filters.ativo === 'true'
    return p
  }, [filters])

  const hasFilters = filters.projeto || filters.orgao || filters.status || filters.ativo !== ''

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', params],
    queryFn: () => getDashboardData(params),
  })

  const kpis = data?.kpis ?? {}

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Navbar */}
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
              <span className="font-semibold text-sm">Painel Executivo</span>
            </div>
          </div>
          <button
            onClick={downloadPdf}
            className="flex items-center gap-1.5 bg-brand-800 hover:bg-brand-700 px-3 py-1.5 rounded-lg text-sm transition"
          >
            <Download size={13} /> Baixar PDF
          </button>
        </div>
      </nav>

      {/* Filtros */}
      <div className="bg-white border-b border-gray-100 sticky top-14 z-20 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-2.5 flex items-center gap-3 flex-wrap">
          <span className="flex items-center gap-1.5 text-gray-400 text-xs font-medium shrink-0">
            <Filter size={12} /> Filtros
          </span>

          <select
            value={filters.status}
            onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
            className="text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">Todos os status</option>
            <option value="EM ANDAMENTO">Em Andamento</option>
            <option value="PENDENTE">Pendente</option>
            <option value="APROVADO">Aprovado</option>
            <option value="CANCELADO">Cancelado</option>
            <option value="REPROVADO">Reprovado</option>
          </select>

          <select
            value={filters.ativo}
            onChange={e => setFilters(f => ({ ...f, ativo: e.target.value }))}
            className="text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">Ativo e Inativo</option>
            <option value="true">Apenas Ativos</option>
            <option value="false">Apenas Inativos</option>
          </select>

          <input
            value={filters.projeto}
            onChange={e => setFilters(f => ({ ...f, projeto: e.target.value }))}
            placeholder="Projeto..."
            className="text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 w-40"
          />

          <input
            value={filters.orgao}
            onChange={e => setFilters(f => ({ ...f, orgao: e.target.value }))}
            placeholder="Órgão..."
            className="text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 w-44"
          />

          {hasFilters && (
            <button
              onClick={() => setFilters({ projeto: '', orgao: '', status: '', ativo: '' })}
              className="text-xs text-brand-600 hover:text-brand-700 font-medium"
            >
              Limpar
            </button>
          )}
        </div>
      </div>

      {/* Conteúdo */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-24 gap-3 text-gray-400 text-sm">
            <svg className="animate-spin h-5 w-5 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Carregando painel...
          </div>
        ) : (
          <div className="space-y-6">

            {/* KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-4">
              <KpiCard label="Total de Protocolos"  value={kpis.total ?? 0}               icon={ClipboardList} accent="blue"   />
              <KpiCard label="Protocolos Ativos"    value={kpis.ativos ?? 0}              icon={CheckCircle2}  accent="green"  />
              <KpiCard label="Mudanças Recentes"    value={kpis.com_mudanca_recente ?? 0} icon={Zap}           accent="amber"  />
              <KpiCard label="Erros de Consulta"    value={kpis.erros_consulta ?? 0}      icon={XCircle}       accent="red"    />
              <KpiCard label="Duração Média (dias)" value={kpis.duracao_media ?? 0}       icon={Timer}         accent="violet" />
              <KpiCard label="Maior Órgão"          value={kpis.orgao_top ?? '—'}         icon={Building2}     accent="slate"  small />
            </div>

            {/* Gráficos: pizza + barras */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card title="Por Status" subtitle="Distribuição atual de protocolos">
                {!(data?.por_status?.length) ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={230}>
                    <PieChart>
                      <Pie
                        data={data.por_status}
                        dataKey="count"
                        nameKey="status"
                        cx="50%" cy="50%"
                        outerRadius={78}
                        innerRadius={42}
                        paddingAngle={2}
                      >
                        {data.por_status.map((entry, i) => (
                          <Cell key={i} fill={STATUS_COLORS[entry.status] ?? PALETTE[i % PALETTE.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v, n) => [v, n]} />
                      <Legend iconSize={10} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </Card>

              <div className="lg:col-span-2">
                <Card title="Por Órgão" subtitle="Top 8 órgãos por volume de protocolos">
                  {!(data?.por_orgao?.length) ? <EmptyChart /> : (
                    <ResponsiveContainer width="100%" height={230}>
                      <BarChart
                        layout="vertical"
                        data={data.por_orgao}
                        margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                        <XAxis
                          type="number"
                          tick={{ fontSize: 10 }}
                          axisLine={false}
                          tickLine={false}
                          allowDecimals={false}
                        />
                        <YAxis
                          type="category"
                          dataKey="orgao"
                          width={132}
                          tick={{ fontSize: 10 }}
                          axisLine={false}
                          tickLine={false}
                          tickFormatter={v => v.length > 20 ? v.slice(0, 20) + '…' : v}
                        />
                        <Tooltip cursor={{ fill: '#f8fafc' }} />
                        <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} maxBarSize={18} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </Card>
              </div>
            </div>

            {/* Gráfico de linha */}
            <Card title="Consultas Realizadas" subtitle="Histórico dos últimos 30 dias">
              <ResponsiveContainer width="100%" height={180}>
                <AreaChart
                  data={data?.consultas_por_periodo ?? []}
                  margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="gradConsultas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#2563eb" stopOpacity={0.12} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis
                    dataKey="data"
                    tick={{ fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    interval={4}
                    tickFormatter={d => d.slice(5).replace('-', '/')}
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    labelFormatter={d => new Date(d + 'T12:00:00').toLocaleDateString('pt-BR')}
                    formatter={v => [v, 'consultas']}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#2563eb"
                    strokeWidth={2}
                    fill="url(#gradConsultas)"
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>

            {/* Protocolos críticos + Alertas */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              <Card
                title="Protocolos Críticos"
                subtitle={`${(data?.protocolos_criticos ?? []).length} identificado(s)`}
              >
                {!(data?.protocolos_criticos?.length) ? (
                  <div className="flex items-center gap-2 text-emerald-600 py-5 text-sm">
                    <CheckCircle2 size={16} /> Nenhum protocolo crítico
                  </div>
                ) : (
                  <div className="divide-y divide-gray-50 -mx-5">
                    {data.protocolos_criticos.slice(0, 8).map(p => {
                      const t = TIPO_MAP[p.tipo] ?? { label: p.tipo, cls: 'bg-gray-100 text-gray-600 border-gray-200' }
                      return (
                        <div key={p.id} className="px-5 py-3 flex items-center justify-between gap-3 hover:bg-gray-50/60 transition-colors">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-mono text-xs text-gray-500">{p.protocolo}</span>
                              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${t.cls}`}>
                                {t.label}
                              </span>
                            </div>
                            <p className="text-xs text-gray-400 mt-0.5 truncate">
                              {p.projeto}{p.orgao ? ` · ${p.orgao}` : ''}
                            </p>
                          </div>
                          <span className="text-xs text-gray-400 shrink-0 tabular-nums">
                            {p.duracao_dias != null ? `${p.duracao_dias}d` : '—'}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </Card>

              <Card
                title="Alertas Recentes"
                subtitle={`${(data?.alertas_recentes ?? []).length} alerta(s)`}
              >
                {!(data?.alertas_recentes?.length) ? (
                  <div className="flex items-center gap-2 text-emerald-600 py-5 text-sm">
                    <CheckCircle2 size={16} /> Nenhum alerta recente
                  </div>
                ) : (
                  <div className="divide-y divide-gray-50 -mx-5">
                    {data.alertas_recentes.slice(0, 8).map((a, i) => (
                      <div key={i} className="px-5 py-3 flex items-start gap-3 hover:bg-gray-50/60 transition-colors">
                        <div className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${a.tipo === 'erro' ? 'bg-red-500' : 'bg-amber-400'}`} />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs text-gray-500">{a.protocolo}</span>
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${
                              a.tipo === 'erro'
                                ? 'bg-red-50 text-red-700 border-red-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}>
                              {a.tipo === 'erro' ? 'Erro' : 'Mudança'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5 truncate">{a.descricao}</p>
                          <p className="text-[10px] text-gray-300 mt-0.5">
                            {a.data
                              ? new Date(a.data).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
                              : '—'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function KpiCard({ label, value, icon: Icon, accent, small }) {
  const accents = {
    blue:   { bar: 'bg-brand-600',   icon: 'bg-brand-50 text-brand-600' },
    green:  { bar: 'bg-emerald-500', icon: 'bg-emerald-50 text-emerald-600' },
    amber:  { bar: 'bg-amber-400',   icon: 'bg-amber-50 text-amber-600' },
    red:    { bar: 'bg-red-500',     icon: 'bg-red-50 text-red-600' },
    violet: { bar: 'bg-violet-500',  icon: 'bg-violet-50 text-violet-600' },
    slate:  { bar: 'bg-slate-400',   icon: 'bg-slate-50 text-slate-600' },
  }
  const { bar, icon } = accents[accent] ?? accents.blue
  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
      <div className={`h-0.5 ${bar}`} />
      <div className="p-4 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider leading-tight">{label}</p>
          <p className={`font-bold text-gray-900 mt-1.5 leading-none tabular-nums ${small ? 'text-sm truncate' : 'text-3xl'}`}>
            {value}
          </p>
        </div>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ml-2 ${icon}`}>
          <Icon size={16} />
        </div>
      </div>
    </div>
  )
}

function Card({ title, subtitle, children }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 pt-4 pb-3 border-b border-gray-50">
        <h3 className="font-semibold text-gray-800 text-sm">{title}</h3>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  )
}

function EmptyChart() {
  return (
    <div className="h-[230px] flex items-center justify-center text-gray-300 text-sm">
      Sem dados disponíveis
    </div>
  )
}
