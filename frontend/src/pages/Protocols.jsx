import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProtocols, createProtocol, updateProtocol, deleteProtocol, bulkDeleteProtocols, runSingleQuery, importSpreadsheet } from '../services/api'
import { Plus, Upload, RefreshCw, Pencil, Trash2, ArrowLeft } from 'lucide-react'
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
  const [filterProjeto, setFilterProjeto] = useState('')
  const [formError, setFormError] = useState(null)
  const [pageError, setPageError] = useState(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [showBulkConfirm, setShowBulkConfirm] = useState(false)

  const { data = [], isLoading } = useQuery({
    queryKey: ['protocols', filterProjeto],
    queryFn: () => getProtocols(filterProjeto ? { projeto: filterProjeto } : {}),
  })

  const saveMut = useMutation({
    mutationFn: (d) => editItem ? updateProtocol(editItem.id, d) : createProtocol(d),
    onSuccess: () => {
      qc.invalidateQueries(['protocols'])
      setShowForm(false)
      setEditItem(null)
      setForm(EMPTY_FORM)
      setFormError(null)
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
    if (!form.projeto?.trim()) return setFormError('Projeto é obrigatório')
    if (!form.protocolo?.trim()) return setFormError('Protocolo é obrigatório')
    if (!form.atividade?.trim()) return setFormError('Atividade é obrigatória')
    if (!form.orgao_site_consultado?.trim()) return setFormError('Órgão / Site é obrigatório')
    if (!form.data_abertura) return setFormError('Data de Abertura é obrigatória')
    setFormError(null)
    saveMut.mutate(form)
  }

  const queryMut = useMutation({
    mutationFn: (id) => runSingleQuery(id),
    onSuccess: () => qc.invalidateQueries(['protocols']),
  })

  const bulkDelMut = useMutation({
    mutationFn: (force) => bulkDeleteProtocols([...selected], force),
    onSuccess: () => {
      qc.invalidateQueries(['protocols'])
      setSelected(new Set())
      setShowBulkConfirm(false)
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || err.message || 'Erro ao excluir'
      setPageError(typeof msg === 'object' ? JSON.stringify(msg) : msg)
      setShowBulkConfirm(false)
    },
  })

  function toggleSelect(id) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (selected.size === data.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(data.map(p => p.id)))
    }
  }

  function openEdit(item) {
    setEditItem(item)
    setForm({
      ...item,
      data_abertura: item.data_abertura?.slice(0, 10) ?? '',
      data_finalizacao: item.data_finalizacao?.slice(0, 10) ?? '',
    })
    setShowForm(true)
  }

  async function handleImport(e) {
    const file = e.target.files[0]
    if (!file) return
    e.target.value = ''
    setImporting(true)
    setImportResult(null)
    try {
      const result = await importSpreadsheet(file)
      setImportResult(result)
      qc.invalidateQueries(['protocols'])
    } finally {
      setImporting(false)
    }
  }

  const campos = [
    ['status', 'Status'], ['projeto', 'Projeto'], ['protocolo', 'Protocolo'],
    ['atividade', 'Atividade'], ['orgao_site_consultado', 'Órgão / Site'],
    ['atribuido_a', 'Atribuído a'], ['data_abertura', 'Data Abertura'],
    ['data_finalizacao', 'Data Finalização'], ['situacao', 'Situação'],
    ['url_consulta', 'URL Consulta'],
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-brand-900 text-white px-6 py-4 flex justify-between items-center">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:underline text-sm">
          <ArrowLeft size={14} /> Dashboard
        </button>
        <h1 className="text-lg font-bold">Protocolos</h1>
        <div className="flex gap-2">
          <label className="flex items-center gap-1 cursor-pointer bg-white/10 px-3 py-1.5 rounded text-sm hover:bg-white/20">
            <Upload size={14} /> Importar Planilha
            <input type="file" accept=".xlsx,.xls" className="hidden" onChange={handleImport} />
          </label>
          <button onClick={() => { setShowForm(true); setEditItem(null); setForm(EMPTY_FORM) }}
            className="flex items-center gap-1 bg-brand-500 px-3 py-1.5 rounded text-sm hover:bg-brand-700">
            <Plus size={14} /> Novo
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6 space-y-4">
        {pageError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex justify-between">
            <span>{pageError}</span>
            <button onClick={() => setPageError(null)} className="font-bold ml-4">×</button>
          </div>
        )}
        <input
          placeholder="Filtrar por projeto..."
          value={filterProjeto}
          onChange={(e) => setFilterProjeto(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-brand-500"
        />

        {showForm && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto p-6">
              <h2 className="text-lg font-semibold mb-4">{editItem ? 'Editar Protocolo' : 'Novo Protocolo'}</h2>
              <div className="grid grid-cols-2 gap-3">
                {campos.map(([key, label]) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                    <input type={key.startsWith('data') ? 'date' : 'text'} value={form[key] ?? ''}
                      onChange={(e) => setForm(f => ({ ...f, [key]: e.target.value }))}
                      className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500" />
                  </div>
                ))}
                <div className="flex items-center gap-2 col-span-2">
                  <input type="checkbox" id="ativo" checked={form.ativo} onChange={(e) => setForm(f => ({ ...f, ativo: e.target.checked }))} />
                  <label htmlFor="ativo" className="text-sm">Ativo</label>
                </div>
              </div>
              {formError && (
                <div className="mt-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {formError}
                </div>
              )}
              <div className="flex justify-end gap-2 mt-4">
                <button onClick={() => { setShowForm(false); setEditItem(null); setFormError(null) }} className="text-sm px-4 py-2 border rounded-lg hover:bg-gray-50">Cancelar</button>
                <button onClick={handleSave} disabled={saveMut.isPending}
                  className="text-sm px-4 py-2 bg-brand-700 text-white rounded-lg hover:bg-brand-900 disabled:opacity-50">
                  {saveMut.isPending ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </div>
          </div>
        )}

        {importing && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl px-10 py-8 flex flex-col items-center gap-4">
              <svg className="animate-spin h-8 w-8 text-brand-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <p className="text-gray-700 font-medium">Importando planilha...</p>
              <p className="text-gray-400 text-xs">Isso pode levar alguns instantes.</p>
            </div>
          </div>
        )}

        {importResult && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl p-6 w-72 flex flex-col gap-3">
              <h3 className="text-base font-semibold text-gray-800">Importação concluída</h3>
              <div className="text-sm space-y-1">
                <p className="text-green-700">Importados: <span className="font-bold">{importResult.importados?.length ?? 0}</span></p>
                <p className="text-yellow-700">Ignorados: <span className="font-bold">{importResult.ignorados?.length ?? 0}</span></p>
                <p className="text-red-700">Erros: <span className="font-bold">{importResult.erros?.length ?? 0}</span></p>
              </div>
              <button onClick={() => setImportResult(null)}
                className="mt-1 self-end text-sm px-4 py-2 bg-brand-700 text-white rounded-lg hover:bg-brand-900">
                OK
              </button>
            </div>
          </div>
        )}

        {showBulkConfirm && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl p-6 w-80 flex flex-col gap-4">
              <h3 className="text-base font-semibold text-gray-800">Excluir {selected.size} protocolo(s)?</h3>
              <p className="text-sm text-gray-500">Protocolos com histórico de consulta serão <span className="font-medium text-yellow-700">inativados</span>. Os demais serão <span className="font-medium text-red-700">removidos permanentemente</span>.</p>
              <p className="text-xs text-gray-400">Para remover tudo permanentemente, use "Forçar exclusão".</p>
              <div className="flex justify-end gap-2 mt-1">
                <button onClick={() => setShowBulkConfirm(false)} className="text-sm px-3 py-2 border rounded-lg hover:bg-gray-50">Cancelar</button>
                <button onClick={() => bulkDelMut.mutate(true)} disabled={bulkDelMut.isPending}
                  className="text-sm px-3 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50">
                  Forçar exclusão
                </button>
                <button onClick={() => bulkDelMut.mutate(false)} disabled={bulkDelMut.isPending}
                  className="text-sm px-3 py-2 bg-brand-700 text-white rounded-lg hover:bg-brand-900 disabled:opacity-50">
                  {bulkDelMut.isPending ? 'Excluindo...' : 'Confirmar'}
                </button>
              </div>
            </div>
          </div>
        )}

        {selected.size > 0 && (
          <div className="flex items-center justify-between bg-brand-50 border border-brand-200 rounded-lg px-4 py-2">
            <span className="text-sm text-brand-900 font-medium">{selected.size} protocolo(s) selecionado(s)</span>
            <div className="flex gap-2">
              <button onClick={() => setSelected(new Set())} className="text-xs text-gray-500 hover:underline">Limpar seleção</button>
              <button onClick={() => setShowBulkConfirm(true)}
                className="flex items-center gap-1 text-sm px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700">
                <Trash2 size={13} /> Excluir selecionados
              </button>
            </div>
          </div>
        )}

        {isLoading ? <p className="text-gray-500">Carregando...</p> : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-500 bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2 w-8">
                    <input type="checkbox" checked={data.length > 0 && selected.size === data.length}
                      onChange={toggleSelectAll} />
                  </th>
                  {['Projeto', 'Protocolo', 'Atividade', 'Órgão', 'Status', 'Situação', 'Ativo', 'Duração', 'Ações'].map(h => (
                    <th key={h} className="text-left px-3 py-2">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((p) => (
                  <tr key={p.id} className={`border-t border-gray-50 hover:bg-gray-50 ${selected.has(p.id) ? 'bg-brand-50' : ''}`}>
                    <td className="px-3 py-2">
                      <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} />
                    </td>
                    <td className="px-3 py-2 font-medium">{p.projeto}</td>
                    <td className="px-3 py-2 font-mono text-xs">{p.protocolo}</td>
                    <td className="px-3 py-2 text-gray-600 max-w-32 truncate">{p.atividade}</td>
                    <td className="px-3 py-2 text-gray-500 text-xs max-w-28 truncate">{p.orgao_site_consultado}</td>
                    <td className="px-3 py-2"><span className="bg-brand-50 text-brand-900 text-xs px-2 py-0.5 rounded-full">{p.status}</span></td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{p.situacao ?? '-'}</td>
                    <td className="px-3 py-2">{p.ativo ? '✅' : '❌'}</td>
                    <td className="px-3 py-2">{p.duracao_dias ?? '-'}d</td>
                    <td className="px-3 py-2 flex gap-1">
                      <button onClick={() => queryMut.mutate(p.id)} title="Consultar" className="p-1 text-brand-700 hover:bg-brand-50 rounded">
                        <RefreshCw size={13} />
                      </button>
                      <button onClick={() => openEdit(p)} title="Editar" className="p-1 text-gray-600 hover:bg-gray-100 rounded">
                        <Pencil size={13} />
                      </button>
                      <button onClick={() => { if (confirm('Remover/inativar?')) delMut.mutate(p.id) }} title="Remover" className="p-1 text-red-500 hover:bg-red-50 rounded">
                        <Trash2 size={13} />
                      </button>
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
