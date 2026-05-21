import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
} from 'recharts'
import {
  ArrowLeft, Download, CheckCircle2, ChevronDown, X,
} from 'lucide-react'
import { getDashboardData, downloadPdf } from '../services/api'

const STATUS_COLORS = {
  'EM ANDAMENTO': '#3454ff',
  PENDENTE:       '#ff8a2a',
  APROVADO:       '#2a8a55',
  CANCELADO:      '#e3463a',
  REPROVADO:      '#c46a4c',
}
const PALETTE = ['#3454ff', '#2a8a55', '#ff8a2a', '#e3463a', '#7a9112', '#3454ff', '#0a0a0a', '#7c7c78']

const TIPO_MAP = {
  erro:            { label: 'Erro',            bg: 'bg-red-50',    fg: 'text-red-700'    },
  sem_atualizacao: { label: 'Sem atualização', bg: 'bg-amber-50',  fg: 'text-amber-700'  },
  duracao_alta:    { label: 'Duração alta',    bg: 'bg-orange-50', fg: 'text-orange-700' },
}

const EMPTY_FILTERS = {
  projeto: '', orgao: '', status: '', ativo: '',
  atribuido_a: '', situacao: '', data_abertura_inicio: '', data_abertura_fim: '',
}

export default function Reports() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState(EMPTY_FILTERS)

  const params = useMemo(() => {
    const p = {}
    if (filters.projeto)               p.projeto               = filters.projeto
    if (filters.orgao)                 p.orgao                 = filters.orgao
    if (filters.status)                p.status                = filters.status
    if (filters.ativo !== '')          p.ativo                 = filters.ativo === 'true'
    if (filters.atribuido_a)           p.atribuido_a           = filters.atribuido_a
    if (filters.situacao)              p.situacao              = filters.situacao
    if (filters.data_abertura_inicio)  p.data_abertura_inicio  = filters.data_abertura_inicio
    if (filters.data_abertura_fim)     p.data_abertura_fim     = filters.data_abertura_fim
    return p
  }, [filters])

  const hasFilters = Object.values(filters).some(v => v !== '')

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', params],
    queryFn: () => getDashboardData(params),
  })

  const kpis = data?.kpis ?? {}
  const totalConsultas = (data?.consultas_por_periodo ?? []).reduce((a, b) => a + (b.count ?? 0), 0)

  function set(key) {
    return v => setFilters(f => ({ ...f, [key]: v }))
  }

  return (
    <div className="min-h-screen bg-paper text-ink">

      {/* ═══ NAVBAR ═══ */}
      <header className="sticky top-0 z-30 h-14 flex items-center justify-between px-6 bg-surface border-b border-line">
        <div className="flex items-center gap-4">
          <button onClick={() => { localStorage.removeItem('reports_token'); navigate('/') }} className="w-9 h-9 rounded-lg flex items-center justify-center bg-paper hover:bg-line transition text-ink">
            <ArrowLeft size={16} />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="logo-mark w-6 h-6" />
            <span className="font-semibold text-sm tracking-tight">Biopark</span>
            <span className="hidden sm:inline text-[10px] font-mono px-1.5 py-0.5 rounded bg-paper text-muted uppercase tracking-wider">Pro</span>
          </div>
          <nav className="hidden sm:flex items-center gap-1 text-sm ml-2">
            <button onClick={() => { localStorage.removeItem('reports_token'); navigate('/') }} className="px-3 py-1.5 rounded-lg text-muted hover:text-ink hover:bg-paper transition">Protocolos</button>
            <button className="px-3 py-1.5 rounded-lg font-medium bg-paper text-ink">Relatórios</button>
          </nav>
        </div>
        <button
          onClick={() => downloadPdf(params)}
          className="px-3.5 py-2 rounded-lg text-sm font-semibold flex items-center gap-1.5 bg-ink text-lime hover:bg-ink-2 transition"
        >
          <Download size={13} /> Baixar PDF
          {hasFilters && <span className="text-[10px] font-mono bg-lime/20 text-lime px-1.5 py-0.5 rounded">filtrado</span>}
        </button>
      </header>

      <div className="px-6 py-6 max-w-[1400px] mx-auto">

        {/* ═══ Hero ═══ */}
        <div className="flex items-end justify-between mb-6 gap-4 flex-wrap">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-wider text-muted mb-1">painel executivo</div>
            <h1 className="text-3xl font-semibold tracking-tight">Performance da operação</h1>
            <p className="text-sm text-muted mt-1">
              {kpis.total ?? 0} protocolos analisados · Atualizado agora
            </p>
          </div>
        </div>

        {/* ═══ Filter panel ═══ */}
        <div className="rounded-2xl bg-surface border border-line p-4 mb-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted uppercase tracking-wider">Filtros</span>
            {hasFilters && (
              <button
                onClick={() => setFilters(EMPTY_FILTERS)}
                className="flex items-center gap-1 text-xs text-muted hover:text-ink font-medium transition"
              >
                <X size={11} /> Limpar tudo
              </button>
            )}
          </div>

          {/* Row 1 */}
          <div className="flex items-center gap-2 flex-wrap">
            <FilterChip
              value={filters.status}
              onChange={set('status')}
              placeholder="Todos os status"
              options={[
                ['EM ANDAMENTO', 'Em andamento'],
                ['PENDENTE',     'Pendente'],
                ['APROVADO',     'Aprovado'],
                ['CANCELADO',    'Cancelado'],
                ['REPROVADO',    'Reprovado'],
              ]}
            />
            <FilterChip
              value={filters.ativo}
              onChange={set('ativo')}
              placeholder="Ativo e inativo"
              options={[['true', 'Apenas ativos'], ['false', 'Apenas inativos']]}
            />
            <TextFilter
              value={filters.projeto}
              onChange={set('projeto')}
              placeholder="Projeto…"
              width="w-40"
            />
            <TextFilter
              value={filters.orgao}
              onChange={set('orgao')}
              placeholder="Órgão…"
              width="w-44"
            />
          </div>

          {/* Row 2 */}
          <div className="flex items-center gap-2 flex-wrap">
            <TextFilter
              value={filters.atribuido_a}
              onChange={set('atribuido_a')}
              placeholder="Atribuído a…"
              width="w-40"
            />
            <TextFilter
              value={filters.situacao}
              onChange={set('situacao')}
              placeholder="Situação…"
              width="w-44"
            />
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-muted whitespace-nowrap">Abertura de</span>
              <input
                type="date"
                value={filters.data_abertura_inicio}
                onChange={e => set('data_abertura_inicio')(e.target.value)}
                className="text-sm border border-line-2 rounded-lg px-3 py-1.5 bg-paper text-ink outline-none focus:ring-2 focus:ring-ink/10 focus:border-ink/30 transition"
              />
              <span className="text-xs text-muted">até</span>
              <input
                type="date"
                value={filters.data_abertura_fim}
                onChange={e => set('data_abertura_fim')(e.target.value)}
                className="text-sm border border-line-2 rounded-lg px-3 py-1.5 bg-paper text-ink outline-none focus:ring-2 focus:ring-ink/10 focus:border-ink/30 transition"
              />
            </div>
          </div>

          {/* Active filter chips */}
          {hasFilters && (
            <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-line-2">
              {filters.status && <ActiveChip label={`Status: ${filters.status}`} onRemove={() => set('status')('')} />}
              {filters.ativo !== '' && <ActiveChip label={filters.ativo === 'true' ? 'Apenas ativos' : 'Apenas inativos'} onRemove={() => set('ativo')('')} />}
              {filters.projeto && <ActiveChip label={`Projeto: ${filters.projeto}`} onRemove={() => set('projeto')('')} />}
              {filters.orgao && <ActiveChip label={`Órgão: ${filters.orgao}`} onRemove={() => set('orgao')('')} />}
              {filters.atribuido_a && <ActiveChip label={`Atribuído: ${filters.atribuido_a}`} onRemove={() => set('atribuido_a')('')} />}
              {filters.situacao && <ActiveChip label={`Situação: ${filters.situacao}`} onRemove={() => set('situacao')('')} />}
              {filters.data_abertura_inicio && <ActiveChip label={`De: ${filters.data_abertura_inicio}`} onRemove={() => set('data_abertura_inicio')('')} />}
              {filters.data_abertura_fim && <ActiveChip label={`Até: ${filters.data_abertura_fim}`} onRemove={() => set('data_abertura_fim')('')} />}
            </div>
          )}
        </div>

        {/* ═══ CONTENT ═══ */}
        {isLoading ? (
          <div className="flex items-center justify-center py-24 gap-3 text-muted text-sm">
            <svg className="animate-spin h-5 w-5 text-ink" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Carregando painel…
          </div>
        ) : (
          <div className="space-y-4">

            {/* ═══ KPI ROW ═══ */}
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
              <Kpi label="Total"               value={kpis.total ?? 0}                tone="neutral" />
              <Kpi label="Ativos"              value={kpis.ativos ?? 0}               tone="green" delta={`${Math.round(((kpis.ativos ?? 0) / Math.max(kpis.total ?? 1, 1)) * 100)}%`} />
              <Kpi label="Mudanças recentes"   value={kpis.com_mudanca_recente ?? 0}  tone="lime"  delta="hoje" />
              <Kpi label="Erros de consulta"   value={kpis.erros_consulta ?? 0}       tone={kpis.erros_consulta > 0 ? 'red' : 'green'} />
              <Kpi label="Duração média (d)"   value={kpis.duracao_media ?? 0}        tone="neutral" />
              <Kpi label="Maior órgão"         value={kpis.orgao_top ?? '—'}          tone="neutral" small />
            </div>

            {/* ═══ Charts row 1 — Timeline + Donut ═══ */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">

              <Card
                className="lg:col-span-8"
                title="Consultas automáticas"
                subtitle="Últimos 30 dias"
                right={
                  <div className="flex items-center gap-5">
                    <Metric label="Total" value={totalConsultas} />
                    <Metric label="Por dia (méd.)" value={(data?.consultas_por_periodo?.length ?? 0) > 0 ? Math.round(totalConsultas / data.consultas_por_periodo.length) : 0} />
                  </div>
                }
              >
                <ResponsiveContainer width="100%" height={210}>
                  <AreaChart data={data?.consultas_por_periodo ?? []} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                    <defs>
                      <linearGradient id="grad-consultas" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"  stopColor="#d4ff3a" stopOpacity={0.45} />
                        <stop offset="95%" stopColor="#d4ff3a" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eeede8" vertical={false} />
                    <XAxis
                      dataKey="data"
                      tick={{ fontSize: 10, fill: '#7c7c78' }}
                      axisLine={false} tickLine={false}
                      interval={4}
                      tickFormatter={d => d.slice(5).replace('-', '/')}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: '#7c7c78' }}
                      axisLine={false} tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{ background: '#0a0a0a', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#d4ff3a' }}
                      labelFormatter={d => new Date(d + 'T12:00:00').toLocaleDateString('pt-BR')}
                      formatter={v => [v, 'consultas']}
                    />
                    <Area type="monotone" dataKey="count" stroke="#0a0a0a" strokeWidth={2.5} fill="url(#grad-consultas)" dot={false} activeDot={{ r: 5, fill: '#d4ff3a', stroke: '#0a0a0a', strokeWidth: 2 }} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>

              <Card className="lg:col-span-4" title="Por status" subtitle="Distribuição atual">
                {!(data?.por_status?.length) ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={210}>
                    <PieChart>
                      <Pie
                        data={data.por_status}
                        dataKey="count"
                        nameKey="status"
                        cx="50%" cy="50%"
                        outerRadius={78}
                        innerRadius={48}
                        paddingAngle={2}
                        stroke="#fff"
                        strokeWidth={2}
                      >
                        {data.por_status.map((entry, i) => (
                          <Cell key={i} fill={STATUS_COLORS[entry.status] ?? PALETTE[i % PALETTE.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#0a0a0a', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12 }}
                        labelStyle={{ color: '#d4ff3a' }}
                      />
                      <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 11, color: '#7c7c78' }} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </Card>
            </div>

            {/* ═══ Charts row 2 — Org volume + Atribuído ═══ */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">

              <Card className="lg:col-span-7" title="Por órgão" subtitle="Top 8 por volume">
                {!(data?.por_orgao?.length) ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart
                      layout="vertical"
                      data={data.por_orgao}
                      margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eeede8" />
                      <XAxis type="number" tick={{ fontSize: 10, fill: '#7c7c78' }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="orgao"
                        width={132}
                        tick={{ fontSize: 11, fill: '#0a0a0a' }}
                        axisLine={false} tickLine={false}
                        tickFormatter={v => v.length > 20 ? v.slice(0, 20) + '…' : v}
                      />
                      <Tooltip
                        cursor={{ fill: '#f7f7f5' }}
                        contentStyle={{ background: '#0a0a0a', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12 }}
                        labelStyle={{ color: '#d4ff3a' }}
                      />
                      <Bar dataKey="count" fill="#0a0a0a" radius={[0, 6, 6, 0]} maxBarSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Card>

              <Card className="lg:col-span-5" title="Por responsável" subtitle="Top 8 por volume">
                {!(data?.por_atribuido?.length) ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart
                      layout="vertical"
                      data={data.por_atribuido}
                      margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eeede8" />
                      <XAxis type="number" tick={{ fontSize: 10, fill: '#7c7c78' }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="atribuido_a"
                        width={110}
                        tick={{ fontSize: 11, fill: '#0a0a0a' }}
                        axisLine={false} tickLine={false}
                        tickFormatter={v => v.length > 16 ? v.slice(0, 16) + '…' : v}
                      />
                      <Tooltip
                        cursor={{ fill: '#f7f7f5' }}
                        contentStyle={{ background: '#0a0a0a', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12 }}
                        labelStyle={{ color: '#d4ff3a' }}
                      />
                      <Bar dataKey="count" fill="#3454ff" radius={[0, 6, 6, 0]} maxBarSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Card>
            </div>

            {/* ═══ Charts row 3 — Críticos ═══ */}
            <Card
              title="Protocolos críticos"
              subtitle={`${(data?.protocolos_criticos ?? []).length} identificado(s)`}
              right={(data?.protocolos_criticos ?? []).length > 0 && (
                <span className="pill bg-red-50 text-red-700">{data.protocolos_criticos.length}</span>
              )}
            >
              {!(data?.protocolos_criticos?.length) ? (
                <div className="flex items-center gap-2 text-emerald-600 py-5 text-sm">
                  <CheckCircle2 size={16} /> Nenhum protocolo crítico
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2 max-h-[300px] overflow-y-auto -mr-2 pr-2">
                  {data.protocolos_criticos.slice(0, 12).map(p => {
                    const t = TIPO_MAP[p.tipo] ?? { label: p.tipo, bg: 'bg-paper', fg: 'text-muted' }
                    return (
                      <div key={p.id} className="flex items-center justify-between gap-3 p-3 rounded-lg bg-paper hover:bg-line transition">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs text-ink">{p.protocolo}</span>
                            <span className={`pill ${t.bg} ${t.fg}`}>{t.label}</span>
                          </div>
                          <p className="text-xs text-muted mt-1 truncate">
                            {p.projeto}{p.orgao ? ` · ${p.orgao}` : ''}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-base font-semibold num text-accent-red">{p.duracao_dias != null ? `${p.duracao_dias}d` : '—'}</div>
                          <div className="text-[10px] font-mono uppercase text-muted">sem ação</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>

            {/* ═══ Alertas — timeline ═══ */}
            <Card title="Alertas recentes" subtitle={`${(data?.alertas_recentes ?? []).length} alerta(s)`}>
              {!(data?.alertas_recentes?.length) ? (
                <div className="flex items-center gap-2 text-emerald-600 py-5 text-sm">
                  <CheckCircle2 size={16} /> Nenhum alerta recente
                </div>
              ) : (
                <div className="relative pl-6">
                  <div className="absolute left-[7px] top-2 bottom-2 w-px bg-line-2" />
                  {data.alertas_recentes.slice(0, 12).map((a, i) => (
                    <div key={i} className="relative pb-4 last:pb-0">
                      <div
                        className="absolute -left-[22px] top-1 w-3 h-3 rounded-full"
                        style={{
                          background: a.tipo === 'erro' ? '#e3463a' : '#d4ff3a',
                          boxShadow: `0 0 0 4px #fff, 0 0 0 5px ${a.tipo === 'erro' ? '#e3463a33' : '#d4ff3a55'}`,
                        }}
                      />
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                            <span className="font-mono text-xs font-medium text-ink">{a.protocolo}</span>
                            <span className={`pill ${
                              a.tipo === 'erro' ? 'bg-red-50 text-red-700' : 'bg-lime-soft text-lime-deep'
                            }`}>
                              {a.tipo === 'erro' ? 'erro' : 'mudança'}
                            </span>
                          </div>
                          <div className="text-sm text-ink-2">{a.descricao}</div>
                        </div>
                        <div className="text-[11px] font-mono uppercase tracking-wider shrink-0 text-muted">
                          {a.data
                            ? new Date(a.data).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
                            : '—'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

          </div>
        )}
      </div>
    </div>
  )
}

/* ──── helpers ──── */

function Kpi({ label, value, tone, delta, small }) {
  const toneClr = { green: 'text-accent-green', amber: 'text-accent-amber', red: 'text-accent-red', lime: 'text-lime-deep', neutral: 'text-muted' }[tone] || 'text-muted'
  return (
    <div className="rounded-xl p-4 bg-surface border border-line">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted mb-2 truncate">{label}</div>
      <div className="flex items-baseline justify-between gap-2">
        <div className={`font-medium num tracking-tight ${small ? 'text-base truncate' : 'text-3xl'}`}>{value}</div>
        {delta && <div className={`text-[11px] font-medium ${toneClr}`}>{delta}</div>}
      </div>
    </div>
  )
}

function Card({ title, subtitle, right, children, className = '' }) {
  return (
    <div className={`rounded-2xl bg-surface border border-line overflow-hidden ${className}`}>
      <div className="px-5 pt-4 pb-3 border-b border-line flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-sm text-ink">{title}</h3>
          {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
        </div>
        {right && <div className="shrink-0">{right}</div>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="text-right">
      <div className="text-[10px] font-mono uppercase text-muted">{label}</div>
      <div className="text-base font-semibold num">{value}</div>
    </div>
  )
}

function FilterChip({ value, onChange, placeholder, options }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="appearance-none bg-paper border border-line-2 rounded-lg pl-3 pr-7 py-1.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-ink/10 focus:border-ink/30 cursor-pointer transition"
      >
        <option value="">{placeholder}</option>
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
    </div>
  )
}

function TextFilter({ value, onChange, placeholder, width = 'w-40' }) {
  return (
    <div className="relative">
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`text-sm border border-line-2 rounded-lg px-3 py-1.5 bg-paper text-ink placeholder:text-muted-faint outline-none focus:ring-2 focus:ring-ink/10 focus:border-ink/30 transition ${width}`}
      />
      {value && (
        <button onClick={() => onChange('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-ink transition">
          <X size={11} />
        </button>
      )}
    </div>
  )
}

function ActiveChip({ label, onRemove }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs bg-ink text-lime font-medium px-2 py-0.5 rounded-full">
      {label}
      <button onClick={onRemove} className="hover:opacity-70 transition ml-0.5">
        <X size={10} />
      </button>
    </span>
  )
}

function EmptyChart() {
  return (
    <div className="h-[210px] flex items-center justify-center text-muted-faint text-sm">
      Sem dados disponíveis
    </div>
  )
}
