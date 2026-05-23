import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Bot, User, Loader2 } from 'lucide-react'
import api from '../services/api'

export default function AgentChat() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Olá! Sou o assistente PratiFacil. Posso te ajudar a consultar protocolos, verificar status e muito mais. Como posso ajudar?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100)
  }, [open])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    const next = [...messages, userMsg]
    setMessages(next)
    setInput('')
    setLoading(true)

    try {
      const { data } = await api.post('/agent/chat', {
        messages: next.filter(m => m.role !== 'system'),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message || 'Erro desconhecido'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Ocorreu um erro ao processar sua mensagem: ${detail}. Tente novamente.`,
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(v => !v)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-ink text-lime shadow-pop flex items-center justify-center hover:bg-ink-2 transition-all"
        title="Assistente PratiFacil"
      >
        {open ? <X size={20} /> : <MessageCircle size={22} />}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-[360px] max-h-[560px] flex flex-col rounded-2xl shadow-pop bg-surface border border-line overflow-hidden">

          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-line bg-ink text-white">
            <div className="w-8 h-8 rounded-full bg-lime/20 flex items-center justify-center">
              <Bot size={16} className="text-lime" />
            </div>
            <div>
              <p className="text-sm font-semibold">Assistente PratiFacil</p>
              <p className="text-[11px] text-white/60">Powered by Ollama · Llama 3.2 3B</p>
            </div>
            <button onClick={() => setOpen(false)} className="ml-auto text-white/60 hover:text-white transition">
              <X size={16} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-ink text-lime' : 'bg-paper border border-line'}`}>
                  {msg.role === 'user' ? <User size={13} /> : <Bot size={13} className="text-muted" />}
                </div>
                <div className={`max-w-[80%] px-3 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-ink text-lime rounded-tr-sm'
                    : 'bg-paper border border-line text-ink rounded-tl-sm'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-2.5">
                <div className="w-7 h-7 rounded-full bg-paper border border-line flex items-center justify-center shrink-0">
                  <Bot size={13} className="text-muted" />
                </div>
                <div className="bg-paper border border-line rounded-2xl rounded-tl-sm px-3 py-2.5 flex items-center gap-1.5">
                  <Loader2 size={13} className="animate-spin text-muted" />
                  <span className="text-xs text-muted">Consultando...</span>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-line bg-paper">
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Pergunte sobre os protocolos…"
                className="flex-1 resize-none bg-surface border border-line-2 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ink/10 focus:border-ink/30 transition max-h-28 overflow-y-auto"
                style={{ minHeight: '42px' }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="w-10 h-10 rounded-xl bg-ink text-lime flex items-center justify-center hover:bg-ink-2 disabled:opacity-40 disabled:cursor-not-allowed transition shrink-0"
              >
                <Send size={15} />
              </button>
            </div>
            <p className="text-[10px] text-muted-faint mt-1.5 text-center">Enter para enviar · Shift+Enter para nova linha</p>
          </div>
        </div>
      )}
    </>
  )
}
