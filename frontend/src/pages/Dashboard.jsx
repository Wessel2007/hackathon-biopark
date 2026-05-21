import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDashboardData, downloadPdf, runAllQueries,
  getProtocols, createProtocol, updateProtocol, deleteProtocol,
  bulkDeleteProtocols, runSingleQuery, previewSpreadsheet, confirmImport,
} from '../services/api'
import { useNavigate } from 'react-router-dom'
import {
  FileText, RefreshCw, LogOut, AlertTriangle, Building2,
  BarChart3, CheckCircle2, Zap, ChevronDown, ClipboardList,
  Plus, Upload, Search, X, Pencil, Trash2, Layers,
} from 'lucide-react'

const STATUS_CONFIG = [
  { key: 'EM ANDAMENTO', label: 'ANDAMENTO', badge: 'bg-blue-50 text-blue-700 border-blue-200',         badgeActive: 'bg-blue-100 text-blue-800 border-blue-300',         activeBg: 'bg-blue-50',    activeBorder: 'border-blue-200',    activeValue: 'text-blue-800'    },
  { key: 'PENDENTE',     label: 'PENDENTE',   badge: 'bg-amber-50 text-amber-700 border-amber-200',     badgeActive: 'bg-amber-100 text-amber-800 border-amber-300',     activeBg: 'bg-amber-50',   activeBorder: 'border-amber-200',   activeValue: 'text-amber-800'   },
  { key: 'APROVADO',    label: 'APROVADO',   badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', badgeActive: 'bg-emerald-100 text-emerald-800 border-emerald-300', activeBg: 'bg-emerald-50', activeBorder: 'border-emerald-200', activeValue: 'text-emerald-800' },
  { key: 'CANCELADO',   label: 'CANCELADO',  badge: 'bg-red-50 text-red-700 border-red-200',            badgeActive: 'bg-red-100 text-red-800 border-red-300',            activeBg: 'bg-red-50',     activeBorder: 'border-red-200',     activeValue: 'text-red-800'     },
  { key: 'REPROVADO',   label: 'REPROVADO',  badge: 'bg-red-50 text-red-700 border-red-200',            badgeActive: 'bg-red-100 text-red-800 border-red-300',            activeBg: 'bg-red-50',     activeBorder: 'border-red-200',     activeValue: 'text-red-800'     },
]

const EMPTY_FORM = {
  status: 'PENDENTE', projeto: '', protocolo: '', atividade: '',
  orgao_site_consultado: '', atribuido_a: '', data_abertura: '',
  data_finalizacao: '', situacao: '', ativo: true, url_consulta: '',
}

const CAMPOS = [
  ['status', 'Status'], ['projeto', 'Projeto'], ['protocolo', 'Protocolo'],
  ['atividade', 'Atividade'], ['orgao_site_consultado', 'Órgão / Site'],
  ['atribuido_a', 'Atribuído a'], ['data_abertura', 'Data Abertura'],
  ['data_finalizacao', 'Data Finalização'], ['situacao', 'Situação'],
  ['url_consulta', 'URL Consulta'],
]

export default function Dashboard() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  // filtros
  const [searchQuery,   setSearchQuery]   = useState('')
  const [filterOrgao,   setFilterOrgao]   = useState('')
  const [filterStatus,  setFilterStatus]  = useState('')
  const [filterProject, setFilterProject] = useState('')

  // CRUD
  const [showForm,       setShowForm]       = useState(false)
  const [editItem,       setEditItem]       = useState(null)
  const [form,           setForm]           = useState(EMPTY_FORM)
  const [formError,      setFormError]      = useState(null)
  const [pageError,      setPageError]      = useState(null)
  const [importing,      setImporting]      = useState(false)
  const [confirming,     setConfirming]     = useState(false)
  const [importPreview,  setImportPreview]  = useState(null)
  const [importResult,   setImportResult]   = useState(null)
  const [selected,       setSelected]       = useState(new Set())
  const [showBulkConfirm,setShowBulkConfirm]= useState(false)
  const [queryResult,    setQueryResult]    = useState(null)

  // queries
  const { data: dashData, refetch: refetchDash } = useQuery({
    queryKey: ['dashboard'], queryFn: getDashboardData,
  })
  const { data: protocols = [], isLoading } = useQuery({
    queryKey: ['protocols'], queryFn: () => getProtocols({ limit: 10000 }),
  })

  // mapa id → houve_mudanca vindo do dashboard
  const mudancaMap = useMemo(() => {
    const map = {}
    Object.values(dashData?.por_projeto ?? {}).flat().forEach(p => { map[p.id] = p.houve_mudanca })
    return map
  }, [dashData])

  const uniqueOrgaos = useMemo(() =>
    [...new Set(protocols.map(p => p.orgao_site_consultado).filter(Boolean))].sort(), [protocols])

  const uniqueProjects = useMemo(() =>
    [...new Set(protocols.map(p => p.projeto).filter(Boolean))].sort(), [protocols])

  const statusCounts = useMemo(() => {
    const c = {}
    protocols.forEach(p => { c[p.status] = (c[p.status] ?? 0) + 1 })
    return c
  }, [protocols])

  const filteredData = useMemo(() => {
    const q = searchQuery.toLowerCase().trim()
    return protocols.filter(p => {
      const matchSearch  = !q || [p.projeto, p.protocolo, p.atividade, p.orgao_site_consultado, p.situacao, p.atribuido_a].some(f => f?.toLowerCase().includes(q))
      const matchOrgao   = !filterOrgao   || p.orgao_site_consultado === filterOrgao
      const matchStatus  = !filterStatus  || p.status === filterStatus
      const matchProject = !filterProject || p.projeto === filterProject
      return matchSearch && matchOrgao && matchStatus && matchProject
    })
  }, [protocols, searchQuery, filterOrgao, filterStatus, filterProject])

  const hasFilters = searchQuery || filterOrgao || filterStatus || filterProject

  // mutations
  const saveMut = useMutation({
    mutationFn: (d) => editItem ? updateProtocol(editItem.id, d) : createProtocol(d),
    onSuccess: () => {
      qc.invalidateQueries(['protocols']); qc.invalidateQueries(['dashboard'])
      setShowForm(false); setEditItem(null); setForm(EMPTY_FORM); setFormError(null)
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao salvar'
      setFormError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
    },
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteProtocol(id),
    onSuccess: () => { qc.invalidateQueries(['protocols']); qc.invalidateQueries(['dashboard']); setPageError(null) },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao excluir'
      setPageError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
    },
  })

  const queryMut = useMutation({
    mutationFn: (id) => runSingleQuery(id),
    onSuccess: (res) => { qc.invalidateQueries(['protocols']); qc.invalidateQueries(['dashboard']); setQueryResult(res) },
  })

  const bulkDelMut = useMutation({
    mutationFn: (force) => bulkDeleteProtocols([...selected], force),
    onSuccess: () => {
      qc.invalidateQueries(['protocols']); qc.invalidateQueries(['dashboard'])
      setSelected(new Set()); setShowBulkConfirm(false)
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao excluir'
      setPageError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
      setShowBulkConfirm(false)
    },
  })

  // handlers
  function handleLogout() { localStorage.removeItem('token'); navigate('/login') }

  async function handleRunAll() {
    await runAllQueries()
    setTimeout(() => { refetchDash(); qc.invalidateQueries(['protocols']) }, 3000)
  }

  function handleSave() {
    if (!form.projeto?.trim())               return setFormError('Projeto é obrigatório')
    if (!form.protocolo?.trim())             return setFormError('Protocolo é obrigatório')
    if (!form.atividade?.trim())             return setFormError('Atividade é obrigatória')
    if (!form.orgao_site_consultado?.trim()) return setFormError('Órgão / Site é obrigatório')
    if (!form.data_abertura)                 return setFormError('Data de Abertura é obrigatória')
    setFormError(null); saveMut.mutate(form)
  }

  function openEdit(item) {
    setEditItem(item)
    setForm({ ...item, data_abertura: item.data_abertura?.slice(0, 10) ?? '', data_finalizacao: item.data_finalizacao?.slice(0, 10) ?? '' })
    setShowForm(true)
  }

  async function handleImport(e) {
    const file = e.target.files[0]; if (!file) return
    e.target.value = ''; setImporting(true); setImportResult(null); setImportPreview(null)
    try {
      const result = await previewSpreadsheet(file)
      setImportPreview(result)
    } catch (err) {
      setPageError(err.response?.data?.detail || 'Erro ao processar planilha')
    } finally { setImporting(false) }
  }

  async function handleConfirmImport() {
    if (!importPreview) return
    setConfirming(true)
    try {
      const result = await confirmImport(importPreview.rows)
      setImportResult(result)
      setImportPreview(null)
      qc.invalidateQueries(['protocols']); qc.invalidateQueries(['dashboard'])
    } catch (err) {
      setPageError(err.response?.data?.detail || 'Erro ao importar dados')
    } finally { setConfirming(false) }
  }

  function toggleSelect(id) {
    setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  }
  function toggleSelectAll() {
    if (selected.size === filteredData.length) setSelected(new Set())
    else setSelected(new Set(filteredData.map(p => p.id)))
  }

  function clearFilters() { setSearchQuery(''); setFilterOrgao(''); setFilterStatus(''); setFilterProject('') }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── Topbar ── */}
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
            <button onClick={() => navigate('/reports')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-brand-300 hover:text-white hover:bg-brand-800 text-sm transition">
              <BarChart3 size={13} /> Relatórios
            </button>
            <div className="w-px h-5 bg-brand-800 mx-1" />
            <button onClick={handleLogout} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-brand-400 hover:text-white hover:bg-brand-800 text-sm transition">
              <LogOut size={13} /> Sair
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-5">

        {/* ── Cabeçalho + ações ── */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Gestão de Protocolos</h1>
            <p className="text-sm text-gray-400 mt-0.5">Acompanhe e gerencie todas as tramitações</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={handleRunAll} className="flex items-center gap-1.5 bg-brand-700 hover:bg-brand-800 text-white px-3.5 py-2 rounded-lg text-sm font-medium transition shadow-sm">
              <RefreshCw size={14} /> Consultar Todos
            </button>
            <button onClick={downloadPdf} className="flex items-center gap-1.5 bg-white border border-gray-200 text-gray-700 px-3.5 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition shadow-sm">
              <FileText size={14} /> Baixar PDF
            </button>
            <label className="flex items-center gap-1.5 cursor-pointer bg-white border border-gray-200 text-gray-700 px-3.5 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition shadow-sm">
              <Upload size={14} /> Importar Planilha
              <input type="file" accept=".xlsx,.xls" className="hidden" onChange={handleImport} />
            </label>
            <button onClick={() => { setShowForm(true); setEditItem(null); setForm(EMPTY_FORM) }} className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white px-3.5 py-2 rounded-lg text-sm font-medium transition shadow-sm">
              <Plus size={14} /> Novo Protocolo
            </button>
          </div>
        </div>

        {/* ── Erro de página ── */}
        {pageError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center justify-between">
            <span>{pageError}</span>
            <button onClick={() => setPageError(null)} className="ml-4 text-red-400 hover:text-red-600 transition"><X size={14} /></button>
          </div>
        )}

        {/* ── Stat cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Total de Protocolos"  value={dashData?.total ?? protocols.length}              icon={ClipboardList} color="blue" />
          <StatCard label="Protocolos Ativos"    value={dashData?.ativos ?? 0}                           icon={CheckCircle2}  color="green" />
          <StatCard label="Com Mudança Recente"  value={dashData?.com_mudanca_recente ?? 0}              icon={Zap}           color="amber" />
        </div>

        {/* ── Cards de status (clicáveis) ── */}
        {!isLoading && protocols.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {STATUS_CONFIG.filter(s => statusCounts[s.key] > 0).map(s => (
              <button
                key={s.key}
                onClick={() => setFilterStatus(prev => prev === s.key ? '' : s.key)}
                className={`text-left rounded-xl border p-3.5 transition ${
                  filterStatus === s.key
                    ? `${s.activeBg} ${s.activeBorder} shadow-sm`
                    : 'bg-white border-gray-100 shadow-sm hover:shadow hover:border-gray-200'
                }`}
              >
                <div className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border mb-2 ${filterStatus === s.key ? s.badgeActive : s.badge}`}>
                  {s.label}
                </div>
                <p className={`text-2xl font-bold tabular-nums leading-none ${filterStatus === s.key ? s.activeValue : 'text-gray-900'}`}>
                  {statusCounts[s.key]}
                </p>
              </button>
            ))}
          </div>
        )}

        {/* ── Barra de busca e filtros ── */}
        <div className="flex gap-2 items-center flex-wrap">
          <div className="relative flex-1 min-w-60">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              placeholder="Buscar por projeto, protocolo, órgão, atividade..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-xl pl-9 pr-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent shadow-sm transition"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition">
                <X size={13} />
              </button>
            )}
          </div>

          <FilterSelect icon={Layers} value={filterProject} onChange={setFilterProject} placeholder="Todos os projetos">
            {uniqueProjects.map(p => <option key={p} value={p}>{p}</option>)}
          </FilterSelect>

          <FilterSelect icon={Building2} value={filterOrgao} onChange={setFilterOrgao} placeholder="Todos os órgãos">
            {uniqueOrgaos.map(o => <option key={o} value={o}>{o}</option>)}
          </FilterSelect>

          {hasFilters && (
            <button onClick={clearFilters} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 bg-white border border-gray-200 px-3 py-2.5 rounded-xl shadow-sm transition">
              <X size={12} /> Limpar
            </button>
          )}

          <span className="ml-auto text-sm text-gray-400 whitespace-nowrap">
            {filteredData.length !== protocols.length
              ? `${filteredData.length} de ${protocols.length}`
              : protocols.length} protocolo(s)
          </span>
        </div>

        {/* ── Barra de seleção em massa ── */}
        {selected.size > 0 && (
          <div className="flex items-center justify-between bg-brand-50 border border-brand-200 rounded-xl px-4 py-3">
            <span className="text-sm text-brand-800 font-medium">{selected.size} protocolo(s) selecionado(s)</span>
            <div className="flex gap-2">
              <button onClick={() => setSelected(new Set())} className="text-xs text-gray-500 hover:text-gray-700 transition">Limpar seleção</button>
              <button onClick={() => setShowBulkConfirm(true)} className="flex items-center gap-1.5 text-sm px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition">
                <Trash2 size={12} /> Excluir selecionados
              </button>
            </div>
          </div>
        )}

        {/* ── Tabela ── */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner />
          </div>
        ) : filteredData.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm py-16 flex flex-col items-center gap-3 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
              <Search size={20} className="text-gray-400" />
            </div>
            <p className="text-gray-600 font-medium">Nenhum protocolo encontrado</p>
            <p className="text-sm text-gray-400">Tente ajustar os filtros</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/70">
                  <th className="px-3 py-3 w-8">
                    <input type="checkbox" checked={filteredData.length > 0 && selected.size === filteredData.length} onChange={toggleSelectAll} className="rounded" />
                  </th>
                  {['Projeto','Protocolo','Atividade','Órgão','Status','Situação','Ativo','Duração','Mudança','Ações'].map(h => (
                    <th key={h} className="text-left px-3 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredData.map(p => (
                  <tr key={p.id} className={`hover:bg-gray-50/70 transition-colors ${selected.has(p.id) ? 'bg-brand-50/60' : ''}`}>
                    <td className="px-3 py-3">
                      <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} className="rounded" />
                    </td>
                    <td className="px-3 py-3 font-medium text-gray-900 max-w-[120px] truncate">{p.projeto}</td>
                    <td className="px-3 py-3 font-mono text-xs text-gray-500">{p.protocolo}</td>
                    <td className="px-3 py-3 text-gray-600 max-w-[140px] truncate">{p.atividade}</td>
                    <td className="px-3 py-3 max-w-[110px]">
                      <span className="text-xs text-gray-500 truncate block">{p.orgao_site_consultado}</span>
                    </td>
                    <td className="px-3 py-3"><StatusBadge status={p.status} /></td>
                    <td className="px-3 py-3 text-gray-400 text-xs">{p.situacao ?? <span className="text-gray-300">—</span>}</td>
                    <td className="px-3 py-3">
                      {p.ativo
                        ? <span className="inline-flex text-xs text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">Ativo</span>
                        : <span className="inline-flex text-xs text-gray-500 bg-gray-100 border border-gray-200 px-2 py-0.5 rounded-full">Inativo</span>
                      }
                    </td>
                    <td className="px-3 py-3 text-gray-400 text-xs whitespace-nowrap">{p.duracao_dias != null ? `${p.duracao_dias}d` : '—'}</td>
                    <td className="px-3 py-3">
                      {(mudancaMap[p.id] || p.houve_mudanca) && (
                        <span className="inline-flex items-center gap-1 text-xs bg-amber-50 text-amber-700 border border-amber-100 px-2 py-0.5 rounded-full">
                          <AlertTriangle size={10} /> Mudança
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3 pr-4">
                      <div className="flex gap-0.5">
                        <button onClick={() => queryMut.mutate(p.id)} title="Consultar" className="p-1.5 text-brand-600 hover:bg-brand-50 rounded-lg transition"><RefreshCw size={13} /></button>
                        <button onClick={() => openEdit(p)} title="Editar" className="p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg transition"><Pencil size={13} /></button>
                        <button onClick={() => { if (confirm('Remover/inativar?')) delMut.mutate(p.id) }} title="Remover" className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition"><Trash2 size={13} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Modal: Formulário ── */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">{editItem ? 'Editar Protocolo' : 'Novo Protocolo'}</h2>
              <button onClick={() => { setShowForm(false); setEditItem(null); setFormError(null) }} className="text-gray-400 hover:text-gray-600 transition"><X size={18} /></button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                {CAMPOS.map(([key, label]) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">{label}</label>
                    <input
                      type={key.startsWith('data') ? 'date' : 'text'}
                      value={form[key] ?? ''}
                      onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                      className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent focus:bg-white transition"
                    />
                  </div>
                ))}
                <div className="col-span-2 flex items-center gap-2.5 bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200">
                  <input type="checkbox" id="ativo" checked={form.ativo} onChange={e => setForm(f => ({ ...f, ativo: e.target.checked }))} className="w-4 h-4 rounded accent-brand-600" />
                  <label htmlFor="ativo" className="text-sm text-gray-700 font-medium cursor-pointer">Protocolo ativo</label>
                </div>
              </div>
              {formError && <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{formError}</div>}
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
                <button onClick={() => { setShowForm(false); setEditItem(null); setFormError(null) }} className="px-4 py-2 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition">Cancelar</button>
                <button onClick={handleSave} disabled={saveMut.isPending} className="px-4 py-2 text-sm bg-brand-700 hover:bg-brand-800 text-white rounded-lg disabled:opacity-50 transition font-medium">
                  {saveMut.isPending ? 'Salvando...' : 'Salvar Protocolo'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Processando planilha ── */}
      {importing && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl px-10 py-10 flex flex-col items-center gap-4">
            <svg className="animate-spin h-8 w-8 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            <div className="text-center">
              <p className="text-gray-800 font-semibold">Processando planilha</p>
              <p className="text-gray-400 text-sm mt-1">Isso pode levar alguns instantes...</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Preview de importação ── */}
      {importPreview && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Preview da Importação</h3>
              <button onClick={() => setImportPreview(null)} className="text-gray-400 hover:text-gray-600 transition">
                <X size={18} />
              </button>
            </div>

            <div className="px-6 py-3 bg-gray-50/70 border-b border-gray-100 flex gap-6 text-sm">
              <span className="text-emerald-700 font-medium">{importPreview.rows.length} linha(s) para importar</span>
              <span className="text-amber-700 font-medium">{importPreview.ignorados.length} ignorada(s)</span>
              <span className="text-red-700 font-medium">{importPreview.erros.length} erro(s)</span>
            </div>

            <div className="flex-1 overflow-auto p-4 space-y-4">
              {importPreview.rows.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">Nenhuma linha válida encontrada para importar.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-gray-50/70 border-b border-gray-100 text-gray-400 text-left uppercase tracking-wider">
                        {['Linha', 'Projeto', 'Protocolo', 'Atividade', 'Status', 'Abertura'].map(h => (
                          <th key={h} className="px-3 py-2 font-medium whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {importPreview.rows.map((row, i) => (
                        <tr key={i} className="hover:bg-gray-50/70 transition-colors">
                          <td className="px-3 py-2 font-mono text-gray-400 whitespace-nowrap">{row.linha}</td>
                          <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">{row.projeto}</td>
                          <td className="px-3 py-2 font-mono text-gray-500 whitespace-nowrap">{row.protocolo}</td>
                          <td className="px-3 py-2 text-gray-600 max-w-xs truncate">{row.atividade}</td>
                          <td className="px-3 py-2 whitespace-nowrap"><StatusBadge status={row.status} /></td>
                          <td className="px-3 py-2 text-gray-400 whitespace-nowrap">{row.data_abertura}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {importPreview.ignorados.length > 0 && (
                <details>
                  <summary className="text-sm text-amber-700 cursor-pointer font-medium select-none">
                    {importPreview.ignorados.length} linha(s) ignorada(s) — clique para ver
                  </summary>
                  <ul className="mt-2 space-y-1">
                    {importPreview.ignorados.map((ig, i) => (
                      <li key={i} className="flex gap-2 text-xs bg-amber-50 border border-amber-100 rounded-lg px-3 py-1.5">
                        <span className="font-mono text-gray-400 whitespace-nowrap">{ig.linha}</span>
                        <span className="text-amber-800">{ig.motivo}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              {importPreview.erros.length > 0 && (
                <details>
                  <summary className="text-sm text-red-700 cursor-pointer font-medium select-none">
                    {importPreview.erros.length} erro(s) de parsing — clique para ver
                  </summary>
                  <ul className="mt-2 space-y-1">
                    {importPreview.erros.map((er, i) => (
                      <li key={i} className="flex gap-2 text-xs bg-red-50 border border-red-100 rounded-lg px-3 py-1.5">
                        <span className="font-mono text-gray-400 whitespace-nowrap">{er.linha}</span>
                        <span className="text-red-800">{er.erro}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>

            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={() => setImportPreview(null)}
                disabled={confirming}
                className="px-4 py-2 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmImport}
                disabled={importPreview.rows.length === 0 || confirming}
                className="px-4 py-2 text-sm bg-brand-700 hover:bg-brand-800 text-white rounded-lg disabled:opacity-50 transition font-medium"
              >
                {confirming
                  ? 'Importando...'
                  : `Confirmar importação (${importPreview.rows.length} linha${importPreview.rows.length !== 1 ? 's' : ''})`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Resultado importação ── */}
      {importResult && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-80">
            <h3 className="text-base font-semibold text-gray-900 mb-4">Importação concluída</h3>
            <div className="space-y-2">
              <ResultRow color="emerald" label="Importados" value={importResult.importados?.length ?? 0} />
              <ResultRow color="amber"   label="Ignorados"  value={importResult.ignorados?.length ?? 0} />
              <ResultRow color="red"     label="Erros"      value={importResult.erros?.length ?? 0} />
            </div>
            <button onClick={() => setImportResult(null)} className="mt-4 w-full py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-sm font-medium transition">OK</button>
          </div>
        </div>
      )}

      {/* ── Modal: Confirmar exclusão em massa ── */}
      {showBulkConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-96">
            <h3 className="text-base font-semibold text-gray-900 mb-2">Excluir {selected.size} protocolo(s)?</h3>
            <p className="text-sm text-gray-500 mb-1">Protocolos com histórico serão <span className="font-medium text-amber-700">inativados</span>. Os demais serão <span className="font-medium text-red-700">removidos permanentemente</span>.</p>
            <p className="text-xs text-gray-400 mb-5">Para remover tudo permanentemente, use "Forçar exclusão".</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowBulkConfirm(false)} className="px-3 py-2 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition">Cancelar</button>
              <button onClick={() => bulkDelMut.mutate(true)} disabled={bulkDelMut.isPending} className="px-3 py-2 text-sm border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 rounded-lg disabled:opacity-50 transition">Forçar exclusão</button>
              <button onClick={() => bulkDelMut.mutate(false)} disabled={bulkDelMut.isPending} className="px-3 py-2 text-sm bg-brand-700 hover:bg-brand-800 text-white rounded-lg disabled:opacity-50 transition">
                {bulkDelMut.isPending ? 'Excluindo...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Resultado de consulta individual ── */}
      {queryResult && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-[440px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-gray-900">
                Resultado — <span className="font-mono text-brand-700">{queryResult.protocolo}</span>
              </h3>
              <button onClick={() => setQueryResult(null)} className="text-gray-400 hover:text-gray-600 transition"><X size={16} /></button>
            </div>
            {queryResult.resultado?.erro ? (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
                {queryResult.mudancas_detectadas?.[0] ?? queryResult.resultado.erro}
              </div>
            ) : queryResult.mudancas_detectadas?.length > 0 ? (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold uppercase tracking-wider text-amber-600 mb-2">Mudanças detectadas</p>
                {queryResult.mudancas_detectadas.map((m, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-gray-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2.5">
                    <AlertTriangle size={13} className="text-amber-500 mt-0.5 flex-shrink-0" /> {m}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3 text-sm text-emerald-700">
                Nenhuma mudança detectada em relação à última consulta.
              </div>
            )}
            {queryResult.resultado?.status_consultado && (
              <p className="text-xs text-gray-400 mt-3">
                Status atual: <span className="font-medium text-gray-600">{queryResult.resultado.status_consultado}</span>
              </p>
            )}
            <button onClick={() => setQueryResult(null)} className="mt-4 w-full py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-sm font-medium transition">OK</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Componentes auxiliares ──

function FilterSelect({ icon: Icon, value, onChange, placeholder, children }) {
  return (
    <div className="relative">
      <Icon size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="appearance-none bg-white border border-gray-200 rounded-xl pl-8 pr-7 py-2.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm transition cursor-pointer"
      >
        <option value="">{placeholder}</option>
        {children}
      </select>
      <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
    </div>
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
    APROVADO:       'bg-emerald-50 text-emerald-700 border-emerald-200',
    'EM ANDAMENTO': 'bg-blue-50 text-blue-700 border-blue-200',
    PENDENTE:       'bg-amber-50 text-amber-700 border-amber-200',
    CANCELADO:      'bg-red-50 text-red-700 border-red-200',
    REPROVADO:      'bg-red-50 text-red-700 border-red-200',
  }
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border leading-none ${map[status] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}>
      {status === 'EM ANDAMENTO' ? 'ANDAMENTO' : status}
    </span>
  )
}

function ResultRow({ color, label, value }) {
  const s = {
    emerald: { row: 'bg-emerald-50 border-emerald-100', text: 'text-emerald-700', val: 'text-emerald-800' },
    amber:   { row: 'bg-amber-50 border-amber-100',     text: 'text-amber-700',   val: 'text-amber-800'   },
    red:     { row: 'bg-red-50 border-red-100',         text: 'text-red-700',     val: 'text-red-800'     },
  }[color]
  return (
    <div className={`flex items-center justify-between ${s.row} border rounded-lg px-4 py-2.5`}>
      <span className={`text-sm ${s.text}`}>{label}</span>
      <span className={`font-bold ${s.val}`}>{value}</span>
    </div>
  )
}

function Spinner() {
  return (
    <div className="flex items-center gap-3 text-gray-400 text-sm">
      <svg className="animate-spin h-5 w-5 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      Carregando...
    </div>
  )
}
