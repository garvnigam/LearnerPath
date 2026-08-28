import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, ChatResponse, TopicInput } from '../lib/types'
import { apiPost } from '../lib/api'
import { Send, Sparkles, Bot, User, MessageCircleMore } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import LoadingScene from './LoadingScene'

const THINKING_PHRASES = ['Thinking…', 'Weighing your goals…', 'Considering your pace…', 'Almost got it…']

function useCyclingText(active: boolean, phrases: string[], intervalMs = 1600) {
  const [i, setI] = useState(0)
  useEffect(() => {
    if (!active) { setI(0); return }
    const t = setInterval(() => setI((n) => (n + 1) % phrases.length), intervalMs)
    return () => clearInterval(t)
  }, [active, phrases, intervalMs])
  return phrases[i]
}

type Props = {
  userId: string | null
  sessionId: string
  topicInput: TopicInput
  messages: ChatMessage[]
  setMessages: (m: ChatMessage[]) => void
  onReady: (focus: string[]) => void
}

export default function TabChat({ userId, sessionId, topicInput, messages, setMessages, onReady }: Props) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const isFirstLoad = loading && messages.length === 0
  const thinkingText = useCyclingText(loading && !isFirstLoad, THINKING_PHRASES)

  useEffect(() => {
    if (messages.length !== 0) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await apiPost<ChatResponse>('/api/chat', {
          user_id: userId,
          session_id: sessionId,
          topic_input: topicInput,
          messages: [],
        })
        if (!cancelled) setMessages([res.message])
      } catch (e: any) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    if (!input.trim() || loading) return
    const next = [...messages, { role: 'user' as const, content: input.trim() }]
    setMessages(next)
    setInput('')
    setLoading(true)
    setError(null)
    try {
      const res = await apiPost<ChatResponse>('/api/chat', {
        user_id: userId,
        session_id: sessionId,
        topic_input: topicInput,
        messages: next,
      })
      setMessages([...next, res.message])
      if (res.ready_for_assessment) {
        setTimeout(() => onReady(res.focus_areas), 800)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass p-6 min-h-[560px] flex flex-col relative overflow-hidden">
      <div className="relative flex items-center gap-3 mb-4 pb-4 border-b border-white/10">
        <div className="w-9 h-9 rounded-md border border-amber-300/30 bg-amber-400/10 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-4 h-4 text-amber-300" />
        </div>
        <h2 className="text-lg font-display font-semibold">Let's narrow it down</h2>
        <span className="label-caps ml-auto hidden sm:inline-flex bg-white/5 border border-white/10 rounded-full px-3 py-1 normal-case">
          {topicInput.subjects.join(' • ')} · {topicInput.duration_months}mo · {topicInput.hours_per_day}h/day
        </span>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pr-2 mb-4">
        {isFirstLoad && (
          <LoadingScene
            title="Starting your conversation"
            icons={[Sparkles, MessageCircleMore, Bot]}
            messages={[
              `Looking at ${topicInput.subjects.join(', ')}…`,
              'Thinking of a good opening question…',
              'Tailoring it to your pace and goals…',
            ]}
          />
        )}
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-md border border-white/10 bg-white/5 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div className={`max-w-[75%] px-4 py-3 rounded-lg text-sm leading-relaxed
                ${m.role === 'user'
                  ? 'bg-amber-400/90 text-slate-950 rounded-br-sm'
                  : 'bg-white/5 border border-white/10 rounded-bl-sm'}`}
              >
                {m.content}
              </div>
              {m.role === 'user' && (
                <div className="w-8 h-8 rounded-md bg-white/10 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && !isFirstLoad && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3 items-center">
            <div className="relative w-8 h-8 flex-shrink-0 rounded-md border border-white/10 bg-white/5 flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-white/5 border border-white/10 px-4 py-3 rounded-lg rounded-bl-sm flex items-center gap-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <AnimatePresence mode="wait">
                <motion.span
                  key={thinkingText}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.25 }}
                  className="text-xs text-slate-400"
                >
                  {thinkingText}
                </motion.span>
              </AnimatePresence>
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <div className="text-sm text-rose-400 mb-2">{error}</div>}

      <div className="flex gap-2">
        <input
          className="input"
          placeholder="Type your reply…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          disabled={loading}
        />
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="btn-primary"
          onClick={send}
          disabled={loading || !input.trim()}
        >
          <Send className="w-4 h-4" />
        </motion.button>
      </div>
    </motion.div>
  )
}
