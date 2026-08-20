import { useEffect, useState } from 'react'
import type { MCQ, RecommendationResponse, TopicInput } from '../lib/types'
import { apiPost } from '../lib/api'
import { Loader2, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

type Props = {
  userId: string | null
  sessionId: string
  topicInput: TopicInput
  focusAreas: string[]
  questions: MCQ[]
  setQuestions: (qs: MCQ[]) => void
  answers: Record<number, 'A' | 'B' | 'C' | 'D'>
  setAnswers: (a: Record<number, 'A' | 'B' | 'C' | 'D'>) => void
  onSubmit: (rec: RecommendationResponse) => void
}

export default function TabAssessment({
  userId, sessionId, topicInput, focusAreas, questions, setQuestions, answers, setAnswers, onSubmit,
}: Props) {
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (questions.length === 0) {
      setLoading(true)
      apiPost<{ questions: MCQ[] }>('/api/assessment', {
        session_id: sessionId, topic_input: topicInput, focus_areas: focusAreas,
      })
        .then((r) => setQuestions(r.questions))
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const answered = Object.keys(answers).length
  const canSubmit = answered === questions.length && questions.length > 0

  async function submit() {
    setSubmitting(true)
    setError(null)
    try {
      const rec = await apiPost<RecommendationResponse>('/api/score', {
        user_id: userId,
        session_id: sessionId,
        topic_input: topicInput,
        focus_areas: focusAreas,
        questions,
        answers,
      })
      onSubmit(rec)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="glass p-16 flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        <p className="text-slate-300">Generating your personalized quiz…</p>
        <p className="text-xs text-slate-500">Focus areas: {focusAreas.join(', ') || '—'}</p>
      </div>
    )
  }

  if (error) return <div className="glass p-6 text-rose-400">{error}</div>

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <div className="glass p-6 flex items-center justify-between sticky top-24 z-10 backdrop-blur-xl">
        <div>
          <h2 className="text-lg font-semibold">10-question assessment</h2>
          <p className="text-sm text-slate-400">Answer all to unlock your personalized path.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-2xl font-bold">{answered}<span className="text-slate-500">/{questions.length}</span></div>
            <div className="text-xs text-slate-400">answered</div>
          </div>
          <div className="w-32 h-2 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
                 style={{ width: `${(answered / Math.max(1, questions.length)) * 100}%` }} />
          </div>
        </div>
      </div>

      {questions.map((q, i) => (
        <motion.div key={q.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="glass p-6">
          <div className="flex items-start gap-3 mb-4">
            <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-sm font-bold flex-shrink-0">
              {q.id}
            </span>
            <div className="flex-1">
              <p className="font-medium leading-relaxed">{q.question}</p>
              <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400">
                {q.difficulty}
              </span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-2 pl-11">
            {q.options.map((o) => {
              const active = answers[q.id] === o.key
              return (
                <button
                  key={o.key}
                  onClick={() => setAnswers({ ...answers, [q.id]: o.key })}
                  className={`text-left px-4 py-3 rounded-xl border transition flex items-start gap-3
                    ${active
                      ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border-indigo-400'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'}`}
                >
                  <span className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold flex-shrink-0
                    ${active ? 'bg-indigo-500 text-white' : 'bg-white/10 text-slate-300'}`}>
                    {active ? <CheckCircle2 className="w-4 h-4" /> : o.key}
                  </span>
                  <span className="text-sm">{o.text}</span>
                </button>
              )
            })}
          </div>
        </motion.div>
      ))}

      <div className="flex justify-end sticky bottom-4">
        <button className="btn-primary" disabled={!canSubmit || submitting} onClick={submit}>
          {submitting ? (<><Loader2 className="w-4 h-4 animate-spin inline mr-2" /> Analyzing…</>) : 'Submit & get my path'}
        </button>
      </div>
    </motion.div>
  )
}
