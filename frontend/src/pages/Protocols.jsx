import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getProtocols, createProtocol, updateProtocol, deleteProtocol,
  bulkDeleteProtocols, runSingleQuery, importSpreadsheet,
  previewSpreadsheet, confirmImport,
} from '../services/api'
import {
  Plus, Upload, RefreshCw, Pencil, Trash2, ArrowLeft,
  Search, Building2, X, ChevronDown, AlertTriangle, ClipboardList,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const EMPTY_FORM = {
  status: 'PENDENTE', projeto: '', protocolo: '', atividade: '',
  orgao_site_consultado: '', atribuido_a: '', data_abertura: '',
  data_finalizacao: '', situacao: '', ativo: true, url_consulta: '',
}

export default function Protocols() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterOrgao, setFilterOrgao] = useState('')
  const [formError, setFormError] = useState(null)
  const [pageError, setPageError] = useState(null)
  const [importing, setImporting] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [importPreview, setImportPreview] = useState(null)
  const [importResult, setImportResult] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [showBulkConfirm, setShowBulkConfirm] = useState(false)
  const [queryResult, setQueryResult] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['protocols'],
    queryFn: () => getProtocols({}),
  })

  const uniqueOrgaos = useMemo(() =>
    [...new Set(data.map(p => p.orgao_site_consultado).filter(Boolean))].sort(),
    [data]
  )

  const filteredData = useMemo(() => {
    const q = searchQuery.toLowerCase().trim()
    return data.filter(p => {
      const matchesSearch = !q || [
        p.projeto, p.protocolo, p.atividade,
        p.orgao_site_consultado, p.situacao, p.atribuido_a,
      ].some(f => f?.toLowerCase().includes(q))
      const matchesOrgao = !filterOrgao || p.orgao_site_consultado === filterOrgao
      return matchesSearch && matchesOrgao
    })
  }, [data, searchQuery, filterOrgao])

  const saveMut = useMutation({
    mutationFn: (d) => editItem ? updateProtocol(editItem.id, d) : createProtocol(d),
    onSuccess: () => {
      qc.invalidateQueries(['protocols'])
      setShowForm(false); setEditItem(null); setForm(EMPTY_FORM); setFormError(null)
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao salvar protocolo'
      setFormError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
    },
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteProtocol(id),
    onSuccess: () => { qc.invalidateQueries(['protocols']); setPageError(null) },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao excluir protocolo'
      setPageError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
    },
  })

  function handleSave() {
    if (!form.projeto?.trim())               return setFormError('Projeto é obrigatório')
    if (!form.protocolo?.trim())             return setFormError('Protocolo é obrigatório')
    if (!form.atividade?.trim())             return setFormError('Atividade é obrigatória')
    if (!form.orgao_site_consultado?.trim()) return setFormError('Órgão / Site é obrigatório')
    if (!form.data_abertura)                 return setFormError('Data de Abertura é obrigatória')
    setFormError(null)
    saveMut.mutate(form)
  }

  const queryMut = useMutation({
    mutationFn: (id) => runSingleQuery(id),
    onSuccess: (res) => { qc.invalidateQueries(['protocols']); setQueryResult(res) },
  })

  const bulkDelMut = useMutation({
    mutationFn: (force) => bulkDeleteProtocols([...selected], force),
    onSuccess: () => { qc.invalidateQueries(['protocols']); setSelected(new Set()); setShowBulkConfirm(false) },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao excluir'
      setPageError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
      setShowBulkConfirm(false)
    },
  })

  function toggleSelect(id) {
    setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  }

  function toggleSelectAll() {
    if (selected.size === filteredData.length) setSelected(new Set())
    else setSelected(new Set(filteredData.map(p => p.id)))
  }

  function openEdit(item) {
    setEditItem(item)
    setForm({ ...item, data_abertura: item.data_abertura?.slice(0, 10) ?? '', data_finalizacao: item.data_finalizacao?.slice(0, 10) ?? '' })
    setShowForm(true)
  }

  async function handleImport(e) {
    const file = e.target.files[0]
    if (!file) return
    e.target.value = ''
    setImporting(true)
    setImportResult(null)
    setImportPreview(null)
    try {
      const result = await previewSpreadsheet(file)
      setImportPreview(result)
    } catch (err) {
      setPageError(err.response?.data?.detail || 'Erro ao processar planilha')
    } finally {
      setImporting(false)
    }
  }

  async function handleConfirmImport() {
    if (!importPreview) return
    setConfirming(true)
    try {
      const result = await confirmImport(importPreview.rows)
      setImportResult(result)
      setImportPreview(null)
      qc.invalidateQueries(['protocols'])
    } catch (err) {
      setPageError(err.response?.data?.detail || 'Erro ao importar dados')
    } finally {
      setConfirming(false)
    }
  }

  const campos = [
    ['status', 'Status'], ['projeto', 'Projeto'], ['protocolo', 'Protocolo'],
    ['atividade', 'Atividade'], ['orgao_site_consultado', 'Órgão / Site'],
    ['atribuido_a', 'Atribuído a'], ['data_abertura', 'Data Abertura'],
    ['data_finalizacao', 'Data Finalização'], ['situacao', 'Situação'],
    ['url_consulta', 'URL Consulta'],
  ]

  const hasFilters = searchQuery || filterOrgao

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Topbar */}
      <nav className="bg-brand-950 border-b border-brand-900/50 text-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="text-brand-400 hover:text-white transition">
              <ArrowLeft size={16} />
            </button>
            <div className="w-px h-5 bg-brand-800" />
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-brand-600 rounded-md flex items-center justify-center">
                <ClipboardList size={12} />
              </div>
              <span className="font-semibold text-sm">Protocolos</span>
            </div>
          </div>
          <div className="flex gap-2">
            <label className="flex items-center gap-1.5 cursor-pointer text-brand-300 hover:text-white hover:bg-brand-800 px-3 py-1.5 rounded-lg text-sm transition">
              <Upload size={13} /> Importar Planilha
              <input type="file" accept=".xlsx,.xls" className="hidden" onChange={handleImport} />
            </label>
            <button
              onClick={() => { setShowForm(true); setEditItem(null); setForm(EMPTY_FORM) }}
              className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition"
            >
              <Plus size={13} /> Novo Protocolo
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-4">
        {pageError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center justify-between">
            <span>{pageError}</span>
            <button onClick={() => setPageError(null)} className="ml-4 text-red-400 hover:text-red-600 transition"><X size={14} /></button>
          </div>
        )}

        {/* Search & filter bar */}
        <div className="flex gap-3 items-center flex-wrap">
          <div className="relative flex-1 min-w-64">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              placeholder="Buscar por projeto, protocolo, órgão, atividade..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-xl pl-9 pr-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent shadow-sm transition"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition">
                <X size={13} />
              </button>
            )}
          </div>

          <div className="relative">
            <Building2 size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <select
              value={filterOrgao}
              onChange={(e) => setFilterOrgao(e.target.value)}
              className="appearance-none bg-white border border-gray-200 rounded-xl pl-8 pr-8 py-2.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm transition cursor-pointer"
            >
              <option value="">Todos os órgãos</option>
              {uniqueOrgaos.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
            <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          </div>

          {hasFilters && (
            <button
              onClick={() => { setSearchQuery(''); setFilterOrgao('') }}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 bg-white border border-gray-200 px-3 py-2.5 rounded-xl shadow-sm transition"
            >
              <X size={12} /> Limpar filtros
            </button>
          )}

          <span className="ml-auto text-sm text-gray-400">
            {filteredData.length !== data.length
              ? `${filteredData.length} de ${data.length} protocolo(s)`
              : `${data.length} protocolo(s)`}
          </span>
        </div>

        {/* Modal: Formulário */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">{editItem ? 'Editar Protocolo' : 'Novo Protocolo'}</h2>
                <button onClick={() => { setShowForm(false); setEditItem(null); setFormError(null) }} className="text-gray-400 hover:text-gray-600 transition">
                  <X size={18} />
                </button>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  {campos.map(([key, label]) => (
                    <div key={key}>
                      <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">{label}</label>
                      <input
                        type={key.startsWith('data') ? 'date' : 'text'}
                        value={form[key] ?? ''}
                        onChange={(e) => setForm(f => ({ ...f, [key]: e.target.value }))}
                        className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent focus:bg-white transition"
                      />
                    </div>
                  ))}
                  <div className="col-span-2 flex items-center gap-2.5 bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200">
                    <input type="checkbox" id="ativo" checked={form.ativo} onChange={(e) => setForm(f => ({ ...f, ativo: e.target.checked }))} className="w-4 h-4 rounded accent-brand-600" />
                    <label htmlFor="ativo" className="text-sm text-gray-700 font-medium cursor-pointer">Protocolo ativo</label>
                  </div>
                </div>
                {formError && (
                  <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{formError}</div>
                )}
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

        {/* Modal: Preview de importação */}
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

        {/* Modal: Importando */}
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

        {/* Modal: Resultado importação */}
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

        {/* Modal: Confirmar exclusão em massa */}
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

        {/* Barra seleção em massa */}
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

        {/* Modal: Resultado de consulta individual */}
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
                      <AlertTriangle size={13} className="text-amber-500 mt-0.5 flex-shrink-0" />
                      {m}
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

        {/* Tabela */}
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-gray-400 text-sm">
              <svg className="animate-spin h-5 w-5 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Carregando protocolos...
            </div>
          </div>
        ) : filteredData.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm py-16 flex flex-col items-center gap-3 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
              <Search size={20} className="text-gray-400" />
            </div>
            <p className="text-gray-600 font-medium">Nenhum protocolo encontrado</p>
            <p className="text-sm text-gray-400">Tente ajustar os filtros de busca</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/70">
                  <th className="px-4 py-3 w-8">
                    <input type="checkbox" checked={filteredData.length > 0 && selected.size === filteredData.length} onChange={toggleSelectAll} className="rounded" />
                  </th>
                  {['Projeto', 'Protocolo', 'Atividade', 'Órgão', 'Status', 'Situação', 'Ativo', 'Atribuído a', 'Data Abertura', 'Data Finalização', 'URL', 'Duração', 'Ações'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredData.map((p) => (
                  <tr key={p.id} className={`hover:bg-gray-50/70 transition-colors ${selected.has(p.id) ? 'bg-brand-50/60' : ''}`}>
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} className="rounded" />
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 max-w-[140px] truncate">{p.projeto}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{p.protocolo}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate">{p.atividade}</td>
                    <td className="px-4 py-3 max-w-[120px]">
                      <span className="text-xs text-gray-500 truncate block">{p.orgao_site_consultado}</span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={p.status} /></td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{fmt(p.situacao)}</td>
                    <td className="px-4 py-3">
                      {p.ativo
                        ? <span className="inline-flex text-xs text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">Ativo</span>
                        : <span className="inline-flex text-xs text-gray-500 bg-gray-100 border border-gray-200 px-2 py-0.5 rounded-full">Inativo</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs max-w-[120px] truncate">{fmt(p.atribuido_a)}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{fmt(p.data_abertura)}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{fmt(p.data_finalizacao)}</td>
                    <td className="px-4 py-3 text-xs max-w-[140px] truncate">
                      {fmtUrl(p.url_consulta)}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{calcDuracao(p.data_abertura, p.data_finalizacao)}</td>
                    <td className="px-4 py-3">
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
    </div>
  )
}

function fmt(val) {
  if (val == null) return '-'
  const s = String(val).trim()
  if (s === '' || s.toLowerCase() === 'nan') return '-'
  return s
}

function fmtUrl(val) {
  const s = fmt(val)
  if (s === '-') return <span className="text-gray-300">-</span>
  return (
    <a href={s} target="_blank" rel="noopener noreferrer" title={s}
      className="text-brand-600 hover:underline truncate block max-w-[140px]">
      {s.replace(/^https?:\/\//, '')}
    </a>
  )
}

function calcDuracao(data_abertura, data_finalizacao) {
  const a = fmt(data_abertura)
  if (a === '-') return '-'
  try {
    const abertura = new Date(a)
    if (isNaN(abertura.getTime())) return '-'
    const fim = data_finalizacao && fmt(data_finalizacao) !== '-'
      ? new Date(data_finalizacao)
      : new Date()
    const dias = Math.max(0, Math.floor((fim - abertura) / 86400000))
    return `${dias}d`
  } catch {
    return '-'
  }
}

function StatusBadge({ status }) {
  const map = {
    APRO:           'bg-emerald-50 text-emerald-700 border-emerald-200',
    APROVADO:       'bg-emerald-50 text-emerald-700 border-emerald-200',
    'EM ANDAMENTO': 'bg-blue-50   text-blue-700   border-blue-200',
    PENDENTE:       'bg-amber-50  text-amber-700  border-amber-200',
    CANCELADO:      'bg-red-50    text-red-700    border-red-200',
    REPROVADO:      'bg-red-50    text-red-700    border-red-200',
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
    amber:   { row: 'bg-amber-50 border-amber-100',     text: 'text-amber-700',   val: 'text-amber-800' },
    red:     { row: 'bg-red-50 border-red-100',         text: 'text-red-700',     val: 'text-red-800' },
  }[color]
  return (
    <div className={`flex items-center justify-between ${s.row} border rounded-lg px-4 py-2.5`}>
      <span className={`text-sm ${s.text}`}>{label}</span>
      <span className={`font-bold ${s.val}`}>{value}</span>
    </div>
  )
}
